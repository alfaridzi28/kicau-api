from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import database, models
from app.core.security import get_current_user

router = APIRouter(prefix="/aset", tags=["aset"])

@router.get("/")
def get_aset(
    kepemilikan: str = None, 
    rt: str = None, 
    rw: str = None, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Aset)
    
    if kepemilikan:
        query = query.filter(models.Aset.kepemilikan == kepemilikan)
        
    # Filter based on RT/RW of the owner
    if rt or rw:
        query = query.join(models.User, models.Aset.pemilik_id == models.User.id)
        if rt:
            query = query.filter(models.User.rt == rt)
        if rw:
            query = query.filter(models.User.rw == rw)
            
    return query.all()

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
        raise HTTPException(status_code=400, detail="Aset sedang tidak tersedia")
        
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
    # RT/RW see requests for their assets
    # Warga see their own requests
    query = db.query(models.PeminjamanAset).join(models.Aset)
    
    if current_user.role == "warga":
        query = query.filter(models.PeminjamanAset.peminjam_id == current_user.id)
    elif current_user.role in ["rt", "rw"]:
        query = query.filter(models.Aset.pemilik_id == current_user.id)
        
    return query.order_by(models.PeminjamanAset.created_at.desc()).all()

@router.patch("/peminjaman/{peminjaman_id}")
def update_peminjaman_status(peminjaman_id: str, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    p = db.query(models.PeminjamanAset).filter(models.PeminjamanAset.id == peminjaman_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Peminjaman tidak ditemukan")
    
    new_status = data.get("status")
    p.status = new_status
    p.disetujui_oleh = current_user.id
    
    # Update aset status if approved
    aset = db.query(models.Aset).filter(models.Aset.id == p.aset_id).first()
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
    
    # Permission: Owner or Superadmin
    if current_user.role != "superadmin" and aset.pemilik_id != current_user.id:
        raise HTTPException(status_code=403, detail="Hanya pemilik atau superadmin yang dapat menghapus aset")
        
    # Validation: Check active peminjaman
    active_p = db.query(models.PeminjamanAset).filter(
        models.PeminjamanAset.aset_id == aset_id,
        models.PeminjamanAset.status.in_(["menunggu", "disetujui"])
    ).first()
    
    if active_p:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus aset yang sedang dalam proses peminjaman")
        
    db.delete(aset)
    db.commit()
    return {"detail": "Aset berhasil dihapus"}
