import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT nik, password, role FROM users WHERE role = 'rt' LIMIT 1")
    user = cur.fetchone()
    print("RT User:", user)
except Exception as e:
    print("Error:", e)
