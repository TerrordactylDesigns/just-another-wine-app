from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/sensors", tags=["sensors"])

types_router = APIRouter(prefix="/api/sensor-types", tags=["sensor-types"])


@types_router.get("", response_model=List[schemas.SensorTypeOut])
def list_sensor_types(db: Session = Depends(get_db)):
    return db.query(models.SensorType).all()


@router.get("", response_model=List[schemas.SensorOut])
def list_sensors(zone_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(models.Sensor)
    if zone_id:
        q = q.filter(models.Sensor.zone_id == zone_id)
    return q.order_by(models.Sensor.name).all()


@router.post("", response_model=schemas.SensorOut, status_code=201)
def create_sensor(data: schemas.SensorCreate, db: Session = Depends(get_db)):
    sensor = models.Sensor(**data.model_dump())
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


@router.get("/{sensor_id}", response_model=schemas.SensorOut)
def get_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


@router.put("/{sensor_id}", response_model=schemas.SensorOut)
def update_sensor(sensor_id: int, data: schemas.SensorUpdate, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    for k, v in data.model_dump().items():
        setattr(sensor, k, v)
    db.commit()
    db.refresh(sensor)
    return sensor


@router.delete("/{sensor_id}", status_code=204)
def delete_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    db.delete(sensor)
    db.commit()


@router.post("/{sensor_id}/readings", response_model=schemas.SensorReadingOut, status_code=201)
def ingest_reading(sensor_id: int, data: schemas.SensorReadingCreate, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    reading = models.SensorReading(
        sensor_id=sensor_id,
        value=data.value,
        recorded_at=data.recorded_at or datetime.utcnow(),
    )
    db.add(reading)
    sensor.last_seen_at = datetime.utcnow()
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/{sensor_id}/readings", response_model=List[schemas.SensorReadingOut])
def get_readings(
    sensor_id: int,
    hours: int = Query(24, description="Hours of history to return"),
    limit: int = Query(500),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(models.SensorReading)
        .filter(
            models.SensorReading.sensor_id == sensor_id,
            models.SensorReading.recorded_at >= since,
        )
        .order_by(desc(models.SensorReading.recorded_at))
        .limit(limit)
        .all()
    )


@router.get("/{sensor_id}/readings/latest", response_model=schemas.SensorReadingOut)
def latest_reading(sensor_id: int, db: Session = Depends(get_db)):
    reading = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.sensor_id == sensor_id)
        .order_by(desc(models.SensorReading.recorded_at))
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")
    return reading


@router.get("/{sensor_id}/readings/summary", response_model=schemas.SensorReadingSummary)
def readings_summary(
    sensor_id: int,
    hours: int = Query(24),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=hours)
    result = (
        db.query(
            func.min(models.SensorReading.value),
            func.max(models.SensorReading.value),
            func.avg(models.SensorReading.value),
            func.count(models.SensorReading.id),
        )
        .filter(
            models.SensorReading.sensor_id == sensor_id,
            models.SensorReading.recorded_at >= since,
        )
        .first()
    )
    latest = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.sensor_id == sensor_id)
        .order_by(desc(models.SensorReading.recorded_at))
        .first()
    )
    return schemas.SensorReadingSummary(
        sensor_id=sensor_id,
        min_value=result[0],
        max_value=result[1],
        avg_value=round(result[2], 2) if result[2] else None,
        latest_value=latest.value if latest else None,
        latest_at=latest.recorded_at if latest else None,
        count=result[3] or 0,
    )
