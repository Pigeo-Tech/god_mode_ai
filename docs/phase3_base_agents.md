# GOD MODE AI — Phase 3: Base Agent System

> **Status:** Phase 3 of 12 complete. The agent layer now sits on top of the Phase 2 Core
> Framework: a working `BaseAgent` runtime plus `BaseSoldier` and `BaseGeneral`, all wired to
> the Message/Event buses, Tool Registry, Memory Manager, and Permission Manager via dependency
> injection. Agents communicate **only** through the buses — no direct references.

## What was built

| Component | File | Role |
|---|---|---|
| **AgentDeps (DI context)** | `core/agent_context.py` | Bundles the core services an agent needs; `deps_from_container()` builds it from the Phase 2 container. Agents never touch globals. |
| **BaseAgent runtime** | `core/base_agent.py` | Template-method `run()` wraps `execute()` with validation gating, latency timing, metrics, structured logging, and uniform error handling. Subclasses implement only `execute()`. |
| **Envelope serde** | `schemas/serde.py` | Converts `AgentRequest`/`AgentResponse` ↔ dicts for bus transport (Pydantic- and dataclass-safe). |
| **BaseSoldier** | `soldiers/base/base_soldier.py` | Single-responsibility worker. Set `tool_name` to wrap one registry tool, or override `work()`. Registers `soldier.<id>` on the Message Bus. |
| **BaseGeneral + routers** | `generals/base.py` | Domain coordinator. `SoldierRouter` strategy (`AllRouter`, `KeywordRouter`) selects soldiers; dispatches over the bus; aggregates replies. Registers `general.<id>`. |

## How a request flows (Phase 3 slice)

```
General.run(request)
  → validate() → execute()
      → router.select(soldiers)              # Strategy
      → message_bus.request("soldier.X", …)  # point-to-point, no direct ref
          → Soldier.run(request)
              → validate() → execute() → tool.invoke()  # via Tool Registry (perm-checked)
          ← AgentResponse (dict)
      → aggregate(results)                   # domain merge
  ← AgentResponse (latency-stamped, COMPLETED/FAILED)
```

Every hop returns the same `AgentResponse` envelope, and `run()` guarantees a failing agent
yields a `FAILED` envelope rather than throwing — so one bad soldier never crashes its general
or the King.

## Design patterns applied

- **Template Method** — `BaseAgent.run()` fixes the lifecycle (validate → execute → measure →
  envelope); subclasses fill in only `execute()`.
- **Strategy** — `SoldierRouter` makes soldier selection swappable (`AllRouter`,
  `KeywordRouter`, and any future learned router).
- **Dependency Injection** — services arrive via `AgentDeps`; agents are unit-testable with
  fakes and have zero coupling to the composition root.
- **Adapter** — `_on_message()` adapts the dict-based bus to the typed agent API.

## Tests

`backend/tests/unit/test_agents.py` — **10 tests, all passing** (total project suite now **29**).
Covers: soldier single-tool execution + latency stamping, validation gating, error→`FAILED`
envelope (no crash), custom `work()` soldiers, general routing + aggregation over the bus,
`KeywordRouter` subset selection, graceful handling of a missing soldier, reaching a general
purely via the Message Bus, and `BaseAgent` health/abstractness.

Run offline: `python scripts/run_tests.py` (or `... agents` to filter). With deps installed:
`pytest backend/tests/unit`.

## Next

**Phase 4 — King Agent:** `KingAgent(BaseAgent)` with `Planner`/`Decomposer`/`Aggregator`,
turning a user objective into a Task DAG (Phase 2 Task Manager), dispatching to Generals over
the bus, monitoring, and synthesising the final answer.
