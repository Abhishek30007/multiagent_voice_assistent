import os
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Information
    APP_NAME: str = "Personal AI Twin"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "temporary-secret-key-for-development-change-in-production-32chars"

    # Symmetric encryption key for storing OAuth tokens securely in PostgreSQL
    TOKEN_ENCRYPTION_KEY: str = Field(
        default="D7h2k9S8z1M3v0B2L5p8W4x1Q7r6E3t8Y9u4I1o0P2s=",
        description="32-byte url-safe base64-encoded key for Fernet encryption",
    )

    # Account Owner Identity
    OWNER_NAME: str = "Abhishek"
    OWNER_EMAIL: str = "abhishekkumarsaw414@gmail.com"

    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./personal_ai_twin.db",
        description="Async database connection string. Defaults to SQLite for local runs, override with postgresql+asyncpg for production.",
    )
    DATABASE_SYNC_URL: str = Field(
        default="sqlite:///./personal_ai_twin.db",
        description="Sync database connection string for Alembic/Celery.",
    )

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # AI & Voice API Keys
    GEMINI_API_KEY: str = ""
    DEEPGRAM_API_KEY: str = ""
    CARTESIA_API_KEY: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""
    LIVEKIT_URL: str = "wss://livekit.example.com"

    # Google OAuth Scopes (Read-only for privacy & security)
    GOOGLE_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    # Data Ingestion Limits and Settings
    GMAIL_MAX_RESULTS_PER_PAGE: int = 100
    GMAIL_INITIAL_SYNC_DAYS: int = 30
    CALENDAR_SYNC_DAYS_PAST: int = 30
    CALENDAR_SYNC_DAYS_FUTURE: int = 90
    SYNC_LOCK_TIMEOUT_SECONDS: int = 600
    AUTO_SYNC_INTERVAL_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
