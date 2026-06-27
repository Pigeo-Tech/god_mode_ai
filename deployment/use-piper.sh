#!/usr/bin/env bash
# Deploy AGNI's OWN self-hosted Piper voice engine (no third-party AI voice service).
# Builds the Piper container with an Indian female voice, runs it, and switches the backend to it.
# Preserves all keys + session + the skills mount.
#
# Usage: sudo bash /opt/app/deployment/use-piper.sh [hindi|malayalam|english]
#   hindi      -> hi_IN-priyamvada  (Indian female, DEFAULT)
#   malayalam  -> ml_IN-meera       (Indian female)
#   english    -> en_US-hfc_female  (English female)
set -e
CHOICE="${1:-hindi}"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
case "$CHOICE" in
  hindi)     VOICE="$BASE/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium";;
  malayalam) VOICE="$BASE/ml/ml_IN/meera/medium/ml_IN-meera-medium";;
  english)   VOICE="$BASE/en/en_US/hfc_female/medium/en_US-hfc_female-medium";;
  *) echo "Unknown voice '$CHOICE' (use: hindi | malayalam | english)"; exit 1;;
esac

cd /opt/app

# 1) Build + run our own Piper voice engine container.
docker build --build-arg VOICE_BASE="$VOICE" -t agni-piper deployment/piper
docker rm -f agni-piper 2>/dev/null || true
docker run -d --name agni-piper --restart unless-stopped -p 5002:5002 agni-piper
sleep 3
echo -n "piper health: "; curl -s http://localhost:5002/health; echo

# 2) Restart AGNI pointed at our own engine (reuse all keys + session; keep skills mounted).
OPENAI="$(docker exec agni printenv OPENAI_API_KEY 2>/dev/null || true)"
TAVILY="$(docker exec agni printenv TAVILY_API_KEY 2>/dev/null || true)"
NVIDIA="$(docker exec agni printenv NVIDIA_API_KEY 2>/dev/null || true)"
ELEVEN="$(docker exec agni printenv ELEVENLABS_API_KEY 2>/dev/null || true)"
SK_URL="$(docker exec agni printenv SKILLS_API_URL 2>/dev/null || true)"
SK_KEY="$(docker exec agni printenv SKILLS_API_KEY 2>/dev/null || true)"
JWT="$(docker exec agni printenv JWT_SECRET 2>/dev/null || true)"; [ -z "$JWT" ] && JWT="$(openssl rand -hex 24)"
mkdir -p /opt/app/backend/skills
chown -R 999:999 /opt/app/backend/skills 2>/dev/null || chmod -R 777 /opt/app/backend/skills
docker rm -f agni 2>/dev/null || true
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$JWT" \
  -e OPENAI_API_KEY="$OPENAI" -e TAVILY_API_KEY="$TAVILY" -e NVIDIA_API_KEY="$NVIDIA" \
  -e ELEVENLABS_API_KEY="$ELEVEN" \
  ${SK_URL:+-e SKILLS_API_URL="$SK_URL"} ${SK_KEY:+-e SKILLS_API_KEY="$SK_KEY"} \
  -e TTS_ENGINE=piper -e PIPER_URL=http://172.17.0.1:5002 \
  -v /opt/app/backend/skills:/app/backend/skills \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
sleep 4
echo -n "agni health: "; curl -s http://localhost:8000/health; echo
echo "Own voice engine live (Piper, $CHOICE female). Buddy uses YOUR engine — no third party."
