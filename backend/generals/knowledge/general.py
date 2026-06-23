"""Knowledge General — Acquire and organize knowledge. (generated from the AGNI spec)."""
from __future__ import annotations

from backend.generals.base import BaseGeneral, KeywordRouter
from backend.generals._spec import GENERAL_SPECS

_S = GENERAL_SPECS["knowledge"]


class KnowledgeGeneral(BaseGeneral):
    domain = "knowledge"
    soldiers = list(_S["soldiers"])
    router = KeywordRouter(_S["keywords"])

    def aggregate(self, request, results):
        base = super().aggregate(request, results)
        base["findings"] = [r["result"] for r in results if r.get("status") == "completed"]
        return base
