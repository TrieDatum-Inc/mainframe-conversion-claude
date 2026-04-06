"""
Application configuration using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = (
        "postgresql+asyncpg://carddemo:carddemo@localhost:5432/carddemo"
    )

    # JWT
    secret_key: str = "change-me-in-production-use-strong-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application
    debug: bool = False
    app_title: str = "CardDemo Authorization API"
    app_version: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
