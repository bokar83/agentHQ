#!/bin/bash
set -euo pipefail

SESSION_KEY="${1:-}"
SUMMARY="${2:-}"
NOTIFY="${3:-}"

if [ -z "$SESSION_KEY" ] || [ -z "$SUMMARY" ]; then
  echo "Usage: sync.sh \"<session_key>\" \"<summary>\" [notify]"
  echo "  session_key — Telegram chat_id or project-scoped key"
  echo "  summary     — What happened in this browser session"
  echo "  notify      — Pass 'notify' to send a Telegram ping"
  exit 1
fi

if [ -z "${ORCHESTRATOR_API_KEY:-}" ]; then
  echo "Error: ORCHESTRATOR_API_KEY not set"
  exit 1
fi

ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://orc-crewai:8000}"
NOTIFY_FLAG="false"
if [ "${NOTIFY:-}" = "notify" ]; then
  NOTIFY_FLAG="true"
fi

PAYLOAD=$(python3 -c "
import json, sys
data = {
    'session_key': sys.argv[1],
    'summary': sys.argv[2],
    'source': 'browser',
    'notify_telegram': sys.argv[3] == 'true'
}
print(json.dumps(data))
" "$SESSION_KEY" "$SUMMARY" "$NOTIFY_FLAG")

echo "Syncing browser session to agentsHQ orchestrator..."
echo "Session key: $SESSION_KEY"
echo "Summary length: ${#SUMMARY} chars"

RESPONSE=$(curl -s -X POST \
  "${ORCHESTRATOR_URL}/sync-session" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${ORCHESTRATOR_API_KEY}" \
  -d "$PAYLOAD")

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('success'):
    chars = data.get('chars_written', 0)
    key = data.get('session_key', '?')
    print(f'Session synced successfully.')
    print(f'Session key: {key}')
    print(f'Characters written: {chars}')
    print('Telegram can now pick up this conversation with full context.')
else:
    print(f'Error: {json.dumps(data, indent=2)}')
    sys.exit(1)
"
