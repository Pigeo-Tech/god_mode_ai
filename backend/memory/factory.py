"""Memory backend factory.

Phase 7. Builds a MemoryManager wired to the right backends based on settings. When
``use_in_memory_backends`` is True (dev/tests) it uses the in-memory stores; otherwise it wires
Redis + PostgreSQL + Qdrant. This is the only place that decides which adapters to use.
"""
from __future__ import annotations

from backend.core.memory_manager.memory import MemoryManager
from backend.memory.embedding import HashingEmbeddingService


def _postgres_dsn(s) -> str:
    return (f"postgresql+psycopg://{s.postgres_user}:{s.postgres_password}"
            f"@{s.postgres_host}:{s.postgres_port}/{s.postgres_db}")


def build_memory_manager(settings, logger=None, metrics=None) -> MemoryManager:
    if getattr(settings, "use_in_memory_backends", True):
        return MemoryManager(logger=logger, metrics=metrics)

    # Production: real backends behind the same ports.
    from backend.memory.long_term.store import PostgresLongTermStore
    from backend.memory.semantic.store import QdrantSemanticStore
    from backend.memory.short_term.store import RedisShortTermStore

    embeddings = HashingEmbeddingService()
    return MemoryManager(
        logger=logger, metrics=metrics, embeddings=embeddings,
        short_term=RedisShortTermStore(settings.redis_url),
        long_term=PostgresLongTermStore(_postgres_dsn(settings)),
        semantic=QdrantSemanticStore(settings.qdrant_url, embeddings),
    )
