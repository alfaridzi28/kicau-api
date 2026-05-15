from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app import database, models
from app.core.security import get_current_user
import datetime

router = APIRouter(prefix="/iuran-setting", tags=["iuran-setting"])

@router.get("/")
def get_iuran_settings(rt: Optional[str] = None, rw: Optional[str] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.IuranSetting)
    if rt:
        query = query.filter(models.IuranSetting.rt == rt)
    if rw:
        query = query.filter(models.IuranSetting.rw == rw)
    return query.all()

@router.post("/")
def create_or_update_iuran_setting(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ["rt", "rw", "superadmin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    rt = data.get("rt")
    rw = data.get("rw")
    nominal = data.get("nominal")
    
    if not rt or not rw or nominal is None:
        raise HTTPException(status_code=400, detail="Data tidak lengkap")
        
    # Check if exists
    db_setting = db.query(models.IuranSetting).filter(models.IuranSetting.rt == rt, models.IuranSetting.rw == rw).first()
    
    if db_setting:
        db_setting.nominal = nominal
        db_setting.set_by = current_user.id
        db_setting.created_at = datetime.datetime.utcnow()
    else:
        db_setting = models.IuranSetting(
            rt=rt,
            rw=rw,
            nominal=nominal,
            set_by=current_user.id
        )
        db.add(db_setting)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting
