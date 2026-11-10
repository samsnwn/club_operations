"""Password hashing for internal accounts (Argon2id via pwdlib)."""

import threading

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

# `recommended()` selects Argon2id when argon2-cffi is installed, which the
# `pwdlib[argon2]` dependency guarantees.
_hasher = PasswordHash.recommended()

# Argon2id is deliberately memory-hard, so the number of hashes running at
# once is bounded: a burst of sign-ins queues instead of exhausting memory.
_hash_slots = threading.BoundedSemaphore(4)

# Verified against when the username does not exist, so failed logins take the
# same time whether or not the account is real.
DUMMY_PASSWORD_HASH = _hasher.hash("blue-velvet-dummy-password")


def hash_password(password: str) -> str:
    with _hash_slots:
        return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        with _hash_slots:
            return _hasher.verify(password, password_hash)
    except UnknownHashError:
        # A malformed stored hash must fail closed, never crash the request.
        return False
