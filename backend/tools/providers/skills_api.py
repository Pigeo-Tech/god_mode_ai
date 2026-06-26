"""External Skills API tool — let soldiers CALL your Skills API during a task (Option 2).

Registered as the ``skills.invoke`` tool when ``SKILLS_API_URL`` is configured. A soldier sends the
user's request to your Skills API, gets back a result, and uses it in its answer/action — so your
skills actually *execute* inside AGNI's King → General → Soldier flow, not just describe steps.

Fully env-configurable so it works with most REST skill APIs without code changes:

    SKILLS_API_URL     required — the endpoint to call (enables the tool)
    SKILLS_API_KEY     optional — your API key/token
    SKILLS_API_AUTH    optional — how the key is sent: "bearer" (default) | "x-api-key" | "none"
    SKILLS_API_METHOD  optional — "POST" (default) | "GET"
    SKILLS_API_FIELD   optional — request field that carries the query (default "input")

The tool returns the raw parsed response plus a flattened ``text`` for easy prompt injection.
Stdlib only — no extra dependencies.
"""
from __future__ import annotations

import asyncio
import json
import os
import urllib.parse
import urllib.request

from backend.core.tool_registry.registry import BaseTool


class SkillsApiProvider:
    name = "skills_api"

    def __init__(self, url: str, key: str = "", auth: str = "bearer",
                 method: str = "POST", field: str = "input") -> None:
        self._url = url
        self._key = key
        self._auth = (auth or "bearer").lower()
        self._method = (method or "POST").upper()
        self._field = field or "input"

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._key and self._auth == "bearer":
            h["Authorization"] = f"Bearer {self._key}"
        elif self._key and self._auth == "x-api-key":
            h["x-api-key"] = self._key
        return h

    def _call(self, query: str) -> dict:
        if self._method == "GET":
            sep = "&" if "?" in self._url else "?"
            url = f"{self._url}{sep}{urllib.parse.urlencode({self._field: query})}"
            req = urllib.request.Request(url, headers=self._headers(), method="GET")
        else:
            payload = json.dumps({self._field: query}).encode("utf-8")
            req = urllib.request.Request(self._url, data=payload,
                                         headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 - configured endpoint
            raw = resp.read().decode("utf-8", "replace")
        try:
            return {"body": json.loads(raw)}
        except json.JSONDecodeError:
            return {"body": raw}

    async def invoke(self, query: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call, query)


def _flatten(body) -> str:
    """Best-effort flatten of any response into prompt-friendly text."""
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        for k in ("result", "output", "answer", "text", "content", "message", "data"):
            if k in body and body[k]:
                return _flatten(body[k])
        return json.dumps(body)[:1500]
    if isinstance(body, list):
        return "\n".join(_flatten(x) for x in body[:10])
    return str(body)


class SkillsApiTool(BaseTool):
    kind = "skills"

    def __init__(self, name: str, provider: SkillsApiProvider) -> None:
        self.name = name
        self._provider = provider

    def schema(self) -> dict:
        return {"type": "object", "properties": {"query": {"type": "string"}}}

    async def invoke(self, args: dict) -> dict:
        query = args.get("query") or args.get("objective") or args.get("prompt") or ""
        try:
            res = await self._provider.invoke(query)
        except Exception as exc:  # best-effort — soldier degrades to model knowledge
            return {"query": query, "text": "", "body": None, "error": str(exc)}
        return {"query": query, "text": _flatten(res.get("body")), "body": res.get("body")}


def skills_api_from_env(secrets=None):
    """Build a SkillsApiTool from env, or None if SKILLS_API_URL isn't set."""
    get = (secrets.get if secrets is not None else os.getenv)
    url = get("SKILLS_API_URL")
    if not url:
        return None
    return SkillsApiTool("skills.invoke", SkillsApiProvider(
        url=url, key=get("SKILLS_API_KEY") or "",
        auth=get("SKILLS_API_AUTH") or "bearer",
        method=get("SKILLS_API_METHOD") or "POST",
        field=get("SKILLS_API_FIELD") or "input"))
