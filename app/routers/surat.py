from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import database, models
from app.core.security import get_current_user

router = APIRouter(prefix="/surat", tags=["surat"])

@router.get("/")
def get_surat(
    status: str = None,
    rt: str = None,
    rw: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.SuratPengantar).join(models.User, models.SuratPengantar.user_id == models.User.id)
    
    if current_user.role == "warga":
        query = query.filter(models.SuratPengantar.user_id == current_user.id)
    elif current_user.role == "rt":
        query = query.filter(models.User.rt == current_user.rt)
    elif current_user.role == "rw":
        query = query.filter(models.User.rw == current_user.rw)
    
    if status:
        query = query.filter(models.SuratPengantar.status == status)
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
        
    total = query.count()
    items = query.order_by(models.SuratPengantar.created_at.desc()).offset(skip).limit(limit).all()
            
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }

@router.post("/")
def create_surat(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_s = models.SuratPengantar(**data, user_id=current_user.id)
    db.add(new_s)
    db.commit()
    db.refresh(new_s)
    return new_s

@router.patch("/{surat_id}")
def update_surat_status(surat_id: str, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    s = db.query(models.SuratPengantar).filter(models.SuratPengantar.id == surat_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Surat tidak ditemukan")
    
    # Permission check: Only RT/RW/Lurah can update status
    if current_user.role not in ["rt", "rw", "lurah", "superadmin", "staff"]:
         raise HTTPException(status_code=403, detail="Akses ditolak")
    
    for key, value in data.items():
        if hasattr(s, key):
            setattr(s, key, value)
            
    if data.get("status") == "approved":
        s.rt_id = current_user.id
        
    db.commit()
    db.refresh(s)
    return s
