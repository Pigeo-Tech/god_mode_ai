"""Tests for the Phase 8 Tool Orchestration layer."""
from __future__ import annotations

import pytest

from backend.core.permission_manager.permissions import PermissionManager
from backend.core.tool_registry.registry import RateLimitExceeded, ToolRegistry
from backend.tools.factory import ToolFactory
from backend.tools.mcp.adapter import McpTool
from backend.tools.orchestration import register_provider_tools
from backend.tools.providers.base import LocalProvider
from backend.tools.providers.llm_tool import LLMTool
from backend.tools.rate_limit import TokenBucketRateLimiter
from backend.tools.rest_tool import RestApiTool


def _perms_for(agent: str) -> PermissionManager:
    pm = PermissionManager()
    pm.grant("r", "tool:*")
    pm.assign(agent, "r")
    return pm


# --------------------------------------------------------------------------- LLM
async def test_local_llm_tool_completes():
    tool = LLMTool("llm.local", LocalProvider())
    out = await tool.invoke({"prompt": "hello"})
    assert out["provider"] == "local"
    assert "hello" in out["completion"]


async def test_llm_tool_via_registry_with_permissions():
    pm = _perms_for("research")
    reg = ToolRegistry(permissions=pm)
    reg.register(LLMTool("llm.local", LocalProvider()))
    out = await reg.invoke("llm.local", {"prompt": "summarize x"}, agent_id="research")
    assert out["completion"].startswith("[local-stub]")


async def test_provider_tools_registered_offline_only_local():
    reg = ToolRegistry()

    class NoKeys:
        def get(self, key):
            return None

    names = register_provider_tools(reg, secrets=NoKeys())
    assert names == ["llm.local"]  # no API keys -> only local
    assert "llm.local" in reg.list()


async def test_provider_tools_registers_remote_when_key_present():
    reg = ToolRegistry()

    class FakeSecrets:
        def get(self, key):
            return "sk-test" if key == "OPENAI_API_KEY" else None

    names = register_provider_tools(reg, secrets=FakeSecrets())
    assert "llm.openai" in names
    assert reg.get("llm.openai").kind == "llm"


# --------------------------------------------------------------------------- REST
async def test_rest_tool_with_injected_transport():
    seen = {}

    async def fake_transport(method, url, *, params=None, json=None, headers=None):
        seen.update(method=method, url=url, params=params)
        return {"status": 200, "body": {"ok": True}}

    tool = RestApiTool("weather_api", "https://api.example.com", transport=fake_transport)
    out = await tool.invoke({"path": "/v1/weather", "params": {"city": "Paris"}})
    assert out["body"] == {"ok": True}
    assert seen["url"] == "https://api.example.com/v1/weather"
    assert seen["params"] == {"city": "Paris"}


# --------------------------------------------------------------------------- MCP
async def test_mcp_tool_with_injected_caller():
    async def caller(server, tool, args):
        return {"echo": args}

    tool = McpTool("mcp.search", "http://mcp.local", "search", caller=caller)
    out = await tool.invoke({"q": "hi"})
    assert out["tool"] == "search"
    assert out["result"] == {"echo": {"q": "hi"}}


# --------------------------------------------------------------------------- rate limit
async def test_rate_limiter_blocks_after_capacity():
    pm = _perms_for("a")
    limiter = TokenBucketRateLimiter()
    limiter.configure("burst", capacity=2, refill_per_sec=0.0)  # no refill
    reg = ToolRegistry(permissions=pm, rate_limiter=limiter)
    reg.register(LLMTool("burst", LocalProvider()))
    await reg.invoke("burst", {"prompt": "1"}, agent_id="a")
    await reg.invoke("burst", {"prompt": "2"}, agent_id="a")
    with pytest.raises(RateLimitExceeded):
        await reg.invoke("burst", {"prompt": "3"}, agent_id="a")


# --------------------------------------------------------------------------- factory
def test_tool_factory_creates_by_kind():
    f = ToolFactory()
    assert set(f.kinds()) >= {"llm", "rest", "mcp", "docker", "python"}
    rest = f.create("rest", "svc", base_url="https://x.test")
    assert rest.kind == "rest"
    llm = f.create("llm", "model", provider=LocalProvider())
    assert llm.kind == "llm"


def test_tool_factory_unknown_kind():
    f = ToolFactory()
    with pytest.raises(KeyError):
        f.create("quantum", "q")


def test_registry_list_by_kind():
    reg = ToolRegistry()
    reg.register(LLMTool("llm.local", LocalProvider()))
    reg.register(RestApiTool("svc", "https://x.test"))
    by_kind = reg.list_by_kind()
    assert by_kind["llm"] == ["llm.local"]
    assert by_kind["rest"] == ["svc"]
