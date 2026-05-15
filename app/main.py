from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from . import database, models
from app.core.security import verify_password, create_access_token, get_password_hash
from app.schemas import UserLogin, Token, UserInfo
from app.routers import warga, iuran, bansos, stats, aduan, surat, aset, iuran_setting
from app.routers import upload, pemberitahuan
import datetime

app = FastAPI(
    title="KICAU API",
    description="Sistem Backend KICAU - Pelayanan Administrasi Warga Digital",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static Files (upload gambar) ─────────────────────────────────
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
(static_dir / "uploads").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── Mount Routers ────────────────────────────────────────────────
app.include_router(warga.router)
app.include_router(iuran.router)
app.include_router(iuran_setting.router)
app.include_router(bansos.router)
app.include_router(stats.router)
app.include_router(aduan.router)
app.include_router(surat.router)
app.include_router(aset.router)
app.include_router(upload.router)
app.include_router(pemberitahuan.router)


@app.get("/")
def root():
    return {
        "message": "KICAU API v2.0 Berjalan",
        "docs": "/docs",
        "endpoints": ["/warga", "/iuran", "/iuran-setting", "/bansos", "/stats/dashboard",
                      "/aduan", "/surat", "/aset", "/upload", "/pemberitahuan"]
    }


@app.get("/health")
def health_check():
    try:
        db = next(database.get_db())
        db.execute(__import__('sqlalchemy').text("SELECT 1"))
        db.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@app.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.nik == user_credentials.nik).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NIK atau Password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun Anda telah dinonaktifkan. Hubungi superadmin.",
        )

    password_valid = False
    if user.password:
        try:
            password_valid = verify_password(user_credentials.password, user.password)
        except Exception:
            password_valid = (user_credentials.password == user.password)

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NIK atau Password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = datetime.timedelta(minutes=60 * 24 * 7)
    access_token = create_access_token(
        data={"sub": user.nik, "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_info": {
            "id": user.id,
            "nama": user.nama,
            "nik": user.nik,
            "role": user.role,
            "rt": user.rt,
            "rw": user.rw,
        }
    }
