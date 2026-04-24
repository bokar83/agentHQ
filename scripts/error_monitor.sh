#!/bin/bash
# error_monitor.sh - Smoke alarm for the orc-crewai container.
#
# Runs on the VPS host via cron every 15 minutes. Scans docker logs for
# the last 15 minutes, counts Traceback + [ERROR] lines (excluding the
# allow-list of benign messages), sends a Telegram alert if the count
# crosses ALERT_THRESHOLD. Rate-limited via a state file so a sustained
# spike does not spam.
#
# No LLM, no crew. This is the dumb layer shipped Day 1.
# The full Concierge crew (LLM analysis + propose fix) lands later.
#
# Install: cron entry on VPS host (not inside container):
#   */15 * * * * /root/agentsHQ/scripts/error_monitor.sh >> /var/log/error_monitor.log 2>&1
#
# Requires: jq, curl. Reads TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID from
# /root/agentsHQ/.env.

set -eu

CONTAINER="${ERROR_MONITOR_CONTAINER:-orc-crewai}"
WINDOW_MIN="${ERROR_MONITOR_WINDOW:-15}"
THRESHOLD="${ERROR_MONITOR_THRESHOLD:-5}"
COOLDOWN_MIN="${ERROR_MONITOR_COOLDOWN:-60}"
STATE_FILE="${ERROR_MONITOR_STATE:-/root/agentsHQ/data/error_monitor_state.txt}"
ENV_FILE="${ERROR_MONITOR_ENV:-/root/agentsHQ/.env}"

# Load token + chat id from .env without leaking into logs.
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    TELEGRAM_TOKEN=$(grep -m1 '^ORCHESTRATOR_TELEGRAM_BOT_TOKEN=' "$ENV_FILE" | cut -d= -f2-)
    TELEGRAM_CHAT=$(grep -m1 '^TELEGRAM_CHAT_ID=' "$ENV_FILE" | cut -d= -f2-)
else
    echo "error_monitor: env file $ENV_FILE not found"
    exit 0
fi

if [ -z "${TELEGRAM_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT:-}" ]; then
    echo "error_monitor: missing TELEGRAM_TOKEN or TELEGRAM_CHAT in env"
    exit 0
fi

# Pull recent logs. docker logs writes errors to stderr too; combine.
LOG_TEXT=$(docker logs --since="${WINDOW_MIN}m" "$CONTAINER" 2>&1 || true)
if [ -z "$LOG_TEXT" ]; then
    exit 0
fi

# Filter errors. Exclude known-benign lines.
ERRORS=$(echo "$LOG_TEXT" | grep -E 'Traceback \(most recent call last\):|\[ERROR\]|^ERROR:|CRITICAL:' \
    | grep -v 'griot_morning_tick: Notion fetch failed' \
    | grep -v 'griot_scheduler_tick: occupancy fetch failed' \
    | grep -v 'self_test episodic_memory write failed' \
    || true)
COUNT=$(echo "$ERRORS" | grep -c . || true)

if [ "$COUNT" -lt "$THRESHOLD" ]; then
    exit 0
fi

# Cooldown check. State file stores last alert unix epoch.
NOW=$(date +%s)
LAST=0
if [ -f "$STATE_FILE" ]; then
    LAST=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
fi
ELAPSED=$((NOW - LAST))
COOLDOWN_SEC=$((COOLDOWN_MIN * 60))
if [ "$ELAPSED" -lt "$COOLDOWN_SEC" ]; then
    echo "error_monitor: $COUNT errors but cooldown active ($((COOLDOWN_SEC - ELAPSED))s remaining)"
    exit 0
fi

# Build alert body. Keep under Telegram's 4096 char limit.
SAMPLES=$(echo "$ERRORS" | head -5 | cut -c 1-250)
MSG=$(cat <<EOF
Error monitor alert
Container: $CONTAINER
Errors in last ${WINDOW_MIN} min: $COUNT (threshold: $THRESHOLD)

Sample lines:
$SAMPLES

Cooldown: next alert in ${COOLDOWN_MIN} min minimum.
Inspect: ssh root@agentshq.boubacarbarry.com 'docker logs orc-crewai --tail 100'
EOF
)

# Send via Telegram API. urlencode the message.
curl -s --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT}" \
    --data-urlencode "text=${MSG}" > /dev/null

# Update state on successful-or-not-send; we do not want to spam even if
# the send fails intermittently.
mkdir -p "$(dirname "$STATE_FILE")"
echo "$NOW" > "$STATE_FILE"

echo "error_monitor: alert sent ($COUNT errors)"
