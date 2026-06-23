"""Common schemas shared by every agent in the hierarchy.

Phase 2. Uses Pydantic when available (production); falls back to dataclasses so the Core
Framework runs and is testable with zero third-party dependencies during development.
The public surface (AgentRequest / AgentResponse / enums) is identical either way.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AgentTier(str, Enum):
    KING = "king"
    GENERAL = "general"
    SOLDIER = "soldier"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _now() -> datetime:
    return datetime.now(timezone.utc)


try:  # pragma: no cover - production path
    from pydantic import BaseModel, Field

    class AgentRequest(BaseModel):
        """Uniform request envelope passed down the hierarchy."""
        request_id: UUID = Field(default_factory=uuid4)
        parent_id: UUID | None = None
        objective: str
        context: dict[str, Any] = Field(default_factory=dict)
        deadline: datetime | None = None

    class AgentResponse(BaseModel):
        """Uniform response envelope returned up the hierarchy. EVERY agent uses this."""
        request_id: UUID
        agent_id: str
        tier: AgentTier
        status: TaskStatus
        result: Any | None = None
        error: str | None = None
        latency_ms: float | None = None
        created_at: datetime = Field(default_factory=_now)

except ImportError:  # pragma: no cover - dependency-free fallback
    from dataclasses import dataclass, field

    @dataclass
    class AgentRequest:  # type: ignore[no-redef]
        objective: str
        request_id: UUID = field(default_factory=uuid4)
        parent_id: UUID | None = None
        context: dict[str, Any] = field(default_factory=dict)
        deadline: datetime | None = None

    @dataclass
    class AgentResponse:  # type: ignore[no-redef]
        request_id: UUID
        agent_id: str
        tier: AgentTier
        status: TaskStatus
        result: Any | None = None
        error: str | None = None
        latency_ms: float | None = None
        created_at: datetime = field(default_factory=_now)
