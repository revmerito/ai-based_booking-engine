import asyncio
import sys
import os
from sqlalchemy import text

# Add backend to path
sys.path.append(os.getcwd())

from app.core.database import engine

async def run():
    print("Updating amenities table schema...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE amenities ADD COLUMN IF NOT EXISTS scope TEXT DEFAULT 'room';"))
            await conn.execute(text("ALTER TABLE amenities ADD COLUMN IF NOT EXISTS description TEXT;"))
            print("Successfully updated amenities table.")
        except Exception as e:
            print(f"Error updating table: {e}")

if __name__ == "__main__":
    asyncio.run(run())
