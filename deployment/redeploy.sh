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
# Reuse the existing JWT secret so redeploys DON'T log everyone out (sessions stay valid).
JWT="$(docker exec agni printenv JWT_SECRET 2>/dev/null || true)"
[ -z "$JWT" ] && JWT="$(openssl rand -hex 24)"
# ElevenLabs voice (Buddy) — reused if already set.
ELEVEN="$(docker exec agni printenv ELEVENLABS_API_KEY 2>/dev/null || true)"
ELVOICE="$(docker exec agni printenv ELEVENLABS_VOICE_ID 2>/dev/null || true)"
docker build -f docker/Dockerfile -t agni-api .
docker rm -f agni 2>/dev/null || true
# Persist runtime-added skills (uploaded from the dashboard) on the host so they survive
# rebuilds. git reset keeps untracked skill folders, so user-added skills are never lost.
mkdir -p /opt/app/backend/skills
# the container runs as uid 999 (app); make the mounted skills dir writable for uploads
chown -R 999:999 /opt/app/backend/skills 2>/dev/null || chmod -R 777 /opt/app/backend/skills
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$JWT" \
  -e OPENAI_API_KEY="$OPENAI" \
  -e TAVILY_API_KEY="$TAVILY" \
  -e NVIDIA_API_KEY="$NVIDIA" \
  -e ELEVENLABS_API_KEY="$ELEVEN" \
  ${ELVOICE:+-e ELEVENLABS_VOICE_ID="$ELVOICE"} \
  -v /opt/app/backend/skills:/app/backend/skills \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
sleep 4
curl -s http://localhost:8000/health; echo
echo "Redeployed. Keys preserved (OpenAI / Tavily / NVIDIA)."
