from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app import database, models
from app.core.security import get_current_user
import datetime

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    total_warga = db.query(models.User).filter(models.User.role == "warga").count()
    total_rt = db.query(func.count(func.distinct(models.User.rt))).scalar()
    total_rw = db.query(func.count(func.distinct(models.User.rw))).scalar()
    
    # Total iuran bulan ini
    now = datetime.datetime.now()
    bulan_tahun = now.strftime("%Y-%m")
    total_iuran = db.query(func.sum(models.Keuangan.nominal)).filter(
        models.Keuangan.tipe == "iuran",
        models.Keuangan.bulan_tahun == bulan_tahun
    ).scalar() or 0
    
    total_bansos = db.query(models.User).filter(
        (models.User.is_fakir == True) | (models.User.is_miskin == True)
    ).count()

    total_aduan = db.query(models.Aduan).count()
    total_surat = db.query(models.SuratPengantar).count()

    # Warga per RT
    warga_per_rt_raw = db.query(models.User.rt, func.count(models.User.id)).group_by(models.User.rt).all()
    warga_per_rt = {str(rt): count for rt, count in warga_per_rt_raw if rt}

    return {
        "total_warga": total_warga,
        "total_rt": total_rt,
        "total_rw": total_rw,
        "total_iuran_bulan_ini": total_iuran,
        "total_bansos_penerima": total_bansos,
        "total_aduan": total_aduan,
        "total_surat": total_surat,
        "warga_per_rt": warga_per_rt
    }
