from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import cast, Integer
from typing import Optional
from app import database, models
from app.core.security import get_current_user

router = APIRouter(prefix="/aduan", tags=["aduan"])

def _normalize_int(val: str) -> Optional[int]:
    """Safely convert an RT/RW string to integer for DB casting."""
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None

@router.get("/")
def get_all_aduan(
    status: Optional[str] = None,
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Aduan).join(models.User, models.Aduan.user_id == models.User.id)

    # --- Role-based automatic filtering ---
    role = current_user.role
    if role == "rt":
        rt_int = _normalize_int(current_user.rt)
        rw_int = _normalize_int(current_user.rw)
        if rt_int and rw_int:
            query = query.filter(cast(models.User.rt, Integer) == rt_int, cast(models.User.rw, Integer) == rw_int)
        else:
            query = query.filter(models.User.rt == current_user.rt, models.User.rw == current_user.rw)
    elif role == "rw":
        rw_int = _normalize_int(current_user.rw)
        if rw_int:
            query = query.filter(cast(models.User.rw, Integer) == rw_int)
        else:
            query = query.filter(models.User.rw == current_user.rw)
    elif role == "warga":
        query = query.filter(models.Aduan.user_id == current_user.id)

    # --- Optional query-param overrides (Lurah / Superadmin only) ---
    HIGH_ROLES = {"lurah", "superadmin", "camat", "bupati"}
    if role in HIGH_ROLES:
        if rt:
            query = query.filter(models.User.rt == rt)
        if rw:
            query = query.filter(models.User.rw == rw)

    if status:
        query = query.filter(models.Aduan.status == status)

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
