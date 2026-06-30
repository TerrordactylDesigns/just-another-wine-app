from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

# ---------------------------------------------------------------------------
# Bottle Inventory
# ---------------------------------------------------------------------------

inventory_router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@inventory_router.get("", response_model=List[schemas.BottleInventoryOut])
def list_inventory(zone_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.BottleInventory)
    if zone_id:
        q = q.filter(models.BottleInventory.zone_id == zone_id)
    return q.all()


@inventory_router.post("", response_model=schemas.BottleInventoryOut, status_code=201)
def add_inventory(data: schemas.BottleInventoryCreate, db: Session = Depends(get_db)):
    item = models.BottleInventory(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@inventory_router.put("/{item_id}", response_model=schemas.BottleInventoryOut)
def update_inventory(item_id: int, data: schemas.BottleInventoryUpdate, db: Session = Depends(get_db)):
    item = db.query(models.BottleInventory).filter(models.BottleInventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    for k, v in data.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@inventory_router.delete("/{item_id}", status_code=204)
def delete_inventory(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.BottleInventory).filter(models.BottleInventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    db.delete(item)
    db.commit()


# ---------------------------------------------------------------------------
# Purchase History
# ---------------------------------------------------------------------------

purchases_router = APIRouter(prefix="/api/purchases", tags=["purchases"])


@purchases_router.post("", response_model=schemas.PurchaseOut, status_code=201)
def add_purchase(data: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    purchase = models.PurchaseHistory(**data.model_dump())
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@purchases_router.delete("/{purchase_id}", status_code=204)
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.query(models.PurchaseHistory).filter(models.PurchaseHistory.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    db.delete(purchase)
    db.commit()


# ---------------------------------------------------------------------------
# Consumption History
# ---------------------------------------------------------------------------

consumed_router = APIRouter(prefix="/api/consumed", tags=["consumed"])


@consumed_router.post("", response_model=schemas.ConsumptionOut, status_code=201)
def log_consumption(data: schemas.ConsumptionCreate, db: Session = Depends(get_db)):
    entry = models.ConsumptionHistory(**data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    # Decrement inventory
    inv = (
        db.query(models.BottleInventory)
        .filter(models.BottleInventory.wine_id == data.wine_id)
        .first()
    )
    if inv:
        inv.quantity = max(0, inv.quantity - data.quantity)
        db.commit()
    return entry


@consumed_router.delete("/{entry_id}", status_code=204)
def delete_consumption(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.ConsumptionHistory).filter(models.ConsumptionHistory.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Consumption entry not found")
    db.delete(entry)
    db.commit()
