from app import database, models
from sqlalchemy import func

db = next(database.get_db())

print("--- REKAPITULASI DATA DATABASE KICAU ---")
print(f"Total Warga: {db.query(models.User).count()}")
print(f"Total Iuran (Semua): {db.query(models.Keuangan).filter(models.Keuangan.tipe == 'iuran').count()}")

print("\n--- SEBARAN WILAYAH (Warga per RT/RW) ---")
sebaran = db.query(models.User.rt, models.User.rw, func.count(models.User.id)).group_by(models.User.rt, models.User.rw).all()
for rt, rw, count in sebaran:
    print(f"RT: {rt} | RW: {rw} | Jumlah: {count} Warga")

print("\n--- ADUAN & SURAT ---")
print(f"Total Aduan: {db.query(models.Aduan).count()}")
print(f"Total Surat: {db.query(models.SuratPengantar).count()}")

print("\n--- KESIMPULAN ---")
if db.query(models.User).count() > 0:
    print("✅ Data sudah ada di database.")
else:
    print("❌ Database masih kosong!")
