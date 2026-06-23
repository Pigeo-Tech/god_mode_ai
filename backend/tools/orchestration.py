"""Tool orchestration bootstrap.

Phase 8. Wires LLM provider tools into a Tool Registry based on which API keys are present (via
the secret provider). The deterministic local provider is always registered so the system has a
working model offline; OpenAI/Anthropic/Gemini are added when their keys are configured.
"""
from __future__ import annotations

from backend.tools.providers.base import (AnthropicProvider, GeminiProvider, LocalProvider,
                                          OpenAIProvider)
from backend.tools.providers.llm_tool import LLMTool
from backend.tools.secrets import EnvSecretProvider

# tool name -> (env key, provider class)
_REMOTE_PROVIDERS = {
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

    return registered
