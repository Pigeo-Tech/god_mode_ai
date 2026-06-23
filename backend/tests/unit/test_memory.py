"""Tests for the Phase 7 Memory System."""
from __future__ import annotations

from backend.core.memory_manager.memory import MemoryManager
from backend.memory.embedding import HashingEmbeddingService
from backend.memory.factory import build_memory_manager
from backend.memory.long_term.store import InMemoryLongTermStore
from backend.memory.record import MemoryRecord
from backend.memory.scopes import ConversationMemory, KnowledgeMemory
from backend.memory.semantic.store import InMemorySemanticStore
from backend.memory.short_term.store import InMemoryShortTermStore


# --------------------------------------------------------------------------- embedding
def test_embedding_is_deterministic_and_normalised():
    emb = HashingEmbeddingService()
    v1 = emb.embed("hello world")
    v2 = emb.embed("hello world")
    assert v1 == v2
    assert abs(sum(x * x for x in v1) - 1.0) < 1e-6  # unit length


def test_cosine_self_similarity():
    emb = HashingEmbeddingService()
    v = emb.embed("quantum entanglement")
    assert abs(HashingEmbeddingService.cosine(v, v) - 1.0) < 1e-6


# --------------------------------------------------------------------------- short term
def test_short_term_ttl_expiry():
    store = InMemoryShortTermStore()
    store.set("k", {"v": 1}, ttl=1000)
    assert store.get("k") == {"v": 1}
    store.set("gone", "x", ttl=-1)  # already expired
    assert store.get("gone") is None


# --------------------------------------------------------------------------- recall@k
async def test_recall_ranks_relevant_first():
    mm = MemoryManager()
    await mm.remember("the capital of France is Paris", scope="kb", owner="u")
    await mm.remember("bananas are a good source of potassium", scope="kb", owner="u")
    await mm.remember("the Eiffel Tower is in Paris France", scope="kb", owner="u")
    hits = await mm.recall("France capital city", scope="kb", owner="u", k=2)
    assert len(hits) == 2
    assert "Paris" in hits[0]["content"]  # most relevant first
    assert hits[0]["score"] >= hits[1]["score"]


async def test_recall_is_scoped_and_owned():
    mm = MemoryManager()
    await mm.remember("secret note", scope="kb", owner="alice")
    await mm.remember("secret note", scope="kb", owner="bob")
    hits = await mm.recall("secret", scope="kb", owner="alice", k=10)
    assert len(hits) == 1  # only alice's


async def test_forget_cascades_long_and_semantic():
    mm = MemoryManager()
    mid = await mm.remember("temporary fact", scope="kb", owner="u")
    assert mm.long_term.get(mid) is not None
    await mm.forget(mid)
    assert mm.long_term.get(mid) is None
    hits = await mm.recall("temporary fact", scope="kb", owner="u")
    assert all(h["id"] != mid for h in hits)


# --------------------------------------------------------------------------- scopes
async def test_scope_facades_partition_memory():
    mm = MemoryManager()
    await mm.conversation.remember("we discussed launch dates", owner="u")
    await mm.knowledge.remember("launch dates are confidential", owner="u")
    conv = await mm.conversation.recall("launch", owner="u", k=10)
    know = await mm.knowledge.recall("launch", owner="u", k=10)
    assert len(conv) == 1 and len(know) == 1
    assert "discussed" in conv[0]["content"]
    assert "confidential" in know[0]["content"]


def test_scope_classes_have_distinct_scopes():
    assert ConversationMemory.scope == "conversation"
    assert KnowledgeMemory.scope == "knowledge"


async def test_history_is_chronological():
    mm = MemoryManager()
    await mm.remember("first", scope="task", owner="u")
    await mm.remember("second", scope="task", owner="u")
    hist = mm.history("task", "u")
    assert [r.content for r in hist] == ["second", "first"]  # newest first


# --------------------------------------------------------------------------- DI / factory
async def test_backend_injection_with_fakes():
    """A drop-in fake store proves the manager depends only on the ports."""
    calls: list[str] = []

    class CountingLong(InMemoryLongTermStore):
        def insert(self, rec: MemoryRecord) -> None:
            calls.append("insert")
            super().insert(rec)

    mm = MemoryManager(long_term=CountingLong())
    await mm.remember("x", scope="s", owner="o")
    assert calls == ["insert"]


def test_factory_uses_in_memory_by_default():
    class S:
        use_in_memory_backends = True

    mm = build_memory_manager(S())
    assert isinstance(mm.long_term, InMemoryLongTermStore)
    assert isinstance(mm.semantic, InMemorySemanticStore)
    assert isinstance(mm.short_term, InMemoryShortTermStore)
