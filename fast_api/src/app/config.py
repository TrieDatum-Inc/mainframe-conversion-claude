"""Application configuration via pydantic-settings.

Reads environment variables with CARDDEMO_ prefix.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="CARDDEMO_",
        env_file=".env",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"

    # Application
    app_title: str = "CardDemo Batch Processing API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Batch processing
    # CBACT04C: default run date used when none supplied
    default_run_date: str = ""

    # CBTRN02C: interest transaction type/category (hardcoded in COBOL)
    interest_tran_type_cd: str = "01"
    interest_tran_cat_cd: str = "05"


settings = Settings()
