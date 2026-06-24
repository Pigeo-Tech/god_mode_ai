"""Tests for the SuperSoldier expert pipeline (reference: research soldier)."""
from __future__ import annotations

from backend.bootstrap import bootstrap_system
from backend.core.container import Container
from backend.schemas.agent import AgentRequest
from backend.schemas.serde import request_to_dict


async def test_research_super_soldier_runs_full_pipeline():
    c = Container()
    deps, _ = await bootstrap_system(c)
    reply = await deps.message_bus.request(
        "soldier.research",
        request_to_dict(AgentRequest(objective="explain black holes",
                                     context={"user_id": "u1"})))
    assert reply["status"] == "completed"
    r = reply["result"]
    assert r["domain"] == "research"
    assert r["answer"]
    assert 0.0 <= r["confidence"] <= 1.0
    assert "reason" in r["plan"] and "validate" in r["plan"]
    assert r["stages"]["validated"] is True


async def test_super_soldier_learns_to_memory():
    c = Container()
    deps, _ = await bootstrap_soldiers(c)
    await deps.message_bus.request(
        "soldier.research",
        request_to_dict(AgentRequest(objective="explain quantum entanglement",
                                     context={"user_id": "u2"})))
    hits = await deps.memory.recall("entanglement", scope="knowledge", owner="u2", k=5)
    assert any("research" in h["content"] for h in hits)


async def test_super_soldier_actionable_emits_deep_link():
    c = Container()
    deps, _ = await bootstrap_soldiers(c)
    reply = await deps.message_bus.request(
        "soldier.research",
        request_to_dict(AgentRequest(objective="install whatsapp app",
                                     context={"user_id": "u3"})))
    action = reply["result"]["action"]
    assert action is not None
    assert action["url"].startswith("https://play.google.com")
