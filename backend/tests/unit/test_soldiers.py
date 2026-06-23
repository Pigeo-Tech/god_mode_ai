"""Tests for the Phase 6 Soldier agents and full-system integration."""
from __future__ import annotations

import pytest

from backend.bootstrap import bootstrap_system
from backend.core.agent_context import deps_from_container
from backend.core.container import Container
from backend.core.permission_manager.permissions import PermissionError
from backend.generals.registry import GENERAL_CLASSES
from backend.soldiers.bootstrap import bootstrap_soldiers
from backend.soldiers.catalog import SOLDIER_CATALOG
from backend.soldiers.tools import TOOL_NAMES
from backend.schemas.agent import AgentRequest, TaskStatus
from backend.schemas.serde import request_to_dict


# --------------------------------------------------------------------------- catalogue
def test_catalogue_has_41_unique_soldiers():
    names = [s.name for s in SOLDIER_CATALOG]
    assert len(names) == 145
    assert len(set(names)) == 145


def test_every_general_roster_soldier_exists_in_catalogue():
    catalog = {s.name for s in SOLDIER_CATALOG}
    for cls in GENERAL_CLASSES:
        for soldier in cls.soldiers:
            assert soldier in catalog, f"{cls.domain} references missing soldier {soldier}"


# --------------------------------------------------------------------------- bootstrap
async def test_bootstrap_soldiers_starts_all_live_with_tools():
    c = Container()
    deps, names = await bootstrap_soldiers(c)
    assert len(names) == 145
    assert len(c.agents.list_live()) == len(names) == 145
    assert set(c.tools.list()) == set(TOOL_NAMES)
    assert len(TOOL_NAMES) == 144  # only the custom memory soldier has no tool


# --------------------------------------------------------------------------- behaviour
async def test_weather_soldier_returns_shaped_data_over_bus():
    c = Container()
    deps, _ = await bootstrap_soldiers(c)
    reply = await deps.message_bus.request(
        "soldier.weather", request_to_dict(AgentRequest(objective="London")))
    assert reply["status"] == "completed"
    data = reply["result"]["data"]
    assert "temp_c" in data and "condition" in data


async def test_memory_soldier_store_then_recall():
    c = Container()
    deps, _ = await bootstrap_soldiers(c)
    store = await deps.message_bus.request(
        "soldier.long_term_memory", request_to_dict(AgentRequest(objective="the sky is blue",
                                                       context={"user_id": "u1"})))
    assert store["result"]["action"] == "remember"
    recall = await deps.message_bus.request(
        "soldier.long_term_memory", request_to_dict(AgentRequest(objective="sky colour",
                                                       context={"user_id": "u1",
                                                                "action": "recall"})))
    assert recall["result"]["action"] == "recall"
    assert any("sky" in h["content"] for h in recall["result"]["recalled"])


async def test_allow_list_enforces_single_responsibility():
    c = Container()
    deps, _ = await bootstrap_soldiers(c)
    # the stock soldier is locked to the 'stock' tool; calling 'weather' must be denied
    with pytest.raises(PermissionError):
        await c.tools.invoke("weather", {"objective": "x"}, agent_id="stock")
    # its own tool is allowed
    out = await c.tools.invoke("stock", {"objective": "AAPL"}, agent_id="stock")
    assert out["tool"] == "stock"


# --------------------------------------------------------------------------- full system
async def test_full_system_king_to_real_soldiers():
    c = Container()
    deps, king = await bootstrap_system(c)
    resp = await king.run(AgentRequest(
        objective="research the market and check the stock price then notify me",
        context={"user_id": "u1"}))
    assert resp.status == TaskStatus.COMPLETED
    body = resp.result
    assert body["steps_total"] == body["steps_completed"]  # all subtasks succeeded
    assert body["steps_failed"] == 0
    generals = {b["general"] for b in body["breakdown"]}
    assert {"knowledge", "finance"} & generals


async def test_full_system_single_domain_findings():
    c = Container()
    deps, king = await bootstrap_system(c)
    resp = await king.run(AgentRequest(objective="research quantum computing",
                                       context={"user_id": "u2"}))
    body = resp.result
    assert body["steps_completed"] == 1
    # knowledge general surfaces findings from its soldier
    kb = body["breakdown"][0]
    assert kb["general"] == "knowledge"
    assert kb["result"]["findings"]
