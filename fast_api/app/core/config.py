"""
Configuration module for CardDemo API.
Maps to CICS system-level settings (APPLID, SYSID, dataset names).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application identity (from COTTL01Y constants)
    app_title: str = "AWS Mainframe Modernization - CardDemo API"
    app_version: str = "1.0.0"
    app_applid: str = "CARDDEMO"
    app_sysid: str = "CD01"

    # Database (replaces VSAM + DB2 datasets)
    database_url: str = "postgresql+asyncpg://mridul:mridul12345&@localhost:5432/carddemo_4"
    database_echo: bool = False

    # JWT Auth (replaces USRSEC plain-text password VSAM)
    # Original COSGN00C used plain-text; we use bcrypt + JWT
    secret_key: str = "carddemo-secret-key-change-in-production-minimum-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours (typical mainframe shift)

    # Pagination defaults
    # COTRN00C: 10 rows per page; COCRDLIC: 7 rows; COUSR00C: 10 rows
    default_page_size: int = 10
    card_list_page_size: int = 7
    user_list_page_size: int = 10
    tran_type_list_page_size: int = 7

    # Batch processing limits
    # COPAUA0C processes max 500 authorization messages per invocation
    auth_batch_limit: int = 500

    # Interest rate calculation
    # CBACT04C applies monthly interest = balance * rate / 12
    interest_calc_divisor: int = 12

    # User type constants (from CSUSR01Y SEC-USR-TYPE)
    user_type_admin: str = "A"
    user_type_regular: str = "U"


settings = Settings()
