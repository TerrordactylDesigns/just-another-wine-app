"""Seed the sensor_types registry with built-in supported sensor types."""
from database import SessionLocal
import models

SENSOR_TYPES = [
    dict(slug="temperature", label="Temperature", default_unit="°F", min_safe=45, max_safe=65, icon="mdi:thermometer"),
    dict(slug="humidity", label="Humidity", default_unit="% RH", min_safe=50, max_safe=80, icon="mdi:water-percent"),
    dict(slug="light_level", label="Light Level", default_unit="lux", min_safe=0, max_safe=50, icon="mdi:brightness-6"),
    dict(slug="vibration", label="Vibration", default_unit="mm/s", min_safe=0, max_safe=1, icon="mdi:vibrate"),
    dict(slug="co2", label="CO2", default_unit="ppm", min_safe=300, max_safe=1000, icon="mdi:molecule-co2"),
    dict(slug="barometric_pressure", label="Barometric Pressure", default_unit="hPa", min_safe=980, max_safe=1050, icon="mdi:gauge"),
]


def seed_sensor_types():
    db = SessionLocal()
    try:
        existing = {t.slug for t in db.query(models.SensorType).all()}
        for st in SENSOR_TYPES:
            if st["slug"] not in existing:
                db.add(models.SensorType(**st, supports_alerts=True))
        db.commit()
    finally:
        db.close()
