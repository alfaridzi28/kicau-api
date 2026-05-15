import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

queries = [
    "ALTER TABLE pemberitahuan ADD COLUMN IF NOT EXISTS foto TEXT;",
    "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS foto_bukti TEXT;",
    "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS foto_selesai TEXT;",
    "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS latitude FLOAT;",
    "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS longitude FLOAT;",
    "ALTER TABLE aduan ADD COLUMN IF NOT EXISTS balasan TEXT;",
    "ALTER TABLE aset ADD COLUMN IF NOT EXISTS foto TEXT;",
    "ALTER TABLE surat_pengantar ADD COLUMN IF NOT EXISTS file_ttd_digital TEXT;",
    "ALTER TABLE surat_pengantar ADD COLUMN IF NOT EXISTS catatan TEXT;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS no_telp VARCHAR(20);",
    "ALTER TABLE users ALTER COLUMN foto TYPE TEXT;"
]

with engine.connect() as conn:
    for query in queries:
        try:
            conn.execute(text(query))
            print(f"Executed: {query}")
        except Exception as e:
            print(f"Error on {query}: {e}")
    conn.commit()
    print("Migration completed successfully.")
