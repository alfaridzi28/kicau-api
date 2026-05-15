from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app import database, models
from app.schemas import IuranCreate, IuranUpdate, IuranResponse
from app.core.security import get_current_user
import datetime

router = APIRouter(prefix="/iuran", tags=["iuran"])

@router.get("/transaksi")
def get_transaksi(
    tipe: Optional[str] = None,
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Keuangan)
    
    if current_user.role == "rt":
        query = query.join(models.User, models.Keuangan.user_id == models.User.id).filter(models.User.rt == current_user.rt, models.User.rw == current_user.rw)
    elif current_user.role == "rw":
        query = query.join(models.User, models.Keuangan.user_id == models.User.id).filter(models.User.rw == current_user.rw)
    
    if tipe:
        query = query.filter(models.Keuangan.tipe == tipe)
        
    return query.order_by(models.Keuangan.created_at.desc()).all()

@router.post("/")
def create_transaksi(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Tipe: pemasukan, pengeluaran, iuran
    new_t = models.Keuangan(
        **data,
        rt_id=current_user.id # Penanggung jawab transaksi
    )
    db.add(new_t)
    db.commit()
    db.refresh(new_t)
    return new_t

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
    rt: str = Query(...),
    rw: str = Query(...),
    bulan_tahun: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validasi akses
    if current_user.role not in ["superadmin", "lurah"]:
        if current_user.role == "rw" and str(current_user.rw).strip() != str(rw).strip():
            raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke RW ini")
            
    if not bulan_tahun:
        bulan_tahun = datetime.datetime.now().strftime("%Y-%m")
        
    # Ambil SEMUA orang di wilayah tersebut (kecuali superadmin)
    warga_list = db.query(models.User).filter(
        func.trim(models.User.rt) == rt.strip(), 
        func.trim(models.User.rw) == rw.strip(),
        models.User.role != "superadmin"
    ).all()
    
    # Get paid records
    paid_records = db.query(models.Keuangan).filter(
        models.Keuangan.tipe == "iuran",
        models.Keuangan.bulan_tahun == bulan_tahun
    ).join(models.User, models.Keuangan.user_id == models.User.id).filter(
        func.trim(models.User.rt) == rt.strip(),
        func.trim(models.User.rw) == rw.strip()
    ).all()
    
    paid_ids = [r.user_id for r in paid_records]
    
    data = []
    for w in warga_list:
        is_paid = w.id in paid_ids
        data.append({
            "id": w.id,
            "nama": w.nama,
            "nik": w.nik,
            "role": w.role,
            "status": "Lunas" if is_paid else "Belum Bayar",
            "nominal": next((r.nominal for r in paid_records if r.user_id == w.id), 0)
        })
        
    return {"rt": rt, "rw": rw, "bulan_tahun": bulan_tahun, "data": data}

@router.get("/rt-to-rw-status")
def get_rt_to_rw_status(
    bulan_tahun: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["rw", "lurah", "superadmin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    if not bulan_tahun:
        bulan_tahun = datetime.datetime.now().strftime("%Y-%m")
        
    rw = current_user.rw
    query_rt = db.query(models.User.rt).filter(models.User.rw == rw).distinct().all()
    rts = [r[0] for r in query_rt if r[0]]
    
    rekap = []
    for rt_num in rts:
        rt_chair = db.query(models.User).filter(models.User.rt == rt_num, models.User.rw == rw, models.User.role == "rt").first()
        
        is_paid = False
        if rt_chair:
            is_paid = db.query(models.Keuangan).filter(
                models.Keuangan.user_id == rt_chair.id,
                models.Keuangan.kategori == "Kas RW",
                models.Keuangan.bulan_tahun == bulan_tahun
            ).first() is not None

        total_jiwa = db.query(models.User).filter(models.User.rt == rt_num, models.User.rw == rw).count()
        sudah_bayar = db.query(models.User).join(models.Keuangan, models.Keuangan.user_id == models.User.id).filter(
            models.User.rt == rt_num,
            models.User.rw == rw,
            models.Keuangan.tipe == "iuran",
            models.Keuangan.bulan_tahun == bulan_tahun
        ).count()

        rekap.append({
            "rt": rt_num,
            "rt_chair_id": rt_chair.id if rt_chair else None,
            "status_kas_rw": "Lunas" if is_paid else "Belum Setor",
            "performa_warga": {
                "total": total_jiwa,
                "sudah": sudah_bayar,
                "belum": total_jiwa - sudah_bayar,
                "persen": (sudah_bayar / total_jiwa * 100) if total_jiwa > 0 else 0
            }
        })
        
    return rekap

@router.get("/unpaid")
def get_unpaid_warga(
    rt: Optional[str] = None, 
    rw: Optional[str] = None, 
    bulan_tahun: Optional[str] = None,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == "warga":
        raise HTTPException(status_code=403, detail="Akses ditolak")
        
    if not bulan_tahun:
        bulan_tahun = datetime.datetime.now().strftime("%Y-%m")
    
    if not rw and current_user.role == "rw":
        rw = current_user.rw
        
    # Ambil SEMUA orang di wilayah tersebut tanpa melihat role
    query = db.query(models.User)
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
        
    all_warga = query.all()
    
    # Get paid user IDs for this specific month
    paid_user_ids = db.query(models.Keuangan.user_id).filter(
        models.Keuangan.tipe == "iuran",
        models.Keuangan.bulan_tahun == bulan_tahun
    ).all()
    paid_user_ids = [p[0] for p in paid_user_ids]
    
    unpaid = [w for w in all_warga if w.id not in paid_user_ids]
    
    return unpaid
