"""
Unified alert engine for Just Another Wine App.
Evaluates all alert domains and fires/resolves AlertEvents.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import models


OFFLINE_THRESHOLD_MINUTES = 30


def fire_alert(db: Session, rule: models.AlertRule, entity_type: str, entity_id: int, title: str, message: str, metadata: dict = None):
    """Create an alert event if not already active and cooldown has passed."""
    # Check for existing unresolved event for this rule+entity
    existing = (
        db.query(models.AlertEvent)
        .filter(
            models.AlertEvent.rule_id == rule.id,
            models.AlertEvent.entity_id == entity_id,
            models.AlertEvent.resolved_at == None,
        )
        .first()
    )
    if existing:
        return  # Already firing

    # Check cooldown — don't re-fire if resolved recently
    cooldown_ago = datetime.utcnow() - timedelta(seconds=rule.cooldown_seconds)
    recent = (
        db.query(models.AlertEvent)
        .filter(
            models.AlertEvent.rule_id == rule.id,
            models.AlertEvent.entity_id == entity_id,
            models.AlertEvent.triggered_at >= cooldown_ago,
        )
        .first()
    )
    if recent:
        return

    event = models.AlertEvent(
        rule_id=rule.id,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=rule.severity,
        title=title,
        message=message,
        triggered_at=datetime.utcnow(),
        event_metadata=metadata or {},
    )
    db.add(event)
    db.commit()


def resolve_alerts_for(db: Session, rule_id: int, entity_id: int):
    """Resolve any open alerts for a rule+entity when condition clears."""
    events = (
        db.query(models.AlertEvent)
        .filter(
            models.AlertEvent.rule_id == rule_id,
            models.AlertEvent.entity_id == entity_id,
            models.AlertEvent.resolved_at == None,
        )
        .all()
    )
    for event in events:
        event.resolved_at = datetime.utcnow()
    db.commit()


# ---------------------------------------------------------------------------
# Sensor Alerts
# ---------------------------------------------------------------------------

def evaluate_sensor_reading(db: Session, sensor_id: int, value: float):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor:
        return

    rules = (
        db.query(models.AlertRule)
        .filter(
            models.AlertRule.domain == "sensor",
            models.AlertRule.enabled == True,
            (models.AlertRule.entity_id == sensor_id) | (models.AlertRule.entity_id == None),
        )
        .all()
    )

    for rule in rules:
        breached = False
        if rule.condition_type == "sensor.threshold.high" and rule.threshold_high is not None:
            breached = value > rule.threshold_high
        elif rule.condition_type == "sensor.threshold.low" and rule.threshold_low is not None:
            breached = value < rule.threshold_low
        elif rule.condition_type == "sensor.out_of_range":
            breached = (
                (rule.threshold_low is not None and value < rule.threshold_low) or
                (rule.threshold_high is not None and value > rule.threshold_high)
            )

        if breached:
            fire_alert(
                db, rule, "sensor", sensor_id,
                title=f"Sensor '{sensor.name}' alert: {rule.condition_type}",
                message=f"Current value: {value} {sensor.unit or ''}",
                metadata={"value": value, "sensor_name": sensor.name},
            )
        else:
            resolve_alerts_for(db, rule.id, sensor_id)


def evaluate_rapid_change(db: Session, sensor_id: int, value: float, window_seconds: int = 1800):
    """Check if value changed rapidly in the last window."""
    since = datetime.utcnow() - timedelta(seconds=window_seconds)
    oldest = (
        db.query(models.SensorReading)
        .filter(
            models.SensorReading.sensor_id == sensor_id,
            models.SensorReading.recorded_at >= since,
        )
        .order_by(models.SensorReading.recorded_at.asc())
        .first()
    )
    if not oldest:
        return

    delta = abs(value - oldest.value)
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()

    rules = (
        db.query(models.AlertRule)
        .filter(
            models.AlertRule.domain == "sensor",
            models.AlertRule.condition_type.in_(["sensor.rapid_change"]),
            models.AlertRule.enabled == True,
            (models.AlertRule.entity_id == sensor_id) | (models.AlertRule.entity_id == None),
        )
        .all()
    )
    for rule in rules:
        if rule.threshold_high is not None and delta > rule.threshold_high:
            fire_alert(
                db, rule, "sensor", sensor_id,
                title=f"Rapid change on '{sensor.name}'",
                message=f"Changed {delta:.1f} {sensor.unit or ''} in {window_seconds//60} minutes",
                metadata={"delta": delta, "from": oldest.value, "to": value},
            )


# ---------------------------------------------------------------------------
# Zone / Environmental Alerts
# ---------------------------------------------------------------------------

def evaluate_zone_environment(db: Session, zone_id: int):
    """Cross-sensor zone-level alerts (sustained breach, sensor disagreement)."""
    sensors = db.query(models.Sensor).filter(models.Sensor.zone_id == zone_id, models.Sensor.active == True).all()
    if not sensors:
        return

    rules = (
        db.query(models.AlertRule)
        .filter(
            models.AlertRule.domain == "environmental",
            models.AlertRule.enabled == True,
            (models.AlertRule.entity_id == zone_id) | (models.AlertRule.entity_id == None),
        )
        .all()
    )

    for rule in rules:
        if "sustained" in rule.condition_type and rule.duration_seconds:
            # Check if all temp/humidity sensors in zone have been out of range
            since = datetime.utcnow() - timedelta(seconds=rule.duration_seconds)
            for sensor in sensors:
                readings = (
                    db.query(models.SensorReading)
                    .filter(
                        models.SensorReading.sensor_id == sensor.id,
                        models.SensorReading.recorded_at >= since,
                    )
                    .all()
                )
                if not readings:
                    continue
                avg = sum(r.value for r in readings) / len(readings)
                breached = False
                if "temp_high" in rule.condition_type and rule.threshold_high:
                    breached = avg > rule.threshold_high
                elif "temp_low" in rule.condition_type and rule.threshold_low:
                    breached = avg < rule.threshold_low
                elif "humidity_high" in rule.condition_type and rule.threshold_high:
                    breached = avg > rule.threshold_high
                elif "humidity_low" in rule.condition_type and rule.threshold_low:
                    breached = avg < rule.threshold_low

                zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
                if breached:
                    fire_alert(
                        db, rule, "zone", zone_id,
                        title=f"Sustained condition breach in zone '{zone.name}'",
                        message=f"Average {avg:.1f} for {rule.duration_seconds//60} minutes",
                        metadata={"avg": avg, "zone_name": zone.name},
                    )
                else:
                    resolve_alerts_for(db, rule.id, zone_id)


# ---------------------------------------------------------------------------
# Wine / Inventory Alerts
# ---------------------------------------------------------------------------

def evaluate_wine_windows(db: Session):
    """Daily job: drinking windows, aging targets, low stock."""
    year = datetime.utcnow().year
    wines = db.query(models.Wine).all()

    rules = (
        db.query(models.AlertRule)
        .filter(
            models.AlertRule.domain.in_(["wine", "inventory"]),
            models.AlertRule.enabled == True,
        )
        .all()
    )

    for wine in wines:
        total_bottles = (
            db.query(func.sum(models.BottleInventory.quantity))
            .filter(models.BottleInventory.wine_id == wine.id)
            .scalar() or 0
        )

        for rule in rules:
            if rule.entity_id and rule.entity_id != wine.id:
                continue

            if rule.condition_type == "wine.past_peak":
                if wine.drink_until and year > wine.drink_until:
                    fire_alert(
                        db, rule, "wine", wine.id,
                        title=f"'{wine.producer} {wine.name}' is past peak",
                        message=f"Drinking window ended {year - wine.drink_until} year(s) ago",
                        metadata={"drink_until": wine.drink_until},
                    )
                else:
                    resolve_alerts_for(db, rule.id, wine.id)

            elif rule.condition_type == "wine.entering_window":
                days_threshold = int(rule.threshold_high or 365)
                if wine.drink_from:
                    days_until = (datetime(wine.drink_from, 1, 1) - datetime.utcnow()).days
                    if 0 < days_until <= days_threshold:
                        fire_alert(
                            db, rule, "wine", wine.id,
                            title=f"'{wine.producer} {wine.name}' entering drinking window soon",
                            message=f"Ready to drink in approximately {days_until} days",
                            metadata={"days_until": days_until, "drink_from": wine.drink_from},
                        )

            elif rule.condition_type == "wine.low_stock":
                threshold = int(rule.threshold_low or 2)
                if 0 < total_bottles <= threshold:
                    fire_alert(
                        db, rule, "wine", wine.id,
                        title=f"Low stock: '{wine.producer} {wine.name}'",
                        message=f"Only {total_bottles} bottle(s) remaining",
                        metadata={"bottles": total_bottles},
                    )
                else:
                    resolve_alerts_for(db, rule.id, wine.id)


# ---------------------------------------------------------------------------
# Camera Health Alerts
# ---------------------------------------------------------------------------

def evaluate_camera_health(db: Session):
    cameras = db.query(models.Camera).filter(models.Camera.enabled == True).all()
    rules = (
        db.query(models.AlertRule)
        .filter(
            models.AlertRule.domain == "camera",
            models.AlertRule.enabled == True,
        )
        .all()
    )

    for camera in cameras:
        for rule in rules:
            if rule.entity_id and rule.entity_id != camera.id:
                continue

            if rule.condition_type == "camera.offline":
                threshold_minutes = int(rule.threshold_high or OFFLINE_THRESHOLD_MINUTES)
                if camera.last_seen_at:
                    minutes_ago = (datetime.utcnow() - camera.last_seen_at).total_seconds() / 60
                    if minutes_ago > threshold_minutes:
                        fire_alert(
                            db, rule, "camera", camera.id,
                            title=f"Camera '{camera.name}' appears offline",
                            message=f"Last seen {int(minutes_ago)} minutes ago",
                            metadata={"last_seen_at": str(camera.last_seen_at)},
                        )
                    else:
                        resolve_alerts_for(db, rule.id, camera.id)


# ---------------------------------------------------------------------------
# Sensor Offline Alerts
# ---------------------------------------------------------------------------

def evaluate_sensor_offline(db: Session):
    sensors = db.query(models.Sensor).filter(models.Sensor.active == True).all()
    rules = (
        db.query(models.AlertRule)
        .filter(
            models.AlertRule.condition_type.in_(["sensor.offline", "system.sensor_offline"]),
            models.AlertRule.enabled == True,
        )
        .all()
    )

    for sensor in sensors:
        for rule in rules:
            if rule.entity_id and rule.entity_id != sensor.id:
                continue
            threshold_minutes = int(rule.threshold_high or OFFLINE_THRESHOLD_MINUTES)
            if sensor.last_seen_at:
                minutes_ago = (datetime.utcnow() - sensor.last_seen_at).total_seconds() / 60
                if minutes_ago > threshold_minutes:
                    fire_alert(
                        db, rule, "sensor", sensor.id,
                        title=f"Sensor '{sensor.name}' not reporting",
                        message=f"No readings in {int(minutes_ago)} minutes",
                        metadata={"last_seen_at": str(sensor.last_seen_at)},
                    )
                else:
                    resolve_alerts_for(db, rule.id, sensor.id)


# ---------------------------------------------------------------------------
# System Health Alerts
# ---------------------------------------------------------------------------

def evaluate_system_health(db: Session):
    import os
    import shutil

    rules = (
        db.query(models.AlertRule)
        .filter(
            models.AlertRule.domain == "system",
            models.AlertRule.enabled == True,
        )
        .all()
    )

    for rule in rules:
        if rule.condition_type == "system.low_disk":
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024 ** 3)
            threshold_gb = rule.threshold_low or 1.0
            if free_gb < threshold_gb:
                fire_alert(
                    db, rule, "system", 0,
                    title="Low disk space",
                    message=f"Only {free_gb:.1f} GB free",
                    metadata={"free_gb": free_gb},
                )
            else:
                resolve_alerts_for(db, rule.id, 0)

        elif rule.condition_type == "system.readings_retention":
            count = db.query(models.SensorReading).count()
            threshold = int(rule.threshold_high or 1_000_000)
            if count > threshold:
                fire_alert(
                    db, rule, "system", 0,
                    title="Sensor readings table is large",
                    message=f"{count:,} rows — consider running retention cleanup",
                    metadata={"row_count": count},
                )
