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
    invoice_service_url: str = "http://localhost:8081"
    invoice_service_token: str = "development-invoice-service-token"

    # Internal auth: opaque database sessions in an HttpOnly cookie.
    session_ttl_hours: int = 12
    # Set true once the app is served over HTTPS.
    session_cookie_secure: bool = False
    # Comma-separated browser origins allowed to send state-changing requests.
    # Same-origin requests are always allowed; the dev frontend is the default.
    allowed_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
