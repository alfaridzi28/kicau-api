from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app import database, models
from app.schemas import BansosResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/bansos", tags=["bansos"])

@router.get("/", response_model=List[BansosResponse])
def get_bansos_eligible(
    rt: Optional[str] = None,
    rw: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.User).filter(
        (models.User.is_fakir == True) | 
        (models.User.is_miskin == True) |
        (models.User.is_ibu_hamil == True) |
        (models.User.is_balita == True)
    )
    
    if rt:
        query = query.filter(models.User.rt == rt)
    if rw:
        query = query.filter(models.User.rw == rw)
        
    return query.all()

@router.get("/stats")
def get_bansos_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return {
        "fakir": db.query(models.User).filter(models.User.is_fakir == True).count(),
        "miskin": db.query(models.User).filter(models.User.is_miskin == True).count(),
        "ibu_hamil": db.query(models.User).filter(models.User.is_ibu_hamil == True).count(),
        "balita": db.query(models.User).filter(models.User.is_balita == True).count()
    }
