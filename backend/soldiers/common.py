"""Common soldier implementations.

Phase 6. ToolSoldier is a parameterized single-tool worker (most soldiers are instances of it).
MemorySoldier is an example of a soldier whose responsibility is served by a core service (the
Memory Manager) rather than a registry tool.
"""
from __future__ import annotations

from backend.schemas.agent import AgentRequest, AgentResponse
from backend.soldiers.base.base_soldier import BaseSoldier


class ToolSoldier(BaseSoldier):
    """A soldier that wraps exactly one named tool from the Tool Registry."""

    def __init__(self, agent_id: str, deps=None, *, tool: str | None = None,
                 required: list[str] | None = None) -> None:
        super().__init__(agent_id, deps)
        self.tool_name = tool or agent_id
        self.required_context = list(required or [])


class MemorySoldier(BaseSoldier):
    """Stores or recalls memories via the Memory Manager (no registry tool)."""

    tool_name = None

    async def work(self, request: AgentRequest) -> AgentResponse:
        ctx = request.context or {}
        owner = str(ctx.get("user_id", "anon"))
        if ctx.get("action") == "recall":
            hits = await self.deps.memory.recall(request.objective, scope="knowledge",
                                                 owner=owner, k=5)
            return self._ok(request, {"action": "recall", "recalled": hits})
        memory_id = await self.deps.memory.remember(request.objective, scope="knowledge",
                                                    owner=owner)
        return self._ok(request, {"action": "remember", "stored": memory_id})


class LlmSoldier(BaseSoldier):
    """Answers the objective with an LLM: OpenAI/Anthropic if a key is configured,
    otherwise the built-in local model. Returns {"answer": text}."""

    tool_name = None

    async def work(self, request: AgentRequest) -> AgentResponse:
        tools = self.deps.tools
        available = tools.list() if tools is not None else []
        tool = (
            "llm.openai" if "llm.openai" in available
            else "llm.anthropic" if "llm.anthropic" in available
            else "llm.local"
        )
        result = await tools.invoke(tool, {"prompt": request.objective}, agent_id=self.agent_id)
        return self._ok(request, {
            "answer": result.get("completion", ""),
            "model": result.get("model"),
            "provider": result.get("provider"),
        })
