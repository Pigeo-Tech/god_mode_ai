#!/bin/bash
# EC2 user-data: runs ONCE on first boot (as root). Installs Docker, pulls the code,
# builds the image, and starts the AGNI API (lite/in-memory) on port 8000.
# EDIT the REPO_URL line below to your GitHub repo, then paste this whole file into the
# EC2 "Advanced details -> User data" box when launching the instance.
set -e
REPO_URL="https://github.com/YOURNAME/god_mode_ai.git"   # <-- CHANGE THIS

exec > /var/log/agni-setup.log 2>&1   # progress log: cat /var/log/agni-setup.log
echo "== AGNI setup starting =="

apt-get update -y
curl -fsSL https://get.docker.com | sh

cd /opt
git clone "$REPO_URL" app
cd app

docker build -f docker/Dockerfile -t agni-api .
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$(openssl rand -hex 24)" \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

echo "== AGNI is up on :8000 =="
