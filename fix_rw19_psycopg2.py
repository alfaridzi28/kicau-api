import psycopg2
import random

DATABASE_URL = "postgresql://postgres.suvydjiabwbtwuttynis:k1c4u_m4n14@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

def get_random_point_in_polygon():
    # Simple bounding box inside RW 19 polygon
    lon = random.uniform(107.457000, 107.459000)
    lat = random.uniform(-6.387000, -6.385000)
    return lat, lon

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM users WHERE rw = '19'")
    users = cur.fetchall()
    
    for user in users:
        lat, lon = get_random_point_in_polygon()
        cur.execute(
            "UPDATE users SET latitude = %s, longitude = %s WHERE id = %s",
            (lat, lon, user[0])
        )
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Updated {len(users)} users in RW 19")

if __name__ == "__main__":
    main()
