import sys
import os
sys.path.append(os.getcwd())

from app.database import engine
from sqlalchemy import text

def sync_jabatan():
    with engine.connect() as conn:
        print("Menyamakan 'jabatan' dengan 'role' untuk data lama...")
        try:
            # Set jabatan='Ketua' untuk role 'rw', 'rt', 'lurah'
            conn.execute(text("UPDATE users SET jabatan = 'Ketua' WHERE role IN ('rw', 'rt', 'lurah')"))
            conn.commit()
            print("Sinkronisasi berhasil!")
        except Exception as e:
            print(f"Gagal sinkronisasi: {e}")

if __name__ == "__main__":
    sync_jabatan()
