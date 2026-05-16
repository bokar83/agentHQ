# STOP-Reply 30-Day Backfill Audit — boubacar@catalystworks.consulting

Date: 2026-05-16
Auditor: agent (Claude general-purpose subagent)
Scope: past 30 days (2026-04-16 -> 2026-05-16) of inbound mail to cw OAuth account

## Scope + Method

- Authenticated via cw OAuth `/app/secrets/gws-oauth-credentials-cw.json` in orc-crewai container.
- Gmail API `users.messages.list` with `q="newer_than:30d in:inbox"`. Full pagination.
- Each match fetched with `format=metadata` and `format=full` for body scan.
- Regex case-insensitive: `\bSTOP\b`, "unsubscribe", "remove me", "opt out", "do not (e?)mail", "take me off", "no longer interested".
- Cross-referenced matches against `email_suppressions` table on orc-postgres.

## Findings

**Inbox messages scanned (30d):** 15

**STOP-style regex matches:** 3
- 1 genuine hard opt-out (Jordan Harbertson)
- 2 false positives (Google Workspace marketing footer "unsubscribe" links, not human opt-outs)

**`email_suppressions` table state on VPS:** does NOT exist yet. Branch `fix/stop-suppression-2026-05-16` (commits d0b58f2c + b457ddba) has not been merged to main or deployed. Verified on main at e1197a4.

## Match Table

| sender_email | thread_date | subject | snippet | already_captured |
|---|---|---|---|---|
| jordan@catalina.capital | 2026-05-14 06:59 MDT | Re: Something I thought you'd want to see | "STOP -- Jordan Harbertson, CEO & President, Catalina Capital" | N (table missing) |
| googleworkspace-noreply@google.com | 2026-05-14 | Reach new customers with up to $1500 in Google Ads credit | Marketing footer "unsubscribe" link — NOT a human opt-out | N/A (false positive) |
| workspace-noreply@google.com | 2026-05-13 | Bring your business to Google Maps and Search | Marketing footer "unsubscribe" link — NOT a human opt-out | N/A (false positive) |

## Jordan Harbertson Confirmation

Confirmed present in inbox. Single-word "STOP" reply at 2026-05-14 06:59 MDT to subject "Re: Something I thought you'd want to see" from `jordan@catalina.capital`. Hard opt-out — unambiguous. This is the STOP-reply Boubacar visually saw this week.

## Proposed INSERT SQL

Run only after `fix/stop-suppression-2026-05-16` is merged and migration 012 applied to orc-postgres. Verify schema matches before executing.

```sql
INSERT INTO email_suppressions (email, reason, captured_at, source)
VALUES (
    'jordan@catalina.capital',
    'STOP',
    '2026-05-14 12:59:09+00',  -- 06:59 MDT = 12:59 UTC
    'manual_audit_2026-05-16'
)
ON CONFLICT (email) DO NOTHING;
```

## Anomalies

- Migration table `email_suppressions` does not exist on production yet. Branch `fix/stop-suppression-2026-05-16` has not landed. Until merged + `docker compose restart orchestrator`, every STOP-reply (including Jordan's) is uncaptured by definition. This is in-flight state, not a missed capture.
- Inbox volume unusually low (15 msgs/30d). Consistent with cold outreach being predominantly outbound + replies routed to `signal@` alias forwarding here.
- Token fetch + Gmail API clean. No auth failures.

## Net Finding

**Zero missed STOP-replies beyond the one Boubacar already visually confirmed.** Jordan Harbertson is the only human hard opt-out in the last 30 days. Once migration 012 deploys, the single INSERT above backfills the suppression list cleanly.

## Recommended next actions

1. Gate review + merge of branch `fix/stop-suppression-2026-05-16`. HIGH_RISK gate (per CLAUDE.md edits) — Telegram approval required.
2. VPS deploy: `git pull && docker compose restart orchestrator` (volume-mounted).
3. Run `scripts/install_reply_scanner_cron.sh` to install ongoing STOP-reply scanner.
4. Execute the INSERT SQL above to backfill Jordan.
5. Verify `_filter_suppressed_emails` excludes Jordan from any upcoming T3 send before 2026-05-21 (when his sequence's T3 would fire).
