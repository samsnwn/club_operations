"""Service configuration.

Phase 0.5 credentials (Gmail OAuth, Drive API, Sheets API) live outside the
repository per hard rule 4 (`INVOICE_` env vars / a local `.env`).
Every connector degrades to a clean "not configured" skip rather than failing
the whole pipeline run.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The known development token. Production startup refuses to use it; keeping
# the value in one place makes that guard explicit and testable.
DEFAULT_INTERNAL_TOKEN = "development-invoice-service-token"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INVOICE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Blue Velvet Invoice Service"
    api_v1_prefix: str = "/api/v1"
    # Fail closed: an unconfigured deployment is treated as production, so the
    # known development token is rejected at startup. The dev compose file
    # explicitly sets INVOICE_ENVIRONMENT=development.
    environment: Literal["development", "production"] = "production"
    internal_token: str = DEFAULT_INTERNAL_TOKEN
    database_url: str = "sqlite:///./data/invoices.db"
    # Where captured originals are stored (gitignored).
    attachments_dir: str = "./data/attachments"
    inbox_dir: str = "./data/inbox"
    # Resource limits for untrusted captures and document extraction.
    max_attachment_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    max_pdf_pages: int = Field(default=100, gt=0)
    max_extracted_text_chars: int = Field(default=1_000_000, gt=0)

    # Reviewer identity is forwarded by the backend facade as `X-Reviewer`
    # only alongside the internal token; there is no per-user token path.
    # Sheets export stays off (feature flag) until the column mapping against
    # the real accounting sheet is confirmed — hard rule 3.
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
