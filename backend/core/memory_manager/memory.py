"""Memory Manager — unified façade over short-term, long-term, and semantic memory.

Phase 7. The manager now depends on the backend *ports* and receives concrete stores via
dependency injection; it defaults to the in-memory implementations so it runs with zero infra.
The public API (remember / recall / forget) is unchanged from Phase 2, and the
``short_term`` / ``long_term`` / ``semantic`` attributes remain accessible. Scope facades
(``conversation`` / ``task`` / ``project`` / ``knowledge``) bind a fixed scope for convenience.
"""
from __future__ import annotations

from uuid import uuid4

from backend.memory.embedding import EmbeddingService, HashingEmbeddingService
from backend.memory.long_term.store import InMemoryLongTermStore
from backend.memory.record import MemoryRecord
from backend.memory.scopes import (ConversationMemory, KnowledgeMemory, ProjectMemory,
                                   TaskMemory)
from backend.memory.semantic.store import InMemorySemanticStore
from backend.memory.short_term.store import InMemoryShortTermStore

# Back-compat aliases (Phase 2 names).
ShortTermStore = InMemoryShortTermStore
LongTermStore = InMemoryLongTermStore
SemanticStore = InMemorySemanticStore

__all__ = ["MemoryManager", "MemoryRecord", "EmbeddingService",
           "ShortTermStore", "LongTermStore", "SemanticStore"]


class MemoryManager:
    """Implements the IMemoryManager port. Backends are injected (defaults: in-memory)."""

    def __init__(self, logger=None, metrics=None, *, embeddings=None,
                 short_term=None, long_term=None, semantic=None) -> None:
        self._emb = embeddings or HashingEmbeddingService()
        self.short_term = short_term or InMemoryShortTermStore()
        self.long_term = long_term or InMemoryLongTermStore()
        self.semantic = semantic or InMemorySemanticStore(self._emb)
        self._log = logger
        self._metrics = metrics

        # scope facades
        self.conversation = ConversationMemory(self)
        self.task = TaskMemory(self)
        self.project = ProjectMemory(self)
        self.knowledge = KnowledgeMemory(self)

    async def remember(self, content: str, *, scope: str, owner: str,
                       kind: str = "note", metadata: dict | None = None) -> str:
        rec = MemoryRecord(id=str(uuid4()), scope=scope, owner=owner, kind=kind,
                           content=content, metadata=metadata or {})
        self.long_term.insert(rec)
        self.semantic.upsert(rec.id, content, {"scope": scope, "owner": owner})
        if self._metrics:
            self._metrics.counter("memory_remember", scope=scope)
        if self._log:
            self._log.debug("memory.remember", id=rec.id, scope=scope, owner=owner)
        return rec.id

    async def recall(self, query: str, *, scope: str, owner: str, k: int = 8) -> list[dict]:
        hits = self.semantic.search(query, k, {"scope": scope, "owner": owner})
        records = self.long_term.hydrate([mid for mid, _ in hits])
        scores = dict(hits)
        if self._metrics:
            self._metrics.counter("memory_recall", scope=scope)
        return [
            {"id": r.id, "content": r.content, "kind": r.kind,
             "metadata": r.metadata, "score": round(scores.get(r.id, 0.0), 4)}
            for r in records
        ]

    async def forget(self, memory_id: str) -> None:
        self.long_term.delete(memory_id)
        self.semantic.delete(memory_id)
        if self._log:
            self._log.info("memory.forget", id=memory_id)

    def history(self, scope: str, owner: str, limit: int = 50) -> list[MemoryRecord]:
        """Recent records in a scope (chronological), independent of semantic search."""
        return self.long_term.query(scope, owner, limit)
