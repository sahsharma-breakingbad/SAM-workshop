#!/usr/bin/env bash
# Run this DIRECTLY on the EC2 instance to patch or restart places-mcp-server.
# Usage: bash ec2-patch.sh
# Assumes: server.py, Dockerfile, requirements.txt are in the current directory.
# Env vars FOURSQUARE_CLIENT_ID and FOURSQUARE_CLIENT_SECRET must be set (or in .env).

set -e

CONTAINER="places-mcp-server"
IMAGE="places-mcp-server"
PORT="${PORT:-3001}"

echo "==> Managing $CONTAINER"

# Load env file if present
if [ -f .env ]; then
  echo "==> Loading env from .env"
  set -a; source .env; set +a
fi

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "WARNING: container '$CONTAINER' is not running — doing a full build+start"
  FULL_BUILD=true
else
  FULL_BUILD=false
fi

if [ "$FULL_BUILD" = "false" ]; then
  echo "==> Hot-patching server.py into running container"
  docker cp server.py "${CONTAINER}:/app/server.py"

  echo "==> Restarting container"
  docker restart "${CONTAINER}"

  sleep 3
  docker ps --filter "name=${CONTAINER}" --format "{{.Names}}\t{{.Status}}"
  echo "==> Hot-patch complete."
fi

if [ "$FULL_BUILD" = "true" ]; then
  echo "==> Full build — rebuilding image"
  docker build --no-cache -t "${IMAGE}" .

  docker stop "${CONTAINER}" 2>/dev/null || true
  docker rm   "${CONTAINER}" 2>/dev/null || true

  docker run -d \
    --name "${CONTAINER}" \
    --restart unless-stopped \
    -p "${PORT}:${PORT}" \
    -e "PORT=${PORT}" \
    -e "FOURSQUARE_CLIENT_ID=${FOURSQUARE_CLIENT_ID}" \
    -e "FOURSQUARE_CLIENT_SECRET=${FOURSQUARE_CLIENT_SECRET}" \
    "${IMAGE}"

  sleep 3
  docker ps --filter "name=${CONTAINER}" --format "{{.Names}}\t{{.Status}}"
  echo "==> Full build complete."
fi

echo ""
echo "==> Health check: GET http://localhost:${PORT}/health"
curl -sf "http://localhost:${PORT}/health" && echo "" || echo "WARNING: health check failed"
echo "==> MCP endpoint: http://localhost:${PORT}/mcp"
