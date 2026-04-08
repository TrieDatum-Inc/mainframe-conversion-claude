"""
Application configuration via environment variables.
Replaces CICS COMMAREA static configuration and JCL SYSIN parameters.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "CardDemo API"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://mridul:mridul12345&@localhost:5432/carddemo_3"
    database_url_sync: str = "postgresql+psycopg2://mridul:mridul12345&@localhost:5432/carddemo_3"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # JWT / Security
    # Replaces CICS COMMAREA session management (COCOM01Y)
    jwt_secret_key: str = "CHANGE-ME-IN-PRODUCTION-USE-32+-CHAR-SECRET"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Pagination — mirrors CICS screen page sizes (CT00: 10 rows, CU00: 10 rows)
    default_page_size: int = 10
    max_page_size: int = 100

    # COBOL compatibility
    # COSGN00C: USRSEC file name
    usrsec_file: str = "USRSEC"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton)."""
    return Settings()
