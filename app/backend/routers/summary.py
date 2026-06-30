from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("", response_model=schemas.SummaryOut)
def get_summary(db: Session = Depends(get_db)):
    year = datetime.utcnow().year

    total_bottles = db.query(func.sum(models.BottleInventory.quantity)).scalar() or 0
    total_wines = db.query(models.Wine).count()
    total_cellars = db.query(models.Cellar).count()
    total_zones = db.query(models.Zone).count()
    wishlist_count = db.query(models.Wishlist).filter(models.Wishlist.fulfilled_at == None).count()

    wines = db.query(models.Wine).all()
    ready = aging = past_peak = 0
    for w in wines:
        if w.drink_from and year < w.drink_from:
            aging += 1
        elif w.drink_until and year > w.drink_until:
            past_peak += 1
        elif w.drink_from or w.drink_until:
            ready += 1

    def alert_count(severity):
        return (
            db.query(models.AlertEvent)
            .filter(
                models.AlertEvent.severity == severity,
                models.AlertEvent.resolved_at == None,
            )
            .count()
        )

    return schemas.SummaryOut(
        total_bottles=total_bottles,
        total_wines=total_wines,
        total_cellars=total_cellars,
        total_zones=total_zones,
        wines_ready=ready,
        wines_aging=aging,
        wines_past_peak=past_peak,
        wishlist_count=wishlist_count,
        alerts_critical=alert_count("critical"),
        alerts_warning=alert_count("warning"),
        alerts_info=alert_count("info"),
    )


@router.get("/health")
def health():
    return {"status": "ok", "app": "Just Another Wine App", "version": "1.0.0"}
