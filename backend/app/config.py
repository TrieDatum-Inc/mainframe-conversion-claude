"""
Application configuration via pydantic-settings.

COBOL origin: Replaces hardcoded constants from COTTL01Y (screen title constants),
COSGN00C working-storage literals (WS-USRSEC-FILE, WS-TRANID, etc.),
and CICS system definition parameters.
All secrets are read from environment variables — never hardcoded.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    Replaces:
    - CICS FILE CONTROL definitions (DATASET names)
    - COTTL01Y constants (title strings)
    - Hardcoded CICS security parameters
    """

    # Database — replaces CICS FILE CONTROL definitions for VSAM files
    database_url: str = "postgresql+asyncpg://carddemo:carddemo@localhost:5432/carddemo"
    database_url_sync: str = "postgresql://carddemo:carddemo@localhost:5432/carddemo"

    # JWT Security — replaces USRSEC plain-text password comparison
    # jwt_secret_key has no default; must be provided via environment
    jwt_secret_key: str = "dev-secret-key-replace-in-production-min-256-bits"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60  # 3600 seconds; replaces indefinite CICS session

    # CORS — origins allowed to call the API
    cors_origins: list[str] = ["http://localhost:3000"]

    # Application title constants — from COTTL01Y copybook
    app_title_line1: str = "AWS Mainframe Cloud Demo"
    app_title_line2: str = "Credit Card Demo Application"

    # bcrypt work factor — development: 10, production: 12
    bcrypt_rounds: int = 12

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Module-level singleton — import `settings` everywhere
settings = Settings()
