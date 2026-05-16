import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def sync_jabatan():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Set 'Ketua' for RT and RW
        cur.execute("UPDATE users SET jabatan = 'Ketua' WHERE role IN ('rt', 'rw')")
        
        # Set 'Warga Biasa' for regular warga
        cur.execute("UPDATE users SET jabatan = 'Warga Biasa' WHERE role = 'warga'")
        
        conn.commit()
        print("Successfully synchronized all jabatan in the database.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sync_jabatan()
