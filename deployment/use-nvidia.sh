#!/usr/bin/env bash
# Add your NVIDIA NIM key and restart AGNI, keeping the OpenAI + Tavily keys already in the
# running container. With an NVIDIA key present, soldiers prefer NVIDIA (free tier) over OpenAI.
#
# Usage: sudo bash /opt/app/deployment/use-nvidia.sh nvapi-YOURNVIDIAKEY
set -e
NVIDIA="$1"
if [ -z "$NVIDIA" ]; then echo "Pass your NVIDIA key (nvapi-...) as the first argument"; exit 1; fi

OPENAI="$(docker exec agni printenv OPENAI_API_KEY 2>/dev/null || true)"
TAVILY="$(docker exec agni printenv TAVILY_API_KEY 2>/dev/null || true)"
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
echo "NVIDIA key applied. Soldiers now prefer NVIDIA (meta/llama-3.3-70b-instruct)."
