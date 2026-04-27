import asyncio
import logging
from sqlalchemy import text
from dotenv import load_dotenv
import os

# Load .env before importing engine
load_dotenv("backend/.env")

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def optimize_database():
    """
    Database performance ko improve karne ke liye indexes add karta hai.
    Correct table names (room_types, room_rates, etc.) use karta hai.
    """
    indexes = [
        # Bookings
        ("idx_bookings_hotel_id", "bookings", "hotel_id"),
        ("idx_bookings_status", "bookings", "status"),
        ("idx_bookings_dates", "bookings", "check_in, check_out"),
        
        # Room Rates
        ("idx_rates_hotel_date", "room_rates", "hotel_id, date_from, date_to"),
        ("idx_rates_room_type", "room_rates", "room_type_id"),
        
        # Availability
        ("idx_availability_hotel_date", "availability", "hotel_id, date"),
        
        # Analytics
        ("idx_analytics_hotel_event", "analytics_events", "hotel_id, event_type"),
        ("idx_analytics_timestamp", "analytics_events", "timestamp"),
        
        # Room Types
        ("idx_room_types_hotel", "room_types", "hotel_id"),
        
        # Amenity Links
        ("idx_room_amenity_links", "room_amenity_links", "room_id, amenity_id"),
    ]

    logger.info("Starting database optimization...")
    
    async with engine.connect() as conn:
        for idx_name, table, columns in indexes:
            try:
                # Check if table exists
                result = await conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
                if not result.scalar():
                    logger.warning(f"Table {table} does not exist. Skipping.")
                    continue

                # Check if index exists
                result = await conn.execute(text(f"SELECT 1 FROM pg_indexes WHERE indexname = '{idx_name}'"))
                if not result.fetchone():
                    logger.info(f"Creating index {idx_name} on {table}({columns})...")
                    await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})"))
                    await conn.commit()
                    logger.info(f"Index {idx_name} processed.")
                else:
                    logger.info(f"Index {idx_name} already exists. Skipping.")
            except Exception as e:
                logger.warning(f"Skipping index {idx_name} for {table}: {e}")
                await conn.rollback()
        
        # ANALYZE tables for query planner optimization
        try:
            logger.info("Running ANALYZE to optimize query planner...")
            await conn.execute(text("ANALYZE"))
            await conn.commit()
            logger.info("Database optimization complete!")
        except Exception as e:
            logger.error(f"ANALYZE failed: {e}")

if __name__ == "__main__":
    asyncio.run(optimize_database())
