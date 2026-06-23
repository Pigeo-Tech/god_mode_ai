"""In-memory Message Bus (directed request/reply).

Phase 2. Implements the IMessageBus port. While the Event Bus is fan-out pub/sub, the Message
Bus is point-to-point: an agent sends a request to a named target and awaits exactly one reply.
This is how the King reaches a specific General and how Generals reach specific Soldiers without
any direct object references between them.
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

ReplyHandler = Callable[[dict], Awaitable[dict]]


class MessageBus:
    """Implements the IMessageBus port."""

    def __init__(self, logger=None, metrics=None) -> None:
        self._handlers: dict[str, ReplyHandler] = {}
        self._log = logger
        self._metrics = metrics

    def handle(self, target: str, handler: ReplyHandler) -> None:
        """Register the single handler that answers requests to `target`."""
        self._handlers[target] = handler

    def unregister(self, target: str) -> None:
        self._handlers.pop(target, None)

    def targets(self) -> list[str]:
        return list(self._handlers)

    async def request(self, target: str, payload: dict, timeout: float = 30.0) -> dict:
        handler = self._handlers.get(target)
        if handler is None:
            raise KeyError(f"no handler registered for target {target!r}")
        if self._metrics:
            self._metrics.counter("messagebus_request", target=target)
        try:
            with self._metrics.timer("messagebus_latency", target=target) if self._metrics \
                    else _nullctx():
                return await asyncio.wait_for(handler(dict(payload)), timeout=timeout)
        except asyncio.TimeoutError:
            if self._log:
                self._log.error("message.timeout", target=target, timeout=timeout)
            raise


class _nullctx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
