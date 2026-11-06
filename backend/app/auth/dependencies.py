"""Request-time authentication dependencies.

`authenticated_user` resolves the cookie to an active account.
`current_user` additionally blocks accounts that must still choose a password,
which is what all normal API routes depend on.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.sessions import COOKIE_NAME, lookup_session
from app.db.base import get_db
from app.models import User


def authenticated_user(
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> User:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = lookup_session(db, session_token)
    if session is None:
        raise HTTPException(status_code=401, detail="Session expired")
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account is not active")
    return user


def current_user(
    user: Annotated[User, Depends(authenticated_user)],
) -> User:
    if user.must_change_password:
        raise HTTPException(status_code=403, detail="Password change required")
    return user


def require_role(*roles: str) -> Callable[..., User]:
    """Dependency factory: allow only the given roles (on top of `current_user`)."""

    def dependency(
        user: Annotated[User, Depends(current_user)],
    ) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency
