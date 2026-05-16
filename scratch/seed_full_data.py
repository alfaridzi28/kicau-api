import datetime
import random
import uuid
from app import database, models
from app.core.security import get_password_hash

def seed_data():
    db = next(database.get_db())
    
    print("START: Memperbaiki dan menyegarkan data KICAU (Full Clean)...")

    # Clean in correct order to respect Foreign Keys
    db.query(models.PeminjamanAset).delete()
    db.query(models.Aset).delete()
    db.query(models.Keuangan).delete()
    db.query(models.Aduan).delete()
    db.query(models.SuratPengantar).delete()
    db.query(models.User).filter(models.User.role == "warga").delete()
    db.commit()

    # --- 1. USERS (Warga) ---
    rts = ["01", "02", "03", "04", "05"]
    rw = "19"
    nama_depan = ["Budi", "Siti", "Agus", "Dewi", "Eko", "Ani", "Bambang", "Rina", "Dedi", "Maya", "Ruben", "Dimas", "Asep", "Cecep"]
    nama_belakang = ["Santoso", "Lestari", "Saputra", "Wulandari", "Hidayat", "Sari", "Wijaya", "Putri", "Kurniawan", "Sitorus", "Gultom", "Pratama"]

    users = []
    for rt in rts:
        for i in range(12):
            new_user = models.User(
                id=str(uuid.uuid4()),
                nik="".join([str(random.randint(0, 9)) for _ in range(16)]),
                nama=f"{random.choice(nama_depan)} {random.choice(nama_belakang)}",
                password=get_password_hash("password123"),
                role="warga",
                rt=rt,
                rw=rw,
                no_telp=f"0812{random.randint(10000000, 99999999)}",
                alamat=f"Jl. Kicau Raya No. {random.randint(1, 100)}",
                desa_kelurahan="Lontar",
                kecamatan="Sambikerep",
                is_active=True,
                is_fakir=random.random() > 0.9,
                is_miskin=random.random() > 0.8
            )
            db.add(new_user)
            users.append(new_user)
    
    db.commit()
    print(f"OK: {len(users)} Warga berhasil dibuat.")

    # --- 2. IURAN (Tipe: 'iuran') ---
    current_bulan = datetime.datetime.now().strftime("%Y-%m")
    for u in users:
        if random.random() > 0.3:
            db.add(models.Keuangan(
                id=str(uuid.uuid4()),
                tipe="iuran",
                kategori="Iuran Bulanan",
                nominal=50000,
                keterangan=f"Iuran Keamanan {current_bulan}",
                user_id=u.id,
                bulan_tahun=current_bulan,
                created_at=datetime.datetime.utcnow()
            ))
    
    db.commit()
    print("OK: Data Iuran berhasil disemai.")

    # --- 3. ADUAN ---
    for _ in range(15):
        u = random.choice(users)
        db.add(models.Aduan(
            id=str(uuid.uuid4()),
            judul=random.choice(["Jalan Rusak", "Lampu Mati", "Sampah"]),
            isi="Mohon bantuan tindak lanjut.",
            user_id=u.id,
            status=random.choice(["belum_dibaca", "diproses", "selesai"]),
            created_at=datetime.datetime.utcnow()
        ))
    
    db.commit()
    print("OK: Aduan berhasil disemai.")

    print("\nFINISH: Data Beranda sekarang 100% AKURAT!")

if __name__ == "__main__":
    seed_data()
