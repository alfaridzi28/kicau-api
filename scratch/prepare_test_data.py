"""
Script untuk menyiapkan semua data pengurus yang diperlukan untuk testing.
Jalankan dengan: python scratch/prepare_test_data.py
"""
import uuid
import random
from app import database, models
from app.core.security import get_password_hash

def prepare():
    db = next(database.get_db())
    hashed = get_password_hash("password123")
    
    officials = [
        # Lurah
        {"nama": "Bpk. Heru Santoso",   "role": "lurah", "jabatan": "Lurah Lontar",                  "nik": "3200000000000010", "rt": None, "rw": None},
        {"nama": "Maya Sartika",          "role": "lurah", "jabatan": "Staf Administrasi Kelurahan",   "nik": "3200000000000011", "rt": None, "rw": None},
        # RW
        {"nama": "H. Ahmad Subarjo",     "role": "rw",    "jabatan": "Ketua RW 19",                   "nik": "3200000000000012", "rt": "01", "rw": "19"},
        {"nama": "Rizky Ramadhan",        "role": "rw",    "jabatan": "Sekretaris RW 19",              "nik": "3200000000000013", "rt": "01", "rw": "19"},
        # RT 01
        {"nama": "Bpk. Supriatna",       "role": "rt",    "jabatan": "Ketua RT 01",                   "nik": "3200000000000014", "rt": "01", "rw": "19"},
        {"nama": "Ibu Ratna Sari",        "role": "rt",    "jabatan": "Bendahara RT 01",               "nik": "3200000000000015", "rt": "01", "rw": "19"},
        # RT 02
        {"nama": "Bpk. Agus Wiratno",    "role": "rt",    "jabatan": "Ketua RT 02",                   "nik": "3200000000000016", "rt": "02", "rw": "19"},
    ]

    print("Mempersiapkan data pengurus...")
    for off in officials:
        existing = db.query(models.User).filter(models.User.nik == off["nik"]).first()
        if existing:
            # Update password and jabatan to be safe
            existing.password = hashed
            existing.jabatan = off["jabatan"]
            print(f"  Updated : {off['nama']} ({off['role']})")
        else:
            db.add(models.User(
                id=str(uuid.uuid4()),
                nik=off["nik"],
                nama=off["nama"],
                password=hashed,
                role=off["role"],
                jabatan=off["jabatan"],
                rt=off["rt"],
                rw=off["rw"],
                no_telp=f"0812{random.randint(10000000, 99999999)}",
                is_active=True,
                desa_kelurahan="Lontar",
                kecamatan="Sambikerep"
            ))
            print(f"  Dibuat  : {off['nama']} ({off['role']})")
    
    db.commit()

    # Tampilkan semua akun untuk testing
    print("\n=== AKUN TESTING ===")
    print(f"{'Role':<12} {'NIK':<20} {'Nama':<30} {'Jabatan'}")
    print("-" * 80)
    for role in ["superadmin", "lurah", "rw", "rt", "warga"]:
        users = db.query(models.User).filter(models.User.role == role).limit(2).all()
        for u in users:
            print(f"{u.role:<12} {u.nik:<20} {u.nama[:28]:<30} {u.jabatan or '-'}")
    
    print("\nPassword semua akun: password123")
    print("SELESAI!")

if __name__ == "__main__":
    prepare()
