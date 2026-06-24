"""Tests for the Phase 9 ApiService (the FastAPI-free request path)."""
from __future__ import annotations

from backend.api.service import ApiService


async def test_service_chat_and_request_store():
    service = await ApiService.create()
    env = await service.chat("research quantum computing", user_id="u1")
    assert env["status"] == "completed"
    assert env["tier"] == "king"
    # request is retrievable by id
    fetched = service.get_request(env["request_id"])
    assert fetched is not None and fetched["request_id"] == env["request_id"]


async def test_service_stream_emits_lifecycle_events():
    service = await ApiService.create()
    events = [e async for e in service.stream_chat("research black holes", user_id="u1")]
    types = [e["type"] for e in events]
    assert types[0] == "accepted"
    assert "progress" in types
    assert types[-1] == "done"
    result_event = next(e for e in events if e["type"] == "result")
    assert result_event["status"] == "completed"


async def test_service_lists_agents_and_tools():
    service = await ApiService.create()
    agents = service.list_agents()
    assert agents["count"] == 161  # 146 soldiers + 15 generals live
    tools = service.list_tools()
    assert "llm" in tools["by_kind"]            # LLM provider tools registered
    assert "llm.local" in tools["all"]


async def test_service_health_ok():
    service = await ApiService.create()
    code, detail = await service.health()
    assert code == 200 and detail["healthy"] is True
