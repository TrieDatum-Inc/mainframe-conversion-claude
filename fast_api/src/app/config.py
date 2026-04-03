"""Application configuration via environment variables.

Mirrors the external configuration pattern that replaces CICS COMMAREA
constants and JCL DD statement filenames in the original COBOL programs.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://cardemo:cardemo@localhost:5432/cardemo"
    )

    # Application
    app_title: str = "CardDemo Account Management API"
    app_version: str = "1.0.0"
    debug: bool = False

    # CORS (allow Next.js dev server)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]


settings = Settings()
