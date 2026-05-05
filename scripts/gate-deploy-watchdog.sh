#!/usr/bin/env bash
# Watchdog: if gate wrote a deploy trigger, run orc_rebuild.sh
TRIGGER=/root/agentsHQ/data/gate_deploy_trigger
LOGFILE=/var/log/gate-deploy-watchdog.log

if [ ! -f "$TRIGGER" ]; then
  exit 0
fi

echo "$(date -u): trigger found, starting rebuild" >> "$LOGFILE"
rm -f "$TRIGGER"
bash /root/agentsHQ/scripts/orc_rebuild.sh >> "$LOGFILE" 2>&1
echo "$(date -u): rebuild exit $?" >> "$LOGFILE"
