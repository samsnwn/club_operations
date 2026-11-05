"""Application settings, loaded from environment variables and a local `.env`.

Credentials and real club data must never be committed; `.env` is gitignored.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Blue Velvet API"
    # SQLite for now; a relative path resolves against the working directory.
    database_url: str = "sqlite:///./blue_velvet.db"
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
