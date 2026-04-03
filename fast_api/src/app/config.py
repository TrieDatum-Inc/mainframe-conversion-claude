from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/carddemo"

    # Application
    app_title: str = "CardDemo Transaction Processing API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Pagination defaults (matches COBOL page size of 10)
    default_page_size: int = 10
    max_page_size: int = 100

    # Transaction ID format (16-digit zero-padded string, matching COBOL PIC X(16))
    tran_id_length: int = 16


settings = Settings()
