from dotenv import load_dotenv
load_dotenv() # Load environment variables dari .env

from app.database import engine, SessionLocal, Base
from app import models
from sqlalchemy import text

# Membuat tabel-tabel di database Supabase
print("Menghubungkan ke Supabase dan membuat ekstensi postgis (jika belum ada)...")
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    conn.commit()

print("Membuat tabel-tabel...")
Base.metadata.create_all(bind=engine)
print("Tabel berhasil dibuat!")

# Inisialisasi Data
print("Mempersiapkan data contoh (Seeding)...")
db = SessionLocal()

# Cek apakah superadmin sudah ada
if not db.query(models.User).filter(models.User.nik == "3215252801990001").first():
    print("Memasukkan data user...")
    
    # User 1: Superadmin
    superadmin = models.User(
        nomor_kk="321525170001", nik="3215252801990001", nama="Muhammad Yusuf Rifqi Al Faridzi",
        password="password", alamat="Regency 2 blok i9/85", rt="1", rw="19",
        desa_kelurahan="cikampek utara", kecamatan="kotabaru", kabupaten="karawang", role="superadmin"
    )
    
    # User 2: RW
    rw = models.User(
        nomor_kk="321525170002", nik="3215252801990002", nama="Eko Sulistiyono",
        password="password", alamat="Regency 2 blok k2/43", rt="1", rw="19",
        desa_kelurahan="cikampek utara", kecamatan="kotabaru", kabupaten="karawang", role="rw"
    )
    
    # User 3: RT
    rt = models.User(
        nomor_kk="321525170003", nik="3215252801990003", nama="Salsya Sabrina Rismaya",
        password="password", alamat="Regency 2 blok i9/85", rt="1", rw="19",
        desa_kelurahan="cikampek utara", kecamatan="kotabaru", kabupaten="karawang", role="rt"
    )
    
    # User 4: Warga
    warga = models.User(
        nomor_kk="321525170004", nik="3215252801990004", nama="Willy Sabillu Rosyad",
        password="password", alamat="Regency 2 blok k2/43", rt="1", rw="19",
        desa_kelurahan="cikampek utara", kecamatan="kotabaru", kabupaten="karawang", role="warga"
    )
    
    db.add_all([superadmin, rw, rt, warga])
    db.commit()
    print("Berhasil memasukkan data: Superadmin, RW, RT, dan Warga!")
else:
    print("Data superadmin sudah ada. Melewati proses seeding data.")

db.close()
print("Selesai!")
