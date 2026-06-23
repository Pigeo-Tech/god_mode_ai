"""BaseAgent — the runtime contract every King, General, and Soldier inherits.

Phase 3. The Phase 1 abstract contract is now a working base class implementing the
**Template Method** pattern: `run()` wraps the agent's `execute()` with validation gating,
latency timing, metrics, structured logging, and uniform error handling — so every agent at
every tier returns a well-formed AgentResponse and never crashes the caller.

Subclasses (BaseSoldier, BaseGeneral, KingAgent) only have to implement `execute()`; the rest
have sensible defaults. Agents communicate solely through the injected buses — never directly.
"""
from __future__ import annotations

import abc
from time import perf_counter

from backend.core.agent_context import AgentDeps
from backend.schemas.agent import (AgentRequest, AgentResponse, AgentTier, TaskStatus)


class BaseAgent(abc.ABC):
    tier: AgentTier = AgentTier.SOLDIER

    def __init__(self, agent_id: str, deps: AgentDeps | None = None) -> None:
        self.agent_id = agent_id
        self.deps = deps or AgentDeps()
        self._log = (self.deps.logger.bind(agent=agent_id)
                     if self.deps.logger is not None else None)
        self._initialized = False

    # ---- lifecycle (override as needed) ----
    async def initialize(self) -> None:
        self._initialized = True
        if self._log:
            self._log.debug("agent.initialized", tier=self.tier.value)

    async def validate(self, request: AgentRequest) -> bool:
        """Return True if this agent can handle the request. Default: yes."""
        return True

    @abc.abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Perform the unit of work. Must return an AgentResponse."""

    async def health_check(self) -> dict:
        return {"status": "ok" if self._initialized else "down",
                "agent": self.agent_id, "tier": self.tier.value}

    async def shutdown(self) -> None:
        self._initialized = False

    # ---- template method: the public entry point ----
    async def run(self, request: AgentRequest) -> AgentResponse:
        start = perf_counter()
        try:
            if not await self.validate(request):
                return self._fail(request, "validation failed", start)
            response = await self.execute(request)
            response.latency_ms = (perf_counter() - start) * 1000
            self._record(start, "ok")
            return response
        except Exception as exc:  # noqa: BLE001 - never let an agent crash its caller
            if self._log:
                self._log.error("agent.execute_failed", error=str(exc))
            self._record(start, "error")
            return self._fail(request, str(exc), start)

    # ---- response envelope helpers ----
    def _ok(self, request: AgentRequest, result) -> AgentResponse:
        return AgentResponse(request_id=request.request_id, agent_id=self.agent_id,
                             tier=self.tier, status=TaskStatus.COMPLETED, result=result)

    def _fail(self, request: AgentRequest, error: str, start: float | None = None) -> AgentResponse:
        latency = (perf_counter() - start) * 1000 if start else None
        return AgentResponse(request_id=request.request_id, agent_id=self.agent_id,
                             tier=self.tier, status=TaskStatus.FAILED, error=error,
                             latency_ms=latency)

    def _record(self, start: float, status: str) -> None:
        if self.deps.metrics is not None:
            self.deps.metrics.observe("agent_latency_seconds", perf_counter() - start,
                                      tier=self.tier.value, status=status)
            self.deps.metrics.counter("agent_runs", tier=self.tier.value, status=status)
