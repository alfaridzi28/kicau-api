from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import database, models
import datetime

router = APIRouter(prefix="/pemberitahuan", tags=["pemberitahuan"])

@router.get("/publik")
def get_pemberitahuan_publik(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    limit: int = 6,
    db: Session = Depends(database.get_db)
):
    detected_rt = rt
    detected_rw = rw
    
    # Spatial Lookup if lat/lng provided
    if lat is not None and lng is not None and not (rt and rw):
        from geoalchemy2.functions import ST_Distance, ST_SetSRID, ST_Point
        
        # Find the nearest user with RT/RW info to identify the area
        # Note: In a production app, you might have a dedicated 'Wilayah' table with polygons.
        # Here we use nearest-neighbor from citizens' locations as a proxy.
        point = ST_SetSRID(ST_Point(lng, lat), 4326)
        nearest_user = db.query(models.User).filter(
            models.User.rt != None, 
            models.User.rw != None,
            models.User.lokasi != None
        ).order_by(ST_Distance(models.User.lokasi, point)).first()
        
        if nearest_user:
            detected_rt = nearest_user.rt
            detected_rw = nearest_user.rw

    query = db.query(models.Pemberitahuan).filter(models.Pemberitahuan.is_publik == True)
    
    if detected_rt and detected_rw:
        # Show notifications for this RT/RW OR general ones (rt=null, rw=null)
        query = query.filter(
            ((models.Pemberitahuan.target_rt == detected_rt) & (models.Pemberitahuan.target_rw == detected_rw)) |
            ((models.Pemberitahuan.target_rt == None) & (models.Pemberitahuan.target_rw == None))
        )
    
    return {
        "detected_region": {"rt": detected_rt, "rw": detected_rw} if detected_rt else None,
        "pemberitahuan": query.order_by(models.Pemberitahuan.created_at.desc()).limit(limit).all()
    }

@router.get("/")
def get_all_pemberitahuan(db: Session = Depends(database.get_db)):
    return db.query(models.Pemberitahuan).all()

@router.post("/")
def create_pemberitahuan(data: dict, db: Session = Depends(database.get_db)):
    # Simple implementation for now
    new_p = models.Pemberitahuan(**data)
    db.add(new_p)
    db.commit()
    db.refresh(new_p)
    return new_p
