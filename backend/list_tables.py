import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import get_settings

async def check():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, connect_args={"statement_cache_size": 0})
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [r[0] for r in res]
        print("\n=== DATABASE TABLES FOUND ===")
        for t in sorted(tables):
            print(f"- {t}")
        print("============================\n")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
