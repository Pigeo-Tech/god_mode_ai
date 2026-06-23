"""Dependency-Injection container — wires the whole Core Framework together.

Phase 2. This is the composition root. Everything that needs a service receives it from here;
nothing constructs its own infrastructure. Swapping in-memory backends for Redis/Postgres/Qdrant
later means changing only this file.
"""
from __future__ import annotations

from backend.config.settings import settings
from backend.core.agent_manager.manager import AgentManager, AgentRegistry
from backend.core.event_bus.event_bus import EventBus
from backend.core.health.health import HealthService
from backend.core.logger.logger import get_logger
from backend.memory.factory import build_memory_manager
from backend.core.message_bus.message_bus import MessageBus
from backend.core.metrics.metrics import MetricsRegistry
from backend.core.permission_manager.permissions import PermissionManager
from backend.core.scheduler.scheduler import Scheduler
from backend.core.task_manager.tasks import TaskManager
from backend.core.tool_registry.registry import ToolRegistry
from backend.core.workflow_engine.engine import WorkflowEngine
from backend.tools.factory import ToolFactory


class Container:
    """Composition root holding singletons of every core service."""

    def __init__(self) -> None:
        self.settings = settings
        self.logger = get_logger(settings.app_name)
        self.metrics = MetricsRegistry()

        self.permissions = PermissionManager(logger=self.logger)
        self.event_bus = EventBus(logger=self.logger, metrics=self.metrics)
        self.message_bus = MessageBus(logger=self.logger, metrics=self.metrics)
        self.tools = ToolRegistry(permissions=self.permissions, metrics=self.metrics,
                                  logger=self.logger)
        self.memory = build_memory_manager(self.settings, self.logger, self.metrics)
        self.tasks = TaskManager(bus=self.event_bus, logger=self.logger, metrics=self.metrics)
        self.workflows = WorkflowEngine(logger=self.logger, metrics=self.metrics)
        self.scheduler = Scheduler(bus=self.event_bus, logger=self.logger, metrics=self.metrics)
        self.agents = AgentManager(registry=AgentRegistry(), logger=self.logger,
                                   metrics=self.metrics)
        self.tool_factory = ToolFactory()
        self.health = HealthService()
        self._register_health()

    def _register_health(self) -> None:
        async def core_ok() -> dict:
            return {"status": "ok"}

        async def bus_ok() -> dict:
            return {"status": "ok", "topics": self.event_bus.topics(),
                    "dead_letter": len(self.event_bus.dead_letter)}

        async def agents_ok() -> dict:
            return {"status": "ok", "live": len(self.agents.list_live())}

        self.health.register("core", core_ok)
        self.health.register("event_bus", bus_ok)
        self.health.register("agents", agents_ok)

    async def startup(self) -> None:
        self.logger.info("container.startup", env=self.settings.app_env,
                         in_memory=self.settings.use_in_memory_backends)

    async def shutdown(self) -> None:
        await self.scheduler.stop()
        await self.event_bus.shutdown()
        self.logger.info("container.shutdown")


# Module-level singleton used by the API layer (Phase 9).
container = Container()
