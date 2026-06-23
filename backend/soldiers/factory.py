"""Soldier factory.

Phase 6. Registers every Soldier with the Agent Manager (Factory pattern). Registry keys are
tier-qualified (``soldier:<name>``) so they never clash with same-named Generals; the soldier's
own id stays the bare name, so Generals reach it at ``soldier.<name>``.
"""
from __future__ import annotations

from backend.core.agent_context import AgentDeps
from backend.core.agent_manager.manager import AgentManager, AgentSpec
from backend.schemas.agent import AgentTier
from backend.soldiers.catalog import SOLDIER_CATALOG, SoldierSpec
from backend.soldiers.common import ToolSoldier


def soldier_key(name: str) -> str:
    return f"soldier:{name}"


def _builder(spec: SoldierSpec, deps: AgentDeps):
    if spec.cls is not None:
        return lambda agent_id, c=spec.cls, n=spec.name, d=deps: c(n, d)
    tool = spec.tool or spec.name
    return lambda agent_id, n=spec.name, t=tool, d=deps: ToolSoldier(n, d, tool=t)


def register_soldiers(manager: AgentManager, deps: AgentDeps) -> list[str]:
    names: list[str] = []
    for spec in SOLDIER_CATALOG:
        manager.register(AgentSpec(name=soldier_key(spec.name), tier=AgentTier.SOLDIER,
                                   builder=_builder(spec, deps)))
        names.append(spec.name)
    return names


async def ensure_all_soldiers(manager: AgentManager) -> list:
    return [await manager.ensure(soldier_key(spec.name)) for spec in SOLDIER_CATALOG]
