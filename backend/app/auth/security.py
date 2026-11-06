"""Password hashing for internal accounts (Argon2id via pwdlib)."""

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

# `recommended()` selects Argon2id when argon2-cffi is installed, which the
# `pwdlib[argon2]` dependency guarantees.
_hasher = PasswordHash.recommended()

# Verified against when the username does not exist, so failed logins take the
# same time whether or not the account is real.
DUMMY_PASSWORD_HASH = _hasher.hash("blue-velvet-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password, password_hash)
    except UnknownHashError:
        # A malformed stored hash must fail closed, never crash the request.
        return False
