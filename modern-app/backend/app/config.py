"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://carddemo:carddemo@localhost:5432/carddemo"

    # JWT
    secret_key: str = "change-me-in-production-use-a-long-random-string-at-least-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # App
    app_title: str = "CardDemo API"
    app_version: str = "1.0.0"
    debug: bool = False


settings = Settings()
