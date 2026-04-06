"""
Application configuration using pydantic-settings.
Replaces hardcoded connection strings and CICS system definitions.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Replaces CICS SIT parameters and RACF definitions.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database (replaces CICS DB2 entry and IMS PSB definitions)
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"
    )
    database_url_sync: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/carddemo"
    )

    # JWT (replaces CICS RACF token / EIBCALEN auth check)
    secret_key: str = "carddemo-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "CardDemo Authorization API"
    debug: bool = False

    # Pagination defaults (COPAUS0C: 5 rows per screen page)
    default_page_size: int = 5
    max_page_size: int = 100


settings = Settings()
