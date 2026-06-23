"""Agent Manager — lifecycle authority for all agents.

Phase 2. Registers agent specs, builds instances via a Factory, tracks liveness via heartbeats,
and supervises (restarts crashed agents). The concrete King/General/Soldier classes arrive in
Phases 4-6; here the manager works against the BaseAgent contract and a registry of builders.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from backend.core.base_agent import BaseAgent
from backend.schemas.agent import AgentTier

# A builder takes an agent_id and returns a BaseAgent instance (Factory pattern).
AgentBuilder = Callable[[str], BaseAgent]


@dataclass
class AgentSpec:
    name: str
    tier: AgentTier
    builder: AgentBuilder
    max_instances: int = 1


@dataclass
class AgentRecord:
    name: str
    tier: AgentTier
    instance: BaseAgent
    status: str = "initialized"
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRegistry:
    """Catalogue of known agent specs (what *can* be built)."""

    def __init__(self) -> None:
        self._specs: dict[str, AgentSpec] = {}

    def register(self, spec: AgentSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"agent spec {spec.name!r} already registered")
        self._specs[spec.name] = spec

    def get(self, name: str) -> AgentSpec:
        if name not in self._specs:
            raise KeyError(f"unknown agent {name!r}")
        return self._specs[name]

    def list(self, tier: AgentTier | None = None) -> list[str]:
        return sorted(n for n, s in self._specs.items() if tier is None or s.tier == tier)


class AgentManager:
    """Implements the IAgentManager port."""

    def __init__(self, registry: AgentRegistry | None = None, logger=None, metrics=None) -> None:
        self._registry = registry or AgentRegistry()
        self._live: dict[str, AgentRecord] = {}
        self._log = logger
        self._metrics = metrics

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    def register(self, spec: AgentSpec) -> None:
        self._registry.register(spec)

    async def ensure(self, name: str) -> BaseAgent:
        """Return a live instance, building + initializing it on first use."""
        if name in self._live:
            return self._live[name].instance
        spec = self._registry.get(name)
        instance = spec.builder(name)
        await instance.initialize()
        self._live[name] = AgentRecord(name=name, tier=spec.tier, instance=instance,
                                       status="ready")
        if self._metrics:
            self._metrics.counter("agent_spawned", tier=spec.tier.value)
        if self._log:
            self._log.info("agent.spawned", name=name, tier=spec.tier.value)
        return instance

    def get(self, name: str) -> BaseAgent:
        return self._live[name].instance

    def list_live(self) -> list[AgentRecord]:
        return list(self._live.values())

    async def health_check(self, name: str) -> dict:
        rec = self._live.get(name)
        if not rec:
            return {"status": "down", "reason": "not running"}
        try:
            res = await rec.instance.health_check()
            rec.last_heartbeat = datetime.now(timezone.utc)
            rec.status = "ready"
            return res
        except Exception as exc:  # noqa: BLE001
            rec.status = "unhealthy"
            return {"status": "error", "error": str(exc)}

    async def supervise(self) -> list[str]:
        """Restart any agent whose health check fails. Returns restarted names."""
        restarted: list[str] = []
        for name, rec in list(self._live.items()):
            res = await self.health_check(name)
            if res.get("status") != "ok":
                await self.retire(name)
                await self.ensure(name)
                restarted.append(name)
                if self._metrics:
                    self._metrics.counter("agent_restarted", tier=rec.tier.value)
        return restarted

    async def retire(self, name: str) -> None:
        rec = self._live.pop(name, None)
        if rec:
            try:
                await rec.instance.shutdown()
            except Exception:  # noqa: BLE001
                pass
            if self._log:
                self._log.info("agent.retired", name=name)
