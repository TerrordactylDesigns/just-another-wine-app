"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cellars",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "zones",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("cellar_id", sa.Integer, sa.ForeignKey("cellars.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("target_temp_f", sa.Float),
        sa.Column("target_humidity", sa.Float),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "wines",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("producer", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vintage", sa.Integer),
        sa.Column("region", sa.String(200)),
        sa.Column("grapes", sa.String(300)),
        sa.Column("tasting_notes", sa.Text),
        sa.Column("drink_from", sa.Integer),
        sa.Column("drink_until", sa.Integer),
        sa.Column("external_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "bottle_inventory",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("wine_id", sa.Integer, sa.ForeignKey("wines.id"), nullable=False),
        sa.Column("zone_id", sa.Integer, sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("condition", sa.String(50), server_default="good"),
        sa.Column("location_notes", sa.String(255)),
        sa.Column("added_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "purchase_history",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("wine_id", sa.Integer, sa.ForeignKey("wines.id"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("price_per_bottle", sa.Float),
        sa.Column("total_price", sa.Float),
        sa.Column("purchased_from", sa.String(200)),
        sa.Column("purchase_date", sa.DateTime),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "consumption_history",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("wine_id", sa.Integer, sa.ForeignKey("wines.id"), nullable=False),
        sa.Column("quantity", sa.Integer, server_default="1"),
        sa.Column("consumed_at", sa.DateTime),
        sa.Column("occasion", sa.String(200)),
        sa.Column("rating", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "wine_images",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("wine_id", sa.Integer, sa.ForeignKey("wines.id"), nullable=False),
        sa.Column("source_type", sa.String(20), server_default="upload"),
        sa.Column("file_path", sa.String(500)),
        sa.Column("external_url", sa.String(500)),
        sa.Column("is_primary", sa.Boolean, server_default=sa.false()),
        sa.Column("label", sa.String(100)),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "wishlist",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("producer", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vintage", sa.Integer),
        sa.Column("region", sa.String(200)),
        sa.Column("grapes", sa.String(300)),
        sa.Column("notes", sa.Text),
        sa.Column("external_url", sa.String(500)),
        sa.Column("target_price", sa.Float),
        sa.Column("priority", sa.Integer, server_default="3"),
        sa.Column("fulfilled_at", sa.DateTime),
        sa.Column("fulfilled_wine_id", sa.Integer, sa.ForeignKey("wines.id"), nullable=True),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "sensor_types",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("default_unit", sa.String(20)),
        sa.Column("min_safe", sa.Float),
        sa.Column("max_safe", sa.Float),
        sa.Column("icon", sa.String(50)),
        sa.Column("supports_alerts", sa.Boolean, server_default=sa.true()),
    )

    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("zone_id", sa.Integer, sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("sensor_type_id", sa.Integer, sa.ForeignKey("sensor_types.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("manufacturer", sa.String(120)),
        sa.Column("model", sa.String(120)),
        sa.Column("unit", sa.String(20)),
        sa.Column("active", sa.Boolean, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("sensor_id", sa.Integer, sa.ForeignKey("sensors.id"), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("recorded_at", sa.DateTime, index=True),
    )

    op.create_table(
        "cameras",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("zone_id", sa.Integer, sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("stream_type", sa.String(20), server_default="rtsp"),
        sa.Column("stream_url", sa.Text),
        sa.Column("snapshot_url", sa.Text),
        sa.Column("username", sa.String(200)),
        sa.Column("password", sa.Text),
        sa.Column("enabled", sa.Boolean, server_default=sa.true()),
        sa.Column("manufacturer", sa.String(120)),
        sa.Column("model", sa.String(120)),
        sa.Column("resolution", sa.String(20)),
        sa.Column("notes", sa.Text),
        sa.Column("last_seen_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "camera_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("camera_id", sa.Integer, sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("captured_at", sa.DateTime, index=True),
    )

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("domain", sa.String(30), nullable=False),
        sa.Column("entity_type", sa.String(30)),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("condition_type", sa.String(60), nullable=False),
        sa.Column("threshold_low", sa.Float),
        sa.Column("threshold_high", sa.Float),
        sa.Column("duration_seconds", sa.Integer, server_default="0"),
        sa.Column("severity", sa.String(10), server_default="warning"),
        sa.Column("enabled", sa.Boolean, server_default=sa.true()),
        sa.Column("cooldown_seconds", sa.Integer, server_default="3600"),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("rule_id", sa.Integer, sa.ForeignKey("alert_rules.id"), nullable=False),
        sa.Column("entity_type", sa.String(30)),
        sa.Column("entity_id", sa.Integer),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("triggered_at", sa.DateTime, index=True),
        sa.Column("resolved_at", sa.DateTime),
        sa.Column("acknowledged_at", sa.DateTime),
        sa.Column("acknowledged_by", sa.String(100)),
        sa.Column("metadata", sa.JSON),
    )

    op.create_table(
        "alert_channels",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("channel_type", sa.String(30), nullable=False),
        sa.Column("config", sa.JSON),
        sa.Column("enabled", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime),
    )


def downgrade():
    op.drop_table("alert_channels")
    op.drop_table("alert_events")
    op.drop_table("alert_rules")
    op.drop_table("camera_snapshots")
    op.drop_table("cameras")
    op.drop_table("sensor_readings")
    op.drop_table("sensors")
    op.drop_table("sensor_types")
    op.drop_table("wishlist")
    op.drop_table("wine_images")
    op.drop_table("consumption_history")
    op.drop_table("purchase_history")
    op.drop_table("bottle_inventory")
    op.drop_table("wines")
    op.drop_table("zones")
    op.drop_table("cellars")
