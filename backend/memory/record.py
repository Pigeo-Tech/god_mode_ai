"""MemoryRecord — the structured unit stored in long-term memory."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MemoryRecord:
    id: str
    scope: str
    owner: str
    kind: str
    content: str
    metadata: dict
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
