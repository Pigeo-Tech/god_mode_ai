"""ProgressMonitor — observes task lifecycle events for a request.

Phase 4. The Task Manager publishes task.assigned / task.completed / task.dead_letter events on
the Event Bus. The ProgressMonitor subscribes to these and tallies progress so the King (and
later the API's WebSocket stream) can report how a request is advancing.
"""
from __future__ import annotations

from collections import Counter

_TOPICS = ("task.assigned", "task.completed", "task.dead_letter")


class ProgressMonitor:
    def __init__(self, event_bus, group: str) -> None:
        self._bus = event_bus
        self._group = group
        self._counts: Counter = Counter()
        self._events: list[dict] = []

    async def start(self) -> None:
        if self._bus is None:
            return
        for topic in _TOPICS:
            await self._bus.subscribe(topic, self._group, self._on_event(topic))

    def _on_event(self, topic: str):
        async def handler(payload: dict) -> None:
            self._counts[topic] += 1
            self._events.append({"topic": topic, **payload})
        return handler

    async def stop(self) -> None:
        if self._bus is None:
            return
        for topic in _TOPICS:
            await self._bus.unsubscribe(topic, self._group)

    def snapshot(self) -> dict:
        return {
            "assigned": self._counts["task.assigned"],
            "completed": self._counts["task.completed"],
            "dead_letter": self._counts["task.dead_letter"],
            "events_seen": len(self._events),
        }
