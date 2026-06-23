"""Health Service — aggregates component readiness.

Phase 2. Implements the IHealthService port. Components register an async health check;
``report()`` runs them all and returns an HTTP status (200 if all healthy, else 503) plus a
per-component detail map for the /health endpoint.
"""
from __future__ import annotations

from typing import Awaitable, Callable

HealthCheck = Callable[[], Awaitable[dict]]


class HealthService:
    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register(self, name: str, check: HealthCheck) -> None:
        self._checks[name] = check

    async def report(self) -> tuple[int, dict]:
        results: dict[str, dict] = {}
        healthy = True
        for name, check in self._checks.items():
            try:
                res = await check()
            except Exception as exc:  # noqa: BLE001
                res = {"status": "error", "error": str(exc)}
            results[name] = res
            if res.get("status") != "ok":
                healthy = False
        return (200 if healthy else 503), {"healthy": healthy, "components": results}
