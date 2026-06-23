"""Task Manager — task DAG, state machine, retries.

Phase 2. Owns the lifecycle of tasks/subtasks. The King produces a TaskGraph (a DAG of
subtasks with dependencies); the manager dispatches ready tasks, enforces valid state
transitions, applies retry/backoff, and emits lifecycle events on the Event Bus.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable
from uuid import uuid4

from backend.schemas.agent import TaskStatus

# Allowed transitions enforce a correct lifecycle.
_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
    TaskStatus.ASSIGNED: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.FAILED: {TaskStatus.ASSIGNED},  # retry
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}


class InvalidTransition(Exception):
    pass


@dataclass
class Task:
    objective: str
    owner_agent: str
    id: str = field(default_factory=lambda: str(uuid4()))
    depends_on: set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    result: object | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TaskGraph:
    tasks: dict[str, Task] = field(default_factory=dict)

    def add(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    def ready(self) -> list[Task]:
        done = {t.id for t in self.tasks.values() if t.status == TaskStatus.COMPLETED}
        return [t for t in self.tasks.values()
                if t.status == TaskStatus.PENDING and t.depends_on <= done]

    def complete(self) -> bool:
        return all(t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
                   for t in self.tasks.values())

    def topological_order(self) -> list[str]:
        order: list[str] = []
        seen: set[str] = set()

        def visit(tid: str, stack: set[str]) -> None:
            if tid in seen:
                return
            if tid in stack:
                raise ValueError("cycle detected in task graph")
            stack.add(tid)
            for dep in self.tasks[tid].depends_on:
                visit(dep, stack)
            stack.discard(tid)
            seen.add(tid)
            order.append(tid)

        for tid in self.tasks:
            visit(tid, set())
        return order


# Executor: given a Task, run it and return (result). Raises on failure.
Executor = Callable[[Task], Awaitable[object]]


class TaskManager:
    """Implements the ITaskManager port."""

    def __init__(self, bus=None, logger=None, metrics=None) -> None:
        self._bus = bus
        self._log = logger
        self._metrics = metrics

    def transition(self, task: Task, to: TaskStatus) -> None:
        if to not in _TRANSITIONS[task.status]:
            raise InvalidTransition(f"{task.status} -> {to} not allowed")
        task.status = to

    async def run_graph(self, graph: TaskGraph, executor: Executor) -> dict[str, Task]:
        """Execute the whole DAG, respecting dependencies, with retries. Returns task map."""
        graph.topological_order()  # validates acyclicity up front
        while not graph.complete():
            ready = graph.ready()
            if not ready:
                # nothing ready and not complete -> blocked (e.g. failed dependency)
                break
            await asyncio.gather(*(self._run_one(t, executor) for t in ready))
        return graph.tasks

    async def _run_one(self, task: Task, executor: Executor) -> None:
        self.transition(task, TaskStatus.ASSIGNED)
        await self._emit("task.assigned", task)
        while True:
            task.attempts += 1
            self.transition(task, TaskStatus.RUNNING)
            try:
                task.result = await executor(task)
                self.transition(task, TaskStatus.COMPLETED)
                await self._emit("task.completed", task)
                return
            except Exception as exc:  # noqa: BLE001
                task.error = str(exc)
                self.transition(task, TaskStatus.FAILED)
                if task.attempts >= task.max_attempts:
                    await self._emit("task.dead_letter", task)
                    return
                await asyncio.sleep(0.01 * task.attempts)  # backoff
                self.transition(task, TaskStatus.ASSIGNED)  # retry

    async def _emit(self, topic: str, task: Task) -> None:
        if self._metrics:
            self._metrics.counter("task_event", topic=topic)
        if self._bus:
            await self._bus.publish(topic, {"task_id": task.id, "status": task.status.value,
                                            "owner": task.owner_agent})
        if self._log:
            self._log.debug(topic, task_id=task.id, attempts=task.attempts)
