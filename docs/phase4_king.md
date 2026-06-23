# GOD MODE AI — Phase 4: King Agent

> **Status:** Phase 4 of 12 complete. The King orchestrator is built and wired to the full
> stack. A user objective now flows King → Generals → Soldiers and back as a single aggregated
> answer — entirely over the in-memory buses, with retries, monitoring, and memory persistence.
> The King performs **no** domain work itself.

## What was built

| Component | File | Role |
|---|---|---|
| **Planner / Decomposer** | `king/planner.py` | Strategy interface + deterministic `KeywordPlanner`: splits the objective into clauses, routes each to a General by keyword, and chains "then" clauses as sequential dependencies → a real DAG. An LLM planner can replace it without touching the King. |
| **Aggregator** | `king/aggregator.py` | Merges the completed task graph into a final answer: summary text + per-step breakdown (general, status, attempts, result/error). |
| **ProgressMonitor** | `king/monitor.py` | Subscribes to `task.assigned/completed/dead_letter` on the Event Bus and tallies progress for the response (and the future WebSocket stream). |
| **KingAgent** | `king/king.py` | Ties it together: memory context → plan → Task DAG → dispatch to Generals over the bus → aggregate → persist → respond. Reachable on the Message Bus at `king`. |
| **AgentDeps.tasks** | `core/agent_context.py` | The King receives the Task Manager through DI. |

## Orchestration flow

```
KingAgent.run(objective)
  1. memory.recall(objective)                       # prior context
  2. planner.plan(objective)  -> [PlanStep...]       # decompose (Strategy)
  3. build TaskGraph (deps from "then" sequencing)   # Phase 2 Task Manager
  4. monitor.start()                                  # Event Bus tally
     task_manager.run_graph(graph, dispatch)          # respects DAG + retries
        dispatch(task) -> message_bus.request("general.<owner>", subtask)
                              -> General -> Soldiers -> tool calls
  5. aggregator.merge(...)                            # final answer + breakdown
  6. memory.remember(Q/A exchange)                    # persist outcome
  7. return AgentResponse(COMPLETED, result=final)
```

Because every tier returns the uniform envelope and `BaseAgent.run()` converts exceptions into
`FAILED` envelopes, a broken General surfaces as a failed *subtask* in the breakdown — the King
still completes and returns a coherent answer. The Task Manager applies retry/backoff before a
subtask is marked failed.

## Decomposition example

Objective: *"research the topic and write notes then code the prototype"*

```
Group 1 (parallel):  research the topic  -> knowledge general
                     write notes         -> knowledge general
Group 2 (depends on group 1):
                     code the prototype  -> coding general
```

→ 3 tasks, correct dependency edges, dispatched with the parallel pair first and the coding
step only after both complete.

## Tests

`backend/tests/unit/test_king.py` — **7 tests, all passing** (project total now **36**). Covers
single-step delegation, parallel+sequential decomposition, graceful handling of a failing
General, a missing General reported (not raised), memory persistence of the exchange, the
ProgressMonitor counts, and reaching the King purely via the Message Bus.

Run: `python scripts/run_tests.py king` (offline) or `pytest backend/tests/unit`.

## Next

**Phase 5 — General Agents:** implement the ten concrete Generals (Knowledge, Planning,
Execution, Memory, Coding, Media, Finance, Communication, System, Automation), each with its
soldier roster, domain routing, and aggregation, registered with the Agent Manager so the King
can reach them by name.
