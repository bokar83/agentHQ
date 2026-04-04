#!/usr/bin/env bash
# system-status.sh — agentsHQ health snapshot
# Usage: bash system-status.sh
# Runs from local machine. Checks VPS container, OpenRouter balance, output file count, last deploy.
# Pipes a summary to Telegram via the existing bot.

set -e

VPS="root@72.60.209.109"
REPO="/root/agentsHQ"

# Load Telegram creds from .env (grep specific vars to avoid sourcing the whole file)
ENV_FILE="$(dirname "$0")/.env"
if [ -f "$ENV_FILE" ]; then
  ORCHESTRATOR_TELEGRAM_BOT_TOKEN=$(grep -m1 '^ORCHESTRATOR_TELEGRAM_BOT_TOKEN=' "$ENV_FILE" | cut -d= -f2-)
  TELEGRAM_CHAT_ID=$(grep -m1 '^TELEGRAM_CHAT_ID=' "$ENV_FILE" | cut -d= -f2-)
fi

# --- Gather data from VPS ---
VPS_DATA=$(ssh "$VPS" bash <<'REMOTE'
  REPO="/root/agentsHQ"
  source $REPO/.env 2>/dev/null || true

  # Container status
  CONTAINER=$(docker inspect --format='{{.State.Status}}' orc-crewai 2>/dev/null || echo "not found")

  # Last deploy (last git pull time)
  LAST_DEPLOY=$(cd $REPO && git log -1 --format="%ar — %s")

  # Output file count
  OUTPUT_COUNT=$(find $REPO/outputs -maxdepth 2 -type f 2>/dev/null | wc -l | tr -d ' ')

  # OpenRouter balance (org credits)
  OR_BALANCE=$(curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    https://openrouter.ai/api/v1/credits 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); \
      bal=d.get('data',{}).get('total_credits',0) - d.get('data',{}).get('total_usage',0); \
      print(f'\${bal:.2f} remaining')" 2>/dev/null \
    || echo "unavailable")

  echo "CONTAINER=$CONTAINER"
  echo "LAST_DEPLOY=$LAST_DEPLOY"
  echo "OUTPUT_COUNT=$OUTPUT_COUNT"
  echo "OR_BALANCE=$OR_BALANCE"
REMOTE
)

# Parse
CONTAINER=$(echo "$VPS_DATA" | grep "^CONTAINER=" | cut -d= -f2-)
LAST_DEPLOY=$(echo "$VPS_DATA" | grep "^LAST_DEPLOY=" | cut -d= -f2-)
OUTPUT_COUNT=$(echo "$VPS_DATA" | grep "^OUTPUT_COUNT=" | cut -d= -f2-)
OR_BALANCE=$(echo "$VPS_DATA" | grep "^OR_BALANCE=" | cut -d= -f2-)

# Container status emoji
if [ "$CONTAINER" = "running" ]; then
  STATUS_ICON="✅"
else
  STATUS_ICON="🔴"
fi

# Build message
MESSAGE="🤖 agentsHQ Status
${STATUS_ICON} Orchestrator: ${CONTAINER}
💰 OpenRouter: ${OR_BALANCE}
📁 Output files: ${OUTPUT_COUNT}
🕐 Last deploy: ${LAST_DEPLOY}"

# Print to terminal
echo ""
echo "$MESSAGE"
echo ""

# Send to Telegram if creds available
if [ -n "$ORCHESTRATOR_TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
  python3 - <<PYEOF
import urllib.request, json, os
token = "$ORCHESTRATOR_TELEGRAM_BOT_TOKEN"
chat_id = "$TELEGRAM_CHAT_ID"
text = """$MESSAGE"""
payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
req = urllib.request.Request(
    f"https://api.telegram.org/bot{token}/sendMessage",
    data=payload,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as r:
    print("Sent to Telegram." if r.status == 200 else f"Telegram error: {r.status}")
PYEOF
else
  echo "(Telegram creds not set — printed to terminal only)"
fi
