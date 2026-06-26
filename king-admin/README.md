# AGNI — King Command Center (Admin Web App)

Phase 1. A modern, dark, **ember-on-slate** admin web app for the AGNI King. Pure HTML5 +
Bootstrap 5 + Chart.js + vanilla JS — no build step, deployable as static files (Hostinger-ready).
It talks to the live AGNI FastAPI backend.

## What's live now (real data)
- **Login** → connects to the AGNI API (JWT).
- **Dashboard** → total agents, generals, soldiers, tools, LLMs, server status; activity + hierarchy charts.
- **King · Agent Tree** → King → Generals (live).
- **Generals / Soldiers** → grids from `/v1/agents`, searchable.
- **Buddy Console** → send any request to the King (`/v1/chat`); shows the answer **plus** which provider/model/soldier/skill handled it.
- **LLM Manager** → live providers from `/v1/tools` (NVIDIA primary, OpenAI fallback, local).
- **Settings** → change the server URL; dark/light toggle.

## Designed, backend coming next phase
Skills Manager, Knowledge, Memory, Prompt Library, Users, Automation, Analytics, Wallet,
API Manager, Logs, Security, Backups — each needs new admin endpoints on the backend (Phase 2+).

## Run it locally
A static server is enough (fetch from `file://` is blocked by some browsers, so serve it):
```bash
cd "/mnt/d/Agni Advance/god_mode_ai/king-admin"
python3 -m http.server 9000
```
Open **http://localhost:9000** → Server URL `http://13.60.255.199:8000` → **Create + sign in**.

## Deploy to Hostinger (or any static host)
Upload the **contents of `king-admin/`** to your `public_html` (or a subfolder). That's it — it's
all static. Set the Server URL on the login screen to your API. (CORS is already enabled on the API.)

## Next phases
1. **Skills/Prompts/Knowledge managers** + backend CRUD endpoints (`/v1/admin/...`).
2. **Users/RBAC, Logs, Backups** + persistence (PostgreSQL/Redis).
3. **Analytics/Wallet/Cost** dashboards with real metrics.
