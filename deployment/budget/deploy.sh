#!/usr/bin/env bash
# One-shot deploy on a fresh Ubuntu server. Run as a sudo-capable user from the repo root:
#   bash deployment/budget/deploy.sh
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker..."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
  echo "Docker installed. If this is the first install, log out/in (or run 'newgrp docker') and re-run."
fi

cd "$(dirname "$0")"
[ -f .env ] || { cp .env.example .env; echo "Created .env — edit it (DOMAIN, passwords) then re-run."; exit 0; }

echo "==> Building and starting the stack..."
docker compose up -d --build
echo "==> Status:"
docker compose ps
echo
echo "Done. API health:  curl http://localhost/health"
echo "If DOMAIN is set, HTTPS is provisioned automatically within ~1 minute."
