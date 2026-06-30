from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/zones", tags=["zones"])


@router.get("", response_model=List[schemas.ZoneOut])
def list_zones(cellar_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.Zone)
    if cellar_id:
        q = q.filter(models.Zone.cellar_id == cellar_id)
    return q.order_by(models.Zone.name).all()


@router.post("", response_model=schemas.ZoneOut, status_code=201)
def create_zone(data: schemas.ZoneCreate, db: Session = Depends(get_db)):
    zone = models.Zone(**data.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get("/{zone_id}", response_model=schemas.ZoneOut)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.put("/{zone_id}", response_model=schemas.ZoneOut)
def update_zone(zone_id: int, data: schemas.ZoneUpdate, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    for k, v in data.model_dump().items():
        setattr(zone, k, v)
    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=204)
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()


@router.get("/{zone_id}/inventory")
def zone_inventory(zone_id: int, db: Session = Depends(get_db)):
    items = (
        db.query(models.BottleInventory)
        .filter(models.BottleInventory.zone_id == zone_id)
        .all()
    )
    return items


@router.get("/{zone_id}/summary")
def zone_summary(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    total_bottles = (
        db.query(func.sum(models.BottleInventory.quantity))
        .filter(models.BottleInventory.zone_id == zone_id)
        .scalar() or 0
    )
    sensor_count = db.query(models.Sensor).filter(models.Sensor.zone_id == zone_id).count()
    camera_count = db.query(models.Camera).filter(models.Camera.zone_id == zone_id).count()

    return {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "total_bottles": total_bottles,
        "sensor_count": sensor_count,
        "camera_count": camera_count,
    }
