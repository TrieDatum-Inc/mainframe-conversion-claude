"""
Application configuration via pydantic-settings.

All secrets must be provided via environment variables or a .env file.
Never hardcode secrets in this file — only safe defaults are provided.

COBOL origin: Replaces CICS system configuration (APPLID, SYSID, file names).
"""

from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List

# The sentinel value used as the development default.
# This is a deliberately weak placeholder — it is NOT a real secret.
# Production deployments MUST override SECRET_KEY with a strong random value.
# Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
# The validator below blocks startup if this sentinel is still set when DEBUG=False.
_SECRET_KEY_SENTINEL = "change-me-in-production-use-at-least-32-random-chars-REPLACE-NOW"


class Settings(BaseSettings):
    # Database
    # Default is a development-only placeholder; production must override via DATABASE_URL env var.
    DATABASE_URL: str = "postgresql+asyncpg://carddemo_user:changeme@localhost/carddemo_dev"

    # JWT — must be overridden in production via SECRET_KEY env var
    SECRET_KEY: str = _SECRET_KEY_SENTINEL
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400

    # Security
    BCRYPT_ROUNDS: int = 12

    # Trusted reverse-proxy CIDRs for X-Forwarded-For validation.
    # X-Forwarded-For is only honoured when the direct TCP connection originates
    # from one of these networks (i.e., a reverse proxy we control).
    # Set via the TRUSTED_PROXY_CIDRS environment variable (JSON list or
    # comma-separated CIDR strings) to match your deployment topology.
    # Empty by default — no proxy is trusted unless explicitly configured.
    TRUSTED_PROXY_CIDRS: List[str] = []

    # CORS — list of allowed origins for the Next.js frontend
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # App metadata
    APP_NAME: str = "CardDemo API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """
        Block startup when SECRET_KEY is the development sentinel in a
        non-debug (production) environment.

        Refactoring note (security review finding #3): the original field_validator
        could not access self.DEBUG, so it allowed the sentinel through in all
        environments. A model_validator runs after all fields are populated,
        giving access to both SECRET_KEY and DEBUG together.

        To generate a strong key:
            python -c "import secrets; print(secrets.token_hex(32))"
        """
        if not self.DEBUG and self.SECRET_KEY == _SECRET_KEY_SENTINEL:
            raise ValueError(
                "SECRET_KEY must be set to a strong random value when DEBUG=False. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if self.SECRET_KEY != _SECRET_KEY_SENTINEL and len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
