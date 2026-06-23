"""LLMTool — a Tool that wraps an LLM provider.

Phase 8. Lets any Soldier (e.g. research, coding, translation) call a model through the Tool
Registry with the same permission/rate-limit path as every other tool.
"""
from __future__ import annotations

from backend.core.tool_registry.registry import BaseTool
from backend.tools.providers.base import LLMProvider


class LLMTool(BaseTool):
    kind = "llm"

    def __init__(self, name: str, provider: LLMProvider) -> None:
        self.name = name
        self._provider = provider

    def schema(self) -> dict:
        return {"type": "object", "properties": {"prompt": {"type": "string"}}}

    async def invoke(self, args: dict) -> dict:
        prompt = args.get("prompt") or args.get("objective") or ""
        options = args.get("options") or {}
        completion = await self._provider.complete(prompt, **options)
        return {"provider": self._provider.name, "model": getattr(self._provider, "model", None),
                "completion": completion}
