#!/usr/bin/env bash
# Connect your external Skills API (Option 2) so AGNI's soldiers CALL it during a task.
# Preserves all existing keys + the current session; only adds the Skills API config.
#
# Usage:
#   sudo bash /opt/app/deployment/use-skills-api.sh "https://your-skills-api.com/invoke" "YOUR_KEY"
#
# Optional 3rd/4th/5th args:
#   AUTH    how the key is sent: bearer (default) | x-api-key | none
#   METHOD  POST (default) | GET
#   FIELD   request field that carries the user's query (default: input)
#
# Example:
#   sudo bash .../use-skills-api.sh "https://api.example.com/run" "sk_123" bearer POST query
set -e
SK_URL="$1"; SK_KEY="$2"; SK_AUTH="${3:-}"; SK_METHOD="${4:-}"; SK_FIELD="${5:-}"
if [ -z "$SK_URL" ]; then echo "Pass your Skills API URL as the first argument"; exit 1; fi

OPENAI="$(docker exec agni printenv OPENAI_API_KEY 2>/dev/null || true)"
TAVILY="$(docker exec agni printenv TAVILY_API_KEY 2>/dev/null || true)"
NVIDIA="$(docker exec agni printenv NVIDIA_API_KEY 2>/dev/null || true)"
ELEVEN="$(docker exec agni printenv ELEVENLABS_API_KEY 2>/dev/null || true)"
ELVOICE="$(docker exec agni printenv ELEVENLABS_VOICE_ID 2>/dev/null || true)"
JWT="$(docker exec agni printenv JWT_SECRET 2>/dev/null || true)"; [ -z "$JWT" ] && JWT="$(openssl rand -hex 24)"

mkdir -p /opt/app/backend/skills
chown -R 999:999 /opt/app/backend/skills 2>/dev/null || chmod -R 777 /opt/app/backend/skills
docker rm -f agni 2>/dev/null || true
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$JWT" \
  -e OPENAI_API_KEY="$OPENAI" \
  -e TAVILY_API_KEY="$TAVILY" \
  -e NVIDIA_API_KEY="$NVIDIA" \
  -e ELEVENLABS_API_KEY="$ELEVEN" \
  ${ELVOICE:+-e ELEVENLABS_VOICE_ID="$ELVOICE"} \
  -e SKILLS_API_URL="$SK_URL" \
  ${SK_KEY:+-e SKILLS_API_KEY="$SK_KEY"} \
  ${SK_AUTH:+-e SKILLS_API_AUTH="$SK_AUTH"} \
  ${SK_METHOD:+-e SKILLS_API_METHOD="$SK_METHOD"} \
  ${SK_FIELD:+-e SKILLS_API_FIELD="$SK_FIELD"} \
  -v /opt/app/backend/skills:/app/backend/skills \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
sleep 4
curl -s http://localhost:8000/health; echo
echo "Skills API connected as the 'skills.invoke' tool. Soldiers will call it during tasks."
