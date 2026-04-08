#!/bin/bash
set -euo pipefail

TASK="${1:-}"
SESSION_KEY="${2:-}"

if [ -z "$TASK" ]; then
  echo "Usage: dispatch.sh \"<task description>\" [session_key]"
  exit 1
fi

if [ -z "${ORCHESTRATOR_API_KEY:-}" ]; then
  echo "Error: ORCHESTRATOR_API_KEY not set"
  exit 1
fi

ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://orc-crewai:8000}"
CALLBACK_URL="${APP_URL:-}/webhook/agent-complete"

PAYLOAD=$(python3 -c "
import json, sys
task = sys.argv[1]
session_key = sys.argv[2]
callback_url = sys.argv[3]
data = {'task': task, 'callback_url': callback_url}
if session_key:
    data['session_key'] = session_key
print(json.dumps(data))
" "$TASK" "$SESSION_KEY" "$CALLBACK_URL")

echo "Dispatching task to agentsHQ orchestrator..."
echo "Task: $TASK"

RESPONSE=$(curl -s -X POST \
  "${ORCHESTRATOR_URL}/run-async" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${ORCHESTRATOR_API_KEY}" \
  -d "$PAYLOAD")

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'job_id' in data:
    print(f'Job dispatched successfully.')
    print(f'Job ID: {data[\"job_id\"]}')
    print(f'Status: {data.get(\"status\", \"queued\")}')
else:
    print(f'Error: {json.dumps(data, indent=2)}')
    sys.exit(1)
"
