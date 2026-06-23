# GOD MODE AI — Phase 8: Tool Orchestration

> **Status:** Phase 8 of 12 complete. The Tool Registry now fronts a full set of provider
> adapters — LLMs (OpenAI/Anthropic/Gemini/local), REST, MCP, Docker, and Python — behind the
> `ITool`/`IToolRegistry` ports, with a `ToolFactory`, secret/key handling, and per-tool rate
> limiting. Everything runs offline via a deterministic local LLM provider.

## What was built

| Piece | File | Role |
|---|---|---|
| **LLM providers** | `tools/providers/base.py` | `LLMProvider` Strategy + `LocalProvider` (offline, deterministic) and `OpenAIProvider`/`AnthropicProvider`/`GeminiProvider` (lazy-import SDKs). |
| **LLMTool** | `tools/providers/llm_tool.py` | Wraps a provider as a registry tool so any soldier can call a model through the standard path. |
| **RestApiTool** | `tools/rest_tool.py` | Calls external REST APIs (httpx in prod; injectable transport for tests). |
| **McpTool** | `tools/mcp/adapter.py` | Adapts an MCP server's tool into the local registry (injectable caller). |
| **DockerTool** | `tools/docker_tool.py` | Runs a command in a container (docker SDK; injectable runner). Isolation for untrusted/heavy tools. |
| **ToolFactory** | `tools/factory.py` | Builds tools by kind (`llm`/`rest`/`mcp`/`docker`/`python`) — Factory pattern. |
| **Secrets** | `tools/secrets.py` | `EnvSecretProvider` (env/settings) + `AwsSecretsManagerProvider` (prod). Keys fetched at build time, never stored in specs. |
| **Rate limiter** | `tools/rate_limit.py` | `TokenBucketRateLimiter` (per-tool buckets) → registry raises `RateLimitExceeded`. |
| **Orchestration** | `tools/orchestration.py` | `register_provider_tools()` — registers `llm.local` always; OpenAI/Anthropic/Gemini when keys are present. |

## Registry enhancements

The Tool Registry gained an optional `rate_limiter` (checked on every `invoke` after
permission + allow-list) and `list_by_kind()`. The invocation path is now:

```
invoke(name, args, agent_id)
  → validate args
  → allow-list check        (per-agent single-responsibility)
  → permission check        (tool:<name> scope)
  → rate-limit check        (token bucket)  ← new
  → tool.invoke(args)       (adapter: llm / rest / mcp / docker / python)
  → record latency + count
```

## Provider selection & keys

`register_provider_tools()` consults the secret provider: the offline `llm.local` tool is always
available, and each remote provider (`llm.openai`, `llm.anthropic`, `llm.gemini`) is registered
only when its API key is configured. `bootstrap_system()` now calls this, so the running platform
always has at least a local model, and the container exposes a `ToolFactory`.

## Tests

`backend/tests/unit/test_tools.py` — **10 tests, all passing** (project total now **73**).
Covers: local LLM completion, LLM via registry with permissions, provider registration
(offline → local only; key present → remote registered), REST tool with a fake transport, MCP
tool with an injected caller, rate-limit enforcement after capacity, the ToolFactory by kind +
unknown-kind error, and `list_by_kind`.

Run: `python scripts/run_tests.py` (offline) or `pytest backend/tests/unit`.

## Note on this environment

No package index or network here, so the OpenAI/Anthropic/Gemini/httpx/docker/boto3 SDKs aren't
installed — those adapters are implemented and import-safe (lazy imports) and are exercised
through injected fakes / the local provider. With keys + libraries present they call the real
services unchanged.

## Next

**Phase 9 — API Layer:** FastAPI REST + WebSocket access to the King, streaming responses,
JWT/OAuth2 auth, rate limiting, versioning, and OpenAPI — wiring the operational system from
`bootstrap_system()` to external clients.
