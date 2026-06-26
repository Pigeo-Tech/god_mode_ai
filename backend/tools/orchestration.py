"""Tool orchestration bootstrap.

Phase 8. Wires LLM provider tools into a Tool Registry based on which API keys are present (via
the secret provider). The deterministic local provider is always registered so the system has a
working model offline; OpenAI/Anthropic/Gemini are added when their keys are configured.
"""
from __future__ import annotations

from backend.tools.providers.base import (AnthropicProvider, GeminiProvider, LocalProvider,
                                          NvidiaProvider, OpenAIProvider)
from backend.tools.providers.llm_tool import LLMTool
from backend.tools.providers.skills_api import skills_api_from_env
from backend.tools.providers.web_search import TavilyProvider, WebSearchTool
from backend.tools.secrets import EnvSecretProvider

# tool name -> (env key, provider class)
_REMOTE_PROVIDERS = {
    "llm.nvidia": ("NVIDIA_API_KEY", NvidiaProvider),
    "llm.openai": ("OPENAI_API_KEY", OpenAIProvider),
    "llm.anthropic": ("ANTHROPIC_API_KEY", AnthropicProvider),
    "llm.gemini": ("GOOGLE_API_KEY", GeminiProvider),
}


def register_provider_tools(registry, secrets=None, settings=None) -> list[str]:
    """Register LLM tools. Returns the registered tool names."""
    secrets = secrets or EnvSecretProvider(settings)
    registered: list[str] = []

    # Always-available offline provider.
    registry.register(LLMTool("llm.local", LocalProvider()))
    registered.append("llm.local")

    for tool_name, (env_key, provider_cls) in _REMOTE_PROVIDERS.items():
        api_key = secrets.get(env_key)
        if api_key:
            registry.register(LLMTool(tool_name, provider_cls(api_key)))
            registered.append(tool_name)

    # Live web search (Tavily) — grounds answers in current, sourced results.
    tavily_key = secrets.get("TAVILY_API_KEY")
    if tavily_key:
        registry.register(WebSearchTool("web.search", TavilyProvider(tavily_key)))
        registered.append("web.search")

    # External Skills API (Option 2) — soldiers call your skill service during a task.
    skills_tool = skills_api_from_env(secrets)
    if skills_tool is not None:
        registry.register(skills_tool)
        registered.append("skills.invoke")

    return registered
