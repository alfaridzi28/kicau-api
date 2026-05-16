from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import database, models
from app.schemas import WargaCreate, WargaUpdate, WargaResponse, WargaPagination
from app.core.security import get_current_user, get_password_hash

router = APIRouter(prefix="/warga", tags=["warga"])

@router.get("/", response_model=WargaPagination)
def get_all_warga(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    search: Optional[str] = None,
    bansos: Optional[bool] = None,
    is_fakir: Optional[bool] = None,
    is_miskin: Optional[bool] = None,
    is_ibu_hamil: Optional[bool] = None,
    is_balita: Optional[bool] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    from sqlalchemy import cast, Integer
    if rt:
        try:
            rt_val = int(str(rt).strip())
            query = query.filter(cast(models.User.rt, Integer) == rt_val)
        except:
            query = query.filter(models.User.rt == rt)
    if rw:
        try:
            rw_val = int(str(rw).strip())
            query = query.filter(cast(models.User.rw, Integer) == rw_val)
        except:
            query = query.filter(models.User.rw == rw)
    if search:
        query = query.filter(
            (models.User.nama.ilike(f"%{search}%")) | 
            (models.User.nik.ilike(f"%{search}%"))
        )
    if bansos:
        query = query.filter(
            (models.User.is_fakir == True) | 
            (models.User.is_miskin == True) | 
            (models.User.is_ibu_hamil == True) | 
            (models.User.is_balita == True)
        )
    
    # Specific Category Filters
    if is_fakir:
        query = query.filter(models.User.is_fakir == True)
    if is_miskin:
        query = query.filter(models.User.is_miskin == True)
    if is_ibu_hamil:
        query = query.filter(models.User.is_ibu_hamil == True)
    if is_balita:
        query = query.filter(models.User.is_balita == True)
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }

@router.get("/{warga_id}", response_model=WargaResponse)
def get_warga(warga_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == warga_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Warga tidak ditemukan")
    return user

@router.post("/", response_model=WargaResponse)
def create_warga(warga: WargaCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Check if NIK already exists
    db_user = db.query(models.User).filter(models.User.nik == warga.nik).first()
    if db_user:
        raise HTTPException(status_code=400, detail="NIK sudah terdaftar")
    
    hashed_password = get_password_hash(warga.password or "password123")
    new_user = models.User(**warga.model_dump(exclude={"password"}))
    new_user.password = hashed_password
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{warga_id}", response_model=WargaResponse)
def update_warga(warga_id: str, warga_update: WargaUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    db_user = db.query(models.User).filter(models.User.id == warga_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Warga tidak ditemukan")

    # Access Control: Hanya diri sendiri, RT (untuk warganya), RW (untuk warganya), Lurah, atau Superadmin
    can_edit = (
        current_user.id == db_user.id or 
        current_user.role == 'superadmin' or 
        current_user.role == 'lurah' or
        (current_user.role == 'rw' and current_user.rw == db_user.rw) or
        (current_user.role == 'rt' and current_user.rt == db_user.rt and current_user.rw == db_user.rw)
    )
    
    if not can_edit:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses untuk mengubah data ini")
    
    update_data = warga_update.model_dump(exclude_unset=True)
    
    # Restriksi Role: Lurah & RT boleh ganti role tertentu
    if "role" in update_data:
        if current_user.role == 'lurah':
            if update_data["role"] not in ['warga', 'rt', 'rw', 'staff']:
                raise HTTPException(status_code=403, detail="Lurah hanya diperbolehkan mengubah role menjadi warga, rt, rw, atau staff")
        elif current_user.role == 'rt':
            # RT boleh angkat jadi pengurus (role rt) atau kembalikan ke warga
            if update_data["role"] not in ['warga', 'rt']:
                raise HTTPException(status_code=403, detail="RT hanya diperbolehkan mengubah role menjadi warga atau rt (pengurus)")

    # If NIK is being updated, check if it's already taken by someone else
    if "nik" in update_data and update_data["nik"] != db_user.nik:
        existing_nik = db.query(models.User).filter(models.User.nik == update_data["nik"], models.User.id != warga_id).first()
        if existing_nik:
            raise HTTPException(status_code=400, detail="NIK sudah digunakan oleh warga lain")

    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{warga_id}")
def delete_warga(warga_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    db_user = db.query(models.User).filter(models.User.id == warga_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Warga tidak ditemukan")
    
    db.delete(db_user)
    db.commit()
    return {"message": "Warga berhasil dihapus"}

@router.patch("/{warga_id}/reset-password")
def reset_password(warga_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Hanya superadmin yang bisa reset password")
    
    db_user = db.query(models.User).filter(models.User.id == warga_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Warga tidak ditemukan")
    
    # Reset to default password
    db_user.password = get_password_hash("password123")
    db.commit()
    return {"message": "Password berhasil direset ke 'password123'"}

@router.patch("/{warga_id}/toggle-active")
def toggle_active(warga_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Hanya superadmin yang bisa mengubah status akun")
    
    db_user = db.query(models.User).filter(models.User.id == warga_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Warga tidak ditemukan")
    
    db_user.is_active = not db_user.is_active
    db.commit()
    db.refresh(db_user)
    return {"message": f"Status warga berhasil diubah menjadi {'Aktif' if db_user.is_active else 'Nonaktif'}", "is_active": db_user.is_active}

@router.get("/geojson/points")
def get_warga_geojson(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User).filter(models.User.latitude.isnot(None), models.User.longitude.isnot(None))
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
    
    users = query.all()
    
    features = []
    for user in users:
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
                "is_balita": user.is_balita
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }
