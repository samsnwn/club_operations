"""CLI bootstrap/recovery tests against a temporary SQLite database."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import cli
from app.auth.security import verify_password
from app.db.base import Base
from app.models import AuthSession, User


@pytest.fixture(name="session_factory")
def session_factory_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(cli, "SessionLocal", factory)
    yield factory
    engine.dispose()


def _create_owner(
    monkeypatch: pytest.MonkeyPatch, password: str = "bootstrap-pass"
) -> int:
    monkeypatch.setenv("NEW_USER_PASSWORD", password)
    return cli.main(["create-user", "--username", "owner", "--role", "owner"])


def test_create_user_stores_hashed_password(
    session_factory: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _create_owner(monkeypatch) == 0
    with session_factory() as db:
        user = db.scalar(select(User).where(User.username == "owner"))
        assert user is not None
        assert user.role == "owner"
        assert user.created_by is None
        assert user.is_active is True
        assert user.must_change_password is False
        assert user.password_hash != "bootstrap-pass"
        assert verify_password("bootstrap-pass", user.password_hash)


def test_create_user_rejects_duplicates(
    session_factory: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _create_owner(monkeypatch) == 0
    with pytest.raises(SystemExit, match="already exists"):
        _create_owner(monkeypatch)


def test_create_user_rejects_short_password(
    session_factory: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEW_USER_PASSWORD", "too-short")
    with pytest.raises(SystemExit, match="at least"):
        cli.main(["create-user", "--username", "owner", "--role", "owner"])


def test_create_user_rejects_invalid_username(
    session_factory: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEW_USER_PASSWORD", "bootstrap-pass")
    with pytest.raises(SystemExit, match="Username"):
        cli.main(["create-user", "--username", "bad name!", "--role", "owner"])


def test_reset_password_forces_change_and_revokes_sessions(
    session_factory: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _create_owner(monkeypatch) == 0
    with session_factory() as db:
        user = db.scalar(select(User).where(User.username == "owner"))
        db.add(
            AuthSession(
                token_hash="a" * 64,
                user_id=user.id,
                expires_at=datetime.now() + timedelta(hours=1),
            )
        )
        db.commit()

    monkeypatch.setenv("NEW_USER_PASSWORD", "recovered-pass")
    assert cli.main(["reset-password", "--username", "owner"]) == 0

    with session_factory() as db:
        user = db.scalar(select(User).where(User.username == "owner"))
        assert user.must_change_password is True
        assert verify_password("recovered-pass", user.password_hash)
        assert db.query(AuthSession).filter(AuthSession.user_id == user.id).count() == 0


def test_reset_password_unknown_user(
    session_factory: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEW_USER_PASSWORD", "recovered-pass")
    with pytest.raises(SystemExit, match="does not exist"):
        cli.main(["reset-password", "--username", "nobody"])
