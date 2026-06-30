from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field


# ---------------------------------------------------------------------------
# Cellar
# ---------------------------------------------------------------------------

class CellarBase(BaseModel):
    name: str
    location: Optional[str] = None
    notes: Optional[str] = None

class CellarCreate(CellarBase): pass

class CellarUpdate(CellarBase): pass

class CellarOut(CellarBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Zone
# ---------------------------------------------------------------------------

class ZoneBase(BaseModel):
    name: str
    cellar_id: int
    notes: Optional[str] = None
    target_temp_f: Optional[float] = None
    target_humidity: Optional[float] = None

class ZoneCreate(ZoneBase): pass
class ZoneUpdate(ZoneBase): pass

class ZoneOut(ZoneBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Wine
# ---------------------------------------------------------------------------

class WineBase(BaseModel):
    producer: str
    name: str
    vintage: Optional[int] = None
    region: Optional[str] = None
    grapes: Optional[str] = None
    tasting_notes: Optional[str] = None
    drink_from: Optional[int] = None
    drink_until: Optional[int] = None
    external_url: Optional[str] = None

class WineCreate(WineBase): pass
class WineUpdate(WineBase): pass

class WineOut(WineBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Bottle Inventory
# ---------------------------------------------------------------------------

class BottleInventoryBase(BaseModel):
    wine_id: int
    zone_id: int
    quantity: int = 1
    condition: Optional[str] = "good"
    location_notes: Optional[str] = None

class BottleInventoryCreate(BottleInventoryBase): pass
class BottleInventoryUpdate(BottleInventoryBase): pass

class BottleInventoryOut(BottleInventoryBase):
    id: int
    added_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Purchase History
# ---------------------------------------------------------------------------

class PurchaseBase(BaseModel):
    wine_id: int
    quantity: int
    price_per_bottle: Optional[float] = None
    total_price: Optional[float] = None
    purchased_from: Optional[str] = None
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None

class PurchaseCreate(PurchaseBase): pass

class PurchaseOut(PurchaseBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Consumption History
# ---------------------------------------------------------------------------

class ConsumptionBase(BaseModel):
    wine_id: int
    quantity: int = 1
    consumed_at: Optional[datetime] = None
    occasion: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None

class ConsumptionCreate(ConsumptionBase): pass

class ConsumptionOut(ConsumptionBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Wine Image
# ---------------------------------------------------------------------------

class WineImageOut(BaseModel):
    id: int
    wine_id: int
    source_type: str
    file_path: Optional[str] = None
    external_url: Optional[str] = None
    is_primary: bool
    label: Optional[str] = None
    display_order: int
    created_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------

class WishlistBase(BaseModel):
    producer: str
    name: str
    vintage: Optional[int] = None
    region: Optional[str] = None
    grapes: Optional[str] = None
    notes: Optional[str] = None
    external_url: Optional[str] = None
    target_price: Optional[float] = None
    priority: Optional[int] = 3

class WishlistCreate(WishlistBase): pass
class WishlistUpdate(WishlistBase): pass

class WishlistFulfill(BaseModel):
    zone_id: int
    quantity: int = 1
    purchase_price: Optional[float] = None
    purchase_date: Optional[datetime] = None
    purchased_from: Optional[str] = None

class WishlistOut(WishlistBase):
    id: int
    fulfilled_at: Optional[datetime] = None
    fulfilled_wine_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Sensor Type
# ---------------------------------------------------------------------------

class SensorTypeOut(BaseModel):
    id: int
    slug: str
    label: str
    default_unit: Optional[str] = None
    min_safe: Optional[float] = None
    max_safe: Optional[float] = None
    icon: Optional[str] = None
    supports_alerts: bool
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Sensor
# ---------------------------------------------------------------------------

class SensorBase(BaseModel):
    zone_id: int
    sensor_type_id: int
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    unit: Optional[str] = None
    active: bool = True

class SensorCreate(SensorBase): pass
class SensorUpdate(SensorBase): pass

class SensorOut(SensorBase):
    id: int
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Sensor Reading
# ---------------------------------------------------------------------------

class SensorReadingCreate(BaseModel):
    sensor_id: int
    value: float
    recorded_at: Optional[datetime] = None

class SensorReadingOut(BaseModel):
    id: int
    sensor_id: int
    value: float
    recorded_at: datetime
    class Config: from_attributes = True

class SensorReadingSummary(BaseModel):
    sensor_id: int
    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]
    latest_value: Optional[float]
    latest_at: Optional[datetime]
    count: int


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

class CameraBase(BaseModel):
    zone_id: int
    name: str
    stream_type: str = "rtsp"
    stream_url: Optional[str] = None
    snapshot_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: bool = True
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None

class CameraCreate(CameraBase): pass
class CameraUpdate(CameraBase): pass

class CameraOut(BaseModel):
    id: int
    zone_id: int
    name: str
    stream_type: str
    enabled: bool
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    # stream_url intentionally omitted — credentials never returned raw
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Alert Rule
# ---------------------------------------------------------------------------

class AlertRuleBase(BaseModel):
    name: str
    domain: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    condition_type: str
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    duration_seconds: int = 0
    severity: str = "warning"
    enabled: bool = True
    cooldown_seconds: int = 3600

class AlertRuleCreate(AlertRuleBase): pass
class AlertRuleUpdate(AlertRuleBase): pass

class AlertRuleOut(AlertRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# ---------------------------------------------------------------------------
# Alert Event
# ---------------------------------------------------------------------------

class AlertEventOut(BaseModel):
    id: int
    rule_id: int
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    severity: str
    title: str
    message: Optional[str] = None
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, validation_alias="event_metadata", serialization_alias="metadata")

    class Config:
        from_attributes = True
        populate_by_name = True


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class SummaryOut(BaseModel):
    total_bottles: int
    total_wines: int
    total_cellars: int
    total_zones: int
    wines_ready: int
    wines_aging: int
    wines_past_peak: int
    wishlist_count: int
    alerts_critical: int
    alerts_warning: int
    alerts_info: int
