# GOD MODE AI — Phase 5: General Agents

> **Status:** Phase 5 of 12 complete. All ten domain Generals are implemented, registered with
> the Agent Manager, and reachable by the King over the Message Bus. Each General routes a
> subtask to the right Soldiers in its domain and aggregates their results. (Soldier
> implementations land in Phase 6; the Generals already declare and command their rosters.)

## The ten Generals

| General | Domain | Soldier roster |
|---|---|---|
| **Knowledge** | research & world info | internet, weather, maps, research, search, news, translation |
| **Planning** | calendars & reminders | calendar, reminder |
| **Execution** | commands, tools, APIs | terminal, tool, api |
| **Memory** | recall, files, OCR, PDF | memory, file, ocr, pdf |
| **Coding** | code, git, containers | coding, git, docker |
| **Media** | image/video/audio | image, video, music, movie, vision, camera, audio, speech |
| **Finance** | markets & shopping | finance, stock, crypto, shopping |
| **Communication** | email & messaging | email, whatsapp, notification |
| **System** | cloud & infra | aws, kubernetes, database, security, authentication, monitoring, logging |
| **Automation** | workflows & triggers | tool, api, notification |

Each lives in `backend/generals/<domain>/general.py`, subclasses `BaseGeneral`, sets its
`domain` (which is also its `agent_id` and bus target `general.<domain>`), declares its
`soldiers` roster, and supplies a `KeywordRouter` mapping intent keywords to specific soldiers.
The **Knowledge General** also overrides `aggregate()` to surface a `findings` list — an example
of domain-specific merging that any General can extend.

## Registry & bootstrap

- `generals/registry.py` — `GENERAL_CLASSES` plus `register_generals(manager, deps)` which
  registers each General with the Agent Manager via `AgentSpec` (Factory pattern), and
  `ensure_all_generals(manager)` to build + initialize them.
- `generals/bootstrap.py` — `bootstrap_generals(container)`: one call wires and starts all ten
  from a DI container, ready for the King to delegate to.

## How routing works

```
King → message_bus.request("general.finance", "check the stock price")
        → FinanceGeneral.run()
            → KeywordRouter: "stock" → ["stock" soldier]   (Strategy)
            → message_bus.request("soldier.stock", ...)
            → aggregate() → {domain, soldiers_used, succeeded, results}
```

If no keyword matches, the router falls back to the full roster (fan-out). Missing soldiers are
reported as failed sub-results, never raised — consistent with the platform's
failure-isolation rule.

## Tests

`backend/tests/unit/test_generals.py` — **8 tests, all passing** (project total now **44**).
Covers: exactly ten Generals with unique domains, every General has a roster + router, keyword
routing selects the right soldier, fallback-to-all when no keyword, the registry registers all
ten, bootstrap starts them live, the King delegating across multiple domains in one objective
(parallel + sequential), and reaching a specific General directly over the bus.

Run: `python scripts/run_tests.py` (offline) or `pytest backend/tests/unit`.

## Next

**Phase 6 — Soldier Agents:** implement the 40+ single-responsibility Soldiers referenced by the
rosters above (Internet, Weather, Research, Git, Docker, Stock, OCR, Email, …), each wrapping one
tool via the Tool Registry, registered so every General's roster is fully live.
