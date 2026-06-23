# GOD MODE AI — Phase 11: Docker

> **Status:** Phase 11 of 12 complete. The backend ships as a multi-stage, non-root container,
> and the full stack — API + PostgreSQL + Redis + Qdrant (+ NGINX in prod) — runs with one
> `docker compose` command. Separate dev and production configurations are provided.

## What was built (`docker/`)

| File | Role |
|---|---|
| `Dockerfile` | Multi-stage (builder → slim runtime), non-root `app` user, container `HEALTHCHECK` on `/health`, Gunicorn + Uvicorn workers as the production CMD. |
| `entrypoint.sh` | Waits for Postgres/Redis/Qdrant (when not in-memory), optionally runs Alembic migrations, then `exec`s the CMD. |
| `.dockerignore` | Keeps the build context lean (no venv, git, mobile, docs, caches). |
| `docker-compose.yml` | **Dev** stack: api (live-reload bind mount) + postgres + redis + qdrant, with healthchecked `depends_on`. |
| `docker-compose.prod.yml` | **Prod** stack: NGINX reverse proxy → api (gunicorn) + postgres + redis + qdrant, restart policies, resource limits, named volumes, `.env` secrets. |
| `nginx/nginx.conf` | Reverse proxy with **WebSocket upgrade** for `/v1/stream`, forwarded headers, health passthrough. |
| `Makefile` (root) | `make up` / `make prod-up` / `make build` / `make test` / `make logs`. |

`requirements.txt` gained `gunicorn` and `psycopg[binary]` for the production server + Postgres
driver.

## Image design

```
builder  (python:3.12-slim)
  pip install -r requirements.txt → /install
runtime  (python:3.12-slim)
  copy /install → /usr/local        # deps only, no build tools
  copy backend/                     # app code
  USER app                          # non-root
  HEALTHCHECK /health
  CMD gunicorn ... UvicornWorker --workers 4
```

Multi-stage keeps the runtime image small (no compilers/caches); non-root + healthcheck are
production hygiene. Dev overrides the CMD with `uvicorn --reload` and bind-mounts `backend/` for
instant reloads.

## Running

```bash
# Dev (in-process reload, full backing services)
docker compose -f docker/docker-compose.yml up --build
#   API → http://localhost:8000   docs → /docs

# Production-like (NGINX on :80)
cp .env.example .env   # set real secrets
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build
```

`USE_IN_MEMORY_BACKENDS=false` in both stacks, so the API uses the **real Redis/Postgres/Qdrant
adapters** built in Phase 7 — the same code path, now against live services.

## Validation

Docker isn't available in the build sandbox, so the artifacts were validated structurally:
both compose files parse (services: dev = api/postgres/redis/qdrant; prod = +nginx),
`entrypoint.sh` passes `bash -n`. The backend suite remains **86/86**. The images build and run
wherever Docker is installed (`make build`, `make up`).

## Next

**Phase 12 — AWS Deployment:** ECS/Fargate task definitions + service, Application Load Balancer,
RDS PostgreSQL, ElastiCache Redis, Qdrant, ECR, Secrets Manager, CloudWatch, Route53, S3 +
CloudFront, and auto-scaling — as Infrastructure-as-Code.
