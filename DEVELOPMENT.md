# AGNI — Development Plan (local, zero cost)

We're in the **development stage**. Everything runs on your own machine — **no cloud, no hosting
bills (₹0)**. Cloud only matters at launch, and those configs already exist
(`deployment/budget/`, `deployment/aws/`) for that day.

## What "development" means here

| | Development (now) | Launch (later) |
|---|---|---|
| Where it runs | Your laptop / Ubuntu box | A server (or AWS) |
| Backends | **In-memory** (no Postgres/Redis/Qdrant) | Real Redis/Postgres/Qdrant |
| LLM | offline `llm.local` (free) | optional paid API keys |
| Cost | **₹0** | from ~₹0–420/mo (see `docs/budget_deployment.md`) |
| Command | `bash scripts/dev.sh` | `deployment/budget/deploy.sh` |

## Daily dev loop

### 1. Backend (pick one)

**Fast path — no Docker, auto-reload (recommended for coding):**
```bash
bash scripts/dev.sh
```
Runs the full 161-agent platform with in-memory backends on http://localhost:8000
(API docs at `/docs`). Edits reload automatically.

**Full-stack path — with real data services (when you want to test persistence):**
```bash
docker compose -f docker/docker-compose.yml up --build
```
Brings up API + Postgres + Redis + Qdrant locally (still ₹0 — it's your machine).

### 2. Run the tests (offline, instant)
```bash
python3 scripts/run_tests.py          # no pytest needed
# or, once deps are installed:
pytest backend/tests/unit -q
```
Current status: **86/86 passing.**

### 3. Mobile app
```bash
cd mobile/flutter
bash scripts/setup_ubuntu.sh                       # one-time: generates android/, pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # emulator → your local API
```
See `mobile/flutter/BUILD_UBUNTU.md` for the full guide.

## What to build during development (suggested order)

The skeleton is complete and tested; development now = filling in real behaviour. Highest-value
first:

1. **Pick 3–5 "hero" soldiers and make them real.** Right now soldiers wrap deterministic mock
   tools. Replace those mocks with real integrations one at a time in `backend/soldiers/tools.py`
   (or a real `LLMTool`/`RestApiTool`) — e.g. `research`/`search` via a real LLM, `weather` via a
   weather API, `stock` via a market API. Each is a one-function change behind the Tool Registry;
   nothing else moves.
2. **Wire the King's planner to the local LLM** so decomposition is smarter than keyword routing
   (swap `KeywordPlanner` for an LLM planner behind the same `Planner` interface).
3. **Flesh out the Flutter UX** — group the agents screen by the 15 domains, show the King's
   step-by-step breakdown, add a streaming typing indicator.
4. **Add integration tests** for each soldier you make real.

You can do all of this locally for ₹0; only add a paid LLM key when you want real model output.

## When you're ready to launch

1. Move secrets to a real `.env` (strong `JWT_SECRET`, DB password).
2. Get a cheap VM (Hetzner ~₹420/mo, or Oracle Always-Free ₹0) and run
   `deployment/budget/deploy.sh` — that's the whole launch for a small audience.
3. Point a domain at it for free HTTPS (Caddy handles certs automatically).
4. Scale to AWS (`deployment/aws/`) only if/when traffic demands it.

Full details: `docs/budget_deployment.md`.

## Handy references

- Architecture: `docs/architecture.md`
- Per-phase docs: `docs/phase1…phase12`, `docs/agni_hierarchy.md`
- How agents are created: `docs/how_generals_and_soldiers_are_created.md`
