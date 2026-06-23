"""BaseGeneral — domain coordinator.

Phase 3. A General owns a domain, selects the right Soldiers for a request (Strategy pattern via
SoldierRouter), dispatches to them over the Message Bus (no direct references), and aggregates
their responses into a domain-level result. Registers ``general.<agent_id>`` on the Message Bus
so the King can reach it.
"""
from __future__ import annotations

import abc

from backend.core.base_agent import BaseAgent
from backend.schemas.agent import AgentRequest, AgentResponse, AgentTier
from backend.schemas.serde import dict_to_request, request_to_dict, response_to_dict


# --------------------------------------------------------------------------- routing
class SoldierRouter(abc.ABC):
    """Strategy: choose which soldiers handle a request."""

    @abc.abstractmethod
    def select(self, request: AgentRequest, soldiers: list[str]) -> list[str]: ...


class AllRouter(SoldierRouter):
    """Fan out to every soldier in the domain."""

    def select(self, request: AgentRequest, soldiers: list[str]) -> list[str]:
        return list(soldiers)


class KeywordRouter(SoldierRouter):
    """Pick soldiers whose keywords appear in the objective; fall back to all."""

    def __init__(self, keyword_map: dict[str, str]) -> None:
        # keyword -> soldier name
        self._map = {k.lower(): v for k, v in keyword_map.items()}

    def select(self, request: AgentRequest, soldiers: list[str]) -> list[str]:
        text = request.objective.lower()
        chosen = [s for kw, s in self._map.items() if kw in text and s in soldiers]
        return chosen or list(soldiers)


# --------------------------------------------------------------------------- general
class BaseGeneral(BaseAgent):
    tier = AgentTier.GENERAL

    domain: str = "generic"
    soldiers: list[str] = []
    router: SoldierRouter = AllRouter()

    def target(self) -> str:
        return f"general.{self.agent_id}"

    async def initialize(self) -> None:
        await super().initialize()
        if self.deps.message_bus is not None:
            self.deps.message_bus.handle(self.target(), self._on_message)

    async def shutdown(self) -> None:
        if self.deps.message_bus is not None:
            self.deps.message_bus.unregister(self.target())
        await super().shutdown()

    async def _on_message(self, payload: dict) -> dict:
        response = await self.run(dict_to_request(payload))
        return response_to_dict(response)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        chosen = self.router.select(request, self.soldiers)
        if self.deps.message_bus is None:
            raise RuntimeError(f"{self.agent_id}: no message bus available")

        results: list[dict] = []
        payload = request_to_dict(request)
        for soldier in chosen:
            try:
                reply = await self.deps.message_bus.request(f"soldier.{soldier}", payload)
                results.append(reply)
            except KeyError:
                results.append({"agent_id": soldier, "status": "failed",
                                "error": "soldier not running"})
        merged = self.aggregate(request, results)
        return self._ok(request, merged)

    def aggregate(self, request: AgentRequest, results: list[dict]) -> dict:
        """Combine soldier responses. Override for domain-specific merging."""
        succeeded = [r for r in results if r.get("status") == "completed"]
        return {
            "domain": self.domain,
            "soldiers_used": len(results),
            "succeeded": len(succeeded),
            "results": results,
        }
