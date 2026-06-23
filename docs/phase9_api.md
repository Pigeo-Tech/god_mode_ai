# GOD MODE AI — Phase 9: API Layer

> **Status:** Phase 9 of 12 complete. External clients can now reach the platform: a FastAPI app
> exposes REST + WebSocket access to the King, with JWT/OAuth2-style auth, streaming responses,
> per-client rate limiting, correlation-id tracing, versioned routes, and OpenAPI. All request
> logic lives in framework-agnostic services that are fully unit-tested without a web server.

## Two layers

**1. Framework-agnostic (fully tested offline)**

| Component | File | Role |
|---|---|---|
| `JwtService` | `security/jwt_service.py` | HS256 JWT on the stdlib (issue/verify/exp) — no external dep. |
| `PasswordHasher` | `security/passwords.py` | PBKDF2-HMAC-SHA256, salted, constant-time verify. |
| `AuthService` | `security/auth_service.py` | register / authenticate / refresh / verify; RBAC scopes via the Permission Manager. |
| `ApiService` | `api/service.py` | Owns the bootstrapped system; `chat()`, `stream_chat()`, request store, agent/tool listings, health, metrics. The seam between transport and the agent platform. |

**2. FastAPI transport (real code; runs where FastAPI is installed)**

| Component | File |
|---|---|
| App factory + lifespan bootstrap | `api/main.py` |
| Auth dependency + scope guard | `api/deps.py` |
| Routes: auth / chat / agents+tools / system | `api/v1/routes/*.py` |
| WebSocket stream | `api/v1/websockets/stream.py` |
| Middleware: correlation id, rate limit | `api/middleware/*.py` |

## Endpoints

```
POST /v1/auth/register        create a user
POST /v1/auth/login           -> access + refresh tokens
POST /v1/auth/refresh         -> new access token
POST /v1/chat                 submit an objective (optional SSE stream)   [auth]
GET  /v1/requests/{id}        look up a completed request                 [auth]
GET  /v1/agents               live agent roster                          [auth]
GET  /v1/tools                tools by kind                              [auth]
WS   /v1/stream               live King progress events                  [auth]
GET  /health  /health/ready  /metrics    probes & Prometheus
GET  /docs                    OpenAPI (FastAPI built-in)
```

## Request path

```
POST /v1/chat (Bearer JWT)
  → RateLimitMiddleware (token bucket per client)
  → CorrelationIdMiddleware (x-correlation-id threaded into logs)
  → get_principal (verify JWT → Principal{id, scopes})
  → ApiService.chat(objective, user_id)
       → KingAgent.run(...)  → Generals → Soldiers → tools
  → AgentResponse envelope (JSON)  | or SSE stream of accepted/progress/result/done
```

The same `ApiService.stream_chat()` async generator feeds both the SSE response and the
WebSocket endpoint.

## Security

JWT bearer auth, RBAC scope guard (`require_scope`) with wildcard support, refresh tokens that
can't be used as access tokens, PBKDF2 password hashing, per-client rate limiting (429 on
exceed), and correlation ids on every response. Secrets come from settings/env (Phase 8 secret
provider).

## Tests

- `backend/tests/unit/test_security.py` — **9 tests**: JWT roundtrip/expiry/tamper/wrong-secret,
  password hash+verify (salted), register→login→access, duplicate/bad-credential rejection,
  refresh issues access while a refresh token is rejected as access.
- `backend/tests/unit/test_api.py` — **4 tests**: `chat()` + request store, streaming lifecycle
  events, agent roster (51 live = 41 soldiers + 10 generals) + tool listing incl. `llm.local`,
  health 200.

**Project total now 86, all passing.** The FastAPI wiring is syntax-verified (`py_compile`); it
runs once FastAPI/uvicorn are installed (not available in this sandbox), while the entire request
path it delegates to is exercised here through `ApiService`.

## Next

**Phase 10 — Flutter app:** the mobile client (Android + iOS, Material 3, Riverpod) talking to
this API over REST + WebSockets, with auth, streaming chat, push notifications, and offline
storage.
