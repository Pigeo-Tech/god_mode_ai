"""BaseSoldier — single-responsibility worker.

Phase 3 (+ Phase 6 tweak). A soldier does exactly one thing and returns the common envelope.
Define the work in one of two ways:
  * set ``tool_name`` and the soldier invokes that one tool from the Tool Registry, or
  * override ``work()`` for custom logic.

The soldier passes the request's ``objective`` plus its context into the tool, so tools can act
on the natural-language instruction. On initialize the soldier registers a request/reply handler
on the Message Bus at ``soldier.<agent_id>`` so Generals can reach it by name.
"""
from __future__ import annotations

from backend.core.base_agent import BaseAgent
from backend.schemas.agent import AgentRequest, AgentResponse, AgentTier
from backend.schemas.serde import dict_to_request, response_to_dict


class BaseSoldier(BaseAgent):
    tier = AgentTier.SOLDIER

    #: name of the single tool this soldier wraps (optional if `work` is overridden)
    tool_name: str | None = None
    #: context keys that must be present for the soldier to act
    required_context: list[str] = []

    def target(self) -> str:
        return f"soldier.{self.agent_id}"

    async def initialize(self) -> None:
        await super().initialize()
        if self.deps.message_bus is not None:
            self.deps.message_bus.handle(self.target(), self._on_message)

    async def shutdown(self) -> None:
        if self.deps.message_bus is not None:
            self.deps.message_bus.unregister(self.target())
        await super().shutdown()

    async def _on_message(self, payload: dict) -> dict:
        """Message-bus adapter: dict in -> run -> dict out."""
        response = await self.run(dict_to_request(payload))
        return response_to_dict(response)

    async def validate(self, request: AgentRequest) -> bool:
        return all(key in request.context for key in self.required_context)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        if self.tool_name is not None:
            if self.deps.tools is None:
                raise RuntimeError(f"{self.agent_id}: no tool registry available")
            args = {"objective": request.objective, **(request.context or {})}
            result = await self.deps.tools.invoke(self.tool_name, args, agent_id=self.agent_id)
            return self._ok(request, result)
        return await self.work(request)

    async def work(self, request: AgentRequest) -> AgentResponse:
        """Override for soldiers that don't wrap a single registry tool."""
        raise NotImplementedError(f"{self.agent_id}: set tool_name or override work()")
