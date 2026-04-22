from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App Info
    APP_NAME: str = "Hotelier Hub API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database - Supabase PostgreSQL
    # Optional so a missing/malformed env var fails loudly at query time,
    # not silently with a broken placeholder URL.
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def strip_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Strip accidental trailing tabs/spaces from the env var name."""
        if isinstance(v, str):
            return v.strip() or None
        return v

    # JWT Configuration
    SECRET_KEY: str = "temporary_secret_key_for_build_purposes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS - Dynamically handled from ENV
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "https://ai-based-booking-engine.vercel.app",
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
    # Validators strip accidental trailing tabs/spaces from env var values.
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_JWKS_URL: Optional[str] = None

    @field_validator("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_JWKS_URL", mode="before")
    @classmethod
    def strip_supabase_vars(cls, v: Optional[str]) -> Optional[str]:
        """Strip accidental trailing tabs/spaces from the env var values."""
        if isinstance(v, str):
            return v.strip() or None
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Settings ko cache karta hai taaki bar bar load na ho.
    """
    return Settings()
