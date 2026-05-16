#!/bin/bash
# Install Saturday Lighthouse rituals as host-side cron on VPS.
# Run once on VPS: bash scripts/lighthouse_rituals_cron_install.sh
#
# Cron fires inside the orc-crewai container so the Python env, env-vars,
# and bot token are already wired. 16:00 UTC = 10:00 MDT during DST.

set -e

CRON_FILE="/etc/cron.d/lighthouse-rituals"
LOG="/var/log/lighthouse-rituals.log"

cat > "$CRON_FILE" << 'EOF'
# Lighthouse Saturday rituals - dispatched via orc-crewai container.
# 16:00 UTC = 10:00 MDT (DST); 17:00 UTC = 10:00 MST (standard time).
# Adjust by 1 hour twice a year if DST drift matters.
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Sat 10:00 MDT - L-R4 Triad Lock
0 16 * * 6 root docker exec orc-crewai python /app/scripts/ritual_cron_dispatch.py lr4_triad_lock >> /var/log/lighthouse-rituals.log 2>&1

# Sat 10:30 MDT - L-R5 Conversion Scorecard
30 16 * * 6 root docker exec orc-crewai python /app/scripts/ritual_cron_dispatch.py lr5_conversion_scorecard >> /var/log/lighthouse-rituals.log 2>&1
EOF

chmod 644 "$CRON_FILE"
touch "$LOG"
chmod 644 "$LOG"

echo "Lighthouse ritual cron installed: $CRON_FILE"
echo "Logs: tail -f $LOG"
echo "Manual test: docker exec orc-crewai python /app/scripts/ritual_cron_dispatch.py lr4_triad_lock"
