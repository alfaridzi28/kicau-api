import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# Check data_type
cur.execute("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'surat_pengantar' AND column_name = 'file_ttd_digital'")
print(cur.fetchone())

# Change data_type to TEXT
cur.execute("ALTER TABLE surat_pengantar ALTER COLUMN file_ttd_digital TYPE TEXT")
conn.commit()

print("Done altering.")
