"""Embedding service.

Phase 7. `HashingEmbeddingService` is a deterministic, dependency-free embedding (token hashing
into a fixed vector) so semantic recall works offline. Swap it for a real model (OpenAI,
sentence-transformers, etc.) by providing any object implementing `IEmbeddingService` — the
SemanticStore and MemoryManager depend only on the port.
"""
from __future__ import annotations

import math
import re

_TOKEN = re.compile(r"[a-z0-9]+")
_DIM = 256


class HashingEmbeddingService:
    """Implements IEmbeddingService."""

    def __init__(self, dim: int = _DIM) -> None:
        self._dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for tok in _TOKEN.findall(text.lower()):
            vec[hash(tok) % self._dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def cosine(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))


# Back-compat alias (Phase 2 name).
EmbeddingService = HashingEmbeddingService
