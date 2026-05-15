from pydantic import BaseModel
from typing import Optional, List
import datetime

# ─── AUTH SCHEMAS ────────────────────────────────────────────────
class UserLogin(BaseModel):
    nik: str
    password: str

class UserInfo(BaseModel):
    id: str
    nama: str
    nik: str
    rt: Optional[str] = None
    rw: Optional[str] = None
    no_telp: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_info: UserInfo

class TokenData(BaseModel):
    nik: Optional[str] = None
    role: Optional[str] = None


# ─── WARGA SCHEMAS ───────────────────────────────────────────────
class WargaCreate(BaseModel):
    nomor_kk: Optional[str] = None
    nik: str
    nama: str
    password: Optional[str] = None
    alamat: Optional[str] = None
    no_telp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    foto: Optional[str] = None
    rt: Optional[str] = None
    rw: Optional[str] = None
    desa_kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kabupaten: Optional[str] = None
    role: Optional[str] = "warga"
    is_fakir: Optional[bool] = False
    is_miskin: Optional[bool] = False
    is_ibu_hamil: Optional[bool] = False
    is_balita: Optional[bool] = False

class WargaUpdate(BaseModel):
    nomor_kk: Optional[str] = None
    nama: Optional[str] = None
    alamat: Optional[str] = None
    no_telp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    foto: Optional[str] = None
    rt: Optional[str] = None
    rw: Optional[str] = None
    desa_kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kabupaten: Optional[str] = None
    role: Optional[str] = None
    is_fakir: Optional[bool] = None
    is_miskin: Optional[bool] = None
    is_ibu_hamil: Optional[bool] = None
    is_balita: Optional[bool] = None

class WargaResponse(BaseModel):
    id: str
    nomor_kk: Optional[str] = None
    nik: Optional[str] = None
    nama: str
    alamat: Optional[str] = None
    no_telp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    foto: Optional[str] = None
    rt: Optional[str] = None
    rw: Optional[str] = None
    desa_kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None
    kabupaten: Optional[str] = None
    role: str
    is_active: bool = True          # ← tambahan: status aktif akun
    is_fakir: bool
    is_miskin: bool
    is_ibu_hamil: bool
    is_balita: bool
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True



# ─── IURAN SCHEMAS ───────────────────────────────────────────────
class IuranCreate(BaseModel):
    nominal: float
    keterangan: Optional[str] = None
    user_id: Optional[str] = None
    rt_id: Optional[str] = None
    bulan_tahun: Optional[str] = None  # Format: YYYY-MM

class IuranUpdate(BaseModel):
    nominal: Optional[float] = None
    keterangan: Optional[str] = None
    bulan_tahun: Optional[str] = None

class IuranResponse(BaseModel):
    id: str
    tipe: str
    kategori: str
    nominal: float
    keterangan: Optional[str] = None
    user_id: Optional[str] = None
    rt_id: Optional[str] = None
    bulan_tahun: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


# ─── BANSOS SCHEMAS ──────────────────────────────────────────────
class BansosFilter(BaseModel):
    is_fakir: Optional[bool] = None
    is_miskin: Optional[bool] = None
    is_ibu_hamil: Optional[bool] = None
    is_balita: Optional[bool] = None
    rt: Optional[str] = None
    rw: Optional[str] = None

class BansosResponse(BaseModel):
    id: str
    nik: Optional[str] = None
    nama: str
    alamat: Optional[str] = None
    rt: Optional[str] = None
    rw: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_fakir: bool
    is_miskin: bool
    is_ibu_hamil: bool
    is_balita: bool

    class Config:
        from_attributes = True


# ─── STATS SCHEMA ────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_warga: int
    total_rt: int
    total_rw: int
    total_iuran_bulan_ini: float
    total_bansos_penerima: int
    warga_per_rt: dict
