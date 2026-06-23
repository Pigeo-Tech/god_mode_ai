#!/usr/bin/env bash
# Local development server — fast iteration, ZERO cost, no Docker / no data services.
# Runs the full 161-agent platform with in-memory backends and auto-reload.
# Usage (from repo root):  bash scripts/dev.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "==> Creating virtualenv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing dependencies..."
pip install -q -r requirements.txt pytest pytest-asyncio

export USE_IN_MEMORY_BACKENDS=true       # no Postgres/Redis/Qdrant needed in dev
export APP_ENV=development
export JWT_SECRET=${JWT_SECRET:-dev-secret}

echo "==> API on http://localhost:8000  (docs at /docs).  Ctrl-C to stop."
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
