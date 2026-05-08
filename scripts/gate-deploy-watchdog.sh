#!/usr/bin/env bash
# Watchdog: if gate wrote a deploy trigger, run orc_rebuild.sh
TRIGGER=/root/agentsHQ/data/gate_deploy_trigger
LOGFILE=/var/log/gate-deploy-watchdog.log

if [ ! -f "$TRIGGER" ]; then
  exit 0
fi

echo "$(date -u): trigger found, checking deploy type" >> "$LOGFILE"
rm -f "$TRIGGER"
cd /root/agentsHQ
if ! git fetch origin main --quiet 2>> "$LOGFILE"; then
    echo "$(date -u): git fetch failed -- falling back to full rebuild" >> "$LOGFILE"
    bash /root/agentsHQ/scripts/orc_rebuild.sh >> "$LOGFILE" 2>&1
    echo "$(date -u): deploy exit $?" >> "$LOGFILE"
    exit 0
fi
if git diff HEAD..origin/main -- orchestrator/requirements.txt | grep -q .; then
    echo "$(date -u): requirements.txt changed -- full rebuild" >> "$LOGFILE"
    bash /root/agentsHQ/scripts/orc_rebuild.sh >> "$LOGFILE" 2>&1
else
    echo "$(date -u): code-only deploy -- docker compose up" >> "$LOGFILE"
    git pull && docker compose up -d orchestrator >> "$LOGFILE" 2>&1
fi
echo "$(date -u): deploy exit $?" >> "$LOGFILE"
