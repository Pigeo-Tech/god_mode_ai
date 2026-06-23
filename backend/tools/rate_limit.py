"""Token-bucket rate limiter for tool invocations.

Phase 8. Per-key (per-tool) token buckets: each key refills at a steady rate up to a capacity.
A call consumes one token; if none are available the registry raises RateLimitExceeded. Sync and
lock-free (single-process); a Redis-backed limiter can implement the same `check(key)` contract
for multi-replica deployments.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from backend.core.tool_registry.registry import RateLimitExceeded


@dataclass
class _Bucket:
    capacity: float
    refill_per_sec: float
    tokens: float
    updated: float


class TokenBucketRateLimiter:
    def __init__(self, default_capacity: float = 60, default_refill_per_sec: float = 1.0) -> None:
        self._default = (default_capacity, default_refill_per_sec)
        self._limits: dict[str, tuple[float, float]] = {}
        self._buckets: dict[str, _Bucket] = {}

    def configure(self, key: str, capacity: float, refill_per_sec: float) -> None:
        self._limits[key] = (capacity, refill_per_sec)
        self._buckets.pop(key, None)

    def _bucket(self, key: str) -> _Bucket:
        if key not in self._buckets:
            cap, rate = self._limits.get(key, self._default)
            self._buckets[key] = _Bucket(cap, rate, cap, time.monotonic())
        return self._buckets[key]

    def check(self, key: str) -> None:
        b = self._bucket(key)
        now = time.monotonic()
        b.tokens = min(b.capacity, b.tokens + (now - b.updated) * b.refill_per_sec)
        b.updated = now
        if b.tokens < 1.0:
            raise RateLimitExceeded(f"rate limit exceeded for {key!r}")
        b.tokens -= 1.0
