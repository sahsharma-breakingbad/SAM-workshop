#!/usr/bin/env bash
# Deploy places-mcp-server to EC2
# Usage: EC2_IP=<ip> FSQ_CLIENT_ID=<id> FSQ_CLIENT_SECRET=<secret> ./deploy.sh
#
# Required env vars:
#   FSQ_CLIENT_ID      — Foursquare Legacy API client ID
#   FSQ_CLIENT_SECRET  — Foursquare Legacy API client secret
#
# Optional env vars:
#   EC2_IP     (default: ec2-18-205-38-130.compute-1.amazonaws.com)
#   EC2_USER   (default: ec2-user)
#   PORT       (default: 3001)

set -e

EC2_IP="${EC2_IP:-ec2-18-205-38-130.compute-1.amazonaws.com}"
EC2_USER="${EC2_USER:-ubuntu}"
REMOTE_DIR="${REMOTE_DIR:-/home/ubuntu/places-mcp-server}"
PORT="${PORT:-3001}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$FSQ_CLIENT_ID" ] || [ -z "$FSQ_CLIENT_SECRET" ]; then
  echo "ERROR: FSQ_CLIENT_ID and FSQ_CLIENT_SECRET must be set."
  exit 1
fi

echo "==> Syncing files to ${EC2_USER}@${EC2_IP}:${REMOTE_DIR}"
ssh "${EC2_USER}@${EC2_IP}" "mkdir -p ${REMOTE_DIR}"
scp "$SCRIPT_DIR/server.py" \
    "$SCRIPT_DIR/Dockerfile" \
    "$SCRIPT_DIR/requirements.txt" \
    "${EC2_USER}@${EC2_IP}:${REMOTE_DIR}/"

echo "==> Building and restarting container on EC2"
ssh "${EC2_USER}@${EC2_IP}" bash -s <<EOF
  cd ${REMOTE_DIR}

  docker build --no-cache -t places-mcp-server .

  docker stop places-mcp-server 2>/dev/null || true
  docker rm   places-mcp-server 2>/dev/null || true

  docker run -d \
    --name places-mcp-server \
    --restart unless-stopped \
    -p ${PORT}:${PORT} \
    -e "PORT=${PORT}" \
    -e "FOURSQUARE_CLIENT_ID=${FSQ_CLIENT_ID}" \
    -e "FOURSQUARE_CLIENT_SECRET=${FSQ_CLIENT_SECRET}" \
    places-mcp-server

  echo "==> Container status:"
  docker ps --filter name=places-mcp-server

  echo "==> Health check:"
  sleep 2
  curl -sf http://localhost:${PORT}/health && echo "" || echo "WARNING: health check failed"
EOF

echo "==> Done. MCP endpoint: http://${EC2_IP}:${PORT}/mcp"
