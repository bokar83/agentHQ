#!/bin/bash
# scripts/install_reply_scanner_cron.sh
# =====================================
# One-shot installer for the */15-min STOP/reply/bounce scanner on the VPS host.
# Idempotent: re-running does not duplicate the crontab line.
#
# Run on the VPS host (NOT inside the container):
#   bash /root/agentsHQ/scripts/install_reply_scanner_cron.sh
#
# What it does:
#   1. Applies orchestrator/migrations/012_email_suppressions.sql (idempotent)
#   2. Adds */15 cron line if missing
#   3. Smoke-tests the script (one immediate dry-run via docker exec)
#
# Why it lives on the host: per memory rule feedback_gate_systemd_timer_canonical.md
# the autonomous-job loop is host-owned (cron on host, NOT in container).

set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/agentsHQ}"
CRON_LINE='*/15 * * * * docker exec orc-crewai python3 /app/scripts/sync_replies_from_gmail.py >> /var/log/sync_replies.log 2>&1'

echo "==> Applying migration 012_email_suppressions.sql ..."
docker cp "$REPO_DIR/orchestrator/migrations/012_email_suppressions.sql" orc-postgres:/tmp/
docker exec orc-postgres psql -U postgres -d postgres -f /tmp/012_email_suppressions.sql

echo "==> Installing crontab entry (if missing) ..."
TMP=$(mktemp)
crontab -l 2>/dev/null > "$TMP" || true
if grep -F "sync_replies_from_gmail.py" "$TMP" >/dev/null 2>&1; then
    echo "    (already installed, skipping)"
else
    echo "$CRON_LINE" >> "$TMP"
    crontab "$TMP"
    echo "    installed: $CRON_LINE"
fi
rm -f "$TMP"

echo "==> Touching log file ..."
touch /var/log/sync_replies.log
chmod 644 /var/log/sync_replies.log

echo "==> Running one immediate scan (smoke test) ..."
docker exec orc-crewai python3 /app/scripts/sync_replies_from_gmail.py 2>&1 | tail -20

echo ""
echo "Done. Verify with: docker exec orc-postgres psql -U postgres -d postgres -c 'SELECT COUNT(*) FROM email_suppressions;'"
