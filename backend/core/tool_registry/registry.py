"""Tool Registry — central catalogue of callable capabilities.

Phase 2 (+ Phase 8). Implements the IToolRegistry port. Tools are registered with a JSON schema;
invocation validates args, checks permissions (``tool:<name>`` scope) and per-agent allow-lists,
applies an optional rate limiter, routes through the tool's adapter, and records metrics.
Concrete provider adapters (OpenAI/Anthropic/Gemini/REST/MCP/Docker) live in `backend/tools/`.
"""
from __future__ import annotations

import abc
import time
from typing import Any, Awaitable, Callable

from backend.core.permission_manager.permissions import PermissionError


class RateLimitExceeded(Exception):
    """Raised when a tool is called beyond its configured rate."""


class BaseTool(abc.ABC):
    """Implements the ITool port. One tool == one capability."""

    name: str
    kind: str = "python"

    @abc.abstractmethod
    async def invoke(self, args: dict) -> Any: ...

    def schema(self) -> dict:
        """Override to advertise expected args. Default: accept anything."""
        return {"type": "object", "additionalProperties": True}

    def validate(self, args: dict) -> None:
        """Lightweight required-field validation from the schema's `required` list."""
        for field_name in self.schema().get("required", []):
            if field_name not in args:
                raise ValueError(f"{self.name}: missing required arg {field_name!r}")


class FunctionTool(BaseTool):
    """Wrap a plain async function as a tool (Factory-friendly)."""

    def __init__(self, name: str, fn: Callable[[dict], Awaitable[Any]],
                 schema: dict | None = None, kind: str = "python") -> None:
        self.name = name
        self.kind = kind
        self._fn = fn
        self._schema = schema or {"type": "object", "additionalProperties": True}

    async def invoke(self, args: dict) -> Any:
        return await self._fn(args)

    def schema(self) -> dict:
        return self._schema


class ToolRegistry:
    """Implements the IToolRegistry port."""

    def __init__(self, permissions=None, metrics=None, logger=None, rate_limiter=None) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._permissions = permissions
        self._metrics = metrics
        self._log = logger
        self._rate_limiter = rate_limiter  # any object with .check(key) -> raises on limit
        # per-agent allow-lists; empty/missing == allow all registered tools
        self._allow: dict[str, set[str]] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool {tool.name!r} already registered")
        self._tools[tool.name] = tool
        if self._log:
            self._log.info("tool.registered", name=tool.name, kind=tool.kind)

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"unknown tool {name!r}")
        return self._tools[name]

    def list(self) -> list[str]:
        return sorted(self._tools)

    def list_by_kind(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for name, tool in self._tools.items():
            out.setdefault(tool.kind, []).append(name)
        return {k: sorted(v) for k, v in out.items()}

    def allow(self, agent_id: str, tool_names: set[str]) -> None:
        self._allow[agent_id] = set(tool_names)

    async def invoke(self, name: str, args: dict, *, agent_id: str) -> Any:
        tool = self.get(name)
        tool.validate(args)

        allow = self._allow.get(agent_id)
        if allow is not None and name not in allow:
            raise PermissionError(f"agent {agent_id} not allowed tool {name!r}")
        if self._permissions is not None:
            await self._permissions.require(agent_id, f"tool:{name}")
        if self._rate_limiter is not None:
            self._rate_limiter.check(name)

        start = time.perf_counter()
        status = "ok"
        try:
            return await tool.invoke(args)
        except Exception:
            status = "error"
            raise
        finally:
            if self._metrics:
                self._metrics.observe("tool_latency_seconds", time.perf_counter() - start,
                                      tool=name, status=status)
                self._metrics.counter("tool_invocations", tool=name, status=status)
