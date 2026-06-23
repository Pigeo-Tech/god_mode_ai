"""Soldiers bootstrap.

Phase 6. From a DI container: register all soldier tools, grant capabilities, lock each soldier
to its single tool (per-agent allow-list — defense in depth on the one-responsibility rule),
then register and start every soldier so the Generals' rosters are fully live.
"""
from __future__ import annotations

from backend.core.agent_context import deps_from_container
from backend.soldiers.catalog import SOLDIER_CATALOG
from backend.soldiers.factory import ensure_all_soldiers, register_soldiers
from backend.soldiers.tools import register_soldier_tools


async def bootstrap_soldiers(container):
    """Wire and start all soldiers on the container. Returns (deps, soldier_names)."""
    deps = deps_from_container(container)

    tool_names = register_soldier_tools(container.tools)

    # Capability: soldiers may call tools; the allow-list restricts each to its own.
    container.permissions.grant("soldier", "tool:*")

    names = register_soldiers(container.agents, deps)
    await ensure_all_soldiers(container.agents)

    for spec in SOLDIER_CATALOG:
        container.permissions.assign(spec.name, "soldier")
        if spec.cls is None:  # tool-backed soldiers are locked to their single tool
            container.tools.allow(spec.name, {spec.tool or spec.name})

    container.logger.info("soldiers.bootstrapped", soldiers=len(names), tools=len(tool_names))
    return deps, names
