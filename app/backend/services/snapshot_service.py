"""
Snapshot service: polls snapshot URLs and saves stills to disk.
"""
import os
import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session
import models

logger = logging.getLogger(__name__)

SNAPSHOT_BASE = os.environ.get("SNAPSHOT_DIR", "/media/just_another_wine_app/snapshots")


def snapshot_path(camera_id: int) -> str:
    path = os.path.join(SNAPSHOT_BASE, str(camera_id))
    os.makedirs(path, exist_ok=True)
    return path


async def capture_snapshot(camera_id: int, url: str, db: Session) -> bool:
    """Fetch a snapshot from a URL and store on disk + DB."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"snap_{ts}.jpg"
        filepath = os.path.join(snapshot_path(camera_id), filename)

        with open(filepath, "wb") as f:
            f.write(resp.content)

        snap = models.CameraSnapshot(camera_id=camera_id, file_path=filepath)
        db.add(snap)

        camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
        if camera:
            camera.last_seen_at = datetime.utcnow()

        db.commit()
        return True
    except Exception as e:
        logger.warning(f"Snapshot capture failed for camera {camera_id}: {e}")
        return False


def get_latest_snapshot_path(camera_id: int, db: Session) -> str | None:
    snap = (
        db.query(models.CameraSnapshot)
        .filter(models.CameraSnapshot.camera_id == camera_id)
        .order_by(models.CameraSnapshot.captured_at.desc())
        .first()
    )
    return snap.file_path if snap else None


def prune_snapshots(camera_id: int, db: Session, keep_days: int = 30):
    """Delete snapshots older than keep_days from disk and DB."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=keep_days)
    old = (
        db.query(models.CameraSnapshot)
        .filter(
            models.CameraSnapshot.camera_id == camera_id,
            models.CameraSnapshot.captured_at < cutoff,
        )
        .all()
    )
    for snap in old:
        try:
            os.remove(snap.file_path)
        except FileNotFoundError:
            pass
        db.delete(snap)
    db.commit()
