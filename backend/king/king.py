"""KingAgent — the orchestrator.

Phase 4. The King receives a user objective and:
  1. loads relevant context from Memory,
  2. asks the Planner to decompose it into a Task DAG,
  3. builds the graph in the Task Manager and dispatches each subtask to its General over the
     Message Bus (with retries handled by the Task Manager),
  4. monitors progress via the Event Bus,
  5. aggregates the Generals' results into a final answer,
  6. persists the outcome to Memory,
  7. returns the uniform AgentResponse.

The King performs **no** domain work itself — every step is delegated.
"""
from __future__ import annotations

from uuid import uuid4

from backend.core.base_agent import BaseAgent
from backend.core.task_manager.tasks import Task, TaskGraph
from backend.king.aggregator import Aggregator
from backend.king.monitor import ProgressMonitor
from backend.king.planner import KeywordPlanner, Planner
from backend.schemas.agent import AgentRequest, AgentResponse, AgentTier
from backend.schemas.serde import request_to_dict


def _default_planner() -> Planner:
    # Routes objective keywords to the 10 Generals; falls back to the Knowledge General.
    routes = {
        "search": "knowledge", "research": "knowledge", "weather": "knowledge",
        "news": "knowledge", "look up": "knowledge",
        "plan": "planning", "schedule": "planning", "organize": "planning",
        "run": "execution", "execute": "execution", "deploy": "execution",
        "remember": "memory", "recall": "memory",
        "code": "coding", "program": "coding", "bug": "coding", "git": "coding",
        "image": "media", "video": "media", "music": "media", "speech": "media",
        "stock": "finance", "crypto": "finance", "price": "finance", "budget": "finance",
        "email": "communication", "message": "communication", "notify": "communication",
        "file": "system", "docker": "system", "aws": "system", "terminal": "system",
        "automate": "automation", "workflow": "automation", "trigger": "automation",
        "device": "device", "flashlight": "device", "volume": "device", "brightness": "device",
        "battery": "device", "bluetooth": "device", "wifi": "device", "settings": "device",
        "clipboard": "device", "gallery": "device", "storage": "device",
        "malware": "security", "antivirus": "security", "phishing": "security", "scam": "security",
        "firewall": "security", "encrypt": "security", "password": "security", "privacy": "security",
        "threat": "security", "vault": "security",
        "smart": "iot", "iot": "iot", "appliance": "iot", "vehicle": "iot", "wearable": "iot",
        "lighting": "iot", "matter": "iot",
        "optimize": "asi", "optimization": "asi", "reasoning": "asi", "predict": "asi",
        "performance": "asi", "thermal": "asi", "cache": "asi",
        "voice": "voice", "speech": "voice", "transcribe": "voice", "accent": "voice",
        "conversation": "voice", "wake": "voice",
    }
    return KeywordPlanner(routes, default_general="knowledge")


class KingAgent(BaseAgent):
    tier = AgentTier.KING

    def __init__(self, agent_id: str = "king", deps=None, planner: Planner | None = None) -> None:
        super().__init__(agent_id, deps)
        self._planner = planner or _default_planner()
        self._aggregator = Aggregator()

    async def initialize(self) -> None:
        await super().initialize()
        if self.deps.message_bus is not None:
            self.deps.message_bus.handle("king", self._on_message)

    async def shutdown(self) -> None:
        if self.deps.message_bus is not None:
            self.deps.message_bus.unregister("king")
        await super().shutdown()

    async def _on_message(self, payload: dict) -> dict:
        from backend.schemas.serde import dict_to_request, response_to_dict
        return response_to_dict(await self.run(dict_to_request(payload)))

    async def execute(self, request: AgentRequest) -> AgentResponse:
        owner = str(request.context.get("user_id", "anonymous"))

        # 1. context from memory (best-effort)
        context: list[dict] = []
        if self.deps.memory is not None:
            context = await self.deps.memory.recall(request.objective,
                                                    scope="conversation", owner=owner, k=5)

        # 2. plan -> 3. build graph
        plan = await self._planner.plan(request.objective, context)
        graph = TaskGraph()
        step_tasks: list[Task] = []
        for step in plan:
            deps_ids = {step_tasks[i].id for i in step.depends_on}
            task = graph.add(Task(objective=step.objective, owner_agent=step.general,
                                  depends_on=deps_ids))
            step_tasks.append(task)

        # 4. monitor + execute
        monitor = ProgressMonitor(self.deps.event_bus, group=f"king-{uuid4().hex[:8]}")
        await monitor.start()
        if self.deps.tasks is None:
            raise RuntimeError("King requires a Task Manager (deps.tasks)")
        tasks = await self.deps.tasks.run_graph(graph, self._dispatch_executor(request))
        if self.deps.event_bus is not None:
            await self.deps.event_bus.drain()
        await monitor.stop()

        # 5. aggregate
        final = self._aggregator.merge(request.objective, plan, tasks)
        final["progress"] = monitor.snapshot()

        # 6. persist
        if self.deps.memory is not None:
            await self.deps.memory.remember(
                f"Q: {request.objective}\nA: {final['summary']}",
                scope="conversation", owner=owner, kind="exchange")

        # 7. respond
        return self._ok(request, final)

    def _dispatch_executor(self, parent: AgentRequest):
        """Build the per-task executor that dispatches a subtask to its General over the bus."""
        async def execute_task(task: Task):
            sub = AgentRequest(objective=task.objective, parent_id=parent.request_id,
                               context=dict(parent.context))
            target = f"general.{task.owner_agent}"
            try:
                reply = await self.deps.message_bus.request(target, request_to_dict(sub))
            except KeyError as exc:
                raise RuntimeError(f"general {task.owner_agent!r} not running") from exc
            if reply.get("status") != "completed":
                raise RuntimeError(reply.get("error") or "general failed")
            return reply.get("result")
        return execute_task
