"""Service configuration.

Phase 0.5 credentials (Gmail OAuth, Drive API, Sheets API) live outside the
repository per hard rule 3 (`INVOICE_SERVICE_` env vars / a local `.env`).
Every connector degrades to a clean "not configured" skip rather than failing
the whole pipeline run.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INVOICE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Blue Velvet Invoice Service"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/invoices.db"
    # Where captured originals are stored (gitignored).
    attachments_dir: str = "./data/attachments"
    # Resource limits for untrusted captures and document extraction.
    max_attachment_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    max_pdf_pages: int = Field(default=100, gt=0)
    max_extracted_text_chars: int = Field(default=1_000_000, gt=0)

    # Simple two-user review auth (owner + admin). Tokens come from env only.
    review_tokens: dict[str, str] = {}

    # Sheets export stays off (feature flag) until the column mapping against
    # the real accounting sheet is confirmed — hard rule 2.
    export_enabled: bool = False

    # Notifications
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    digest_from: str | None = None
    digest_to: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
