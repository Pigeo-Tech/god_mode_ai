"""Structured logging with correlation ids.

Phase 2. Emits JSON log lines (production) or human-readable lines (dev). Designed to be
swapped for structlog/CloudWatch later — callers depend only on the ILogger port.
"""
from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

from backend.config.settings import settings

# Correlation id threads a whole request across every log line it produces.
correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}


class StructuredLogger:
    """Implements the ILogger port."""

    def __init__(self, name: str = "god_mode_ai", context: dict[str, Any] | None = None) -> None:
        self._name = name
        self._context = context or {}
        self._min = _LEVELS.get(settings.log_level.upper(), 20)
        self._json = settings.log_json

    def bind(self, **kwargs: Any) -> "StructuredLogger":
        return StructuredLogger(self._name, {**self._context, **kwargs})

    def _emit(self, level: str, event: str, **kw: Any) -> None:
        if _LEVELS[level] < self._min:
            return
        record = {
            "level": level,
            "logger": self._name,
            "event": event,
            "correlation_id": correlation_id.get(),
            **self._context,
            **kw,
        }
        if self._json:
            line = json.dumps(record, default=str)
        else:
            extras = " ".join(f"{k}={v}" for k, v in record.items()
                              if k not in ("level", "event") and v is not None)
            line = f"[{level}] {event} {extras}".rstrip()
        stream = sys.stderr if _LEVELS[level] >= 40 else sys.stdout
        print(line, file=stream, flush=True)

    def debug(self, event: str, **kw: Any) -> None:
        self._emit("DEBUG", event, **kw)

    def info(self, event: str, **kw: Any) -> None:
        self._emit("INFO", event, **kw)

    def warning(self, event: str, **kw: Any) -> None:
        self._emit("WARNING", event, **kw)

    def error(self, event: str, **kw: Any) -> None:
        self._emit("ERROR", event, **kw)


def get_logger(name: str = "god_mode_ai") -> StructuredLogger:
    # Keep the stdlib root quiet; we manage our own emission.
    logging.getLogger().setLevel(logging.WARNING)
    return StructuredLogger(name)
