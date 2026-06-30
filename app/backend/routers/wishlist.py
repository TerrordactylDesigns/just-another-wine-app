from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


@router.get("", response_model=List[schemas.WishlistOut])
def list_wishlist(show_fulfilled: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Wishlist)
    if not show_fulfilled:
        q = q.filter(models.Wishlist.fulfilled_at == None)
    return q.order_by(models.Wishlist.priority, models.Wishlist.producer).all()


@router.post("", response_model=schemas.WishlistOut, status_code=201)
def create_wishlist_item(data: schemas.WishlistCreate, db: Session = Depends(get_db)):
    item = models.Wishlist(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.WishlistOut)
def get_wishlist_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Wishlist).filter(models.Wishlist.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return item


@router.put("/{item_id}", response_model=schemas.WishlistOut)
def update_wishlist_item(item_id: int, data: schemas.WishlistUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Wishlist).filter(models.Wishlist.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    for k, v in data.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_wishlist_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Wishlist).filter(models.Wishlist.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(item)
    db.commit()


@router.post("/{item_id}/fulfill", response_model=schemas.WineOut)
def fulfill_wishlist_item(
    item_id: int,
    data: schemas.WishlistFulfill,
    db: Session = Depends(get_db),
):
    """Promote a wishlist entry into a full wine record in a zone."""
    item = db.query(models.Wishlist).filter(models.Wishlist.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    if item.fulfilled_at:
        raise HTTPException(status_code=400, detail="Wishlist item already fulfilled")

    zone = db.query(models.Zone).filter(models.Zone.id == data.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    # 1. Create wine record
    wine = models.Wine(
        producer=item.producer,
        name=item.name,
        vintage=item.vintage,
        region=item.region,
        grapes=item.grapes,
        tasting_notes=item.notes,
        external_url=item.external_url,
    )
    db.add(wine)
    db.flush()  # get wine.id

    # 2. Create inventory record
    inv = models.BottleInventory(
        wine_id=wine.id,
        zone_id=data.zone_id,
        quantity=data.quantity,
    )
    db.add(inv)

    # 3. Optionally record purchase
    if data.purchase_price or data.purchased_from:
        purchase = models.PurchaseHistory(
            wine_id=wine.id,
            quantity=data.quantity,
            price_per_bottle=data.purchase_price,
            total_price=(data.purchase_price * data.quantity) if data.purchase_price else None,
            purchased_from=data.purchased_from,
            purchase_date=data.purchase_date or datetime.utcnow(),
        )
        db.add(purchase)

    # 4. Mark wishlist item fulfilled
    item.fulfilled_at = datetime.utcnow()
    item.fulfilled_wine_id = wine.id

    db.commit()
    db.refresh(wine)
    return wine
