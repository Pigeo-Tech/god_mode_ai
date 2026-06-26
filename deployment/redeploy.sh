#!/usr/bin/env bash
# Pull latest code, rebuild, and restart AGNI — reusing ALL keys (OpenAI, Tavily, NVIDIA)
# already present in the running container. No keys are typed; nothing is lost on redeploy.
#
# Usage: sudo bash /opt/app/deployment/redeploy.sh
set -e
cd /opt/app
git fetch origin && git reset --hard origin/main
OPENAI="$(docker exec agni printenv OPENAI_API_KEY 2>/dev/null || true)"
TAVILY="$(docker exec agni printenv TAVILY_API_KEY 2>/dev/null || true)"
NVIDIA="$(docker exec agni printenv NVIDIA_API_KEY 2>/dev/null || true)"
docker build -f docker/Dockerfile -t agni-api .
docker rm -f agni 2>/dev/null || true
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$(openssl rand -hex 24)" \
  -e OPENAI_API_KEY="$OPENAI" \
  -e TAVILY_API_KEY="$TAVILY" \
  -e NVIDIA_API_KEY="$NVIDIA" \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
sleep 4
curl -s http://localhost:8000/health; echo
echo "Redeployed. Keys preserved (OpenAI / Tavily / NVIDIA)."
