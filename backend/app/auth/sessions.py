"""Opaque database-backed login sessions.

The cookie carries a random token; only its SHA-256 is stored, so a database
read never exposes a usable session. Revocation is a row delete.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuthSession

COOKIE_NAME = "bv_session"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user_id: int, ttl_hours: int) -> str:
    """Create a session row and return the raw token for the cookie."""
    now = datetime.now()
    # Opportunistic cleanup: a handful of accounts never needs a background job.
    db.query(AuthSession).filter(AuthSession.expires_at < now).delete()
    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            token_hash=hash_token(token),
            user_id=user_id,
            expires_at=now + timedelta(hours=ttl_hours),
        )
    )
    db.commit()
    return token


def lookup_session(db: Session, token: str) -> AuthSession | None:
    session = db.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_token(token))
    )
    if session is None or session.expires_at <= datetime.now():
        return None
    return session


def delete_session(db: Session, token: str) -> None:
    db.query(AuthSession).filter(AuthSession.token_hash == hash_token(token)).delete()
    db.commit()


def delete_user_sessions(db: Session, user_id: int) -> int:
    deleted = db.query(AuthSession).filter(AuthSession.user_id == user_id).delete()
    db.commit()
    return deleted
