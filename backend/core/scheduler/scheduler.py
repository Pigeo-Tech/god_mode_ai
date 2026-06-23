"""Scheduler — time-based and recurring jobs.

Phase 2. Supports DateTrigger (one-shot), IntervalTrigger (every N seconds), and a small
CronTrigger (minute hour day month weekday, with ``*`` and ``*/n``). Due jobs publish to the
Event Bus. A pluggable lock guarantees single-fire across replicas (in-memory lock here; Redis
lock later).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import uuid4


class Trigger(Protocol):
    def next_after(self, now: datetime) -> datetime | None: ...


@dataclass
class DateTrigger:
    when: datetime

    def next_after(self, now: datetime) -> datetime | None:
        return self.when if self.when > now else None


@dataclass
class IntervalTrigger:
    seconds: float
    _anchor: datetime | None = None

    def next_after(self, now: datetime) -> datetime | None:
        base = self._anchor or now
        return base + timedelta(seconds=self.seconds)


@dataclass
class CronTrigger:
    """Minimal cron: 'min hour day month weekday'. Supports '*', 'n', '*/n', and 'a,b'."""
    expr: str

    def _match(self, field_expr: str, value: int) -> bool:
        for part in field_expr.split(","):
            if part == "*":
                return True
            if part.startswith("*/"):
                if value % int(part[2:]) == 0:
                    return True
            elif part.isdigit() and int(part) == value:
                return True
        return False

    def next_after(self, now: datetime) -> datetime | None:
        mins, hrs, day, mon, wday = self.expr.split()
        t = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        for _ in range(0, 366 * 24 * 60):  # search up to ~1 year ahead
            if (self._match(mins, t.minute) and self._match(hrs, t.hour)
                    and self._match(day, t.day) and self._match(mon, t.month)
                    and self._match(wday, t.weekday())):
                return t
            t += timedelta(minutes=1)
        return None


class InMemoryLock:
    """Single-fire lock (Redis SETNX stand-in)."""

    def __init__(self) -> None:
        self._held: dict[str, float] = {}

    async def acquire(self, key: str, ttl: float = 30.0) -> bool:
        now = asyncio.get_event_loop().time()
        exp = self._held.get(key)
        if exp and exp > now:
            return False
        self._held[key] = now + ttl
        return True


@dataclass
class ScheduledJob:
    name: str
    trigger: Trigger
    payload: dict
    topic: str = "job.fired"
    id: str = field(default_factory=lambda: str(uuid4()))
    enabled: bool = True
    next_run: datetime | None = None
    last_run: datetime | None = None


class Scheduler:
    """Implements the IScheduler port."""

    def __init__(self, bus=None, lock: InMemoryLock | None = None,
                 logger=None, metrics=None) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._bus = bus
        self._lock = lock or InMemoryLock()
        self._log = logger
        self._metrics = metrics
        self._task: asyncio.Task | None = None
        self._running = False

    def schedule(self, job: ScheduledJob) -> str:
        job.next_run = job.trigger.next_after(self._now())
        self._jobs[job.id] = job
        if self._log:
            self._log.info("scheduler.scheduled", job=job.name, next_run=str(job.next_run))
        return job.id

    def cancel(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    def list(self) -> list[ScheduledJob]:
        return list(self._jobs.values())

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    async def tick(self, now: datetime | None = None) -> list[str]:
        """Fire all due jobs once. Returns names fired. (Called by the run loop or tests.)"""
        now = now or self._now()
        fired: list[str] = []
        for job in list(self._jobs.values()):
            if not job.enabled or not job.next_run or job.next_run > now:
                continue
            if not await self._lock.acquire(f"job:{job.id}"):
                continue
            if self._bus:
                await self._bus.publish(job.topic, {"job": job.name, **job.payload})
            if self._metrics:
                self._metrics.counter("scheduler_fired", job=job.name)
            job.last_run = now
            job.next_run = job.trigger.next_after(now)
            if job.next_run is None:
                job.enabled = False  # one-shot complete
            fired.append(job.name)
        return fired

    async def start(self, interval: float = 1.0) -> None:
        self._running = True

        async def loop() -> None:
            while self._running:
                await self.tick()
                await asyncio.sleep(interval)

        self._task = asyncio.create_task(loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
