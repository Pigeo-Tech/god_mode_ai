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
# Long-lived tokens (1 year) so the mobile app doesn't keep hitting "token expired".
TTL="$(docker exec agni printenv ACCESS_TOKEN_EXPIRE_MINUTES 2>/dev/null || true)"
[ -z "$TTL" ] && TTL="525600"
# ElevenLabs voice (Buddy) — reused if already set.
ELEVEN="$(docker exec agni printenv ELEVENLABS_API_KEY 2>/dev/null || true)"
ELVOICE="$(docker exec agni printenv ELEVENLABS_VOICE_ID 2>/dev/null || true)"
# Own voice engine (Piper) — reused if already set.
TTS_ENGINE_V="$(docker exec agni printenv TTS_ENGINE 2>/dev/null || true)"
PIPER_URL_V="$(docker exec agni printenv PIPER_URL 2>/dev/null || true)"
# External Skills API (Option 2) — reused if already set.
SK_URL="$(docker exec agni printenv SKILLS_API_URL 2>/dev/null || true)"
SK_KEY="$(docker exec agni printenv SKILLS_API_KEY 2>/dev/null || true)"
SK_AUTH="$(docker exec agni printenv SKILLS_API_AUTH 2>/dev/null || true)"
SK_METHOD="$(docker exec agni printenv SKILLS_API_METHOD 2>/dev/null || true)"
SK_FIELD="$(docker exec agni printenv SKILLS_API_FIELD 2>/dev/null || true)"
docker build -f docker/Dockerfile -t agni-api .
docker rm -f agni 2>/dev/null || true
# Persist runtime-added skills (uploaded from the dashboard) on the host so they survive
# rebuilds. git reset keeps untracked skill folders, so user-added skills are never lost.
mkdir -p /opt/app/backend/skills
# the container runs as uid 999 (app); make the mounted skills dir writable for uploads
chown -R 999:999 /opt/app/backend/skills 2>/dev/null || chmod -R 777 /opt/app/backend/skills
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$JWT" -e ACCESS_TOKEN_EXPIRE_MINUTES="$TTL" \
  -e OPENAI_API_KEY="$OPENAI" \
  -e TAVILY_API_KEY="$TAVILY" \
  -e NVIDIA_API_KEY="$NVIDIA" \
  -e ELEVENLABS_API_KEY="$ELEVEN" \
  ${ELVOICE:+-e ELEVENLABS_VOICE_ID="$ELVOICE"} \
  ${SK_URL:+-e SKILLS_API_URL="$SK_URL"} \
  ${SK_KEY:+-e SKILLS_API_KEY="$SK_KEY"} \
  ${SK_AUTH:+-e SKILLS_API_AUTH="$SK_AUTH"} \
  ${SK_METHOD:+-e SKILLS_API_METHOD="$SK_METHOD"} \
  ${SK_FIELD:+-e SKILLS_API_FIELD="$SK_FIELD"} \
  ${TTS_ENGINE_V:+-e TTS_ENGINE="$TTS_ENGINE_V"} \
  ${PIPER_URL_V:+-e PIPER_URL="$PIPER_URL_V"} \
  -v /opt/app/backend/skills:/app/backend/skills \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
sleep 4
curl -s http://localhost:8000/health; echo
echo "Redeployed. Keys preserved (OpenAI / Tavily / NVIDIA)."
