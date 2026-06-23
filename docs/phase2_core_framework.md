# GOD MODE AI — Phase 2: Core Framework

> **Status:** Phase 2 of 12 complete. The thirteen core services from the Phase 1 architecture
> are implemented as real, working Python against the defined ports. Everything runs and is
> tested with **zero external infrastructure** (in-memory backends); Postgres/Redis/Qdrant slot
> in later behind the same interfaces.

## What was built

| Service | File | Highlights |
|---|---|---|
| **Ports / interfaces** | `core/interfaces.py` | `Protocol` contracts for every service (Hexagonal boundary). |
| **Config** | `config/settings.py` | Typed settings; pydantic-settings with a stdlib fallback. |
| **Logger** | `core/logger/logger.py` | Structured JSON logs + `correlation_id` ContextVar threading. |
| **Metrics** | `core/metrics/metrics.py` | Counters/gauges/histograms, Prometheus exposition, `timer()`. |
| **Event Bus** | `core/event_bus/event_bus.py` | Async pub/sub, consumer groups, retries → dead-letter. |
| **Message Bus** | `core/message_bus/message_bus.py` | Directed request/reply with timeout. |
| **Permission Manager** | `core/permission_manager/permissions.py` | RBAC, deny-by-default, wildcard scopes, audit log. |
| **Tool Registry** | `core/tool_registry/registry.py` | Tool catalogue, arg validation, permission + per-agent allow-list, metrics. |
| **Memory Manager** | `core/memory_manager/memory.py` | Short/long/semantic stores; local embedding + cosine recall; `forget` cascade. |
| **Task Manager** | `core/task_manager/tasks.py` | Task DAG, state machine, dependency ordering, retry/backoff, cycle detection. |
| **Workflow Engine** | `core/workflow_engine/engine.py` | Sequential + conditional + loop steps, resumable state. |
| **Scheduler** | `core/scheduler/scheduler.py` | Date / Interval / Cron triggers, single-fire lock, event firing. |
| **Agent Manager** | `core/agent_manager/manager.py` | Registry + Factory + Supervisor (restart on unhealthy). |
| **Health** | `core/health/health.py` | Aggregates component checks → 200/503. |
| **DI Container** | `core/container.py` | Composition root wiring every service together. |

The API entrypoint (`api/main.py`) now exposes `/health`, `/health/ready` (aggregated), and
`/metrics` (Prometheus) backed by the container.

## Design notes

- **Ports & adapters.** Every service implements a `Protocol` from `interfaces.py`. Swapping an
  in-memory backend for Redis/Postgres/Qdrant means changing only `container.py`.
- **Dependency-free dev.** `settings.py`, `schemas/agent.py` degrade gracefully when
  `pydantic` isn't installed, so the framework runs and tests anywhere. Production installs the
  full stack from `requirements.txt`.
- **No agent coupling.** Agents talk only through the Event Bus (fan-out) and Message Bus
  (request/reply) — never direct references.

## Tests

`backend/tests/unit/test_core.py` — **19 tests, all passing**. Covers metrics rendering, event
bus groups + dead-letter, message bus request/reply, RBAC deny-by-default + wildcards, tool
permission enforcement + arg validation, semantic memory recall + forget, task DAG ordering +
retry-to-dead-letter + invalid-transition + cycle detection, workflow conditional/loop,
scheduler interval + cron, agent ensure/execute + supervise-restart, and full container wiring.

Run with pytest (`pytest backend/tests/unit`) once dependencies are installed, or offline via
`python scripts/run_tests.py` (a stdlib harness with a small `pytest.raises` shim).

## Next

**Phase 3 — Base Agent System:** concrete `BaseAgent` behaviour plus `BaseGeneral` and
`BaseSoldier`, wired to the Message/Event buses, Tool Registry, and Memory Manager built here.
