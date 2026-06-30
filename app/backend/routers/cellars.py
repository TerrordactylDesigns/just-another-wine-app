from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/cellars", tags=["cellars"])


@router.get("", response_model=List[schemas.CellarOut])
def list_cellars(db: Session = Depends(get_db)):
    return db.query(models.Cellar).order_by(models.Cellar.name).all()


@router.post("", response_model=schemas.CellarOut, status_code=201)
def create_cellar(data: schemas.CellarCreate, db: Session = Depends(get_db)):
    cellar = models.Cellar(**data.model_dump())
    db.add(cellar)
    db.commit()
    db.refresh(cellar)
    return cellar


@router.get("/{cellar_id}", response_model=schemas.CellarOut)
def get_cellar(cellar_id: int, db: Session = Depends(get_db)):
    cellar = db.query(models.Cellar).filter(models.Cellar.id == cellar_id).first()
    if not cellar:
        raise HTTPException(status_code=404, detail="Cellar not found")
    return cellar


@router.put("/{cellar_id}", response_model=schemas.CellarOut)
def update_cellar(cellar_id: int, data: schemas.CellarUpdate, db: Session = Depends(get_db)):
    cellar = db.query(models.Cellar).filter(models.Cellar.id == cellar_id).first()
    if not cellar:
        raise HTTPException(status_code=404, detail="Cellar not found")
    for k, v in data.model_dump().items():
        setattr(cellar, k, v)
    db.commit()
    db.refresh(cellar)
    return cellar


@router.delete("/{cellar_id}", status_code=204)
def delete_cellar(cellar_id: int, db: Session = Depends(get_db)):
    cellar = db.query(models.Cellar).filter(models.Cellar.id == cellar_id).first()
    if not cellar:
        raise HTTPException(status_code=404, detail="Cellar not found")
    db.delete(cellar)
    db.commit()


@router.get("/{cellar_id}/zones", response_model=List[schemas.ZoneOut])
def list_cellar_zones(cellar_id: int, db: Session = Depends(get_db)):
    return db.query(models.Zone).filter(models.Zone.cellar_id == cellar_id).all()
