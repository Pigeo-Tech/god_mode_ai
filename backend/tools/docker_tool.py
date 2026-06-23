"""DockerTool — run a command inside a container as a tool.

Phase 8. Production uses the docker SDK; a `runner` can be injected for tests. Output is captured
and returned. Containers are the isolation boundary for untrusted/heavy tools.
"""
from __future__ import annotations

from typing import Awaitable, Callable

from backend.core.tool_registry.registry import BaseTool

# runner(image, command, env) -> {"exit_code": int, "logs": str}
Runner = Callable[..., Awaitable[dict]]


async def _docker_runner(image: str, command: list[str], env: dict | None = None) -> dict:
    import asyncio

    import docker  # type: ignore  # lazy

    def _run() -> dict:
        client = docker.from_env()
        container = client.containers.run(image, command, environment=env or {}, detach=True)
        try:
            result = container.wait()
            logs = container.logs().decode("utf-8", "replace")
            return {"exit_code": result.get("StatusCode", 0), "logs": logs}
        finally:
            container.remove(force=True)

    return await asyncio.to_thread(_run)


class DockerTool(BaseTool):
    kind = "docker"

    def __init__(self, name: str, image: str, runner: Runner | None = None) -> None:
        self.name = name
        self._image = image
        self._runner = runner or _docker_runner

    async def invoke(self, args: dict) -> dict:
        command = args.get("command") or []
        if isinstance(command, str):
            command = command.split()
        return await self._runner(self._image, command, args.get("env"))
