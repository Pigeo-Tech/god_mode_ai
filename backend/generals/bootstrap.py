"""Generals bootstrap.

Phase 5. Convenience wiring used by the API/runtime: from a DI container, register and start all
ten Generals so the King can immediately delegate to them. Soldiers (Phase 6) attach the same
way under each General's roster.
"""
from __future__ import annotations

from backend.core.agent_context import deps_from_container
from backend.generals.registry import ensure_all_generals, register_generals


async def bootstrap_generals(container):
    """Register + ensure all Generals on the given container. Returns (deps, names)."""
    deps = deps_from_container(container)
    names = register_generals(container.agents, deps)
    await ensure_all_generals(container.agents)
    container.logger.info("generals.bootstrapped", count=len(names), domains=names)
    return deps, names
