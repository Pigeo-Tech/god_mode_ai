"""In-memory async Event Bus (publish/subscribe).

Phase 2. Implements the IEventBus port with:
  * topic routing
  * consumer groups (one delivery per group)
  * at-least-once delivery with bounded retries -> dead-letter
The same interface is later backed by Redis Streams / Kafka without touching callers.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Awaitable, Callable

Handler = Callable[[dict], Awaitable[None]]


@dataclass
class _Group:
    handler: Handler
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    task: asyncio.Task | None = None


class EventBus:
    """Implements the IEventBus port."""

    def __init__(self, logger=None, metrics=None, max_retries: int = 3) -> None:
        self._groups: dict[str, dict[str, _Group]] = defaultdict(dict)
        self._dead_letter: list[dict] = []
        self._log = logger
        self._metrics = metrics
        self._max_retries = max_retries
        self._running = True
        self._inflight = 0  # deliveries dequeued but not yet completed

    async def publish(self, topic: str, payload: dict) -> None:
        if self._metrics:
            self._metrics.counter("eventbus_published", topic=topic)
        groups = self._groups.get(topic, {})
        for group in groups.values():
            await group.queue.put(dict(payload))
        if not groups and self._log:
            self._log.debug("event.no_subscribers", topic=topic)

    async def subscribe(self, topic: str, group: str, handler: Handler) -> None:
        if group in self._groups[topic]:
            raise ValueError(f"group {group!r} already subscribed to {topic!r}")
        g = _Group(handler=handler)
        self._groups[topic][group] = g
        g.task = asyncio.create_task(self._consume(topic, group, g))

    async def unsubscribe(self, topic: str, group: str) -> None:
        g = self._groups.get(topic, {}).pop(group, None)
        if g and g.task:
            g.task.cancel()

    async def _consume(self, topic: str, group: str, g: _Group) -> None:
        while self._running:
            try:
                payload = await g.queue.get()
            except asyncio.CancelledError:
                break
            self._inflight += 1
            try:
                await self._deliver(topic, group, g.handler, payload)
            finally:
                self._inflight -= 1

    async def _deliver(self, topic: str, group: str, handler: Handler, payload: dict) -> None:
        for attempt in range(1, self._max_retries + 1):
            try:
                await handler(payload)
                if self._metrics:
                    self._metrics.counter("eventbus_delivered", topic=topic, group=group)
                return
            except Exception as exc:  # noqa: BLE001 - bus must not crash on handler errors
                if self._log:
                    self._log.warning("event.delivery_failed", topic=topic, group=group,
                                      attempt=attempt, error=str(exc))
                await asyncio.sleep(0.01 * attempt)
        self._dead_letter.append({"topic": topic, "group": group, "payload": payload})
        if self._metrics:
            self._metrics.counter("eventbus_dead_letter", topic=topic, group=group)

    @property
    def dead_letter(self) -> list[dict]:
        return list(self._dead_letter)

    def topics(self) -> list[str]:
        return [t for t, g in self._groups.items() if g]

    def _idle(self) -> bool:
        queues_empty = all(g.queue.empty()
                           for groups in self._groups.values() for g in groups.values())
        return queues_empty and self._inflight == 0

    async def drain(self, timeout: float = 2.0) -> None:
        """Wait until all queues are empty AND no delivery is in flight."""
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            await asyncio.sleep(0.01)
            if self._idle():
                return

    async def shutdown(self) -> None:
        self._running = False
        for groups in self._groups.values():
            for g in groups.values():
                if g.task:
                    g.task.cancel()
