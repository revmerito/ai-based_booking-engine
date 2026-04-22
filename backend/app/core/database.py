"""
Database Configuration
SQLModel + Async SQLAlchemy setup.
Development mein SQLite, Production mein PostgreSQL use karo.
"""
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Please configure it in your Railway service variables."
    )

# Async engine banate hain - SQLite ke liye aiosqlite driver
connect_args = {}
engine_args = {
    "echo": settings.DEBUG,
    "future": True,
}

if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False
else:
    # Postgres specific optimization (Transaction Pooler compatibility)
    connect_args["statement_cache_size"] = 0
    engine_args["pool_size"] = 20
    engine_args["max_overflow"] = 10
    engine_args["pool_timeout"] = 30
    engine_args["pool_pre_ping"] = True

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_args
)

# Session factory - har request ke liye new session
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """
    Database tables create karta hai agar exist nahi karte.
    App startup par call hota hai.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    """
    Dependency injection ke liye session provide karta hai.
    FastAPI routes mein use hota hai.
    """
    async with async_session() as session:
        yield session
