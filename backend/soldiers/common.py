"""Common soldier implementations.

Phase 6. ToolSoldier is a parameterized single-tool worker (most soldiers are instances of it).
MemorySoldier is an example of a soldier whose responsibility is served by a core service (the
Memory Manager) rather than a registry tool.
"""
from __future__ import annotations

import re
from urllib.parse import quote_plus

from backend.schemas.agent import AgentRequest, AgentResponse
from backend.soldiers.base.base_soldier import BaseSoldier

# Verbs that signal the user wants AGNI to *act* (open/launch something), not just
# answer a question. Matched against whole words so "display" won't trigger "play".
_ACTION_VERBS = {
    "open", "play", "install", "download", "launch", "watch", "listen",
    "stream", "start", "buy", "order", "find", "search", "update", "reinstall",
}
# Filler words stripped from the search term; product/app names are kept.
_STOP = {
    "i", "am", "im", "iam", "getting", "bored", "please", "pls", "the", "a",
    "an", "to", "me", "my", "for", "can", "you", "want", "wanna", "some",
    "this", "that", "and", "in", "on", "of", "now", "could", "would", "new",
    "it", "up", "go", "let", "us", "we", "is", "are", "from", "store",
}


def build_action_link(objective: str) -> tuple[str | None, str | None]:
    """Turn an actionable request into a deep link the phone can open.

    Returns (url, label) or (None, None) when the request is not actionable
    (e.g. a plain question), so ordinary answers stay link-free.
    """
    low = objective.lower()
    words = re.findall(r"[a-z0-9]+", low)
    if not (set(words) & _ACTION_VERBS):
        return None, None
    term = " ".join(w for w in words if w not in _STOP and w not in _ACTION_VERBS).strip()
    q = quote_plus(term) if term else ""

    # Play Store: install/app/game requests.
    if any(k in low for k in ("play store", "playstore", "install", "app store", "apk")) \
            or "app" in words or "game" in words or "games" in words or "apps" in words:
        return f"https://play.google.com/store/search?q={q}&c=apps", "Open in Play Store"
    # YouTube: explicit youtube, or song/music/video/watch.
    if "youtube" in low:
        extra = term.replace("youtube", "").strip()
        return ((f"https://www.youtube.com/results?search_query={quote_plus(extra)}", "Search YouTube")
                if extra else ("https://www.youtube.com", "Open YouTube"))
    if any(k in low for k in ("song", "music", "video", "watch", "listen", "stream")):
        return f"https://www.youtube.com/results?search_query={q}", "Search YouTube"
    # Fallback: a web search for whatever they asked to open/find.
    return f"https://www.google.com/search?q={q}", "Search the web"


class ToolSoldier(BaseSoldier):
    """A soldier that wraps exactly one named tool from the Tool Registry."""

    def __init__(self, agent_id: str, deps=None, *, tool: str | None = None,
                 required: list[str] | None = None) -> None:
        super().__init__(agent_id, deps)
        self.tool_name = tool or agent_id
        self.required_context = list(required or [])


class MemorySoldier(BaseSoldier):
    """Stores or recalls memories via the Memory Manager (no registry tool)."""

    tool_name = None

    async def work(self, request: AgentRequest) -> AgentResponse:
        ctx = request.context or {}
        owner = str(ctx.get("user_id", "anon"))
        if ctx.get("action") == "recall":
            hits = await self.deps.memory.recall(request.objective, scope="knowledge",
                                                 owner=owner, k=5)
            return self._ok(request, {"action": "recall", "recalled": hits})
        memory_id = await self.deps.memory.remember(request.objective, scope="knowledge",
                                                    owner=owner)
        return self._ok(request, {"action": "remember", "stored": memory_id})


class LlmSoldier(BaseSoldier):
    """Answers the objective with an LLM: OpenAI/Anthropic if a key is configured,
    otherwise the built-in local model. Returns {"answer": text}."""

    tool_name = None

    async def work(self, request: AgentRequest) -> AgentResponse:
        tools = self.deps.tools
        available = tools.list() if tools is not None else []
        tool = (
            "llm.openai" if "llm.openai" in available
            else "llm.anthropic" if "llm.anthropic" in available
            else "llm.local"
        )
        result = await tools.invoke(tool, {"prompt": request.objective}, agent_id=self.agent_id)
        answer = result.get("completion", "")

        # Actionable request? Produce a deep link the app can open, and learn the
        # process by saving it to memory so it is recalled instantly next time.
        url, label = build_action_link(request.objective)
        action = None
        if url:
            answer = f"{answer}\n\n{label}: {url}".strip()
            action = {"type": "open_url", "url": url, "label": label}
            owner = str((request.context or {}).get("user_id", "anon"))
            if self.deps.memory is not None:
                try:
                    await self.deps.memory.remember(
                        f"action :: {request.objective} -> {url}",
                        scope="knowledge", owner=owner)
                except Exception:  # pragma: no cover - learning is best-effort
                    pass

        return self._ok(request, {
            "answer": answer,
            "model": result.get("model"),
            "provider": result.get("provider"),
            "action": action,
        })
