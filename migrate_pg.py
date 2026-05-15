import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tanda_tangan TEXT")
        conn.commit()
        print("Column 'tanda_tangan' ensured in PostgreSQL.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error migrating PostgreSQL: {e}")

if __name__ == "__main__":
    migrate()
