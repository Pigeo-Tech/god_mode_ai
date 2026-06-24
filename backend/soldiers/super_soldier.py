"""SuperSoldier — an autonomous expert soldier.

Upgrades a plain single-tool worker into a reasoning agent that runs a pipeline:

    understand -> plan -> recall -> reason -> validate -> recover -> learn -> metrics

The "super" is built ONCE here and shared by every soldier; each soldier only supplies a small
``ExpertiseProfile`` (domain system prompt + preferred models + validation rules). This keeps all
145 soldiers cheap to specialise and consistent in behaviour.

Cost control: the default path makes exactly ONE model call (the reason stage). Validation is a
fast heuristic (no extra call). Recovery fires at most one extra call, and only when confidence is
below the profile threshold — so ordinary requests cost the same as before.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from backend.schemas.agent import AgentRequest, AgentResponse
from backend.soldiers.base.base_soldier import BaseSoldier
from backend.soldiers.common import build_action_link


@dataclass
class ExpertiseProfile:
    """Per-soldier specialisation. The only thing a concrete soldier must supply."""

    domain: str
    system_prompt: str
    preferred_models: tuple = ("llm.openai", "llm.anthropic", "llm.local")
    min_chars: int = 12
    enable_recovery: bool = True
    recovery_threshold: float = 0.5


class SuperSoldier(BaseSoldier):
    """Base for expert soldiers. Subclasses set ``profile``; ``work`` runs the pipeline."""

    tool_name = None
    profile: ExpertiseProfile = ExpertiseProfile(
        domain="general",
        system_prompt="You are a precise, helpful expert. Answer clearly and completely.",
    )

    #: concise voice used when the request is actionable (open/play/install) — the user wants
    #: the action to happen, not an essay.
    ACTION_PROMPT = (
        "You are a friendly assistant. The user wants you to open/play/launch something and the "
        "app will perform it automatically. Reply in ONE short, upbeat sentence confirming it — "
        "no steps, no lists, no explanations.")

    def __init__(self, agent_id, deps=None, profile: ExpertiseProfile | None = None) -> None:
        super().__init__(agent_id, deps)
        if profile is not None:
            self.profile = profile

    async def work(self, request: AgentRequest) -> AgentResponse:
        t0 = perf_counter()
        intent = self._understand(request)
        plan = self._plan(intent)
        recalled = await self._recall(request)

        # Actionable request? Answer concisely (one line) and let the app auto-open the action.
        url, label = build_action_link(request.objective)
        override = self.ACTION_PROMPT if url else ""

        raw = await self._reason(request, recalled, system_override=override)
        verdict = self._validate(raw)

        recovered = False
        if not verdict["ok"] and self.profile.enable_recovery and not url:
            retry = await self._recover(request, recalled)
            v2 = self._validate(retry)
            if v2["confidence"] >= verdict["confidence"]:
                raw, verdict, recovered = retry, v2, True

        answer = (raw.get("completion") or "").strip()
        action = None
        if url:
            action = {"type": "open_url", "url": url, "label": label}

        await self._learn(request, verdict, recovered)
        self._metric(verdict, recovered, perf_counter() - t0)

        return self._ok(request, {
            "answer": answer,
            "findings": answer,
            "model": raw.get("model"),
            "provider": raw.get("provider"),
            "action": action,
            "confidence": round(verdict["confidence"], 2),
            "domain": self.profile.domain,
            "plan": plan,
            "stages": {
                "recalled": len(recalled),
                "recovered": recovered,
                "validated": verdict["ok"],
            },
        })

    # ----------------------------------------------------------------- pipeline stages
    def _understand(self, request: AgentRequest) -> dict:
        url, _ = build_action_link(request.objective)
        text = request.objective or ""
        return {"actionable": url is not None, "complexity": min(len(text) // 40, 3)}

    def _plan(self, intent: dict) -> list[str]:
        steps = ["recall", "reason", "validate"]
        if intent["actionable"]:
            steps.append("deep_link")
        steps += ["learn", "metrics"]
        return steps

    async def _recall(self, request: AgentRequest) -> list:
        if self.deps.memory is None:
            return []
        owner = str((request.context or {}).get("user_id", "anon"))
        try:
            return await self.deps.memory.recall(
                request.objective, scope="knowledge", owner=owner, k=3)
        except Exception:  # pragma: no cover - recall is best-effort
            return []

    def _pick_model(self) -> str:
        available = self.deps.tools.list() if self.deps.tools is not None else []
        for model in self.profile.preferred_models:
            if model in available:
                return model
        return "llm.local"

    def _compose_prompt(self, request: AgentRequest, recalled: list, emphasis: str = "",
                        system_override: str = "") -> str:
        system = system_override or self.profile.system_prompt
        notes = ("\n".join("- " + str(h.get("content", "")) for h in recalled[:3])
                 if recalled else "(none)")
        return (
            f"{system}\n\n"
            f"Relevant past notes:\n{notes}\n\n"
            f"User request: {request.objective}\n{emphasis}"
        ).strip()

    async def _reason(self, request: AgentRequest, recalled: list, emphasis: str = "",
                      system_override: str = "") -> dict:
        tool = self._pick_model()
        prompt = self._compose_prompt(request, recalled, emphasis, system_override)
        return await self.deps.tools.invoke(tool, {"prompt": prompt}, agent_id=self.agent_id)

    def _validate(self, raw: dict) -> dict:
        text = (raw.get("completion") or "").strip()
        if not text:
            confidence = 0.1
        elif len(text) < self.profile.min_chars:
            confidence = 0.3
        else:
            confidence = 1.0
        return {"ok": confidence >= self.profile.recovery_threshold,
                "confidence": confidence, "len": len(text)}

    async def _recover(self, request: AgentRequest, recalled: list) -> dict:
        return await self._reason(
            request, recalled,
            emphasis="Your previous attempt was weak. Be thorough, specific, and complete.")

    async def _learn(self, request: AgentRequest, verdict: dict, recovered: bool) -> None:
        if self.deps.memory is None:
            return
        owner = str((request.context or {}).get("user_id", "anon"))
        tag = "ok" if verdict["ok"] else "weak"
        suffix = " (recovered)" if recovered else ""
        try:
            await self.deps.memory.remember(
                f"{self.profile.domain} [{tag}] :: {request.objective[:120]}{suffix}",
                scope="knowledge", owner=owner)
        except Exception:  # pragma: no cover - learning is best-effort
            pass

    def _metric(self, verdict: dict, recovered: bool, elapsed: float) -> None:
        metrics = self.deps.metrics
        if metrics is None:
            return
        try:
            metrics.observe("soldier_confidence", verdict["confidence"], domain=self.profile.domain)
            metrics.counter("soldier_pipeline", domain=self.profile.domain,
                            status="ok" if verdict["ok"] else "weak",
                            recovered=str(recovered).lower())
        except Exception:  # pragma: no cover
            pass


# --------------------------------------------------------------------------- reference soldier
class ResearchSoldier(SuperSoldier):
    """Reference implementation: an autonomous research expert."""

    profile = ExpertiseProfile(
        domain="research",
        system_prompt=(
            "You are an elite research expert. Give an accurate, well-structured, "
            "multi-perspective answer. Surface the key facts, note any uncertainty or "
            "contradictions, and finish with a one-line confidence note."),
        min_chars=20,
    )


# --------------------------------------------------------------------------- domain experts
# One ExpertiseProfile per General's domain. Every soldier in a domain inherits its profile,
# turning all 145 soldiers into specialised experts that share the single pipeline above.
DOMAIN_PROFILES: dict[str, ExpertiseProfile] = {
    "knowledge": ExpertiseProfile("knowledge",
        "You are a research and world-knowledge expert. Give accurate, well-structured answers "
        "with key facts and a brief confidence note."),
    "planning": ExpertiseProfile("planning",
        "You are a planning strategist. Break the goal into clear, ordered, actionable steps "
        "with dependencies and a realistic schedule."),
    "execution": ExpertiseProfile("execution",
        "You are an execution and tooling expert. Explain precisely how to run the task and "
        "what tools/commands achieve it, safely and reliably."),
    "memory": ExpertiseProfile("memory",
        "You are a memory and context expert. Recall, organise, and summarise relevant "
        "information clearly and concisely."),
    "coding": ExpertiseProfile("coding",
        "You are a senior software engineer. Produce correct, secure, well-documented code or "
        "precise debugging guidance, with brief reasoning."),
    "media": ExpertiseProfile("media",
        "You are a media expert (image, video, audio, music). Give practical, creative, and "
        "concise guidance or recommendations."),
    "finance": ExpertiseProfile("finance",
        "You are a finance analyst. Give clear, careful, numerate answers. Note that this is "
        "information, not licensed financial advice."),
    "communication": ExpertiseProfile("communication",
        "You are a communication expert. Draft or analyse messages with the right tone, clarity, "
        "and brevity for the audience."),
    "system": ExpertiseProfile("system",
        "You are a cloud and systems/DevOps expert. Give precise, safe, production-minded "
        "guidance on infrastructure and operations."),
    "automation": ExpertiseProfile("automation",
        "You are a workflow-automation expert. Design reliable, event-driven, self-healing "
        "automations with clear triggers and steps."),
    "device": ExpertiseProfile("device",
        "You are a mobile-device and app expert. Give short, practical guidance on device and "
        "app actions."),
    "security": ExpertiseProfile("security",
        "You are a security expert. Identify risks, give safe, responsible, defensive guidance, "
        "and never assist wrongdoing."),
    "iot": ExpertiseProfile("iot",
        "You are a smart-home and IoT expert. Give clear, safe guidance on devices, scenes, and "
        "automation."),
    "asi": ExpertiseProfile("asi",
        "You are an optimisation and reasoning expert. Analyse trade-offs and recommend the most "
        "efficient, well-reasoned option."),
    "voice": ExpertiseProfile("voice",
        "You are a voice and natural-language expert. Respond conversationally, clearly, and "
        "concisely."),
}

_DEFAULT_PROFILE = ExpertiseProfile("general",
    "You are a precise, helpful expert. Answer clearly and completely.")


def profile_for(group: str) -> ExpertiseProfile:
    """Return the expertise profile for a soldier's domain group."""
    return DOMAIN_PROFILES.get(group, _DEFAULT_PROFILE)
