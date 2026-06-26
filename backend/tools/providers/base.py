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


class NvidiaProvider(LLMProvider):
    """NVIDIA NIM — OpenAI-compatible endpoint (integrate.api.nvidia.com). Free tier, nvapi- keys.

    Reuses the OpenAI SDK with a custom base_url, so it's a true drop-in for OpenAI. Default model
    is a strong free one; override with the NVIDIA_MODEL env var.
    """

    name = "nvidia"

    def __init__(self, api_key: str, model: str | None = None,
                 base_url: str = "https://integrate.api.nvidia.com/v1") -> None:
        import os
        self._api_key = api_key
        self.model = model or os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
        self._base_url = base_url

    async def complete(self, prompt: str, **options) -> str:
        from openai import AsyncOpenAI  # type: ignore  # lazy (OpenAI SDK, NVIDIA endpoint)

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
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
