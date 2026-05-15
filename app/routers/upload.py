from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    # Validate extension
    ext = file.filename.split(".")[-1]
    if ext.lower() not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(status_code=400, detail="Format file tidak didukung")
    
    file_name = f"{uuid.uuid4()}.{ext}"
    file_path = UPLOAD_DIR / file_name
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"http://localhost:8000/static/uploads/{file_name}"}

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    return await upload_file(file)
