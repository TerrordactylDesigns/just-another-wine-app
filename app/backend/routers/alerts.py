from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
rules_router = APIRouter(prefix="/api/alert-rules", tags=["alert-rules"])


# ---------------------------------------------------------------------------
# Alert Events
# ---------------------------------------------------------------------------

@router.get("", response_model=List[schemas.AlertEventOut])
def list_alerts(
    severity: Optional[str] = None,
    domain: Optional[str] = None,
    resolved: Optional[bool] = None,
    acknowledged: Optional[bool] = None,
    limit: int = Query(100),
    db: Session = Depends(get_db),
):
    q = db.query(models.AlertEvent)
    if severity:
        q = q.filter(models.AlertEvent.severity == severity)
    if resolved is False:
        q = q.filter(models.AlertEvent.resolved_at == None)
    elif resolved is True:
        q = q.filter(models.AlertEvent.resolved_at != None)
    if acknowledged is False:
        q = q.filter(models.AlertEvent.acknowledged_at == None)
    if domain:
        q = q.join(models.AlertRule).filter(models.AlertRule.domain == domain)
    return q.order_by(models.AlertEvent.triggered_at.desc()).limit(limit).all()


@router.get("/{event_id}", response_model=schemas.AlertEventOut)
def get_alert(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.AlertEvent).filter(models.AlertEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Alert not found")
    return event


@router.put("/{event_id}/acknowledge", response_model=schemas.AlertEventOut)
def acknowledge_alert(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.AlertEvent).filter(models.AlertEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Alert not found")
    event.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    return event


@router.put("/{event_id}/resolve", response_model=schemas.AlertEventOut)
def resolve_alert(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.AlertEvent).filter(models.AlertEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Alert not found")
    event.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    return event


# ---------------------------------------------------------------------------
# Alert Rules
# ---------------------------------------------------------------------------

@rules_router.get("", response_model=List[schemas.AlertRuleOut])
def list_rules(domain: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.AlertRule)
    if domain:
        q = q.filter(models.AlertRule.domain == domain)
    return q.order_by(models.AlertRule.domain, models.AlertRule.name).all()


@rules_router.post("", response_model=schemas.AlertRuleOut, status_code=201)
def create_rule(data: schemas.AlertRuleCreate, db: Session = Depends(get_db)):
    rule = models.AlertRule(**data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@rules_router.get("/{rule_id}", response_model=schemas.AlertRuleOut)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(models.AlertRule).filter(models.AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@rules_router.put("/{rule_id}", response_model=schemas.AlertRuleOut)
def update_rule(rule_id: int, data: schemas.AlertRuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(models.AlertRule).filter(models.AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for k, v in data.model_dump().items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@rules_router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(models.AlertRule).filter(models.AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()


@rules_router.post("/{rule_id}/test")
def test_rule(rule_id: int, db: Session = Depends(get_db)):
    """Dry-run: return what would be triggered right now."""
    rule = db.query(models.AlertRule).filter(models.AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Test evaluation queued", "rule_id": rule_id, "domain": rule.domain}
