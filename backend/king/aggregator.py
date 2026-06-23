"""Aggregator — merges General results into the King's final answer.

Phase 4. The King performs no domain work; the Aggregator is where partial results from the
Generals are combined into a single coherent response, including a human-readable summary and a
structured per-step breakdown for traceability.
"""
from __future__ import annotations

from backend.king.planner import PlanStep
from backend.schemas.agent import TaskStatus


class Aggregator:
    def merge(self, objective: str, steps: list[PlanStep], tasks: dict) -> dict:
        """Combine the completed task graph into a final answer payload.

        `tasks` is the {task_id: Task} map returned by the Task Manager.
        """
        ordered = list(tasks.values())
        breakdown = []
        completed = failed = 0
        for task in ordered:
            ok = task.status == TaskStatus.COMPLETED
            completed += ok
            failed += not ok
            breakdown.append({
                "general": task.owner_agent,
                "objective": task.objective,
                "status": task.status.value,
                "attempts": task.attempts,
                "result": task.result if ok else None,
                "error": task.error,
            })

        summary = self._summarize(objective, breakdown, completed, failed)
        return {
            "objective": objective,
            "summary": summary,
            "steps_total": len(ordered),
            "steps_completed": completed,
            "steps_failed": failed,
            "breakdown": breakdown,
        }

    @staticmethod
    def _summarize(objective: str, breakdown: list[dict], completed: int, failed: int) -> str:
        parts = [f"Objective: {objective}.",
                 f"{completed}/{completed + failed} subtasks completed."]
        if failed:
            failing = ", ".join(b["general"] for b in breakdown if b["status"] != "completed")
            parts.append(f"Failed via: {failing}.")
        return " ".join(parts)
