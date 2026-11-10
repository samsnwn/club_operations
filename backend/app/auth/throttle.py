"""Failed sign-in throttling.

Counts recent failed logins per account name and per client address and
refuses further attempts once either passes its limit, until old failures age
out of the window. A refused attempt is never hashed, so guessing is both
slowed down and cheap to turn away.

State is in memory and per process: enough for a single backend process, and
a restart simply forgets the counters. Behind a reverse proxy every client
shares the proxy's address unless uvicorn runs with `--proxy-headers`.
"""

import math
import threading
import time
from collections import deque


class FailureThrottle:
    def __init__(self) -> None:
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, window: float, now: float) -> deque[float]:
        attempts = self._failures.get(key)
        if attempts is None:
            return deque()
        while attempts and now - attempts[0] >= window:
            attempts.popleft()
        if not attempts:
            del self._failures[key]
        return attempts

    def retry_after(self, key: str, limit: int, window: float) -> int:
        """Seconds until `key` may try again; 0 when it is not blocked."""
        now = time.monotonic()
        with self._lock:
            attempts = self._recent(key, window, now)
            if len(attempts) < limit:
                return 0
            # Blocked until enough old failures leave the window.
            oldest_counted = attempts[len(attempts) - limit]
            return max(1, math.ceil(window - (now - oldest_counted)))

    def record_failure(self, key: str, window: float) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._failures) > 10_000:
                for stale in list(self._failures):
                    self._recent(stale, window, now)
            self._failures.setdefault(key, deque()).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


login_throttle = FailureThrottle()
