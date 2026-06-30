from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/wines", tags=["wines"])


def _wine_status(wine: models.Wine) -> str:
    year = datetime.utcnow().year
    if wine.drink_from and year < wine.drink_from:
        return "aging"
    if wine.drink_until and year > wine.drink_until:
        return "past_peak"
    if wine.drink_from or wine.drink_until:
        return "ready"
    return "unknown"


@router.get("", response_model=List[schemas.WineOut])
def list_wines(
    status: Optional[str] = Query(None, description="aging|ready|past_peak|unknown"),
    zone_id: Optional[int] = None,
    cellar_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Wine)

    if zone_id:
        q = q.join(models.BottleInventory).filter(models.BottleInventory.zone_id == zone_id)
    if cellar_id:
        q = (
            q.join(models.BottleInventory)
            .join(models.Zone)
            .filter(models.Zone.cellar_id == cellar_id)
        )

    wines = q.order_by(models.Wine.producer, models.Wine.name).all()

    if status:
        wines = [w for w in wines if _wine_status(w) == status]

    return wines


@router.post("", response_model=schemas.WineOut, status_code=201)
def create_wine(data: schemas.WineCreate, db: Session = Depends(get_db)):
    wine = models.Wine(**data.model_dump())
    db.add(wine)
    db.commit()
    db.refresh(wine)
    return wine


@router.get("/{wine_id}", response_model=schemas.WineOut)
def get_wine(wine_id: int, db: Session = Depends(get_db)):
    wine = db.query(models.Wine).filter(models.Wine.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine


@router.put("/{wine_id}", response_model=schemas.WineOut)
def update_wine(wine_id: int, data: schemas.WineUpdate, db: Session = Depends(get_db)):
    wine = db.query(models.Wine).filter(models.Wine.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wine not found")
    for k, v in data.model_dump().items():
        setattr(wine, k, v)
    db.commit()
    db.refresh(wine)
    return wine


@router.delete("/{wine_id}", status_code=204)
def delete_wine(wine_id: int, db: Session = Depends(get_db)):
    wine = db.query(models.Wine).filter(models.Wine.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wine not found")
    db.delete(wine)
    db.commit()


@router.get("/{wine_id}/inventory", response_model=List[schemas.BottleInventoryOut])
def wine_inventory(wine_id: int, db: Session = Depends(get_db)):
    return db.query(models.BottleInventory).filter(models.BottleInventory.wine_id == wine_id).all()


@router.get("/{wine_id}/purchases", response_model=List[schemas.PurchaseOut])
def wine_purchases(wine_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.PurchaseHistory)
        .filter(models.PurchaseHistory.wine_id == wine_id)
        .order_by(models.PurchaseHistory.purchase_date.desc())
        .all()
    )


@router.get("/{wine_id}/consumed", response_model=List[schemas.ConsumptionOut])
def wine_consumed(wine_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ConsumptionHistory)
        .filter(models.ConsumptionHistory.wine_id == wine_id)
        .order_by(models.ConsumptionHistory.consumed_at.desc())
        .all()
    )


@router.get("/{wine_id}/images", response_model=List[schemas.WineImageOut])
def wine_images(wine_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.WineImage)
        .filter(models.WineImage.wine_id == wine_id)
        .order_by(models.WineImage.display_order)
        .all()
    )
