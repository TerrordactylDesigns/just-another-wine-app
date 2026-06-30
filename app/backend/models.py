from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database import Base


# ---------------------------------------------------------------------------
# Cellars & Zones
# ---------------------------------------------------------------------------

class Cellar(Base):
    __tablename__ = "cellars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    location = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zones = relationship("Zone", back_populates="cellar", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    cellar_id = Column(Integer, ForeignKey("cellars.id"), nullable=False)
    name = Column(String(120), nullable=False)
    notes = Column(Text)
    target_temp_f = Column(Float)
    target_humidity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cellar = relationship("Cellar", back_populates="zones")
    inventory = relationship("BottleInventory", back_populates="zone")
    sensors = relationship("Sensor", back_populates="zone", cascade="all, delete-orphan")
    cameras = relationship("Camera", back_populates="zone", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Wines
# ---------------------------------------------------------------------------

class Wine(Base):
    __tablename__ = "wines"

    id = Column(Integer, primary_key=True, index=True)
    producer = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)
    vintage = Column(Integer)
    region = Column(String(200))
    grapes = Column(String(300))
    tasting_notes = Column(Text)
    drink_from = Column(Integer)   # year
    drink_until = Column(Integer)  # year
    external_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inventory = relationship("BottleInventory", back_populates="wine", cascade="all, delete-orphan")
    purchases = relationship("PurchaseHistory", back_populates="wine", cascade="all, delete-orphan")
    consumed = relationship("ConsumptionHistory", back_populates="wine", cascade="all, delete-orphan")
    images = relationship("WineImage", back_populates="wine", cascade="all, delete-orphan")


class BottleInventory(Base):
    __tablename__ = "bottle_inventory"

    id = Column(Integer, primary_key=True, index=True)
    wine_id = Column(Integer, ForeignKey("wines.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    condition = Column(String(50), default="good")  # good, damaged, unknown
    location_notes = Column(String(255))  # e.g. "Rack B, Shelf 3"
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    wine = relationship("Wine", back_populates="inventory")
    zone = relationship("Zone", back_populates="inventory")


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id = Column(Integer, primary_key=True, index=True)
    wine_id = Column(Integer, ForeignKey("wines.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_bottle = Column(Float)
    total_price = Column(Float)
    purchased_from = Column(String(200))
    purchase_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    wine = relationship("Wine", back_populates="purchases")


class ConsumptionHistory(Base):
    __tablename__ = "consumption_history"

    id = Column(Integer, primary_key=True, index=True)
    wine_id = Column(Integer, ForeignKey("wines.id"), nullable=False)
    quantity = Column(Integer, default=1)
    consumed_at = Column(DateTime, default=datetime.utcnow)
    occasion = Column(String(200))
    rating = Column(Integer)  # 1-100
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    wine = relationship("Wine", back_populates="consumed")


# ---------------------------------------------------------------------------
# Wine Images
# ---------------------------------------------------------------------------

class WineImage(Base):
    __tablename__ = "wine_images"

    id = Column(Integer, primary_key=True, index=True)
    wine_id = Column(Integer, ForeignKey("wines.id"), nullable=False)
    source_type = Column(String(20), default="upload")  # upload | url | scraped
    file_path = Column(String(500))
    external_url = Column(String(500))
    is_primary = Column(Boolean, default=False)
    label = Column(String(100))  # front label, back label, bottle, cellar
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    wine = relationship("Wine", back_populates="images")


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------

class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    producer = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)
    vintage = Column(Integer)
    region = Column(String(200))
    grapes = Column(String(300))
    notes = Column(Text)
    external_url = Column(String(500))
    target_price = Column(Float)
    priority = Column(Integer, default=3)  # 1=high 5=low
    fulfilled_at = Column(DateTime)
    fulfilled_wine_id = Column(Integer, ForeignKey("wines.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Sensor Types (registry)
# ---------------------------------------------------------------------------

class SensorType(Base):
    __tablename__ = "sensor_types"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False)
    label = Column(String(100), nullable=False)
    default_unit = Column(String(20))
    min_safe = Column(Float)
    max_safe = Column(Float)
    icon = Column(String(50))
    supports_alerts = Column(Boolean, default=True)

    sensors = relationship("Sensor", back_populates="sensor_type")


# ---------------------------------------------------------------------------
# Sensors & Readings
# ---------------------------------------------------------------------------

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    sensor_type_id = Column(Integer, ForeignKey("sensor_types.id"), nullable=False)
    name = Column(String(120), nullable=False)
    manufacturer = Column(String(120))
    model = Column(String(120))
    unit = Column(String(20))
    active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("Zone", back_populates="sensors")
    sensor_type = relationship("SensorType", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    sensor = relationship("Sensor", back_populates="readings")


# ---------------------------------------------------------------------------
# Cameras
# ---------------------------------------------------------------------------

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    name = Column(String(120), nullable=False)
    stream_type = Column(String(20), default="rtsp")  # rtsp|mjpeg|hls|snapshot|webrtc
    stream_url = Column(Text)       # stored encrypted
    snapshot_url = Column(Text)     # stored encrypted
    username = Column(String(200))
    password = Column(Text)         # stored encrypted
    enabled = Column(Boolean, default=True)
    manufacturer = Column(String(120))
    model = Column(String(120))
    resolution = Column(String(20))
    notes = Column(Text)
    last_seen_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zone = relationship("Zone", back_populates="cameras")
    snapshots = relationship("CameraSnapshot", back_populates="camera", cascade="all, delete-orphan")


class CameraSnapshot(Base):
    __tablename__ = "camera_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)

    camera = relationship("Camera", back_populates="snapshots")


# ---------------------------------------------------------------------------
# Alert System
# ---------------------------------------------------------------------------

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    domain = Column(String(30), nullable=False)       # sensor|wine|inventory|environmental|camera|system
    entity_type = Column(String(30))
    entity_id = Column(Integer, nullable=True)        # null = applies to all of this type
    condition_type = Column(String(60), nullable=False)
    threshold_low = Column(Float)
    threshold_high = Column(Float)
    duration_seconds = Column(Integer, default=0)
    severity = Column(String(10), default="warning")  # info|warning|critical
    enabled = Column(Boolean, default=True)
    cooldown_seconds = Column(Integer, default=3600)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("AlertEvent", back_populates="rule")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    entity_type = Column(String(30))
    entity_id = Column(Integer)
    severity = Column(String(10), nullable=False)
    title = Column(String(300), nullable=False)
    message = Column(Text)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))
    event_metadata = Column("metadata", JSON)

    rule = relationship("AlertRule", back_populates="events")


class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_type = Column(String(30), nullable=False)  # webhook|email|push
    config = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
