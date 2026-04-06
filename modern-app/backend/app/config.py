"""Application configuration using pydantic-settings.

Settings are read from environment variables (or a .env file).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configurable values for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"

    # JWT
    secret_key: str = "changeme-use-a-real-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Application
    app_name: str = "CardDemo Transaction API"
    debug: bool = False
    page_size: int = 10


settings = Settings()
