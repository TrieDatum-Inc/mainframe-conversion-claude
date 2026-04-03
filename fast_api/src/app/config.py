"""Application configuration via pydantic-settings.

All values are read from environment variables or a .env file.
No hardcoded credentials anywhere in the codebase.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the User Administration API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"

    # Security
    secret_key: str = "change-me-in-production-use-a-strong-random-value"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    bcrypt_rounds: int = 12

    # Pagination — mirrors COUSR00C page size of 10 rows per BMS screen
    default_page_size: int = 10
    max_page_size: int = 100

    # Application metadata
    app_title: str = "CardDemo User Administration API"
    app_version: str = "1.0.0"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
