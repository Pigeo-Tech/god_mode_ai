# GOD MODE AI — Phase 7: Memory System

> **Status:** Phase 7 of 12 complete. The memory subsystem is now a proper ports-and-adapters
> design: the MemoryManager depends on backend *ports*, defaults to in-memory stores (dev/tests),
> and ships real Redis / PostgreSQL / Qdrant adapters for production — all behind the unchanged
> `IMemoryManager` API. The four memory scopes from the architecture are in place.

## Structure

```
backend/memory/
├── record.py            MemoryRecord
├── embedding.py         HashingEmbeddingService (IEmbeddingService) — swap for a real model
├── ports.py             IShortTermStore / ILongTermStore / ISemanticStore / IEmbeddingService
├── scopes.py            ConversationMemory / TaskMemory / ProjectMemory / KnowledgeMemory
├── factory.py           build_memory_manager(settings) — picks backends
├── short_term/store.py  InMemoryShortTermStore | RedisShortTermStore
├── long_term/store.py   InMemoryLongTermStore  | PostgresLongTermStore (SQLAlchemy Core)
└── semantic/store.py    InMemorySemanticStore  | QdrantSemanticStore
```

`core/memory_manager/memory.py` keeps the `MemoryManager` (now DI-driven) and re-exports the
Phase 2 names for back-compat.

## Backends behind one port

| Tier | Port | Default (dev/tests) | Production adapter |
|---|---|---|---|
| Short-term | `IShortTermStore` | `InMemoryShortTermStore` (TTL dict) | `RedisShortTermStore` (`SETEX`) |
| Long-term | `ILongTermStore` | `InMemoryLongTermStore` | `PostgresLongTermStore` (`memories` table) |
| Semantic | `ISemanticStore` | `InMemorySemanticStore` (cosine) | `QdrantSemanticStore` (COSINE collection) |
| Embedding | `IEmbeddingService` | `HashingEmbeddingService` | any real model (drop-in) |

Production adapters lazy-import their client libraries, so importing the package never requires
redis/sqlalchemy/qdrant to be installed. `build_memory_manager()` selects backends from
`settings.use_in_memory_backends`; the DI container calls it, so switching to real infra is a
config change, not a code change.

## Memory scopes

`mm.conversation`, `mm.task`, `mm.project`, `mm.knowledge` each bind a fixed scope:
`await mm.conversation.remember(text, owner=...)`. Scopes share the stores but partition recall,
so conversation memory never leaks into knowledge memory (verified by test).

## Capabilities

- **Semantic recall@k** — embed query → filtered cosine search → hydrate structured records,
  ranked by score, scoped + owner-isolated.
- **forget cascade** — removes a memory from both the long-term and semantic stores (GDPR-style
  right-to-be-forgotten).
- **history** — chronological recent records in a scope, independent of semantic search.
- **TTL short-term** — ephemeral key/value with expiry.

## Tests

`backend/tests/unit/test_memory.py` — **11 tests, all passing** (project total now **63**).
Covers deterministic unit-norm embeddings + cosine self-similarity, TTL expiry, recall ranking,
scope+owner isolation, forget cascade, the four scope facades, chronological history, backend
injection via a fake store (proving port-only coupling), and factory backend selection.

Run: `python scripts/run_tests.py` (offline) or `pytest backend/tests/unit`.

## Note on this environment

This sandbox has no Redis/PostgreSQL/Qdrant and no package index, so the production adapters are
implemented and import-safe but exercised structurally rather than against live services. The
in-memory path (identical API) is fully tested end-to-end.

## Next

**Phase 8 — Tool Orchestration:** expand the Tool Registry with real provider adapters
(OpenAI, Anthropic, Gemini, local models, REST, MCP servers, Docker), behind the existing
`ITool`/`IToolRegistry` ports, with rate limiting and provider-key handling.
