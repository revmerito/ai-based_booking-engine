"""
Application Configuration
Ye file environment variables se settings load karti hai.
Production mein .env file use karo.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


"""
Application Configuration
Ye file environment variables se settings load karti hai.
Production mein .env file use karo.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Hotelier Hub API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database - PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hotelier_hub"
    
    # JWT Configuration
    # Secret key must be provided via environment variable in production
    SECRET_KEY: str = "temporary_secret_key_for_build_purposes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS - Frontend URL allow karna hai
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:3000", 
        "http://localhost:8080", 
        "http://127.0.0.1:8080", 
        "http://localhost:8081", 
        "http://127.0.0.1:8081",
        "https://*.vercel.app",
        "https://ai-based-booking-engine.vercel.app"
    ]

    # Public URLs (for emails, widgets, etc.)
    API_URL: str = "http://localhost:8001"
    FRONTEND_URL: str = "http://localhost:8080"

    # Supabase Configuration
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_JWKS_URL: str | None = None

    
    class Config:
        import os
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Settings ko cache karta hai taaki bar bar load na ho.
    """
    return Settings()
