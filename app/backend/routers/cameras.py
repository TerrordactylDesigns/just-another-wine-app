import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from services.crypto import encrypt, decrypt
from services import stream_service, snapshot_service
import models, schemas

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("", response_model=List[schemas.CameraOut])
def list_cameras(zone_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(models.Camera)
    if zone_id:
        q = q.filter(models.Camera.zone_id == zone_id)
    return q.order_by(models.Camera.name).all()


@router.post("", response_model=schemas.CameraOut, status_code=201)
def create_camera(data: schemas.CameraCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    if payload.get("stream_url"):
        payload["stream_url"] = encrypt(payload["stream_url"])
    if payload.get("snapshot_url"):
        payload["snapshot_url"] = encrypt(payload["snapshot_url"])
    if payload.get("password"):
        payload["password"] = encrypt(payload["password"])

    camera = models.Camera(**payload)
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


@router.get("/{camera_id}", response_model=schemas.CameraOut)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.put("/{camera_id}", response_model=schemas.CameraOut)
def update_camera(camera_id: int, data: schemas.CameraUpdate, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    payload = data.model_dump()
    if payload.get("stream_url"):
        payload["stream_url"] = encrypt(payload["stream_url"])
    if payload.get("snapshot_url"):
        payload["snapshot_url"] = encrypt(payload["snapshot_url"])
    if payload.get("password"):
        payload["password"] = encrypt(payload["password"])
    for k, v in payload.items():
        setattr(camera, k, v)
    db.commit()
    db.refresh(camera)
    return camera


@router.delete("/{camera_id}", status_code=204)
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    stream_service.stop_stream(camera_id)
    db.delete(camera)
    db.commit()


@router.get("/{camera_id}/stream")
def get_stream(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not camera.enabled:
        raise HTTPException(status_code=400, detail="Camera is disabled")

    stream_url = decrypt(camera.stream_url or "")
    if camera.stream_type in ("rtsp", "mjpeg") and stream_url:
        stream_service.start_stream(camera_id, stream_url)
        return {
            "type": "hls",
            "url": f"/api/cameras/{camera_id}/hls/index.m3u8",
            "status": stream_service.get_stream_status(camera_id),
        }
    elif camera.stream_type == "hls":
        return {"type": "hls", "url": stream_url}
    elif camera.stream_type == "snapshot":
        return {"type": "snapshot", "url": f"/api/cameras/{camera_id}/snapshot"}
    return {"type": "unknown"}


@router.get("/{camera_id}/hls/{filename}")
def serve_hls(camera_id: int, filename: str, db: Session = Depends(get_db)):
    base = stream_service.stream_dir(camera_id)
    path = os.path.join(base, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Stream segment not found")
    media_type = "application/vnd.apple.mpegurl" if filename.endswith(".m3u8") else "video/MP2T"
    return FileResponse(path, media_type=media_type)


@router.get("/{camera_id}/snapshot")
def get_snapshot(camera_id: int, db: Session = Depends(get_db)):
    path = snapshot_service.get_latest_snapshot_path(camera_id, db)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No snapshot available")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/{camera_id}/snapshot/history")
def snapshot_history(camera_id: int, limit: int = 20, db: Session = Depends(get_db)):
    snaps = (
        db.query(models.CameraSnapshot)
        .filter(models.CameraSnapshot.camera_id == camera_id)
        .order_by(models.CameraSnapshot.captured_at.desc())
        .limit(limit)
        .all()
    )
    return [{"id": s.id, "captured_at": s.captured_at, "url": f"/api/cameras/{camera_id}/snapshot/{s.id}"} for s in snaps]


@router.get("/{camera_id}/health")
def camera_health(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    status = stream_service.get_stream_status(camera_id)
    return {
        "camera_id": camera_id,
        "enabled": camera.enabled,
        "last_seen_at": camera.last_seen_at,
        "stream_running": status["running"],
        "stream_pid": status["pid"],
    }
