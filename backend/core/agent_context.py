"""Agent dependency-injection context.

Phase 3-4. Agents never reach into the global container or build their own infrastructure; they
receive exactly the core services they need through an AgentDeps bundle. This keeps agents
unit-testable in isolation (pass fakes) and decoupled from the composition root.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentDeps:
    event_bus: Any = None
    message_bus: Any = None
    tools: Any = None
    memory: Any = None
    permissions: Any = None
    logger: Any = None
    metrics: Any = None
    tasks: Any = None          # Task Manager (used by the King in Phase 4)


def deps_from_container(container: Any) -> AgentDeps:
    """Build an AgentDeps from the Phase 2 DI container."""
    return AgentDeps(
        event_bus=container.event_bus,
        message_bus=container.message_bus,
        tools=container.tools,
        memory=container.memory,
        permissions=container.permissions,
        logger=container.logger,
        metrics=container.metrics,
        tasks=container.tasks,
    )
