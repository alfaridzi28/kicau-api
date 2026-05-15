from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app import database, models
from app.schemas import IuranCreate, IuranUpdate, IuranResponse
from app.core.security import get_current_user
import datetime

router = APIRouter(prefix="/iuran", tags=["iuran"])

@router.get("/", response_model=List[IuranResponse])
def get_all_iuran(
    user_id: Optional[str] = None,
    bulan_tahun: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Keuangan).filter(models.Keuangan.tipe == "iuran")
    if user_id:
        query = query.filter(models.Keuangan.user_id == user_id)
    if bulan_tahun:
        query = query.filter(models.Keuangan.bulan_tahun == bulan_tahun)
    return query.all()

@router.post("/", response_model=IuranResponse)
def create_iuran(iuran: IuranCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_iuran = models.Keuangan(
        tipe="iuran",
        kategori="Iuran Warga",
        **iuran.model_dump()
    )
    db.add(new_iuran)
    db.commit()
    db.refresh(new_iuran)
    return new_iuran

@router.get("/status/{user_id}")
def get_iuran_status(user_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Check if paid for current month
    now = datetime.datetime.now()
    bulan_tahun = now.strftime("%Y-%m")
    record = db.query(models.Keuangan).filter(
        models.Keuangan.user_id == user_id,
        models.Keuangan.bulan_tahun == bulan_tahun,
        models.Keuangan.tipe == "iuran"
    ).first()
    
    return {"paid": record is not None, "bulan_tahun": bulan_tahun}

@router.get("/rekap-rw")
def get_rekap_rw(
    bulan_tahun: Optional[str] = None,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["rw", "lurah", "superadmin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    if not bulan_tahun:
        now = datetime.datetime.now()
        bulan_tahun = now.strftime("%Y-%m")
    
    # Superadmin & Lurah see all RWs
    if current_user.role in ["superadmin", "lurah"]:
        query_rw = db.query(models.User.rw).filter(models.User.rw.isnot(None)).distinct().all()
        rws = [r[0] for r in query_rw]
        
        rekap = []
        for rw in rws:
            total_nominal = db.query(func.sum(models.Keuangan.nominal)).join(models.User, models.Keuangan.user_id == models.User.id).filter(
                models.User.rw == rw,
                models.Keuangan.tipe == "iuran",
                models.Keuangan.bulan_tahun == bulan_tahun
            ).scalar() or 0
            
            total_warga = db.query(models.User).filter(models.User.rw == rw, models.User.role == "warga").count()
            sudah_bayar = db.query(models.User).join(models.Keuangan, models.Keuangan.user_id == models.User.id).filter(
                models.User.rw == rw,
                models.Keuangan.tipe == "iuran",
                models.Keuangan.bulan_tahun == bulan_tahun
            ).count()
            
            rekap.append({
                "rw": rw,
                "total_nominal": total_nominal,
                "total_warga": total_warga,
                "sudah_bayar": sudah_bayar,
                "belum_bayar": total_warga - sudah_bayar
            })
        return rekap # Return array directly for consistency
    
    # RW role sees their own RTs
    rw = current_user.rw
    if not rw:
        raise HTTPException(status_code=400, detail="Data RW tidak ditemukan pada profil Anda")

    query_rt = db.query(models.User.rt).filter(models.User.rw == rw).distinct().all()
    rts = [r[0] for r in query_rt if r[0]]
    
    rekap = []
    for rt in rts:
        collected = db.query(func.sum(models.Keuangan.nominal)).join(models.User, models.Keuangan.user_id == models.User.id).filter(
            models.User.rt == rt,
            models.User.rw == rw,
            models.Keuangan.tipe == "iuran",
            models.Keuangan.bulan_tahun == bulan_tahun
        ).scalar() or 0
        
        total_warga = db.query(models.User).filter(models.User.rt == rt, models.User.rw == rw, models.User.role == "warga").count()
        sudah_bayar = db.query(models.User).join(models.Keuangan, models.Keuangan.user_id == models.User.id).filter(
            models.User.rt == rt,
            models.User.rw == rw,
            models.Keuangan.tipe == "iuran",
            models.Keuangan.bulan_tahun == bulan_tahun
        ).count()

        rekap.append({
            "rw": rw,
            "rt": rt,
            "total_nominal": collected,
            "total_warga": total_warga,
            "sudah_bayar": sudah_bayar,
            "belum_bayar": total_warga - sudah_bayar
        })
        
    return rekap # Return array directly

@router.get("/rekap-rt")
def get_rekap_rt(
    rt: str = None,
    rw: str = None,
    bulan_tahun: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not rt and current_user.role == "rt":
        rt = current_user.rt
    if not rw and current_user.role in ["rt", "rw"]:
        rw = current_user.rw
        
    if not bulan_tahun:
        bulan_tahun = datetime.datetime.now().strftime("%Y-%m")
        
    # Get all warga in RT
    warga_list = db.query(models.User).filter(
        models.User.rt == rt, 
        models.User.rw == rw, 
        models.User.role == "warga"
    ).all()
    
    # Get paid records
    paid_records = db.query(models.Keuangan).filter(
        models.Keuangan.rt_id == current_user.id if current_user.role == "rt" else None, # This might be tricky
        models.Keuangan.tipe == "iuran",
        models.Keuangan.bulan_tahun == bulan_tahun
    ).join(models.User, models.Keuangan.user_id == models.User.id).filter(
        models.User.rt == rt,
        models.User.rw == rw
    ).all()
    
    paid_ids = [r.user_id for r in paid_records]
    
    data = []
    for w in warga_list:
        is_paid = w.id in paid_ids
        data.append({
            "id": w.id,
            "nama": w.nama,
            "nik": w.nik,
            "status": "Lunas" if is_paid else "Belum Bayar",
            "nominal": next((r.nominal for r in paid_records if r.user_id == w.id), 0)
        })
        
    return {"rt": rt, "rw": rw, "bulan_tahun": bulan_tahun, "data": data}

@router.get("/unpaid")
def get_unpaid_warga(rt: str = None, rw: str = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Role check
    if current_user.role == "warga":
        raise HTTPException(status_code=403, detail="Akses ditolak")
        
    now = datetime.datetime.now()
    bulan_tahun = now.strftime("%Y-%m")
    
    # If RT/RW not provided, use from current_user if applicable
    if not rw and current_user.role == "rw":
        rw = current_user.rw
    if not rt and current_user.role == "rt":
        rt = current_user.rt
        rw = current_user.rw
        
    query = db.query(models.User).filter(models.User.role == "warga")
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
        
    all_warga = query.all()
    
    # Get paid user IDs
    paid_user_ids = db.query(models.Keuangan.user_id).filter(
        models.Keuangan.tipe == "iuran",
        models.Keuangan.bulan_tahun == bulan_tahun
    ).all()
    paid_user_ids = [p[0] for p in paid_user_ids]
    
    unpaid = [w for w in all_warga if w.id not in paid_user_ids]
    
    return unpaid
