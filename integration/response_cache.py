"""Small TTL caches for non-personalized, stable generated responses."""

from __future__ import annotations

import hashlib
import re
import threading
import time
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int = 900, *, clock=time.monotonic) -> None:
        self.ttl_seconds = max(1, ttl_seconds)
        self._clock = clock
        self._values: dict[str, tuple[float, T]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> T | None:
        now = self._clock()
        with self._lock:
            entry = self._values.get(key)
            if not entry:
                return None
            created, value = entry
            if now - created >= self.ttl_seconds:
                del self._values[key]
                return None
            return value

    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._values[key] = (self._clock(), value)

    def clear(self) -> None:
        with self._lock:
            self._values.clear()


NON_CACHEABLE_GENERAL = re.compile(
    r"\b(i|me|my|mine|we|our|should i|can i|for me|my family|my health|my account)\b",
    re.IGNORECASE,
)
CURRENT_QUERY = re.compile(r"\b(current|today|latest|now|real[ -]?time|this week|this month)\b", re.IGNORECASE)


def general_response_cache_key(question: str, language: str, format_key: str) -> str | None:
    normalized = re.sub(r"\s+", " ", (question or "").casefold()).strip()
    if not normalized or NON_CACHEABLE_GENERAL.search(normalized) or CURRENT_QUERY.search(normalized):
        return None
    raw = "\x1f".join((normalized, language or "en", format_key or "natural"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
