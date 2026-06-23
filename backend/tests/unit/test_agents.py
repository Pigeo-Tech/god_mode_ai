"""Unit tests for the Phase 3 Base Agent System.

Run offline: python scripts/run_tests.py agents
Or with pytest once deps are installed: pytest backend/tests/unit/test_agents.py
No external infrastructure required.
"""
from __future__ import annotations

import pytest

from backend.core.agent_context import AgentDeps, deps_from_container
from backend.core.base_agent import BaseAgent
from backend.core.container import Container
from backend.generals.base import BaseGeneral, KeywordRouter
from backend.soldiers.base.base_soldier import BaseSoldier
from backend.core.tool_registry.registry import FunctionTool
from backend.schemas.agent import AgentRequest, AgentTier, TaskStatus


# --------------------------------------------------------------------------- helpers
def _container_deps() -> tuple[Container, AgentDeps]:
    c = Container()
    return c, deps_from_container(c)


async def _aok():
    return None


# --------------------------------------------------------------------------- soldiers
class ToolSoldier(BaseSoldier):
    tool_name = "uppercase"
    required_context = ["text"]


async def test_soldier_runs_single_tool():
    c, deps = _container_deps()
    c.permissions.grant("worker", "tool:uppercase")
    c.permissions.assign("upper1", "worker")

    async def upper(args):
        return args["text"].upper()

    c.tools.register(FunctionTool("uppercase", upper,
                                  schema={"type": "object", "required": ["text"]}))
    soldier = ToolSoldier("upper1", deps)
    await soldier.initialize()

    resp = await soldier.run(AgentRequest(objective="up", context={"text": "hello"}))
    assert resp.status == TaskStatus.COMPLETED
    assert resp.result == "HELLO"
    assert resp.latency_ms is not None and resp.latency_ms >= 0
    assert resp.tier == AgentTier.SOLDIER


async def test_soldier_validation_blocks_missing_context():
    c, deps = _container_deps()
    soldier = ToolSoldier("upper2", deps)
    await soldier.initialize()
    resp = await soldier.run(AgentRequest(objective="up", context={}))  # no 'text'
    assert resp.status == TaskStatus.FAILED
    assert "validation" in resp.error


async def test_soldier_error_becomes_fail_envelope_not_crash():
    deps = AgentDeps()  # no tools -> execute raises

    class BadSoldier(BaseSoldier):
        tool_name = "missing_tool"

    s = BadSoldier("bad", deps)
    await s.initialize()
    resp = await s.run(AgentRequest(objective="x"))
    assert resp.status == TaskStatus.FAILED
    assert resp.error  # captured, did not propagate


async def test_custom_work_soldier():
    class ReverseSoldier(BaseSoldier):
        async def work(self, request):
            return self._ok(request, request.objective[::-1])

    s = ReverseSoldier("rev", AgentDeps())
    await s.initialize()
    resp = await s.run(AgentRequest(objective="abc"))
    assert resp.result == "cba"


# --------------------------------------------------------------------------- general
class EchoSoldier(BaseSoldier):
    async def work(self, request):
        return self._ok(request, f"{self.agent_id}:{request.objective}")


class DemoGeneral(BaseGeneral):
    domain = "demo"
    soldiers = ["alpha", "beta"]


async def test_general_routes_and_aggregates_over_bus():
    c, deps = _container_deps()
    # spin up two soldiers; they register on the message bus
    for name in ("alpha", "beta"):
        s = EchoSoldier(name, deps)
        await s.initialize()
    general = DemoGeneral("demo_gen", deps)
    await general.initialize()

    resp = await general.run(AgentRequest(objective="hello"))
    assert resp.status == TaskStatus.COMPLETED
    body = resp.result
    assert body["domain"] == "demo"
    assert body["soldiers_used"] == 2
    assert body["succeeded"] == 2
    contents = {r["result"] for r in body["results"]}
    assert contents == {"alpha:hello", "beta:hello"}


async def test_keyword_router_selects_subset():
    c, deps = _container_deps()
    for name in ("weather", "stock"):
        await EchoSoldier(name, deps).initialize()

    class RoutedGeneral(BaseGeneral):
        domain = "routed"
        soldiers = ["weather", "stock"]
        router = KeywordRouter({"weather": "weather", "price": "stock"})

    g = RoutedGeneral("rg", deps)
    await g.initialize()
    resp = await g.run(AgentRequest(objective="what is the weather today"))
    assert resp.result["soldiers_used"] == 1
    assert resp.result["results"][0]["result"] == "weather:what is the weather today"


async def test_general_handles_missing_soldier_gracefully():
    c, deps = _container_deps()

    class GhostGeneral(BaseGeneral):
        domain = "ghost"
        soldiers = ["does_not_exist"]

    g = GhostGeneral("gg", deps)
    await g.initialize()
    resp = await g.run(AgentRequest(objective="x"))
    assert resp.status == TaskStatus.COMPLETED  # general doesn't crash
    assert resp.result["succeeded"] == 0
    assert resp.result["results"][0]["error"] == "soldier not running"


async def test_general_reachable_via_message_bus():
    """King-style: reach a general by name through the bus (no direct reference)."""
    c, deps = _container_deps()
    await EchoSoldier("alpha", deps).initialize()
    g = DemoGeneral("demo_gen", deps)
    g.soldiers = ["alpha"]
    await g.initialize()

    from backend.schemas.serde import request_to_dict
    reply = await deps.message_bus.request("general.demo_gen",
                                           request_to_dict(AgentRequest(objective="ping")))
    assert reply["status"] == "completed"
    assert reply["result"]["succeeded"] == 1


# --------------------------------------------------------------------------- base agent
async def test_base_agent_health_check():
    class Noop(BaseAgent):
        async def execute(self, request):
            return self._ok(request, None)

    a = Noop("noop", AgentDeps())
    assert (await a.health_check())["status"] == "down"
    await a.initialize()
    assert (await a.health_check())["status"] == "ok"


def test_base_agent_is_abstract():
    with pytest.raises(TypeError):
        BaseAgent("x")  # cannot instantiate abstract class
