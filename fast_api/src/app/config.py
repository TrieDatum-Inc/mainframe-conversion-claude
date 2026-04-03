"""Application configuration — environment-based settings via pydantic-settings.

Replaces COBOL WS-USRSEC-FILE and hardcoded program constants.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"
    )

    # JWT Authentication (replaces CICS COMMAREA session state)
    secret_key: str = "CHANGE-ME-IN-PRODUCTION-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application metadata (mirrors COBOL WS-PGMNAME / WS-TRANID constants)
    app_name: str = "CardDemo"
    app_title01: str = "AWS Mainframe Modernization"
    app_title02: str = "CardDemo"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Logging
    log_level: str = "INFO"


settings = Settings()
