"""Short-term store implementations (the IShortTermStore port).

Phase 7. In-memory TTL cache (default) and a Redis adapter (production). Both expose the same
sync API.
"""
from __future__ import annotations

import json
import time


class InMemoryShortTermStore:
    """TTL key/value cache. Default backend; no external dependency."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, object]] = {}

    def set(self, key: str, value: object, ttl: float = 300.0) -> None:
        self._data[key] = (time.time() + ttl, value)

    def get(self, key: str) -> object | None:
        item = self._data.get(key)
        if not item:
            return None
        expiry, value = item
        if time.time() > expiry:
            self._data.pop(key, None)
            return None
        return value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class RedisShortTermStore:
    """Production adapter backed by Redis (lazy import; sync client)."""

    def __init__(self, url: str, prefix: str = "stm:") -> None:
        import redis  # type: ignore  # lazy: only required in production

        self._r = redis.from_url(url)
        self._prefix = prefix

    def set(self, key: str, value: object, ttl: float = 300.0) -> None:
        self._r.setex(self._prefix + key, int(ttl), json.dumps(value))

    def get(self, key: str) -> object | None:
        raw = self._r.get(self._prefix + key)
        return json.loads(raw) if raw is not None else None

    def delete(self, key: str) -> None:
        self._r.delete(self._prefix + key)
