"""
Application configuration using Pydantic settings.

Reads from environment variables or a .env file.
All COBOL-era CICS SYSID/resource definitions replaced by these settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment or .env file.

    COBOL origin: Replaces CICS resource definitions (PCT, FCT, RCT).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — replaces CICS FILE CONTROL (FCT)
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"
    )

    # JWT settings — replaces CICS COMMAREA session management
    jwt_secret_key: str = "carddemo-dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Password hashing
    bcrypt_rounds: int = 12

    # Application metadata
    app_name: str = "CardDemo API"
    app_version: str = "1.0.0"
    debug: bool = False


settings = Settings()
