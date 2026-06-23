"""ToolFactory — build tools by kind (Factory pattern).

Phase 8. Decouples "what kind of tool" from "how it's constructed". Register a builder per kind,
then create tools from declarative config. Used by orchestration bootstrap and, later, by a tool
marketplace / dynamic registration.
"""
from __future__ import annotations

from typing import Any, Callable

from backend.core.tool_registry.registry import BaseTool, FunctionTool
from backend.tools.docker_tool import DockerTool
from backend.tools.mcp.adapter import McpTool
from backend.tools.providers.llm_tool import LLMTool
from backend.tools.rest_tool import RestApiTool

Builder = Callable[..., BaseTool]


class ToolFactory:
    def __init__(self) -> None:
        self._builders: dict[str, Builder] = {}
        self.register_defaults()

    def register(self, kind: str, builder: Builder) -> None:
        self._builders[kind] = builder

    def register_defaults(self) -> None:
        self.register("llm", lambda name, provider, **_: LLMTool(name, provider))
        self.register("rest", lambda name, **cfg: RestApiTool(name, **cfg))
        self.register("mcp", lambda name, **cfg: McpTool(name, **cfg))
        self.register("docker", lambda name, **cfg: DockerTool(name, **cfg))
        self.register("python", lambda name, fn, **cfg: FunctionTool(name, fn, **cfg))

    def kinds(self) -> list[str]:
        return sorted(self._builders)

    def create(self, kind: str, name: str, **config: Any) -> BaseTool:
        if kind not in self._builders:
            raise KeyError(f"unknown tool kind {kind!r}")
        return self._builders[kind](name, **config)
