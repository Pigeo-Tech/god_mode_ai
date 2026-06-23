"""Unit / integration tests for the Phase 4 King Agent.

Exercises the full vertical slice: King -> Planner -> Task DAG -> Generals -> Soldiers, all over
the in-memory buses. No external infrastructure required.
"""
from __future__ import annotations

from backend.core.agent_context import deps_from_container
from backend.core.container import Container
from backend.generals.base import BaseGeneral
from backend.king.king import KingAgent
from backend.king.planner import KeywordPlanner
from backend.soldiers.base.base_soldier import BaseSoldier
from backend.schemas.agent import AgentRequest, AgentTier, TaskStatus
from backend.schemas.serde import request_to_dict


# --------------------------------------------------------------------------- fixtures
class EchoSoldier(BaseSoldier):
    async def work(self, request):
        return self._ok(request, f"{self.agent_id}:{request.objective}")


def _make_general(name: str, soldiers: list[str]):
    class _G(BaseGeneral):
        domain = name
    g = _G  # noqa: N806
    return g, soldiers


async def _build_system(routes: dict[str, str]):
    """Spin up a container, a couple generals (knowledge, coding) each with a soldier."""
    c = Container()
    deps = deps_from_container(c)

    # soldiers
    await EchoSoldier("researcher", deps).initialize()
    await EchoSoldier("programmer", deps).initialize()

    # generals
    class KnowledgeGeneral(BaseGeneral):
        domain = "knowledge"
        soldiers = ["researcher"]

    class CodingGeneral(BaseGeneral):
        domain = "coding"
        soldiers = ["programmer"]

    await KnowledgeGeneral("knowledge", deps).initialize()
    await CodingGeneral("coding", deps).initialize()

    king = KingAgent("king", deps, planner=KeywordPlanner(routes, default_general="knowledge"))
    await king.initialize()
    return c, deps, king


# --------------------------------------------------------------------------- tests
async def test_king_single_step_delegates_to_general():
    c, deps, king = await _build_system({"research": "knowledge"})
    resp = await king.run(AgentRequest(objective="research black holes",
                                       context={"user_id": "u1"}))
    assert resp.status == TaskStatus.COMPLETED
    assert resp.tier == AgentTier.KING
    body = resp.result
    assert body["steps_total"] == 1
    assert body["steps_completed"] == 1
    assert body["breakdown"][0]["general"] == "knowledge"


async def test_king_decomposes_parallel_and_sequential():
    # "and" => parallel; "then" => sequential dependency
    c, deps, king = await _build_system({"research": "knowledge", "code": "coding"})
    resp = await king.run(AgentRequest(
        objective="research the topic and write notes then code the prototype",
        context={"user_id": "u1"}))
    body = resp.result
    # group 1: "research the topic", "write notes" (parallel) ; group 2: "code the prototype"
    assert body["steps_total"] == 3
    assert body["steps_completed"] == 3
    generals = [b["general"] for b in body["breakdown"]]
    assert "coding" in generals and "knowledge" in generals


async def test_king_handles_failing_general_gracefully():
    c = Container()
    deps = deps_from_container(c)

    class BrokenGeneral(BaseGeneral):
        domain = "coding"
        soldiers = []

        async def execute(self, request):
            raise RuntimeError("general exploded")

    await BrokenGeneral("coding", deps).initialize()
    king = KingAgent("king", deps,
                     planner=KeywordPlanner({"code": "coding"}, default_general="coding"))
    await king.initialize()

    resp = await king.run(AgentRequest(objective="code something", context={"user_id": "u1"}))
    # King itself completes; the failed subtask is reported, not raised
    assert resp.status == TaskStatus.COMPLETED
    assert resp.result["steps_failed"] == 1
    assert resp.result["breakdown"][0]["attempts"] >= 1


async def test_king_persists_exchange_to_memory():
    c, deps, king = await _build_system({"research": "knowledge"})
    await king.run(AgentRequest(objective="research quasars", context={"user_id": "u42"}))
    hits = await c.memory.recall("quasars", scope="conversation", owner="u42", k=5)
    assert any("quasars" in h["content"] for h in hits)


async def test_king_progress_monitor_counts():
    c, deps, king = await _build_system({"research": "knowledge"})
    resp = await king.run(AgentRequest(objective="research stars and research planets",
                                       context={"user_id": "u1"}))
    prog = resp.result["progress"]
    assert prog["completed"] >= 1
    assert prog["assigned"] >= 1


async def test_king_reachable_via_message_bus():
    c, deps, king = await _build_system({"research": "knowledge"})
    reply = await deps.message_bus.request(
        "king", request_to_dict(AgentRequest(objective="research comets",
                                             context={"user_id": "u1"})))
    assert reply["status"] == "completed"
    assert reply["result"]["steps_completed"] == 1


async def test_king_missing_general_reported():
    c = Container()
    deps = deps_from_container(c)
    # No generals running at all
    king = KingAgent("king", deps,
                     planner=KeywordPlanner({}, default_general="knowledge"))
    await king.initialize()
    resp = await king.run(AgentRequest(objective="do something", context={"user_id": "u1"}))
    assert resp.status == TaskStatus.COMPLETED
    assert resp.result["steps_failed"] == 1
    assert "not running" in resp.result["breakdown"][0]["error"]
