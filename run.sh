#!/usr/bin/with-contenv bashio
set -e

LOG_LEVEL=$(bashio::config 'log_level')
SNAPSHOT_RETENTION=$(bashio::config 'snapshot_retention_days')
READINGS_RETENTION=$(bashio::config 'readings_retention_days')
FFMPEG_PATH=$(bashio::config 'ffmpeg_path')

export LOG_LEVEL
export SNAPSHOT_RETENTION_DAYS="$SNAPSHOT_RETENTION"
export READINGS_RETENTION_DAYS="$READINGS_RETENTION"
export FFMPEG_PATH

export DB_DIR="/config/just_another_wine_app"
export IMAGE_DIR="/media/just_another_wine_app/images"
export STREAM_DIR="/media/just_another_wine_app/streams"
export SNAPSHOT_DIR="/media/just_another_wine_app/snapshots"

# Generate (or reuse) an encryption key for camera credentials, persisted
# in the config directory so it survives add-on restarts/updates.
SECRET_FILE="/config/just_another_wine_app/.secret_key"
mkdir -p /config/just_another_wine_app
if [ ! -f "$SECRET_FILE" ]; then
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > "$SECRET_FILE"
fi
export SECRET_KEY=$(cat "$SECRET_FILE")

mkdir -p "$DB_DIR" "$IMAGE_DIR" "$STREAM_DIR" "$SNAPSHOT_DIR"

bashio::log.info "Starting Just Another Wine App..."

cd /app/backend

# Run migrations (safe no-op if already current)
alembic upgrade head || bashio::log.warning "Migration step skipped or failed — continuing startup"

exec uvicorn main:app --host 0.0.0.0 --port 8099 --log-level "${LOG_LEVEL}"
