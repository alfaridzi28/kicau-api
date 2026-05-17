from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app import database, models
from app.schemas import BansosResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/bansos", tags=["bansos"])

@router.get("/", response_model=List[BansosResponse])
def get_bansos_eligible(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User).filter(
        (models.User.is_fakir == True) | 
        (models.User.is_miskin == True) |
        (models.User.is_ibu_hamil == True) |
        (models.User.is_balita == True)
    )
    
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
        
    return query.all()

@router.get("/geojson")
def get_bansos_geojson(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User).filter(
        models.User.latitude.isnot(None),
        models.User.longitude.isnot(None),
        (
            (models.User.is_fakir == True) | 
            (models.User.is_miskin == True) |
            (models.User.is_ibu_hamil == True) |
            (models.User.is_balita == True)
        )
    )
    
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
        
    users = query.all()
    
    features = []
    for user in users:
        kategori_bansos = []
        if user.is_fakir:
            kategori_bansos.append("Fakir")
        if user.is_miskin:
            kategori_bansos.append("Miskin")
        if user.is_ibu_hamil:
            kategori_bansos.append("Ibu Hamil")
        if user.is_balita:
            kategori_bansos.append("Balita")
            
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [user.longitude, user.latitude]
            },
            "properties": {
                "id": user.id,
                "nama": user.nama,
                "nik": user.nik,
                "alamat": user.alamat,
                "rt": user.rt,
                "rw": user.rw,
                "role": user.role,
                "is_fakir": user.is_fakir,
                "is_miskin": user.is_miskin,
                "is_ibu_hamil": user.is_ibu_hamil,
                "is_balita": user.is_balita,
                "kategori_bansos": kategori_bansos
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/stats")
def get_bansos_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return {
        "fakir": db.query(models.User).filter(models.User.is_fakir == True).count(),
        "miskin": db.query(models.User).filter(models.User.is_miskin == True).count(),
        "ibu_hamil": db.query(models.User).filter(models.User.is_ibu_hamil == True).count(),
        "balita": db.query(models.User).filter(models.User.is_balita == True).count()
    }
