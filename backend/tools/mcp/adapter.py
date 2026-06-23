"""McpTool — call a tool exposed by an MCP server.

Phase 8. Adapts an external Model Context Protocol server's tool into the local Tool Registry, so
MCP-provided capabilities are invoked through the same permission/rate-limit path as native
tools. A `caller` is injected (real MCP client in production, fake in tests).
"""
from __future__ import annotations

from typing import Awaitable, Callable

from backend.core.tool_registry.registry import BaseTool

# caller(server_url, tool_name, args) -> result
McpCaller = Callable[[str, str, dict], Awaitable[dict]]


async def _default_caller(server_url: str, tool_name: str, args: dict) -> dict:
    # Production: use an MCP client library to connect and call the remote tool.
    raise RuntimeError("no MCP client configured; inject a caller")


class McpTool(BaseTool):
    kind = "mcp"

    def __init__(self, name: str, server_url: str, remote_tool: str,
                 caller: McpCaller | None = None) -> None:
        self.name = name
        self._server = server_url
        self._remote = remote_tool
        self._caller = caller or _default_caller

    async def invoke(self, args: dict) -> dict:
        result = await self._caller(self._server, self._remote, args)
        return {"server": self._server, "tool": self._remote, "result": result}
