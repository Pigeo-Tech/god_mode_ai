# GOD MODE AI — Phase 6: Soldier Agents

> **Status:** Phase 6 of 12 complete. All **41 Soldiers** are implemented, each wrapping exactly
> one capability, and every General's roster is now fully live. The whole hierarchy runs
> end-to-end: **King → 10 Generals → 41 Soldiers → tools**, over the in-memory buses, with one
> bootstrap call.

## What was built

| Piece | File | Role |
|---|---|---|
| **Soldier tools** | `soldiers/tools.py` | 40 deterministic mock tools (one per tool-backed soldier) with realistic shapers for weather, stock, crypto, search, translation, commands. Each is a thin adapter — swap a mock for a real API/CLI/LLM without touching callers. |
| **ToolSoldier** | `soldiers/common.py` | Parameterized single-tool worker; most soldiers are instances of it. |
| **MemorySoldier** | `soldiers/common.py` | Example of a soldier served by a core service (Memory Manager) instead of a registry tool — `remember` / `recall`. |
| **Catalogue** | `soldiers/catalog.py` | Declarative list of all 41 soldiers (name, General domain, tool/custom class). Adding a soldier is a one-line entry. |
| **Factory** | `soldiers/factory.py` | Registers each soldier with the Agent Manager (tier-qualified keys `soldier:<name>`). |
| **Soldiers bootstrap** | `soldiers/bootstrap.py` | Registers tools, grants the `soldier` role, locks each soldier to its single tool via a per-agent allow-list, then starts all 41. |
| **System bootstrap** | `bootstrap.py` | `bootstrap_system(container)` → soldiers + generals + King, fully operational. |

## The 41 Soldiers by domain

- **Knowledge** (7): internet, weather, maps, research, search, news, translation
- **Planning** (2): calendar, reminder
- **Execution** (3): terminal, tool, api
- **Memory** (4): memory*, file, ocr, pdf  *(custom, uses the Memory Manager)*
- **Coding** (3): coding, git, docker
- **Media** (8): image, video, music, movie, vision, camera, audio, speech
- **Finance** (4): finance, stock, crypto, shopping
- **Communication** (3): email, whatsapp, notification
- **System** (7): aws, kubernetes, database, security, authentication, monitoring, logging

## One responsibility, enforced two ways

1. **Structurally** — each soldier wraps a single tool (or one custom action).
2. **By policy** — the bootstrap sets a per-agent **allow-list** so, e.g., the `stock` soldier
   may call *only* the `stock` tool. Attempting any other tool raises the platform
   `PermissionError`. This is verified by a test.

## Namespacing fix (cross-tier names)

`memory`, `coding`, and `finance` exist as both a General domain and a Soldier name. The Agent
Manager registry is one namespace, so registration keys are now **tier-qualified**
(`general:memory` vs `soldier:memory`) while each agent keeps its **bare id** for the Message Bus
(`general.memory` vs `soldier.memory`). Routing is unaffected; only internal registry keys
changed.

## Tests

`backend/tests/unit/test_soldiers.py` — **8 tests, all passing** (project total now **52**).
Covers: 41 unique soldiers, every General roster soldier exists, bootstrap starts all 41 live
with 40 tools, shaped weather output over the bus, the memory soldier store→recall, allow-list
single-responsibility enforcement, and two full-system King runs hitting real soldiers
(multi-domain success + knowledge `findings`).

Run: `python scripts/run_tests.py` (offline) or `pytest backend/tests/unit`.

## Milestone

With Phase 6, the **agent hierarchy is feature-complete and operational**: a single
`bootstrap_system(container)` brings up the King, all Generals, and all Soldiers, and a natural
objective flows top-to-bottom and back as one aggregated answer.

## Next

**Phase 7 — Memory System:** promote the in-memory short/long/semantic stores to real backends
(Redis, PostgreSQL, Qdrant) behind the existing `IMemoryManager` port, with the
conversation/task/project/knowledge memory scopes from the architecture.
