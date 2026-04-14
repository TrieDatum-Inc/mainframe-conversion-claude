"""
Application configuration via pydantic-settings.

All secrets must be provided via environment variables or a .env file.
Never hardcode secrets in this file — only safe defaults are provided.

COBOL origin: Replaces CICS system configuration (APPLID, SYSID, file names).
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://carddemo:carddemo@localhost/carddemo"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-at-least-32-random-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400

    # Security
    BCRYPT_ROUNDS: int = 12

    # CORS — list of allowed origins for the Next.js frontend
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # App metadata
    APP_NAME: str = "CardDemo API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if v == "change-me-in-production-use-at-least-32-random-chars":
            # Allowed in development; blocked via deployment checks in production
            return v
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
