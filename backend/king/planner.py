"""Planner / Decomposer — turns an objective into a Task DAG plan.

Phase 4. The Planner is a Strategy: the King depends on the `Planner` interface, so an
LLM-backed planner can drop in later without touching the King. The default `KeywordPlanner` is
deterministic (no model required): it splits the objective into clauses, routes each clause to a
General by keyword, and chains clauses joined by "then" as sequential dependencies — producing a
real DAG with parallel and sequential sections.
"""
from __future__ import annotations

import abc
import re
from dataclasses import dataclass, field


@dataclass
class PlanStep:
    general: str                      # which General owns this subtask
    objective: str                    # the subtask text
    depends_on: list[int] = field(default_factory=list)  # indices of prior steps
    context: dict = field(default_factory=dict)


class Planner(abc.ABC):
    @abc.abstractmethod
    async def plan(self, objective: str, context: list[dict] | None = None) -> list[PlanStep]:
        ...


class KeywordPlanner(Planner):
    """Deterministic decomposition by keyword routing + 'then' sequencing."""

    _SEQ = re.compile(r"\bthen\b", flags=re.IGNORECASE)
    _PAR = re.compile(r"\band\b|;|,", flags=re.IGNORECASE)

    def __init__(self, routes: dict[str, str], default_general: str) -> None:
        # keyword -> general name
        self._routes = {k.lower(): v for k, v in routes.items()}
        self._default = default_general

    def _route(self, clause: str) -> str:
        low = clause.lower()
        for keyword, general in self._routes.items():
            if keyword in low:
                return general
        return self._default

    async def plan(self, objective: str, context: list[dict] | None = None) -> list[PlanStep]:
        steps: list[PlanStep] = []
        prev_group: list[int] = []
        # sequential groups separated by "then"
        for group_text in self._SEQ.split(objective):
            group_text = group_text.strip()
            if not group_text:
                continue
            current_group: list[int] = []
            # parallel clauses within a group
            clauses = [c.strip() for c in self._PAR.split(group_text) if c.strip()]
            for clause in clauses or [group_text]:
                idx = len(steps)
                steps.append(PlanStep(general=self._route(clause), objective=clause,
                                      depends_on=list(prev_group)))
                current_group.append(idx)
            prev_group = current_group
        if not steps:  # nothing parsed -> single default step
            steps.append(PlanStep(general=self._default, objective=objective))
        return steps
