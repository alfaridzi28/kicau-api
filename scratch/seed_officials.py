import datetime
import uuid
import random
from sqlalchemy.orm import Session
from app import database, models
from app.core.security import get_password_hash

def seed_officials_refined_roles():
    db = next(database.get_db())
    print("START: Sinkronisasi Role & Jabatan (Role = Tingkat Wilayah)...")

    # Data wilayah target
    RW = "19"
    RT_01 = "01"

    # Bersihkan data lama
    db.query(models.Pemberitahuan).delete()
    db.query(models.SuratPengantar).delete()
    db.query(models.Keuangan).delete()
    db.query(models.Aduan).delete()
    db.query(models.User).filter(models.User.role.in_(["rw", "rt", "lurah", "staff"])).delete(synchronize_session=False)
    db.commit()

    officials = [
        # --- RW LEVEL ---
        {
            "nama": "H. Ahmad Subarjo",
            "role": "rw", # Tingkat RW
            "jabatan": "Ketua RW 19",
            "rt": RT_01, "rw": RW, "nik": "3200000000000001"
        },
        {
            "nama": "Rizky Ramadhan",
            "role": "rw", # SEKARANG ROLE TETAP RW (Bukan Staff)
            "jabatan": "Sekretaris RW 19",
            "rt": RT_01, "rw": RW, "nik": "3200000000000002"
        },
        # --- RT LEVEL ---
        {
            "nama": "Bpk. Supriatna",
            "role": "rt", # Tingkat RT
            "jabatan": "Ketua RT 01",
            "rt": RT_01, "rw": RW, "nik": "3200000000000003"
        },
        {
            "nama": "Ibu Ratna Sari",
            "role": "rt", # SEKARANG ROLE TETAP RT (Bukan Staff)
            "jabatan": "Bendahara RT 01",
            "rt": RT_01, "rw": RW, "nik": "3200000000000004"
        },
        # --- LURAH LEVEL ---
        {
            "nama": "Bpk. Heru Santoso",
            "role": "lurah",
            "jabatan": "Lurah Lontar",
            "rt": None, "rw": None, "nik": "3200000000000005"
        },
        {
            "nama": "Maya Sartika",
            "role": "lurah", # SEKARANG ROLE TETAP LURAH (Bukan Staff)
            "jabatan": "Staf Administrasi Kelurahan",
            "rt": None, "rw": None, "nik": "3200000000000006"
        }
    ]

    for off in officials:
        new_off = models.User(
            id=str(uuid.uuid4()),
            nik=off["nik"],
            nama=off["nama"],
            password=get_password_hash("password123"),
            role=off["role"],
            jabatan=off["jabatan"],
            rt=off["rt"],
            rw=off["rw"],
            no_telp=f"0812{random.randint(10000000, 99999999)}",
            is_active=True,
            desa_kelurahan="Lontar",
            kecamatan="Sambikerep"
        )
        db.add(new_off)
    
    db.commit()
    print(f"OK: Role disederhanakan. Staff sekarang menggunakan Role Wilayah (RT/RW/Lurah) dengan Jabatan spesifik.")

if __name__ == "__main__":
    seed_officials_refined_roles()
