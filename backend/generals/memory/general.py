"""Memory General — Store, retrieve, and manage memory. (generated from the AGNI spec)."""
from __future__ import annotations

from backend.generals.base import BaseGeneral, KeywordRouter
from backend.generals._spec import GENERAL_SPECS

_S = GENERAL_SPECS["memory"]


class MemoryGeneral(BaseGeneral):
    domain = "memory"
    soldiers = list(_S["soldiers"])
    router = KeywordRouter(_S["keywords"])
