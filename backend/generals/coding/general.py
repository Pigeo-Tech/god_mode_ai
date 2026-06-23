"""Coding General — Software engineering and development. (generated from the AGNI spec)."""
from __future__ import annotations

from backend.generals.base import BaseGeneral, KeywordRouter
from backend.generals._spec import GENERAL_SPECS

_S = GENERAL_SPECS["coding"]


class CodingGeneral(BaseGeneral):
    domain = "coding"
    soldiers = list(_S["soldiers"])
    router = KeywordRouter(_S["keywords"])
