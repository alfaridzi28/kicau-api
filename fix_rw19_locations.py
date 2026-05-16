import asyncio
import os
import random
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres.suvydjiabwbtwuttynis:k1c4u_m4n14@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

def get_random_point_in_polygon():
    # Simple bounding box inside RW 19 polygon to avoid shapely dependency
    # POLYGON ((107.456353 -6.384501, ...
    lon = random.uniform(107.457000, 107.459000)
    lat = random.uniform(-6.387000, -6.385000)
    return lat, lon

async def main():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        result = await session.execute(text("SELECT id FROM users WHERE rw = '19'"))
        users = result.fetchall()
        
        for user in users:
            lat, lon = get_random_point_in_polygon()
            # update users lat and lon
            await session.execute(
                text("UPDATE users SET lat = :lat, long = :lon WHERE id = :user_id"),
                {"lat": lat, "lon": lon, "user_id": user.id}
            )
        
        await session.commit()
        print(f"Updated {len(users)} users in RW 19")

if __name__ == "__main__":
    asyncio.run(main())
