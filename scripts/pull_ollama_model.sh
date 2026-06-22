#!/usr/bin/env sh
set -eu

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"

until curl -fsS "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; do
  echo "Waiting for Ollama at ${OLLAMA_BASE_URL}..."
  sleep 3
done

curl -fsS "${OLLAMA_BASE_URL}/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"${OLLAMA_MODEL}\"}"
