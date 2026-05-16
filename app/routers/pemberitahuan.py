from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import database, models
from app.core.security import get_current_user
import datetime
from sqlalchemy import or_

router = APIRouter(prefix="/pemberitahuan", tags=["pemberitahuan"])

def is_empty_or_none(col):
    """Helper to check if a column is None or an empty string."""
    return or_(col == None, col == '')

@router.get("/publik")
def get_pemberitahuan_publik(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    limit: int = 6,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Pemberitahuan).filter(models.Pemberitahuan.is_publik == True)
    
    if rt and rw:
        query = query.filter(
            or_(
                # Admin/Lurah global news (None or empty string)
                (is_empty_or_none(models.Pemberitahuan.target_rw)) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                # RW specific news
                (models.Pemberitahuan.target_rw == rw) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                # RT specific news
                (models.Pemberitahuan.target_rw == rw) & (models.Pemberitahuan.target_rt == rt)
            )
        )
    else:
        # If no region detected, only show global news
        query = query.filter((is_empty_or_none(models.Pemberitahuan.target_rw)) & (is_empty_or_none(models.Pemberitahuan.target_rt)))
    
    return {
        "detected_region": {"rt": rt, "rw": rw} if rt else None,
        "pemberitahuan": query.order_by(models.Pemberitahuan.created_at.desc()).limit(limit).all()
    }

@router.get("/")
def get_all_pemberitahuan(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Base query
    query = db.query(models.Pemberitahuan)
    
    # VISIBILITY RULES based on Hierarchy:
    if current_user.role in ["superadmin", "admin"]:
        # Admin sees everything
        pass
    elif current_user.role == "lurah":
        # Lurah sees Admin/Lurah global news + their own
        query = query.filter(
            or_(
                (is_empty_or_none(models.Pemberitahuan.target_rw)) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                (models.Pemberitahuan.created_by == current_user.id)
            )
        )
    elif current_user.role == "rw":
        # RW sees Admin/Lurah global news + news for their RW + their own
        query = query.filter(
            or_(
                (is_empty_or_none(models.Pemberitahuan.target_rw)) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                (models.Pemberitahuan.target_rw == current_user.rw) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                (models.Pemberitahuan.created_by == current_user.id)
            )
        )
    elif current_user.role == "rt":
        # RT sees Admin/Lurah news + their RW news + news for their RT + their own
        query = query.filter(
            or_(
                (is_empty_or_none(models.Pemberitahuan.target_rw)) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                (models.Pemberitahuan.target_rw == current_user.rw) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                (models.Pemberitahuan.target_rw == current_user.rw) & (models.Pemberitahuan.target_rt == current_user.rt),
                (models.Pemberitahuan.created_by == current_user.id)
            )
        )
    elif current_user.role == "warga":
        # Warga sees Admin/Lurah news + their RW news + their RT news
        query = query.filter(
            or_(
                (is_empty_or_none(models.Pemberitahuan.target_rw)) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                (models.Pemberitahuan.target_rw == current_user.rw) & (is_empty_or_none(models.Pemberitahuan.target_rt)),
                (models.Pemberitahuan.target_rw == current_user.rw) & (models.Pemberitahuan.target_rt == current_user.rt)
            )
        )
        
    return query.order_by(models.Pemberitahuan.created_at.desc()).all()

@router.post("/")
def create_pemberitahuan(
    data: dict, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    payload = {
        "judul": data.get("judul"),
        "isi": data.get("isi"),
        "is_publik": data.get("is_publik", True),
        "created_by": current_user.id,
        "target_rt": None,
        "target_rw": None
    }
    
    # Handle empty strings from frontend as None for DB consistency
    if current_user.role == "rt":
        payload["target_rt"] = current_user.rt
        payload["target_rw"] = current_user.rw
    elif current_user.role == "rw":
        payload["target_rw"] = current_user.rw
        payload["target_rt"] = None
    elif current_user.role in ["lurah", "admin", "superadmin", "staff"]:
        payload["target_rt"] = None
        payload["target_rw"] = None

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
    
    if news.created_by != current_user.id and current_user.role not in ["superadmin", "lurah"]:
        raise HTTPException(status_code=403, detail="Akses ditolak")
        
    db.delete(news)
    db.commit()
    return {"message": "Pengumuman berhasil dihapus"}
