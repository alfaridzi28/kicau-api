from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from .database import Base
import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nomor_kk = Column(String(20), nullable=True)
    nik = Column(String(20), unique=True, index=True, nullable=True)
    nama = Column(String(255), nullable=False)
    password = Column(String(255), nullable=True)
    alamat = Column(Text, nullable=True)
    no_telp = Column(String(20), nullable=True)
    
    # Lokasi spasial (Point PostGIS) untuk Geospatial
    lokasi = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    foto = Column(Text, nullable=True)
    tanda_tangan = Column(Text, nullable=True)
    rt = Column(String(10), nullable=True)
    rw = Column(String(10), nullable=True)
    desa_kelurahan = Column(String(100), nullable=True)
    kecamatan = Column(String(100), nullable=True)
    role = Column(String(50), default="warga")
    jabatan = Column(String(100), default="Warga") # Ketua, Sekretaris, Bendahara, Staff, Warga
    is_active = Column(Boolean, default=True)
    
    # Kategori Bansos / Kondisi Khusus
    is_fakir = Column(Boolean, default=False)
    is_miskin = Column(Boolean, default=False)
    is_ibu_hamil = Column(Boolean, default=False)
    is_balita = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    @property
    def effective_role(self):
        if self.role == "staff":
            if self.rt:
                return "rt"
            elif self.rw:
                return "rw"
            else:
                return "lurah"
        return self.role

class Pemberitahuan(Base):
    __tablename__ = "pemberitahuan"

    id = Column(Integer, primary_key=True, index=True)
    judul = Column(String(255), nullable=False)
    isi = Column(Text, nullable=False)
    foto = Column(Text, nullable=True)
    target_rt = Column(String(10), nullable=True)
    target_rw = Column(String(10), nullable=True)
    is_publik = Column(Boolean, default=True)  # Tampil di dashboard publik
    created_by = Column(String(36), ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    expired_at = Column(TIMESTAMP, nullable=True)  # Auto-delete setelah 3 bulan

class SuratPengantar(Base):
    __tablename__ = "surat_pengantar"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kategori = Column(String(100), nullable=False)  # ktp, kematian, pindah, ganti_kk
    keterangan = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    user_id = Column(String(36), ForeignKey('users.id'))
    user = relationship('User', foreign_keys=[user_id])
    rt_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    file_ttd_digital = Column(Text, nullable=True)  # Base64 PNG tanda tangan
    catatan = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

class Aduan(Base):
    __tablename__ = "aduan"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    judul = Column(String(255), nullable=False)
    isi = Column(Text, nullable=False)
    status = Column(String(50), default="belum_dibaca")  # belum_dibaca, diproses, selesai
    foto_bukti = Column(Text, nullable=True)       # Foto aduan dari warga
    foto_selesai = Column(Text, nullable=True)     # Foto bukti selesai dari RT/RW
    latitude = Column(Float, nullable=True)               # Lokasi kejadian
    longitude = Column(Float, nullable=True)
    user_id = Column(String(36), ForeignKey('users.id'))
    user = relationship('User', foreign_keys=[user_id])
    rt_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    balasan = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

class Keuangan(Base):
    __tablename__ = "keuangan"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tipe = Column(String(20), nullable=False)  # pemasukan, pengeluaran, iuran
    kategori = Column(String(100), nullable=False)
    nominal = Column(Float, nullable=False)
    keterangan = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    rt_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    bulan_tahun = Column(String(20), nullable=True)  # Format: YYYY-MM
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

class IuranSetting(Base):
    """Pengaturan besaran iuran per RT (bisa diatur oleh RT atau RW)"""
    __tablename__ = "iuran_setting"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rt = Column(String(10), nullable=False)
    rw = Column(String(10), nullable=False)
    nominal = Column(Float, nullable=False, default=50000)
    tanggal_mulai = Column(String(20), nullable=True)  # Format: YYYY-MM
    keterangan = Column(Text, nullable=True)
    set_by = Column(String(36), ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

class Aset(Base):
    __tablename__ = "aset"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nama_aset = Column(String(255), nullable=False)
    deskripsi = Column(Text, nullable=True)
    jumlah = Column(Integer, default=1)
    foto = Column(Text, nullable=True)           # URL foto aset
    status = Column(String(50), default="tersedia")     # tersedia, dipinjam, tidak_layak
    kepemilikan = Column(String(50), nullable=False)    # aset_rw, aset_rt
    pemilik_id = Column(String(36), ForeignKey('users.id'))
    pemilik = relationship('User', foreign_keys=[pemilik_id])
    rt = Column(String(10), nullable=True)
    rw = Column(String(10), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

class PeminjamanAset(Base):
    """Sistem peminjaman aset oleh warga atau antar RT/RW"""
    __tablename__ = "peminjaman_aset"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aset_id = Column(String(36), ForeignKey('aset.id'), nullable=False)
    peminjam_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    peminjam = relationship('User', foreign_keys=[peminjam_id])
    disetujui_oleh = Column(String(36), ForeignKey('users.id'), nullable=True)
    status = Column(String(50), default="menunggu")     # menunggu, disetujui, ditolak, dikembalikan
    keperluan = Column(Text, nullable=True)
    tanggal_pinjam = Column(TIMESTAMP, nullable=True)
    tanggal_kembali_rencana = Column(TIMESTAMP, nullable=True)
    tanggal_kembali_aktual = Column(TIMESTAMP, nullable=True)
    catatan = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

class Wilayah(Base):
    __tablename__ = "wilayah"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rt = Column(String(10), nullable=True)
    rw = Column(String(10), nullable=True)
    polygon = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
