"""Workflow Engine — declarative multi-step playbooks.

Phase 2. Executes Workflows composed of Steps with sequential flow, conditional skipping, and
bounded loops. State is a plain dict carried between steps and persisted after each step so a
run can be resumed. Steps call agents/tools via injected callables, keeping the engine pure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable
from uuid import uuid4

State = dict
StepFn = Callable[[State], Awaitable[State]]
Predicate = Callable[[State], bool]


@dataclass
class Step:
    name: str
    run: StepFn
    condition: Predicate | None = None          # skip step if returns False
    loop_while: Predicate | None = None         # repeat step while returns True
    max_loops: int = 100


@dataclass
class Workflow:
    name: str
    steps: list[Step] = field(default_factory=list)
    version: int = 1

    def step(self, name: str, fn: StepFn, **kw) -> "Workflow":
        self.steps.append(Step(name=name, run=fn, **kw))
        return self


@dataclass
class WorkflowRun:
    workflow: str
    id: str = field(default_factory=lambda: str(uuid4()))
    state: State = field(default_factory=dict)
    status: str = "pending"
    cursor: int = 0  # index of next step to run (for resume)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None


class WorkflowEngine:
    """Implements the IWorkflowEngine port."""

    def __init__(self, logger=None, metrics=None) -> None:
        self._runs: dict[str, WorkflowRun] = {}
        self._log = logger
        self._metrics = metrics

    async def run(self, wf: Workflow, initial: State | None = None) -> WorkflowRun:
        run = WorkflowRun(workflow=wf.name, state=dict(initial or {}))
        self._runs[run.id] = run
        return await self._execute(wf, run)

    async def resume(self, wf: Workflow, run_id: str) -> WorkflowRun:
        run = self._runs[run_id]
        return await self._execute(wf, run)

    async def _execute(self, wf: Workflow, run: WorkflowRun) -> WorkflowRun:
        run.status = "running"
        try:
            for idx in range(run.cursor, len(wf.steps)):
                step = wf.steps[idx]
                run.cursor = idx
                if step.condition and not step.condition(run.state):
                    continue
                run.state = await step.run(run.state)
                loops = 0
                while step.loop_while and step.loop_while(run.state):
                    if loops >= step.max_loops:
                        raise RuntimeError(f"step {step.name!r} exceeded max_loops")
                    run.state = await step.run(run.state)
                    loops += 1
                if self._metrics:
                    self._metrics.counter("workflow_step", workflow=wf.name, step=step.name)
            run.cursor = len(wf.steps)
            run.status = "completed"
        except Exception as exc:  # noqa: BLE001
            run.status = "failed"
            run.state["_error"] = str(exc)
            if self._log:
                self._log.error("workflow.failed", workflow=wf.name, error=str(exc))
            raise
        finally:
            run.finished_at = datetime.now(timezone.utc)
        return run

    def get_run(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)
