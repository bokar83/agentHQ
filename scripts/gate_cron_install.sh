#!/bin/bash
# Install gate-agent as a host-side cron job on VPS.
# Run once on VPS host: bash scripts/gate_cron_install.sh
# Gate runs every 60s, reads /root/agentsHQ, git ops work (host has .git + creds).

set -e

CRON_FILE="/etc/cron.d/gate-agent"
REPO="/root/agentsHQ"
LOG="/var/log/gate-agent.log"

cat > "$CRON_FILE" << 'EOF'
# Gate agent -- runs every 60s on VPS host (NOT inside Docker container)
# Merges [READY] branches to main, pushes GitHub, triggers VPS deploy
* * * * * root cd /root/agentsHQ && python3 orchestrator/gate_agent.py >> /var/log/gate-agent.log 2>&1
EOF

chmod 644 "$CRON_FILE"
touch "$LOG"
chmod 644 "$LOG"

echo "Gate cron installed: $CRON_FILE"
echo "Logs: tail -f $LOG"
echo "Test run: cd $REPO && python3 orchestrator/gate_agent.py"
