"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"

    # JWT
    secret_key: str = "change-me-in-production-min-32-chars-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # App
    app_title: str = "CardDemo User Administration API"
    app_version: str = "1.0.0"
    debug: bool = False


settings = Settings()
