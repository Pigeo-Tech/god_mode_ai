#!/usr/bin/env bash
# Restart AGNI with BOTH keys: your existing OpenAI key (reused from the running container) +
# a Tavily web-search key passed as the first argument.
#
# Usage: sudo bash /opt/app/deployment/use-keys.sh tvly-YOURTAVILYKEY
set -e
TAVILY="$1"
if [ -z "$TAVILY" ]; then echo "Pass your Tavily key as the first argument"; exit 1; fi

OPENAI="$(docker exec agni printenv OPENAI_API_KEY 2>/dev/null || true)"
docker rm -f agni 2>/dev/null || true
docker run -d --name agni --restart unless-stopped -p 8000:8000 \
  -e USE_IN_MEMORY_BACKENDS=true -e WAIT_FOR_DEPS=false \
  -e JWT_SECRET="$(openssl rand -hex 24)" \
  -e OPENAI_API_KEY="$OPENAI" \
  -e TAVILY_API_KEY="$TAVILY" \
  agni-api \
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
sleep 4
curl -s http://localhost:8000/health; echo
echo "OpenAI + Tavily keys applied. Live web search is on."
