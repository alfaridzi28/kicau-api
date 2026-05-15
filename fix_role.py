import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Change role of Salsya to 'rt'
with engine.connect() as conn:
    result = conn.execute(text("UPDATE users SET role = 'rt' WHERE nama LIKE 'Salsya Sabrina%'"))
    conn.commit()
    print(f"Updated {result.rowcount} users.")
