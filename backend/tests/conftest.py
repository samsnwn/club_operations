"""Shared API test fixtures: isolated SQLite store and a clean TestClient."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.throttle import login_throttle
from app.db.base import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _fresh_login_throttle() -> Iterator[None]:
    """Failed-login counters are process-wide; never leak them between tests."""
    login_throttle.clear()
    yield
    login_throttle.clear()


@pytest.fixture(name="db_factory")
def db_factory_fixture() -> Iterator[sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture(name="api_client")
def api_client_fixture(db_factory: sessionmaker) -> Iterator[TestClient]:
    def override_get_db():
        db = db_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_db, None)
