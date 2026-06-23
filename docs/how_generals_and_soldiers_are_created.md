# How Generals and Soldiers Are Created

Both tiers are created the same way — **Factory builder → dependency-injected constructor →
`initialize()` (self-registers on the Message Bus) → ready** — managed by the Agent Manager.
They differ only in what the class contains and how they're declared.

---

## The shared lifecycle

```
register_*()        →  AgentManager stores an AgentSpec(name, tier, builder)   # nothing built yet
ensure_*()          →  builder(agent_id)  →  Agent.__init__(agent_id, deps)    # Factory + DI
                    →  await agent.initialize()                                 # registers on the bus
                    →  agent is live, addressable by bus name
```

- **Factory pattern** — `AgentSpec.builder` is a closure that knows how to construct the agent.
- **Dependency injection** — every agent receives an `AgentDeps` bundle (buses, tools, memory,
  permissions, logger, metrics, tasks). Agents never build their own infrastructure or import
  the global container.
- **No direct coupling** — `initialize()` registers a request/reply handler on the Message Bus
  (`general.<domain>` or `soldier.<name>`). Agents reach each other only by these bus addresses.

The Agent Manager's registry is one namespace shared by both tiers, so registration keys are
tier-qualified — `general:memory` vs `soldier:memory` — while each agent's own id stays the bare
name used on the bus.

---

## Generals

A General is a class in `backend/generals/<domain>/general.py` subclassing `BaseGeneral`:

```python
class KnowledgeGeneral(BaseGeneral):
    domain = "knowledge"                          # id + bus address (general.knowledge)
    soldiers = ["internet", "weather", "research", "search", "news", "translation", "maps"]
    router = KeywordRouter({                       # Strategy: keyword -> soldier
        "weather": "weather", "research": "research", "news": "news", ...
    })
    # optional: override aggregate() for domain-specific merging
```

Wiring:
1. `generals/registry.py` lists all ten in `GENERAL_CLASSES`.
2. `register_generals(manager, deps)` registers each as an `AgentSpec` with
   `name=general:<domain>` and `builder=lambda: KnowledgeGeneral("knowledge", deps)`.
3. `ensure_all_generals(manager)` builds + `initialize()`s them (registers `general.<domain>`).
4. `bootstrap_generals(container)` runs steps 2–3 from a DI container.

What a General does at runtime: receive a subtask from the King → `router.select()` picks the
right soldiers → dispatch to each `soldier.<name>` over the bus → `aggregate()` the replies.

---

## Soldiers

Soldiers are declared **declaratively** in `backend/soldiers/catalog.py`, one line each, instead
of a hand-written class per soldier:

```python
SOLDIER_CATALOG = [
    SoldierSpec("weather", "knowledge"),                 # wraps the "weather" tool
    SoldierSpec("stock",   "finance"),                   # wraps the "stock" tool
    SoldierSpec("memory",  "memory", cls=MemorySoldier), # custom class (uses Memory Manager)
    ...
]
```

- Most soldiers are an instance of **`ToolSoldier`** (`soldiers/common.py`) — a single class
  parameterized with the tool name. One soldier == one tool == one responsibility.
- A few have custom logic via a `cls=` (e.g. `MemorySoldier`, which calls the Memory Manager
  instead of a registry tool, by overriding `work()`).

Wiring:
1. `soldiers/factory.py` turns each `SoldierSpec` into an `AgentSpec` with
   `name=soldier:<name>` and a builder that makes `ToolSoldier(name, deps, tool=...)`
   (or the custom class).
2. `bootstrap_soldiers(container)` does the full setup:
   - `register_soldier_tools()` — register the 40 tools in the Tool Registry,
   - grant the `soldier` role the `tool:*` capability,
   - build + `initialize()` all 41 soldiers (each registers `soldier.<name>`),
   - **lock each soldier to its single tool** via a per-agent allow-list (defense in depth on the
     one-responsibility rule).

What a Soldier does at runtime: receive a subtask → `validate()` required context →
`execute()` calls its one tool through the Tool Registry (permission + rate-limit checked) →
return the uniform `AgentResponse`.

---

## Bringing everything online

`backend/bootstrap.py` → `bootstrap_system(container)` chains it all:

```python
await bootstrap_soldiers(container)     # 41 soldiers + their tools, live
register_provider_tools(container.tools)# LLM tools (local always; remote if keys present)
await bootstrap_generals(container)     # 10 generals, live
king = KingAgent("king", deps); await king.initialize()
```

After this, the King can delegate to any General by bus name, and each General to any Soldier in
its roster — the whole hierarchy is created and addressable.

---

## Adding a new agent

- **New General:** create `generals/<domain>/general.py` with a `BaseGeneral` subclass (domain,
  soldiers, router) and add it to `GENERAL_CLASSES`. Done.
- **New Soldier:** add one `SoldierSpec(...)` line to `SOLDIER_CATALOG` (and register a tool for
  it in `soldiers/tools.py` if the capability is new). Done.

No other code changes — the Factory + bootstrap pick them up automatically.

---

### File map

| Concern | File |
|---|---|
| General base + routers | `backend/generals/base.py` |
| Concrete generals | `backend/generals/<domain>/general.py` |
| General registry/factory | `backend/generals/registry.py` |
| General bootstrap | `backend/generals/bootstrap.py` |
| Soldier base | `backend/soldiers/base/base_soldier.py` |
| ToolSoldier / MemorySoldier | `backend/soldiers/common.py` |
| Soldier catalog | `backend/soldiers/catalog.py` |
| Soldier factory | `backend/soldiers/factory.py` |
| Soldier bootstrap + tools | `backend/soldiers/bootstrap.py`, `backend/soldiers/tools.py` |
| Agent Manager (Factory/registry) | `backend/core/agent_manager/manager.py` |
| DI bundle | `backend/core/agent_context.py` |
| Whole-system bootstrap | `backend/bootstrap.py` |
