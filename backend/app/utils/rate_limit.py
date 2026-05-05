"""Small in-process rate limiter for authentication endpoints."""
from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Deque


_attempts: dict[str, Deque[float]] = defaultdict(deque)
_lock = Lock()


def is_rate_limited(key: str, max_attempts: int, window_seconds: int) -> bool:
    """Record an attempt and return True when the key is over limit."""
    now = monotonic()
    cutoff = now - window_seconds

    with _lock:
        attempts = _attempts[key]
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()

        if len(attempts) >= max_attempts:
            return True

        attempts.append(now)
        return False


def clear_rate_limits() -> None:
    """Clear limiter state for tests."""
    with _lock:
        _attempts.clear()
