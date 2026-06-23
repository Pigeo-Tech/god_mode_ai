"""LLM provider adapters (Strategy pattern).

Phase 8. A uniform `LLMProvider.complete()` interface over multiple model backends. The
`LocalProvider` is deterministic and offline (used in dev/tests); the OpenAI/Anthropic/Gemini
providers lazy-import their SDKs and are used when API keys are configured. Swapping providers is
a config change — callers (LLMTool) depend only on this interface.
"""
from __future__ import annotations

import abc


class LLMProvider(abc.ABC):
    name: str

    @abc.abstractmethod
    async def complete(self, prompt: str, **options) -> str: ...


class LocalProvider(LLMProvider):
    """Deterministic offline provider — no network, no keys."""

    name = "local"

    def __init__(self, model: str = "local-stub") -> None:
        self.model = model

    async def complete(self, prompt: str, **options) -> str:
        return f"[{self.model}] response to: {prompt.strip()[:300]}"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self.model = model

    async def complete(self, prompt: str, **options) -> str:
        from openai import AsyncOpenAI  # type: ignore  # lazy

        client = AsyncOpenAI(api_key=self._api_key)
        resp = await client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}], **options)
        return resp.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._api_key = api_key
        self.model = model

    async def complete(self, prompt: str, **options) -> str:
        import anthropic  # type: ignore  # lazy

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        msg = await client.messages.create(
            model=self.model, max_tokens=options.pop("max_tokens", 1024),
            messages=[{"role": "user", "content": prompt}], **options)
        return "".join(block.text for block in msg.content if block.type == "text")


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self._api_key = api_key
        self.model = model

    async def complete(self, prompt: str, **options) -> str:
        import google.generativeai as genai  # type: ignore  # lazy

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self.model)
        resp = await model.generate_content_async(prompt)
        return resp.text
