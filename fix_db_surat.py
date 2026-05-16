import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'surat_pengantar'")
    columns = [row[0] for row in cur.fetchall()]
    print("Columns:", columns)
    
    if "file_ttd_digital" not in columns:
        print("Missing file_ttd_digital. Altering table...")
        cur.execute("ALTER TABLE surat_pengantar ADD COLUMN file_ttd_digital TEXT")
        conn.commit()
    
    if "catatan" not in columns:
        print("Missing catatan. Altering table...")
        cur.execute("ALTER TABLE surat_pengantar ADD COLUMN catatan TEXT")
        conn.commit()
        
    print("Done checking columns.")
except Exception as e:
    print("Error:", e)
