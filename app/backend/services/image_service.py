"""
Image service: handles wine label photo uploads, URL imports, and thumbnails.
"""
import os
import httpx
import logging
from datetime import datetime
from PIL import Image
from sqlalchemy.orm import Session
import models

logger = logging.getLogger(__name__)

IMAGE_BASE = os.environ.get("IMAGE_DIR", "/media/just_another_wine_app/images")
MAX_DIMENSION = 1600
THUMB_SIZE = (400, 400)


def _wine_dir(wine_id: int, subdir: str = "original") -> str:
    path = os.path.join(IMAGE_BASE, "wines", str(wine_id), subdir)
    os.makedirs(path, exist_ok=True)
    return path


def _make_thumbnail(src_path: str, wine_id: int, filename: str) -> str:
    thumb_dir = _wine_dir(wine_id, "thumbnails")
    thumb_path = os.path.join(thumb_dir, filename)
    with Image.open(src_path) as img:
        img.thumbnail(THUMB_SIZE)
        img.save(thumb_path, optimize=True, quality=85)
    return thumb_path


def save_upload(wine_id: int, file_bytes: bytes, filename: str, label: str, db: Session) -> models.WineImage:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{ts}_{filename.replace(' ', '_')}"
    orig_path = os.path.join(_wine_dir(wine_id, "original"), safe_name)

    with open(orig_path, "wb") as f:
        f.write(file_bytes)

    # Resize if too large
    with Image.open(orig_path) as img:
        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
            img.save(orig_path)

    _make_thumbnail(orig_path, wine_id, safe_name)

    has_primary = db.query(models.WineImage).filter(
        models.WineImage.wine_id == wine_id, models.WineImage.is_primary == True
    ).first()

    img_record = models.WineImage(
        wine_id=wine_id,
        source_type="upload",
        file_path=orig_path,
        is_primary=not bool(has_primary),
        label=label,
    )
    db.add(img_record)
    db.commit()
    db.refresh(img_record)
    return img_record


async def save_from_url(wine_id: int, url: str, label: str, db: Session) -> models.WineImage:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    ext = url.split("?")[0].rsplit(".", 1)[-1] or "jpg"
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_url.{ext}"
    orig_path = os.path.join(_wine_dir(wine_id, "original"), filename)

    with open(orig_path, "wb") as f:
        f.write(resp.content)

    _make_thumbnail(orig_path, wine_id, filename)

    has_primary = db.query(models.WineImage).filter(
        models.WineImage.wine_id == wine_id, models.WineImage.is_primary == True
    ).first()

    img_record = models.WineImage(
        wine_id=wine_id,
        source_type="url",
        file_path=orig_path,
        external_url=url,
        is_primary=not bool(has_primary),
        label=label,
    )
    db.add(img_record)
    db.commit()
    db.refresh(img_record)
    return img_record


def delete_image(img_id: int, db: Session):
    img = db.query(models.WineImage).filter(models.WineImage.id == img_id).first()
    if not img:
        return
    for path in [img.file_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        # Remove thumbnail
        if path:
            thumb = path.replace("/original/", "/thumbnails/")
            if os.path.exists(thumb):
                try:
                    os.remove(thumb)
                except OSError:
                    pass
    was_primary = img.is_primary
    wine_id = img.wine_id
    db.delete(img)
    db.commit()

    if was_primary:
        # Promote next image to primary
        next_img = (
            db.query(models.WineImage)
            .filter(models.WineImage.wine_id == wine_id)
            .order_by(models.WineImage.display_order)
            .first()
        )
        if next_img:
            next_img.is_primary = True
            db.commit()
