from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer
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
    now = datetime.datetime.now()
    bulan_tahun = now.strftime("%Y-%m")
    
    # Base queries
    q_warga = db.query(models.User)
    q_iuran = db.query(func.sum(models.Keuangan.nominal)).filter(models.Keuangan.tipe == "iuran", models.Keuangan.bulan_tahun == bulan_tahun)
    q_aduan = db.query(models.Aduan)
    q_surat = db.query(models.SuratPengantar)
    q_bansos = db.query(models.User).filter((models.User.is_fakir == True) | (models.User.is_miskin == True) | (models.User.is_ibu_hamil == True) | (models.User.is_balita == True))

    # Apply Filters based on role
    if current_user.role == 'rt':
        rt_val = str(current_user.rt).strip() if current_user.rt else ""
        rw_val = str(current_user.rw).strip() if current_user.rw else ""
        q_warga = q_warga.filter(models.User.rt == rt_val, models.User.rw == rw_val)
        q_aduan = q_aduan.join(models.User, models.Aduan.user_id == models.User.id).filter(models.User.rt == rt_val, models.User.rw == rw_val)
        q_surat = q_surat.join(models.User, models.SuratPengantar.user_id == models.User.id).filter(models.User.rt == rt_val, models.User.rw == rw_val)
        q_bansos = q_bansos.filter(models.User.rt == rt_val, models.User.rw == rw_val)
        q_iuran = q_iuran.join(models.User, models.Keuangan.user_id == models.User.id).filter(models.User.rt == rt_val, models.User.rw == rw_val)
    elif current_user.role == 'rw':
        rw_val = str(current_user.rw).strip() if current_user.rw else ""
        q_warga = q_warga.filter(models.User.rw == rw_val)
        q_aduan = q_aduan.join(models.User, models.Aduan.user_id == models.User.id).filter(models.User.rw == rw_val)
        q_surat = q_surat.join(models.User, models.SuratPengantar.user_id == models.User.id).filter(models.User.rw == rw_val)
        q_bansos = q_bansos.filter(models.User.rw == rw_val)
        q_iuran = q_iuran.join(models.User, models.Keuangan.user_id == models.User.id).filter(models.User.rw == rw_val)
    
    # Global/Lurah role (no filter needed, shows all in kelurahan)
    else:
        pass

    total_jiwa = q_warga.count()
    total_iuran = q_iuran.scalar() or 0
    total_aduan = q_aduan.count()
    total_surat = q_surat.count()
    total_bansos = q_bansos.count()

    # Iuran details for the chart
    bayar_count = db.query(models.Keuangan.user_id).filter(models.Keuangan.tipe == "iuran", models.Keuangan.bulan_tahun == bulan_tahun).distinct()
    if current_user.role == 'rt':
        bayar_count = bayar_count.join(models.User, models.Keuangan.user_id == models.User.id).filter(models.User.rt == current_user.rt, models.User.rw == current_user.rw)
    elif current_user.role == 'rw':
        bayar_count = bayar_count.join(models.User, models.Keuangan.user_id == models.User.id).filter(models.User.rw == current_user.rw)
    
    count_sudah = bayar_count.count()
    count_belum = max(0, total_jiwa - count_sudah)

    # Regional distribution (RT)
    warga_per_rt_raw = db.query(models.User.rt, func.count(models.User.id)).filter(models.User.rt.isnot(None)).group_by(models.User.rt).all()
    warga_per_rt = {}
    for rt, count in warga_per_rt_raw:
        if rt:
            clean_rt = str(rt).strip().lstrip('0') or '0'
            warga_per_rt[clean_rt] = warga_per_rt.get(clean_rt, 0) + count

    # Regional distribution (RW)
    warga_per_rw_raw = db.query(models.User.rw, func.count(models.User.id)).filter(models.User.rw.isnot(None)).group_by(models.User.rw).all()
    sebaran_rw = {str(rw).strip(): count for rw, count in warga_per_rw_raw if rw}

    # Efektivitas Sosial (Percentage of citizens with bansos flags)
    efektivitas_sosial = 0
    if total_jiwa > 0:
        efektivitas_sosial = round((total_bansos / total_jiwa) * 100)

    return {
        "total_warga": total_jiwa,
        "total_iuran_bulan_ini": total_iuran,
        "total_bansos_penerima": total_bansos,
        "total_aduan": total_aduan,
        "total_surat": total_surat,
        "efektivitas_sosial": efektivitas_sosial,
        "iuran_stats": {
            "sudah_bayar": count_sudah,
            "belum_bayar": count_belum
        },
        "warga_per_rt": warga_per_rt,
        "sebaran_rw": sebaran_rw,
        "server_time": now.strftime("%d-%m-%Y %H:%M:%S"),
        "kecamatan": current_user.kecamatan or "Sambikerep",
        "kelurahan": current_user.desa_kelurahan or "Lontar"
    }

@router.get("/regions")
def get_regions(db: Session = Depends(database.get_db)):
    rws = db.query(models.User.rw).filter(models.User.rw.isnot(None)).distinct().all()
    rts = db.query(models.User.rt).filter(models.User.rt.isnot(None)).distinct().all()
    
    return {
        "rw_list": sorted([r[0] for r in rws if r[0]]),
        "rt_list": sorted([r[0] for r in rts if r[0]])
    }
