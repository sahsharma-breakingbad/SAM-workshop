#!/usr/bin/env bash
# Deploy weather-advisor-agent to EC2
# Usage: EC2_IP=<ip> LLM_API_KEY=<key> ./deploy.sh

set -e

EC2_IP="${EC2_IP:-ec2-18-205-38-130.compute-1.amazonaws.com}"
EC2_USER="${EC2_USER:-ubuntu}"
REMOTE_DIR="${REMOTE_DIR:-/home/ubuntu/weather-advisor-agent}"
LLM_BASE_URL="${LLM_BASE_URL:-https://lite-llm.mymaas.net}"
LLM_MODEL="${LLM_MODEL:-claude-sonnet-4-6}"
PORT="${PORT:-10000}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$LLM_API_KEY" ]; then
  echo "ERROR: LLM_API_KEY is not set. Export it before running this script."
  exit 1
fi

echo "==> Syncing files to ${EC2_USER}@${EC2_IP}:${REMOTE_DIR}"
scp "$SCRIPT_DIR/agent.py" \
    "$SCRIPT_DIR/Dockerfile" \
    "$SCRIPT_DIR/requirements.txt" \
    "${EC2_USER}@${EC2_IP}:${REMOTE_DIR}/"

echo "==> Building and restarting container on EC2"
ssh "${EC2_USER}@${EC2_IP}" bash -s <<EOF
  cd ${REMOTE_DIR}

  docker build --no-cache -t weather-advisor-agent .

  docker stop weather-advisor-agent 2>/dev/null || true
  docker rm   weather-advisor-agent 2>/dev/null || true

  docker run -d \
    --name weather-advisor-agent \
    --restart unless-stopped \
    -p ${PORT}:${PORT} \
    -e "PORT=${PORT}" \
    -e "AGENT_BASE_URL=http://${EC2_IP}:${PORT}" \
    -e "LLM_API_KEY=${LLM_API_KEY}" \
    -e "LLM_BASE_URL=${LLM_BASE_URL}" \
    -e "LLM_MODEL=${LLM_MODEL}" \
    weather-advisor-agent

  echo "==> Container status:"
  docker ps --filter name=weather-advisor-agent
EOF

echo "==> Done. Agent card: http://${EC2_IP}:${PORT}/.well-known/agent.json"
