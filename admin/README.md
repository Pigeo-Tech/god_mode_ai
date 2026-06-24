# AGNI — Web Admin Command Center (Flutter Web)

A dark, glassmorphism admin dashboard for AGNI Advanced God Mode AI. It connects to the live
AGNI API and gives you a single command center for the whole ecosystem.

## What's live now (real data from your API)
- **Executive Center** — agent/tool counts, system health, hierarchy, live activity sparkline
- **King Agent** — status + control buttons (controls wire up as the admin API grows)
- **Generals / Soldiers** — searchable grids of every agent, grouped by tier, with status
- **Command Console** — send commands to the King (`/v1/chat`) and see answers + actions
- **Tools** — every registered tool, grouped by kind

## Styled & ready (light up when their backend lands)
LLM Models, Memory, Users, Security, Infrastructure, Live Tasks, Performance, Analytics,
Notifications, Billing.

## Run it

You need Flutter (with web enabled: `flutter config --enable-web`).

```bash
cd "/mnt/d/Agni Advance/god_mode_ai/admin"

# generate the web/ scaffolding (index.html etc.) without touching lib/ or pubspec:
flutter create . --platforms=web

flutter pub get

# develop:
flutter run -d chrome
# or build for hosting:
flutter build web --release   # output in build/web/
```

On the login screen, set **Server URL** to `http://13.60.255.199:8000`, then **Create + sign in**.

## Notes
- The browser→API call needs **CORS** on the backend (added to `backend/api/main.py`). Make sure the
  backend has been redeployed with that change, or the dashboard will show "Could not reach the API".
- Dependencies are intentionally minimal (`flutter` + `http`) so it builds cleanly.
