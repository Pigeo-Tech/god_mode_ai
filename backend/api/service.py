"""ApiService — framework-agnostic application service behind the API.

Phase 9. This is the seam between the transport layer (FastAPI routers/websockets) and the agent
platform. It owns the bootstrapped system (King + Generals + Soldiers), runs chat requests,
streams progress, keeps a request store for status lookups, and exposes roster/tool listings.
Keeping this FastAPI-free makes the whole request path unit-testable without a web server.
"""
from __future__ import annotations

import time
from collections import deque
from typing import AsyncIterator
from uuid import uuid4

from backend.bootstrap import bootstrap_system
from backend.core.container import Container
from backend.schemas.agent import AgentRequest
from backend.schemas.serde import response_to_dict


class ApiService:
    def __init__(self, container: Container, king) -> None:
        self.container = container
        self.king = king
        self._requests: dict[str, dict] = {}  # request_id -> result envelope
        self.started_at = time.time()
        self.audit: deque = deque(maxlen=500)   # recent events for the Logs/Security views
        self.record_audit("system", "boot", "AGNI platform online")

    def record_audit(self, kind: str, event: str, detail: str = "", user: str = "") -> None:
        self.audit.appendleft({"ts": time.time(), "kind": kind, "event": event,
                               "detail": detail, "user": user})

    def recent_audit(self, limit: int = 100) -> list[dict]:
        return list(self.audit)[:limit]

    @classmethod
    async def create(cls, container: Container | None = None) -> "ApiService":
        container = container or Container()
        await container.startup()
        _, king = await bootstrap_system(container)
        return cls(container, king)

    async def chat(self, objective: str, user_id: str) -> dict:
        request = AgentRequest(objective=objective, context={"user_id": user_id})
        response = await self.king.run(request)
        envelope = response_to_dict(response)
        self._requests[envelope["request_id"]] = envelope
        self.record_audit("chat", "request", objective[:120],
                          user=str(user_id)[:8])
        return envelope

    async def stream_chat(self, objective: str, user_id: str) -> AsyncIterator[dict]:
        """Yield lifecycle events then the final result (for SSE / WebSocket)."""
        stream_id = uuid4().hex
        yield {"type": "accepted", "stream_id": stream_id, "objective": objective}
        envelope = await self.chat(objective, user_id)
        result = envelope.get("result") or {}
        yield {"type": "progress", "progress": result.get("progress", {})}
        yield {"type": "result", "request_id": envelope["request_id"],
               "status": envelope["status"], "result": result}
        yield {"type": "done"}

    def get_request(self, request_id: str) -> dict | None:
        return self._requests.get(request_id)

    def list_agents(self) -> dict:
        live = self.container.agents.list_live()
        return {"count": len(live),
                "agents": [{"name": r.name, "tier": r.tier.value, "status": r.status}
                           for r in live]}

    def list_tools(self) -> dict:
        return {"by_kind": self.container.tools.list_by_kind(),
                "all": self.container.tools.list()}

    async def health(self) -> tuple[int, dict]:
        return await self.container.health.report()

    def metrics(self) -> str:
        return self.container.metrics.render()
