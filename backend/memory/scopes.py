"""Memory scope facades.

Phase 7. The architecture calls for distinct memory scopes. Each facade binds a fixed scope so
callers don't repeat it: e.g. ``mm.conversation.remember(text, owner=...)``. All scopes share the
same underlying stores; the scope is just a partition key used for filtering on recall.
"""
from __future__ import annotations


class ScopedMemory:
    scope: str = "generic"

    def __init__(self, manager) -> None:
        self._mm = manager

    async def remember(self, content: str, *, owner: str, kind: str = "note",
                       metadata: dict | None = None) -> str:
        return await self._mm.remember(content, scope=self.scope, owner=owner,
                                       kind=kind, metadata=metadata)

    async def recall(self, query: str, *, owner: str, k: int = 8) -> list[dict]:
        return await self._mm.recall(query, scope=self.scope, owner=owner, k=k)


class ConversationMemory(ScopedMemory):
    scope = "conversation"


class TaskMemory(ScopedMemory):
    scope = "task"


class ProjectMemory(ScopedMemory):
    scope = "project"


class KnowledgeMemory(ScopedMemory):
    scope = "knowledge"
