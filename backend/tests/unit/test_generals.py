"""Tests for the Phase 5 General agents.

Validates routing per domain, the registry/bootstrap, and end-to-end King -> every General ->
stub soldiers over the in-memory buses.
"""
from __future__ import annotations

from backend.core.agent_context import deps_from_container
from backend.core.container import Container
from backend.generals.bootstrap import bootstrap_generals
from backend.generals.knowledge.general import KnowledgeGeneral
from backend.generals.registry import GENERAL_CLASSES, register_generals
from backend.king.king import KingAgent
from backend.king.planner import KeywordPlanner
from backend.soldiers.base.base_soldier import BaseSoldier
from backend.schemas.agent import AgentRequest, AgentTier, TaskStatus


class StubSoldier(BaseSoldier):
    async def work(self, request):
        return self._ok(request, f"{self.agent_id}->{request.objective}")


# --------------------------------------------------------------------------- structure
def test_there_are_fifteen_generals_with_unique_domains():
    domains = [c.domain for c in GENERAL_CLASSES]
    assert len(domains) == 15
    assert len(set(domains)) == 15


def test_every_general_has_soldiers_and_router():
    for cls in GENERAL_CLASSES:
        assert cls.soldiers, f"{cls.__name__} has no soldiers"
        assert cls.tier == AgentTier.GENERAL
        assert cls.router is not None


# --------------------------------------------------------------------------- routing
async def test_knowledge_general_routes_by_keyword():
    c = Container()
    deps = deps_from_container(c)
    for s in KnowledgeGeneral.soldiers:
        await StubSoldier(s, deps).initialize()
    gen = KnowledgeGeneral("knowledge", deps)
    await gen.initialize()
    resp = await gen.run(AgentRequest(objective="what is the weather in Paris"))
    body = resp.result
    assert body["soldiers_used"] == 1
    assert body["results"][0]["agent_id"] == "weather"
    # domain-specific aggregation surfaces findings
    assert body["findings"] == ["weather->what is the weather in Paris"]


async def test_router_falls_back_to_all_when_no_keyword():
    c = Container()
    deps = deps_from_container(c)
    for s in KnowledgeGeneral.soldiers:
        await StubSoldier(s, deps).initialize()
    gen = KnowledgeGeneral("knowledge", deps)
    await gen.initialize()
    resp = await gen.run(AgentRequest(objective="tell me something interesting"))
    assert resp.result["soldiers_used"] == 1  # collapses to a single research answer
    assert resp.result["results"][0]["agent_id"] == "research"


# --------------------------------------------------------------------------- registry
async def test_register_generals_registers_all_ten():
    c = Container()
    deps = deps_from_container(c)
    names = register_generals(c.agents, deps)
    assert len(names) == 15
    assert {"knowledge", "device", "security", "iot", "asi", "voice"} <= set(names)
    assert len(c.agents.registry.list(AgentTier.GENERAL)) == 15


async def test_bootstrap_starts_all_generals_live():
    c = Container()
    deps, names = await bootstrap_generals(c)
    assert len(c.agents.list_live()) == len(names) == 15


# --------------------------------------------------------------------------- end to end
async def test_king_delegates_to_each_domain():
    c = Container()
    deps, names = await bootstrap_generals(c)
    # attach one stub soldier per soldier name referenced by any general
    all_soldiers = {s for cls in GENERAL_CLASSES for s in cls.soldiers}
    for s in all_soldiers:
        await StubSoldier(s, deps).initialize()

    king = KingAgent("king", deps)
    await king.initialize()

    # objective with keywords hitting several domains in parallel + a sequential step
    resp = await king.run(AgentRequest(
        objective="research the market and check the stock price then email the summary",
        context={"user_id": "u1"}))
    assert resp.status == TaskStatus.COMPLETED
    body = resp.result
    generals_used = {b["general"] for b in body["breakdown"]}
    assert {"knowledge", "finance", "communication"} & generals_used
    assert body["steps_completed"] == body["steps_total"]


async def test_king_reaches_specific_general_via_bus():
    c = Container()
    deps, names = await bootstrap_generals(c)
    await StubSoldier("stock", deps).initialize()
    from backend.schemas.serde import request_to_dict
    reply = await deps.message_bus.request(
        "general.finance",
        request_to_dict(AgentRequest(objective="get the stock quote")))
    assert reply["status"] == "completed"
    assert reply["result"]["results"][0]["agent_id"] == "stock"
