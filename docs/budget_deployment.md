# AGNI — Budget Deployment (one small server)

You don't need the AWS Phase 12 stack. The entire platform — API + Postgres + Redis + Qdrant —
runs on **one small VM** with Docker, behind **Caddy** (free automatic HTTPS). This fits well
under a ~2000/month budget; several options are effectively free.

The AGNI hierarchy (161 agents) is in-process and lightweight, so resource needs are modest. A
**4 GB RAM / 2 vCPU** server is comfortable; 2 GB works for light/personal use.

## Where to host (cost ≈ per month)

| Provider / plan | Specs | Approx cost | Notes |
|---|---|---|---|
| **Oracle Cloud — Always Free** | 4 ARM vCPU / 24 GB | **₹0 / $0** | Free forever. Best value. ARM (all our images are ARM-ready). Card required at signup. |
| **Hetzner CX22** | 2 vCPU / 4 GB / 40 GB | **~₹420 / ~$5** | Best paid value. (CAX11 ARM is even cheaper, ~₹350.) |
| **DigitalOcean** | 2 vCPU / 2 GB | ~₹1,000 / $12 | 4 GB plan ~₹2,000 / $24 (right at budget). |
| **AWS Lightsail** | 2 GB | ~₹1,000 / $12 | Fixed-price AWS VM (not the Fargate stack). |

All of these are **far** below ₹2000/month. Recommendation: **Hetzner CX22** (cheap, reliable
x86) or **Oracle Always Free** (₹0).

## Deploy in 5 steps

1. **Create the VM** (Ubuntu 22.04/24.04) on any provider above. Note its public IP.
2. **(Optional) Point a domain** — add an `A` record for `api.yourdomain.com` → the server IP.
   This unlocks free HTTPS. You can skip it and use plain HTTP on the IP.
3. **Get the code on the server:**
   ```bash
   git clone <your-repo-url> agni && cd agni/god_mode_ai
   # or scp the project folder up
   ```
4. **Configure and launch:**
   ```bash
   cd deployment/budget
   cp .env.example .env
   nano .env            # set POSTGRES_PASSWORD, JWT_SECRET; set DOMAIN=api.yourdomain.com (or leave :80)
   cd ../.. && bash deployment/budget/deploy.sh
   ```
   The script installs Docker (if missing) and runs `docker compose up -d --build`.
5. **Verify:**
   ```bash
   curl http://localhost/health           # {"status":"ok",...}
   # with a domain set, https://api.yourdomain.com/docs works within ~1 minute (auto-TLS)
   ```

Point the Flutter app at it: `flutter run --dart-define=API_BASE_URL=https://api.yourdomain.com`.

## What's in the stack (`deployment/budget/`)

- `docker-compose.yml` — api (1 GB), postgres (512 MB), redis (256 MB), qdrant (768 MB), caddy
  (64 MB). Memory-capped so it fits a 4 GB box with headroom; data persists in named volumes.
- `Caddyfile` — reverse proxy with gzip; **automatic HTTPS** when `DOMAIN` is a real hostname;
  WebSocket (`/v1/stream`) proxied automatically.
- `.env.example` — passwords, JWT secret, optional LLM keys.
- `deploy.sh` — one-command install + launch.

## Even cheaper: "lite" mode (1 GB VM, ~₹200 or free)

For a demo or very light personal use, skip Postgres/Redis/Qdrant entirely and run just the API
with in-memory backends:

```bash
docker build -f docker/Dockerfile -t agni-api .
docker run -d -p 80:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET=change-me agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

This runs the full 161-agent hierarchy in one ~400 MB container. Trade-off: memory isn't
persisted across restarts (it's in-process). Great for trying it out on the cheapest 1 GB VM.

## Running cost reality check

The only real ongoing cost is the VM (₹0–2000/mo above). LLM usage is **extra and optional** —
with no API keys, AGNI uses the built-in offline `llm.local` model and costs nothing. Add an
OpenAI/Anthropic key later only when you want real model answers, and you pay per token to them,
not for hosting.

## When to revisit AWS

Stick with the single-VM setup until you genuinely need high availability or to serve many
concurrent users. The Phase 12 Terraform is there for that day — it's the same Docker image, just
orchestrated across managed services.
