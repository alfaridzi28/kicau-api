from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import database, models
from app.schemas import WargaCreate, WargaUpdate, WargaResponse
from app.core.security import get_current_user, get_password_hash

router = APIRouter(prefix="/warga", tags=["warga"])

@router.get("/", response_model=List[WargaResponse])
def get_all_warga(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User)
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
    return query.all()

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
    
    update_data = warga_update.model_dump(exclude_unset=True)
    
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
