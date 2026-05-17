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
# L-R5 Conversion Scorecard chains automatically after L-R4 Confirm & Commit
# via on_complete hook in lr4_triad_lock.json (event-driven, not time-driven).
0 16 * * 6 root docker exec orc-crewai python /app/orchestrator/scripts/ritual_cron_dispatch.py lr4_triad_lock >> /var/log/lighthouse-rituals.log 2>&1

# Sun 18:00 MDT (DST = 00:00 UTC Mon) - L-R9 Sunday Digest auto-send.
# Carve-out: self-recipient only (boubacar@cw + bokar83@gmail), cw OAuth From-line,
# kill-switch (data/lighthouse-digest-skip.flag) + idempotency-flag enforced.
# DST drift: 01:00 UTC Mon during standard time (Nov-Mar) -- adjust then.
0 0 * * 1 root docker exec orc-crewai python /app/orchestrator/scripts/lighthouse_digest_send.py >> /var/log/lighthouse-rituals.log 2>&1
EOF

chmod 644 "$CRON_FILE"
touch "$LOG"
chmod 644 "$LOG"

echo "Lighthouse ritual cron installed: $CRON_FILE"
echo "Logs: tail -f $LOG"
echo "Manual test: docker exec orc-crewai python /app/orchestrator/scripts/ritual_cron_dispatch.py lr4_triad_lock"
