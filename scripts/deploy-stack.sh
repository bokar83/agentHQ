#!/usr/bin/env bash
# deploy-stack.sh -- Auto-deploy for agentsHQ stack
# Runs inside thepopebot-runner container via docker exec
# Triggered by .github/workflows/deploy-agentshq.yml

set -euo pipefail

REPO="/root/agentsHQ"
SHA_FILE="${REPO}/.deploy-sha"
COMPOSE_MAIN="${REPO}/docker-compose.yml"
COMPOSE_TPB="${REPO}/docker-compose.thepopebot.yml"
ORCHESTRATOR_IMAGE="agentshq-orchestrator"

# Git credential setup
if [ -n "${GH_TOKEN:-}" ]; then
  git config --global url."https://${GH_TOKEN}@github.com/".insteadOf "https://github.com/"
fi

# Pull latest
echo "[deploy] Pulling latest from origin/main..."
git -C "$REPO" fetch origin main
git -C "$REPO" reset --hard origin/main
NEW_SHA=$(git -C "$REPO" rev-parse HEAD)
echo "[deploy] HEAD is now ${NEW_SHA}"

# Change detection
DEPLOY_ALL=false
OLD_SHA=""

if [ ! -f "$SHA_FILE" ]; then
  echo "[deploy] No .deploy-sha found -- full deploy"
  DEPLOY_ALL=true
else
  OLD_SHA=$(cat "$SHA_FILE")
  if ! git -C "$REPO" cat-file -e "${OLD_SHA}^{commit}" 2>/dev/null; then
    echo "[deploy] Stored SHA ${OLD_SHA} not in history (force-push?) -- full deploy"
    DEPLOY_ALL=true
  fi
fi

# NOTE: all callers must use "|| true" -- grep exits 1 on no match and set -e would abort
changed_in() {
  local pattern="$1"
  if [ "$DEPLOY_ALL" = "true" ]; then return 0; fi
  git -C "$REPO" diff --name-only "${OLD_SHA}" "${NEW_SHA}" | grep -q "^${pattern}"
}

ORC_CHANGED=false
CHATUI_CHANGED=false
TPB_COMPOSE_CHANGED=false

changed_in "orchestrator/" && ORC_CHANGED=true || true
changed_in "thepopebot/chat-ui/" && CHATUI_CHANGED=true || true
changed_in "docker-compose.thepopebot.yml" && TPB_COMPOSE_CHANGED=true || true

echo "[deploy] orc_changed=${ORC_CHANGED} chatui_changed=${CHATUI_CHANGED} tpb_compose_changed=${TPB_COMPOSE_CHANGED}"

# Track exit codes independently
ORC_EXIT=0
CHATUI_EXIT=0
TPB_EXIT=0

# Orchestrator deploy
if [ "$ORC_CHANGED" = "true" ]; then
  echo "[deploy] Orchestrator changed -- rebuilding..."

  if docker image inspect "${ORCHESTRATOR_IMAGE}:latest" &>/dev/null; then
    docker tag "${ORCHESTRATOR_IMAGE}:latest" "${ORCHESTRATOR_IMAGE}:previous"
    echo "[deploy] Tagged previous image as :previous"
  fi

  if docker compose -f "$COMPOSE_MAIN" build orchestrator; then
    docker compose -f "$COMPOSE_MAIN" up -d --force-recreate orchestrator

    echo "[deploy] Waiting for orchestrator health..."
    HEALTHY=false
    for i in $(seq 1 10); do
      if docker exec orc-crewai curl -sf http://localhost:8000/health &>/dev/null; then
        HEALTHY=true
        echo "[deploy] Orchestrator healthy after ${i} attempts"
        break
      fi
      echo "[deploy] Health check attempt ${i}/10 failed, retrying..."
      sleep 10
    done

    if [ "$HEALTHY" = "false" ]; then
      echo "[deploy] ERROR: Orchestrator failed health check -- rolling back to :previous"
      if docker image inspect "${ORCHESTRATOR_IMAGE}:previous" &>/dev/null; then
        docker tag "${ORCHESTRATOR_IMAGE}:previous" "${ORCHESTRATOR_IMAGE}:latest"
        docker compose -f "$COMPOSE_MAIN" up -d --force-recreate orchestrator
      fi
      ORC_EXIT=1
    fi
  else
    echo "[deploy] ERROR: Orchestrator build failed"
    ORC_EXIT=1
  fi
fi

# Chat-UI reload
if [ "$CHATUI_CHANGED" = "true" ]; then
  echo "[deploy] Chat-UI changed -- reloading nginx..."
  if docker exec thepopebot-chat-ui nginx -s reload; then
    echo "[deploy] nginx reloaded"
  else
    echo "[deploy] ERROR: nginx reload failed"
    CHATUI_EXIT=1
  fi
fi

# Thepopebot compose redeploy
if [ "$TPB_COMPOSE_CHANGED" = "true" ]; then
  echo "[deploy] docker-compose.thepopebot.yml changed -- redeploying thepopebot services..."
  if docker compose -f "$COMPOSE_TPB" up -d --remove-orphans; then
    echo "[deploy] Thepopebot stack updated"
  else
    echo "[deploy] ERROR: Thepopebot stack redeploy failed"
    TPB_EXIT=1
  fi
fi

# Update deploy SHA atomically, only if no failures
FINAL_EXIT=$((ORC_EXIT + CHATUI_EXIT + TPB_EXIT))
if [ "$FINAL_EXIT" -eq 0 ]; then
  echo "$NEW_SHA" > "${SHA_FILE}.tmp"
  mv "${SHA_FILE}.tmp" "$SHA_FILE"
  echo "[deploy] .deploy-sha updated to ${NEW_SHA}"
else
  echo "[deploy] Skipping .deploy-sha update due to failures"
fi

echo "[deploy] Done. orc=${ORC_EXIT} chatui=${CHATUI_EXIT} tpb=${TPB_EXIT}"
exit $FINAL_EXIT
