from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # App Info
    APP_NAME: str = "Hotelier Hub API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database - Supabase PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    
    # JWT Configuration
    SECRET_KEY: str = "temporary_secret_key_for_build_purposes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS - Dynamically handled from ENV
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "https://ai-based-booking-engine.vercel.app"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Public URLs
    API_URL: str = "http://localhost:8001"
    FRONTEND_URL: str = "http://localhost:8080"

    # Supabase Configuration
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_JWKS_URL: str | None = None


@lru_cache()
def get_settings() -> Settings:
    """
    Settings ko cache karta hai taaki bar bar load na ho.
    """
    return Settings()
