import sys
import os

# Tambahkan path ke folder project
sys.path.append(os.getcwd())

from app.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Menambahkan kolom 'jabatan' ke tabel 'users'...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS jabatan VARCHAR(100) DEFAULT 'Warga'"))
            conn.commit()
            print("Berhasil! Kolom 'jabatan' telah ditambahkan.")
        except Exception as e:
            print(f"Gagal migrasi: {e}")

if __name__ == "__main__":
    migrate()
