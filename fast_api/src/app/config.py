from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    database_url: str = "postgresql+asyncpg://carddemo:carddemo@localhost:5432/carddemo"
    sync_database_url: str = "postgresql://carddemo:carddemo@localhost:5432/carddemo"
    api_prefix: str = "/api"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    default_page_size: int = 7
    max_page_size: int = 50


settings = Settings()
