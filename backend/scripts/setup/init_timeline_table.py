import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.core.database import engine
from app.models.timeline import BookingTimeline
from sqlmodel import SQLModel

async def run():
    print("Creating tables...")
    async with engine.begin() as conn:
        # This will create all tables defined in SQLModel metadata that don't exist
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(run())
