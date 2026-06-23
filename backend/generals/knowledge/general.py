"""Knowledge General — research & world info, with LLM-backed answers."""
from __future__ import annotations

from backend.generals.base import BaseGeneral, KeywordRouter
from backend.generals._spec import GENERAL_SPECS

_S = GENERAL_SPECS["knowledge"]


class _KnowledgeRouter(KeywordRouter):
    """When no keyword matches, answer with a single research soldier (one good LLM reply)
    instead of fanning out to the whole roster."""

    def select(self, request, soldiers):
        chosen = super().select(request, soldiers)
        if set(chosen) == set(soldiers) and "research" in soldiers:
            return ["research"]
        return chosen


class KnowledgeGeneral(BaseGeneral):
    domain = "knowledge"
    soldiers = list(_S["soldiers"])
    router = _KnowledgeRouter(_S["keywords"])

    def aggregate(self, request, results):
        base = super().aggregate(request, results)
        completed = [r["result"] for r in results if r.get("status") == "completed"]
        base["findings"] = completed
        answer = None
        for r in completed:
            if isinstance(r, dict) and r.get("answer"):
                answer = r["answer"]
                break
            if isinstance(r, str):
                answer = r
                break
        if answer:
            base["answer"] = answer
        return base
