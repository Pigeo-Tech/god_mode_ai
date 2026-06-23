#!/usr/bin/env bash
# Container entrypoint: optionally wait for dependencies and run migrations, then exec the CMD.
set -euo pipefail

wait_for() {
  local host="$1" port="$2" name="$3" tries="${4:-30}"
  echo "waiting for ${name} at ${host}:${port}..."
  for _ in $(seq 1 "${tries}"); do
    if python -c "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(0 if s.connect_ex(('${host}',${port}))==0 else 1)"; then
      echo "${name} is up"; return 0
    fi
    sleep 1
  done
  echo "ERROR: ${name} not reachable" >&2; return 1
}

if [ "${WAIT_FOR_DEPS:-true}" = "true" ] && [ "${USE_IN_MEMORY_BACKENDS:-false}" = "false" ]; then
  wait_for "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}" "postgres" || true
  wait_for "$(echo "${REDIS_URL:-redis://redis:6379/0}" | sed -E 's#redis://([^:/]+).*#\1#')" 6379 "redis" || true
  wait_for "$(echo "${QDRANT_URL:-http://qdrant:6333}" | sed -E 's#https?://([^:/]+).*#\1#')" 6333 "qdrant" || true
fi

# Database migrations (Alembic) run here once they are added; no-op if absent.
if [ "${RUN_MIGRATIONS:-false}" = "true" ] && command -v alembic >/dev/null 2>&1; then
  echo "running migrations..."; alembic upgrade head || echo "migrations skipped"
fi

exec "$@"
