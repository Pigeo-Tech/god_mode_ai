#!/usr/bin/env bash
# Enable the ElevenLabs voice for Buddy, preserving ALL existing keys + the current session.
# You only paste your ElevenLabs key; OpenAI / Tavily / NVIDIA / JWT are reused from the running
# container, and uploaded skills stay mounted.
#
# Usage:
#   sudo bash /opt/app/deployment/use-elevenlabs.sh sk_YOUR_ELEVENLABS_KEY [VOICE_ID]
#
# VOICE_ID is optional — omit it to use the default Indian female voice. Find a voice id with:
#   curl -s -H "xi-api-key: $KEY" https://api.elevenlabs.io/v1/voices | python3 -m json.tool
set -e
EL="$1"
VOICE="${2:-}"
if [ -z "$EL" ]; then echo "Pass your ElevenLabs API key as the first argument"; exit 1; fi

OPENAI="$(docker exec agni printenv OPENAI_API_KEY 2>/dev/null || true)"
TAVILY="$(docker exec agni printenv TAVILY_API_KEY 2>/dev/null || true)"
NVIDIA="$(docker exec agni printenv NVIDIA_API_KEY 2>/dev/null || true)"
JWT="$(docker exec agni printenv JWT_SECRET 2>/dev/null || true)"; [ -z "$JWT" ] && JWT="$(openssl rand -hex 24)"
[ -z "$VOICE" ] && VOICE="$(docker exec agni printenv ELEVENLABS_VOICE_ID 2>/dev/null || true)"

mkdir -p /opt/app/backend/skills
chown -R 999:999 /opt/app/backend/skills 2>/dev/null || chmod -R 777 /opt/app/backend/skills
docker rm -f agni 2>/dev/null || true
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$JWT" \
  -e OPENAI_API_KEY="$OPENAI" \
  -e TAVILY_API_KEY="$TAVILY" \
  -e NVIDIA_API_KEY="$NVIDIA" \
  -e ELEVENLABS_API_KEY="$EL" \
  ${VOICE:+-e ELEVENLABS_VOICE_ID="$VOICE"} \
  -v /opt/app/backend/skills:/app/backend/skills \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
sleep 4
curl -s http://localhost:8000/health; echo
echo "ElevenLabs voice enabled for Buddy. Voice: ${VOICE:-default (Indian female)}."
