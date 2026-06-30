import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services import image_service
import models, schemas

router = APIRouter(prefix="/api", tags=["images"])


@router.post("/wines/{wine_id}/images", response_model=schemas.WineImageOut, status_code=201)
async def upload_image(
    wine_id: int,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    label: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    wine = db.query(models.Wine).filter(models.Wine.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wine not found")

    if file:
        contents = await file.read()
        img = image_service.save_upload(wine_id, contents, file.filename, label or "bottle", db)
    elif url:
        img = await image_service.save_from_url(wine_id, url, label or "bottle", db)
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or a url")

    return img


@router.delete("/wines/{wine_id}/images/{img_id}", status_code=204)
def delete_image(wine_id: int, img_id: int, db: Session = Depends(get_db)):
    img = db.query(models.WineImage).filter(
        models.WineImage.id == img_id, models.WineImage.wine_id == wine_id
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    image_service.delete_image(img_id, db)


@router.put("/wines/{wine_id}/images/{img_id}/primary", response_model=schemas.WineImageOut)
def set_primary(wine_id: int, img_id: int, db: Session = Depends(get_db)):
    img = db.query(models.WineImage).filter(
        models.WineImage.id == img_id, models.WineImage.wine_id == wine_id
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    db.query(models.WineImage).filter(models.WineImage.wine_id == wine_id).update({"is_primary": False})
    img.is_primary = True
    db.commit()
    db.refresh(img)
    return img


@router.get("/images/{img_id}")
def serve_image(img_id: int, thumbnail: bool = False, db: Session = Depends(get_db)):
    img = db.query(models.WineImage).filter(models.WineImage.id == img_id).first()
    if not img or not img.file_path:
        raise HTTPException(status_code=404, detail="Image not found")
    path = img.file_path
    if thumbnail:
        thumb = path.replace("/original/", "/thumbnails/")
        if os.path.exists(thumb):
            path = thumb
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(path)
