#!/usr/bin/env bash
# deploy.sh — One-command VPS deploy for agentsHQ orchestrator
# Usage: bash deploy.sh
# Runs from local machine. Pulls latest, rebuilds, force-recreates orchestrator container.

set -e

VPS="root@72.60.209.109"
REPO="/root/agentsHQ"

echo "=== agentsHQ Deploy ==="
echo ""

# Step 1: push local changes if ahead of origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "unknown")

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "[1/4] Pushing local commits to GitHub..."
  git push origin main
else
  echo "[1/4] Local is in sync with GitHub — skipping push"
fi

# Step 2: pull on VPS
echo "[2/4] Pulling on VPS..."
ssh "$VPS" "cd $REPO && git pull origin main && echo '    pulled: \$(git log --oneline -1)'"

# Step 3: rebuild and recreate orchestrator
echo "[3/4] Rebuilding orchestrator container..."
ssh "$VPS" "cd $REPO && docker compose build orchestrator 2>&1 | tail -5"
ssh "$VPS" "cd $REPO && docker compose up -d --force-recreate orchestrator && echo '    container restarted'"

# Step 4: health check
echo "[4/4] Waiting for health check..."
sleep 5
HEALTH=$(ssh "$VPS" "curl -s http://localhost:8000/ 2>/dev/null || echo 'no response'")
echo "    response: $HEALTH"

echo ""
echo "=== Deploy complete ==="
ssh "$VPS" "cd $REPO && git log --oneline -1"
