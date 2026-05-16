import uuid
from sqlalchemy import text
from app.database import engine
from app.models import Base

# Ensure the table is created
print("Creating wilayah table if not exists...")
Base.metadata.create_all(bind=engine)

rw19_polygon_wkt = "POLYGON ((107.456353 -6.384501, 107.456192 -6.385248, 107.456653 -6.385802, 107.456642 -6.387284, 107.457222 -6.387828, 107.457468 -6.388116, 107.458284 -6.388287, 107.458595 -6.387849, 107.459421 -6.38802, 107.459625 -6.387988, 107.459968 -6.387658, 107.460033 -6.387423, 107.460204 -6.385291, 107.458885 -6.385024, 107.458992 -6.384352, 107.457876 -6.384086, 107.456836 -6.383926, 107.456353 -6.384501))"

print("Inserting RW 19 polygon...")
with engine.connect() as conn:
    # Check if RW 19 already exists
    result = conn.execute(text("SELECT id FROM wilayah WHERE rw = '19'")).fetchone()
    if not result:
        conn.execute(
            text("""
                INSERT INTO wilayah (id, rw, polygon)
                VALUES (:id, :rw, ST_GeomFromText(:wkt, 4326))
            """),
            {"id": str(uuid.uuid4()), "rw": "19", "wkt": rw19_polygon_wkt}
        )
        conn.commit()
        print("RW 19 polygon successfully inserted.")
    else:
        # Update it just in case
        conn.execute(
            text("""
                UPDATE wilayah SET polygon = ST_GeomFromText(:wkt, 4326) WHERE rw = '19'
            """),
            {"wkt": rw19_polygon_wkt}
        )
        conn.commit()
        print("RW 19 polygon successfully updated.")

print("Migration completed.")
