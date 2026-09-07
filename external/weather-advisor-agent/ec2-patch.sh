#!/usr/bin/env bash
# Run this DIRECTLY on the EC2 instance to patch weather-advisor-agent in-place.
# Usage: bash ec2-patch.sh
# Assumes: agent.py, Dockerfile, requirements.txt are in the current directory.

set -e

CONTAINER="weather-advisor-agent"
IMAGE="weather-advisor-agent"

echo "==> Patching $CONTAINER in-place"

# ---- 1. Verify the running container exists ----
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "WARNING: container '$CONTAINER' is not running — will do a full build+start instead"
  FULL_BUILD=true
else
  FULL_BUILD=false
fi

# ---- 2. Quick path: copy agent.py into the running container (no rebuild) ----
if [ "$FULL_BUILD" = "false" ]; then
  echo "==> Hot-patching agent.py into running container"
  docker cp agent.py "${CONTAINER}:/app/agent.py"

  echo "==> Restarting container to pick up new code"
  docker restart "${CONTAINER}"

  echo "==> Waiting for container to come back up..."
  sleep 3
  docker ps --filter "name=${CONTAINER}" --format "{{.Names}}\t{{.Status}}"
  echo "==> Hot-patch complete."
  echo ""
fi

# ---- 3. Full rebuild path (container was not running) ----
if [ "$FULL_BUILD" = "true" ]; then
  echo "==> Full build — rebuilding image"
  docker build --no-cache -t "${IMAGE}" .

  docker stop "${CONTAINER}" 2>/dev/null || true
  docker rm   "${CONTAINER}" 2>/dev/null || true

  # Source env file if present, otherwise rely on existing env vars
  if [ -f .env ]; then
    echo "==> Loading env from .env"
    set -a; source .env; set +a
  fi

  docker run -d \
    --name "${CONTAINER}" \
    --restart unless-stopped \
    -p "${PORT:-10000}:${PORT:-10000}" \
    -e "PORT=${PORT:-10000}" \
    -e "AGENT_BASE_URL=${AGENT_BASE_URL}" \
    -e "LLM_API_KEY=${LLM_API_KEY}" \
    -e "LLM_BASE_URL=${LLM_BASE_URL:-https://lite-llm.mymaas.net}" \
    -e "LLM_MODEL=${LLM_MODEL:-claude-sonnet-4-6}" \
    "${IMAGE}"

  sleep 3
  docker ps --filter "name=${CONTAINER}" --format "{{.Names}}\t{{.Status}}"
  echo "==> Full build complete."
fi

# ---- 4. Smoke test ----
PORT_NUM="${PORT:-10000}"
echo ""
echo "==> Smoke test: GET http://localhost:${PORT_NUM}/health"
curl -sf "http://localhost:${PORT_NUM}/health" && echo "" || echo "WARNING: health check failed"

echo "==> Agent card: http://localhost:${PORT_NUM}/.well-known/agent.json"
