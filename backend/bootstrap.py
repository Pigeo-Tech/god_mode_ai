"""System bootstrap — bring the whole hierarchy online from a DI container.

Phase 6 (+ Phase 8). One call wires soldiers (tools + permissions), provider tools (LLM), then
Generals, then the King — leaving a fully operational platform: King → 10 Generals → 41 Soldiers
→ tools, all over the buses. Used by the API layer (Phase 9) and the test/integration harness.
"""
from __future__ import annotations

from backend.generals.bootstrap import bootstrap_generals
from backend.king.king import KingAgent
from backend.soldiers.bootstrap import bootstrap_soldiers
from backend.tools.orchestration import register_provider_tools


async def bootstrap_system(container):
    """Returns (deps, king) with all agents registered and live."""
    deps, soldier_names = await bootstrap_soldiers(container)

    # LLM provider tools (local always; OpenAI/Anthropic/Gemini when keys are present).
    llm_tools = register_provider_tools(container.tools, settings=container.settings)

    _, general_names = await bootstrap_generals(container)

    king = KingAgent("king", deps)
    await king.initialize()

    container.logger.info("system.bootstrapped", soldiers=len(soldier_names),
                          generals=len(general_names), llm_tools=len(llm_tools))
    return deps, king
