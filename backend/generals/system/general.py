"""System General — Infrastructure and cloud operations. (generated from the AGNI spec)."""
from __future__ import annotations

from backend.generals.base import BaseGeneral, KeywordRouter
from backend.generals._spec import GENERAL_SPECS

_S = GENERAL_SPECS["system"]


class SystemGeneral(BaseGeneral):
    domain = "system"
    soldiers = list(_S["soldiers"])
    router = KeywordRouter(_S["keywords"])
