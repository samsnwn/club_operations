# Digest sending: verified TLS only, never a plaintext fallback.

import smtplib
import ssl

import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base, SessionLocal, engine
from app.notify import digest


@pytest.fixture(name="db")
def db_fixture() -> Session:
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


class FakeSMTP:
    """Records the conversation instead of opening a socket."""

    starttls_supported = True
    instances: list["FakeSMTP"] = []

    def __init__(self, host: str, port: int, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.events: list[str] = []
        self.tls_context: object = kwargs.get("context")
        FakeSMTP.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def starttls(self, context: object = None) -> None:
        if not self.starttls_supported:
            raise smtplib.SMTPNotSupportedError("STARTTLS not offered")
        self.tls_context = context
        self.events.append("starttls")

    def login(self, user: str, password: str) -> None:
        self.events.append("login")

    def send_message(self, message: object) -> None:
        self.events.append("send")


@pytest.fixture(name="smtp")
def smtp_fixture(monkeypatch: pytest.MonkeyPatch) -> type[FakeSMTP]:
    FakeSMTP.instances = []
    FakeSMTP.starttls_supported = True
    monkeypatch.setattr(digest.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(digest.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("INVOICE_SMTP_HOST", "mail.example.test")
    monkeypatch.setenv("INVOICE_DIGEST_FROM", "invoices@example.test")
    monkeypatch.setenv("INVOICE_DIGEST_TO", "owner@example.test")
    get_settings.cache_clear()
    yield FakeSMTP
    get_settings.cache_clear()


def _verifies_certificates(context: object) -> bool:
    return (
        isinstance(context, ssl.SSLContext)
        and context.verify_mode == ssl.CERT_REQUIRED
        and context.check_hostname
    )


def test_digest_uses_verified_starttls_even_without_credentials(
    db: Session, smtp: type[FakeSMTP]
) -> None:
    assert digest.send_digest(db) is True
    sent = smtp.instances[0]
    assert sent.events == ["starttls", "send"]
    assert _verifies_certificates(sent.tls_context)
    assert sent.kwargs["timeout"] == digest.SMTP_TIMEOUT_SECONDS


def test_digest_logs_in_only_after_tls(
    db: Session, smtp: type[FakeSMTP], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INVOICE_SMTP_USER", "mailer")
    monkeypatch.setenv("INVOICE_SMTP_PASSWORD", "not-a-real-secret")
    get_settings.cache_clear()
    assert digest.send_digest(db) is True
    assert smtp.instances[0].events == ["starttls", "login", "send"]


def test_digest_is_not_sent_in_plaintext_without_starttls(
    db: Session, smtp: type[FakeSMTP]
) -> None:
    smtp.starttls_supported = False
    assert digest.send_digest(db) is False
    assert "send" not in smtp.instances[0].events


def test_digest_uses_implicit_tls_on_port_465(
    db: Session, smtp: type[FakeSMTP], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INVOICE_SMTP_PORT", "465")
    get_settings.cache_clear()
    assert digest.send_digest(db) is True
    sent = smtp.instances[0]
    assert sent.events == ["send"]
    assert _verifies_certificates(sent.tls_context)
