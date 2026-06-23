"""Memory backend ports.

Phase 7. The MemoryManager depends on these Protocols, not on concrete stores — so the same
manager runs on in-memory stores (dev/tests) or Redis/PostgreSQL/Qdrant (production) with no code
changes upstream. Methods are synchronous to match the sync client libraries used by the
production adapters and to keep the in-memory path simple.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.memory.record import MemoryRecord


@runtime_checkable
class IEmbeddingService(Protocol):
    def embed(self, text: str) -> list[float]: ...


@runtime_checkable
class IShortTermStore(Protocol):
    def set(self, key: str, value: object, ttl: float = 300.0) -> None: ...
    def get(self, key: str) -> object | None: ...
    def delete(self, key: str) -> None: ...


@runtime_checkable
class ILongTermStore(Protocol):
    def insert(self, rec: MemoryRecord) -> None: ...
    def get(self, mid: str) -> MemoryRecord | None: ...
    def delete(self, mid: str) -> None: ...
    def hydrate(self, ids: list[str]) -> list[MemoryRecord]: ...
    def query(self, scope: str, owner: str, limit: int = 50) -> list[MemoryRecord]: ...


@runtime_checkable
class ISemanticStore(Protocol):
    def upsert(self, mid: str, text: str, payload: dict) -> None: ...
    def delete(self, mid: str) -> None: ...
    def search(self, query: str, k: int, flt: dict) -> list[tuple[str, float]]: ...
