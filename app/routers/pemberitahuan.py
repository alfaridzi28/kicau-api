from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import database, models
from app.core.security import get_current_user
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
    
    if lat is not None and lng is not None and not (rt and rw):
        from geoalchemy2.functions import ST_Distance, ST_SetSRID, ST_Point
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
    return db.query(models.Pemberitahuan).order_by(models.Pemberitahuan.created_at.desc()).all()

@router.post("/")
def create_pemberitahuan(
    data: dict, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Map frontend fields to DB fields if necessary
    payload = {
        "judul": data.get("judul"),
        "isi": data.get("isi"),
        "target_rt": data.get("target_rt") or data.get("rt"),
        "target_rw": data.get("target_rw") or data.get("rw"),
        "is_publik": data.get("is_publik", True),
        "created_by": current_user.id
    }
    
    new_p = models.Pemberitahuan(**payload)
    db.add(new_p)
    db.commit()
    db.refresh(new_p)
    return new_p

@router.delete("/{id}")
def delete_pemberitahuan(
    id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    news = db.query(models.Pemberitahuan).filter(models.Pemberitahuan.id == id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Pengumuman tidak ditemukan")
    
    # Only creator or Superadmin/Lurah can delete
    if news.created_by != current_user.id and current_user.role not in ['superadmin', 'lurah']:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses untuk menghapus")
        
    db.delete(news)
    db.commit()
    return {"message": "Pengumuman berhasil dihapus"}
