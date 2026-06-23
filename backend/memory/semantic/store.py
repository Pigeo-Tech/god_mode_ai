"""Semantic store implementations (the ISemanticStore port).

Phase 7. In-memory vector index (default) and a Qdrant adapter (production). Both embed text via
an injected IEmbeddingService and support filtered top-k search.
"""
from __future__ import annotations

from backend.memory.embedding import HashingEmbeddingService


class InMemorySemanticStore:
    """Default brute-force cosine index; no external dependency."""

    def __init__(self, embeddings) -> None:
        self._emb = embeddings
        self._vectors: dict[str, list[float]] = {}
        self._payload: dict[str, dict] = {}

    def upsert(self, mid: str, text: str, payload: dict) -> None:
        self._vectors[mid] = self._emb.embed(text)
        self._payload[mid] = payload

    def delete(self, mid: str) -> None:
        self._vectors.pop(mid, None)
        self._payload.pop(mid, None)

    def search(self, query: str, k: int, flt: dict) -> list[tuple[str, float]]:
        qv = self._emb.embed(query)
        scored: list[tuple[str, float]] = []
        for mid, vec in self._vectors.items():
            payload = self._payload[mid]
            if any(payload.get(key) != val for key, val in flt.items()):
                continue
            scored.append((mid, HashingEmbeddingService.cosine(qv, vec)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


class QdrantSemanticStore:
    """Production adapter backed by Qdrant (lazy import; sync client)."""

    def __init__(self, url: str, embeddings, collection: str = "semantic_memory",
                 dim: int = 256) -> None:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.http import models as qm  # type: ignore

        self._emb = embeddings
        self._collection = collection
        self._qm = qm
        self._client = QdrantClient(url=url)
        existing = {c.name for c in self._client.get_collections().collections}
        if collection not in existing:
            self._client.create_collection(
                collection_name=collection,
                vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE))

    def upsert(self, mid: str, text: str, payload: dict) -> None:
        point = self._qm.PointStruct(id=mid, vector=self._emb.embed(text),
                                     payload={**payload, "memory_id": mid})
        self._client.upsert(collection_name=self._collection, points=[point])

    def delete(self, mid: str) -> None:
        self._client.delete(collection_name=self._collection,
                            points_selector=self._qm.PointIdsList(points=[mid]))

    def search(self, query: str, k: int, flt: dict) -> list[tuple[str, float]]:
        conditions = [self._qm.FieldCondition(key=key, match=self._qm.MatchValue(value=val))
                      for key, val in flt.items()]
        hits = self._client.search(
            collection_name=self._collection, query_vector=self._emb.embed(query), limit=k,
            query_filter=self._qm.Filter(must=conditions) if conditions else None)
        return [(h.payload.get("memory_id", str(h.id)), h.score) for h in hits]
