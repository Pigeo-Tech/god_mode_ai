"""Web-search tool (Tavily) — gives soldiers live, sourced information.

Registered as the ``web.search`` tool when ``TAVILY_API_KEY`` is configured. Soldiers call it to
ground their answers in current web results (movies, news, prices, "near me"), instead of relying
on the model's stale training memory. Uses only the stdlib so it adds no dependencies.
"""
from __future__ import annotations

import asyncio
import json
import urllib.request

from backend.core.tool_registry.registry import BaseTool

_ENDPOINT = "https://api.tavily.com/search"


class TavilyProvider:
    name = "tavily"

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def _call(self, query: str, max_results: int) -> dict:
        payload = json.dumps({
            "api_key": self._key,
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "search_depth": "basic",
        }).encode()
        req = urllib.request.Request(
            _ENDPOINT, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - fixed HTTPS endpoint
            return json.loads(resp.read().decode())

    async def search(self, query: str, max_results: int = 5) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call, query, max_results)


class WebSearchTool(BaseTool):
    kind = "search"

    def __init__(self, name: str, provider: TavilyProvider) -> None:
        self.name = name
        self._provider = provider

    def schema(self) -> dict:
        return {"type": "object", "properties": {"query": {"type": "string"}}}

    async def invoke(self, args: dict) -> dict:
        query = args.get("query") or args.get("objective") or args.get("prompt") or ""
        try:
            data = await self._provider.search(query, int(args.get("max_results", 5)))
        except Exception as exc:  # best-effort: network/timeout -> empty result
            return {"query": query, "answer": "", "results": [], "error": str(exc)}
        results = [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": (r.get("content") or "")[:500],
            }
            for r in (data.get("results") or [])
        ]
        return {"query": query, "answer": data.get("answer") or "", "results": results}
