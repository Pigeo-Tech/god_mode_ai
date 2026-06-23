"""Serialization helpers for moving agent envelopes over the buses.

Phase 3. The Message/Event buses carry plain dicts (so they work over Redis/Kafka later). These
helpers convert AgentRequest/AgentResponse to/from dicts and work whether the schemas are backed
by Pydantic or the dataclass fallback.
"""
from __future__ import annotations

from uuid import UUID

from backend.schemas.agent import (AgentRequest, AgentResponse, AgentTier, TaskStatus)


def request_to_dict(req: AgentRequest) -> dict:
    return {
        "request_id": str(req.request_id),
        "parent_id": str(req.parent_id) if req.parent_id else None,
        "objective": req.objective,
        "context": dict(req.context or {}),
    }


def dict_to_request(d: dict) -> AgentRequest:
    kwargs: dict = {
        "objective": d["objective"],
        "context": dict(d.get("context") or {}),
    }
    if d.get("request_id"):
        kwargs["request_id"] = UUID(d["request_id"])
    if d.get("parent_id"):
        kwargs["parent_id"] = UUID(d["parent_id"])
    return AgentRequest(**kwargs)


def response_to_dict(resp: AgentResponse) -> dict:
    return {
        "request_id": str(resp.request_id),
        "agent_id": resp.agent_id,
        "tier": resp.tier.value if isinstance(resp.tier, AgentTier) else resp.tier,
        "status": resp.status.value if isinstance(resp.status, TaskStatus) else resp.status,
        "result": resp.result,
        "error": resp.error,
        "latency_ms": resp.latency_ms,
    }


def dict_to_response(d: dict) -> AgentResponse:
    return AgentResponse(
        request_id=UUID(d["request_id"]) if isinstance(d["request_id"], str) else d["request_id"],
        agent_id=d["agent_id"],
        tier=AgentTier(d["tier"]),
        status=TaskStatus(d["status"]),
        result=d.get("result"),
        error=d.get("error"),
        latency_ms=d.get("latency_ms"),
    )
