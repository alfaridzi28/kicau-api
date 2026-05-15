from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import database, models
from app.core.security import get_current_user
import datetime

router = APIRouter(prefix="/aduan", tags=["aduan"])

@router.get("/")
def get_all_aduan(
    status: Optional[str] = None,
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Aduan).join(models.User, models.Aduan.user_id == models.User.id)
    
    if status:
        query = query.filter(models.Aduan.status == status)
    
    if rt:
        query = query.filter(models.User.rt == rt)
    
    if rw:
        query = query.filter(models.User.rw == rw)
    
    # If user is not admin/rt/rw, only show their own aduan
    if current_user.role == "warga":
        query = query.filter(models.Aduan.user_id == current_user.id)
        
    return query.order_by(models.Aduan.created_at.desc()).all()

@router.post("/")
def create_aduan(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_aduan = models.Aduan(
        **data,
        user_id=current_user.id,
        status="belum_dibaca"
    )
    db.add(new_aduan)
    db.commit()
    db.refresh(new_aduan)
    return new_aduan

@router.patch("/{aduan_id}")
def update_aduan_status(aduan_id: str, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    aduan = db.query(models.Aduan).filter(models.Aduan.id == aduan_id).first()
    if not aduan:
        raise HTTPException(status_code=404, detail="Aduan tidak ditemukan")
    
    # Ambil data pelapor untuk notifikasi
    pelapor = db.query(models.User).filter(models.User.id == aduan.user_id).first()

    for key, value in data.items():
        setattr(aduan, key, value)
    
    # Jika yang menjawab adalah RW, kirim notifikasi ke Ketua RT pelapor
    if current_user.role == "rw" and "balasan" in data:
        if pelapor and pelapor.rt:
            new_notif = models.Pemberitahuan(
                judul="🔔 Tindak Lanjut Aduan Warga oleh RW",
                isi=f"Ketua RW telah menanggapi aduan dari warga Anda ({pelapor.nama}). Silakan cek manajemen aduan untuk koordinasi lebih lanjut.",
                target_rt=pelapor.rt,
                target_rw=pelapor.rw,
                is_publik=False, # Hanya untuk pengurus/internal
                created_by=current_user.id
            )
            db.add(new_notif)
        
    db.commit()
    db.refresh(aduan)
    return aduan
