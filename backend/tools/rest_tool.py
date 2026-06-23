"""RestApiTool — call an external REST API as a tool.

Phase 8. Uses httpx in production; accepts an injected async transport for testing (so tests run
with no network). Args: ``path`` (appended to base_url), ``method``, ``params``, ``json``.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from backend.core.tool_registry.registry import BaseTool

# transport(method, url, params, json, headers) -> dict
Transport = Callable[..., Awaitable[dict]]


async def _httpx_transport(method: str, url: str, *, params=None, json=None, headers=None) -> dict:
    import httpx  # type: ignore  # lazy

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, params=params, json=json, headers=headers)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        return {"status": resp.status_code,
                "body": resp.json() if "application/json" in ctype else resp.text}


class RestApiTool(BaseTool):
    kind = "rest"

    def __init__(self, name: str, base_url: str, method: str = "GET",
                 headers: dict | None = None, transport: Transport | None = None) -> None:
        self.name = name
        self._base = base_url.rstrip("/")
        self._method = method
        self._headers = headers or {}
        self._transport = transport or _httpx_transport

    async def invoke(self, args: dict) -> dict:
        path = args.get("path", "")
        url = f"{self._base}/{path.lstrip('/')}" if path else self._base
        return await self._transport(
            args.get("method", self._method), url,
            params=args.get("params"), json=args.get("json"),
            headers={**self._headers, **(args.get("headers") or {})})
