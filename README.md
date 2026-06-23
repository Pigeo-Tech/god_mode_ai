# GOD MODE AI

An enterprise-grade, multi-agent AI operating system. Not a chatbot — a platform that
plans, reasons, delegates, remembers, and orchestrates tools across a hierarchy of agents.

## Agent Hierarchy
```
                     KING AGENT
                          |
        +-----------------+-----------------+
        |                 |                 |
     GENERAL           GENERAL           GENERAL
        |                 |                 |
   SOLDIER AGENTS    SOLDIER AGENTS    SOLDIER AGENTS
```
The **King** never does work — it understands, decomposes, assigns, monitors, and merges.
**Generals** own a domain and coordinate. **Soldiers** each do exactly one thing.

## Stack
Python 3.12 · FastAPI · Pydantic · SQLAlchemy/Alembic · PostgreSQL · Redis · Qdrant ·
Docker · AWS ECS/Fargate · Flutter (mobile).

## Repository Layout
See `docs/architecture.md` for the full Phase 1 design and the 14-point spec per component.

## Build Phases
1. Architecture & folder structure  ← **current**
2. Core framework  3. Base agent system  4. King agent  5. Generals  6. Soldiers
7. Memory  8. Tool orchestration  9. API layer  10. Flutter  11. Docker  12. AWS

## Status
Phase 1 scaffold. Directories contain `__init__.py` placeholders; modules are filled in
later phases. Nothing here is runnable yet.
