from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import database, models
from app.core.security import get_current_user
from sqlalchemy import or_

router = APIRouter(prefix="/aset", tags=["aset"])

@router.get("/")
def get_aset(
    kepemilikan: str = None, 
    status: str = None, 
    rt: str = None, 
    rw: str = None, 
    search: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Aset)
    
    # NEW HIERARCHY LOGIC FOR VISIBILITY:
    if current_user.role == 'warga':
        # Warga sees assets from their RT and their RW
        query = query.filter(
            models.Aset.rw == current_user.rw,
            or_(
                models.Aset.rt == current_user.rt,
                models.Aset.rt == None,
                models.Aset.rt == ''
            )
        )
    elif current_user.role == 'rt':
        # RT sees their own assets AND assets of their RW
        query = query.filter(
            models.Aset.rw == current_user.rw,
            or_(
                models.Aset.rt == current_user.rt,
                models.Aset.rt == None,
                models.Aset.rt == ''
            )
        )
    elif current_user.role == 'rw':
        # RW sees their own assets AND all RT assets in their RW
        query = query.filter(models.Aset.rw == current_user.rw)
    elif current_user.role == 'lurah':
        # Lurah sees everything in their kelurahan by default
        pass
    
    # Specific filtering from query params
    if status and status != 'all':
        query = query.filter(models.Aset.status == status)
        
    if search:
        query = query.filter(models.Aset.nama_aset.ilike(f"%{search}%"))
    if kepemilikan:
        query = query.filter(models.Aset.kepemilikan == kepemilikan)
        
    # Manual region filters for Lurah/Superadmin
    if (rt or rw) and current_user.role in ['lurah', 'superadmin']:
        if rt: query = query.filter(models.Aset.rt == rt)
        if rw: query = query.filter(models.Aset.rw == rw)
            
    total = query.count()
    items = query.order_by(models.Aset.created_at.desc()).offset(skip).limit(limit).all()
            
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }

@router.post("/")
def create_aset(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_a = models.Aset(
        **data,
        pemilik_id=current_user.id
    )
    db.add(new_a)
    db.commit()
    db.refresh(new_a)
    return new_a

@router.post("/pinjam")
def pinjam_aset(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    aset_id = data.get("aset_id")
    aset = db.query(models.Aset).filter(models.Aset.id == aset_id).first()
    if not aset:
        raise HTTPException(status_code=404, detail="Aset tidak ditemukan")
    
    if aset.status != "tersedia":
        raise HTTPException(status_code=400, detail="Aset sedang tidak tersedia (sedang dipinjam atau rusak)")
        
    new_p = models.PeminjamanAset(
        aset_id=aset_id,
        peminjam_id=current_user.id,
        keperluan=data.get("keperluan"),
        status="menunggu"
    )
    db.add(new_p)
    db.commit()
    db.refresh(new_p)
    return new_p

@router.get("/peminjaman")
def get_peminjaman(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Requests FOR my assets (for RT/RW to approve)
    # 2. Requests BY me (to see my own status)
    
    from sqlalchemy import or_
    query = db.query(models.PeminjamanAset).join(models.Aset)
    
    if current_user.role == "warga":
        query = query.filter(models.PeminjamanAset.peminjam_id == current_user.id)
    elif current_user.role in ["rt", "rw"]:
        query = query.filter(
            or_(
                models.Aset.pemilik_id == current_user.id, # Requests for my assets
                models.PeminjamanAset.peminjam_id == current_user.id # My own requests to others
            )
        )
    elif current_user.role == "lurah":
        # Lurah sees everything in kelurahan (all requests joined with their assets)
        pass
        
    return query.order_by(models.PeminjamanAset.created_at.desc()).all()

@router.patch("/{aset_id}")
def update_aset(aset_id: str, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    aset = db.query(models.Aset).filter(models.Aset.id == aset_id).first()
    if not aset:
        raise HTTPException(status_code=404, detail="Aset tidak ditemukan")
    
    if current_user.role != "superadmin" and aset.pemilik_id != current_user.id:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    for key, value in data.items():
        if hasattr(aset, key):
            setattr(aset, key, value)
            
    db.commit()
    db.refresh(aset)
    return aset

@router.patch("/peminjaman/{peminjaman_id}")
def update_peminjaman_status(peminjaman_id: str, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    p = db.query(models.PeminjamanAset).filter(models.PeminjamanAset.id == peminjaman_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Peminjaman tidak ditemukan")
    
    new_status = data.get("status")
    
    # SECURITY: Only asset owner can approve/reject
    aset = db.query(models.Aset).filter(models.Aset.id == p.aset_id).first()
    if aset.pemilik_id != current_user.id and current_user.role not in ["superadmin", "lurah"]:
         raise HTTPException(status_code=403, detail="Hanya pemilik aset yang dapat memberikan persetujuan")

    p.status = new_status
    if new_status in ["disetujui", "ditolak"]:
        p.disetujui_oleh = current_user.id
    
    # Auto-update asset status
    if new_status == "disetujui":
        aset.status = "dipinjam"
    elif new_status == "dikembalikan":
        aset.status = "tersedia"
        
    db.commit()
    db.refresh(p)
    return p

@router.delete("/{aset_id}")
def delete_aset(aset_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    aset = db.query(models.Aset).filter(models.Aset.id == aset_id).first()
    if not aset:
        raise HTTPException(status_code=404, detail="Aset tidak ditemukan")
    
    if current_user.role != "superadmin" and aset.pemilik_id != current_user.id:
        raise HTTPException(status_code=403, detail="Hanya pemilik aset yang dapat menghapus")
        
    db.delete(aset)
    db.commit()
    return {"message": "Aset berhasil dihapus"}
