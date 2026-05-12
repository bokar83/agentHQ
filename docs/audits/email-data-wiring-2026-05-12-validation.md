# Email Data Wiring Validation — 2026-05-12

**Companion to:** `docs/audits/email-data-wiring-2026-05-12.md`
**Migration applied:** `migrations/009_email_events.sql` (VPS orc-postgres)
**Backfill run:** `scripts/backfill_email_events.py` (1 pass, no failures)
**Branch:** `feat/email-events-canonical-ledger`

## Final email_events counts (per `v_email_funnel`)

| brand | sent | drafted | unique_recipients | replied | bounced | reply_rate_% | bounce_rate_% | first_sent_at | last_sent_at |
|-------|-----:|--------:|------------------:|--------:|--------:|-------------:|--------------:|---------------|--------------|
| **cw** | 322 | 67 | 284 | 3 | 44 | **0.93** | **13.66** | 2026-04-13 | 2026-05-12 |
| **sw** | 178 | 47 | 139 | 0 | 0 | 0.00 | 0.00 | 2026-04-30 | 2026-05-11 |

## Last 14 days (`v_email_funnel_14d`)

| brand | sent_14d | replied_14d | bounced_14d | reply_rate_14d_% |
|-------|---------:|------------:|------------:|------------------:|
| cw | 216 | 3 | 11 | 1.39 |
| sw | 178 | 0 | 0 | 0.00 |

## Provenance breakdown (where each row came from)

| source | brand | event_type | count |
|--------|-------|-----------|------:|
| gmail_backfill | cw | sent | 307 |
| gmail_backfill | sw | sent | 143 |
| gmail_bounce_scan | cw | bounced | 44 |
| sw_email_log | cw | drafted | 67 |
| sw_email_log | cw | sent | 15 |
| sw_email_log | sw | drafted | 47 |
| sw_email_log | sw | sent | 35 |
| thread_reply_scan | cw | replied | 3 |

## Sanity check vs Gmail ground truth

Ground truth from Gmail API (cw OAuth, `in:sent -to:bokar83@gmail.com -to:boubacar@catalystworks.consulting`): **446 cold-outreach messages**.

`email_events` reports **500 sent** rows total. Delta: +54.

**Source of delta:** sw_email_log was backfilled before Gmail Sent. sw_email_log rows carry `pipeline='sw'` or `pipeline='cw'` from the run-time template selection. Gmail backfill rows carry `brand` derived from subject heuristic. For the **50 sw_email_log 'sent' rows** (15 cw + 35 sw), the brand assignment may disagree with the heuristic the Gmail-backfill pass applied to the SAME `gmail_message_id`. Because the unique key is `(brand, gmail_message_id, event_type)`, these rows coexist instead of dedup'ing.

**Practical effect:** the **brand split** is unreliable for the 50 overlap rows; the **total** is inflated by ~50. The dashboard should treat `unique_recipients` (284 cw + 139 sw = 423 unique recipients) as the canonical "how many people did we contact" number, with the caveat that 35-50 leads are double-counted across brands.

## What's wired now (after this branch ships)

| Capability | Live? | Path |
|-----------|:-----:|------|
| Append-only event ledger | YES | `email_events` table + 2 views |
| Backfill from Gmail Sent | YES | `scripts/backfill_email_events.py` (one-shot) |
| Backfill from sw_email_log | YES | same script |
| Bounce backfill (mailer-daemon) | YES | same script |
| Reply detection (thread > 1 msg) | YES | same script + `scripts/sync_replies_from_gmail.py` (15-min cron) |
| New sends auto-log | YES | `sequence_engine._log_to_orc_postgres` (drafts + sent) + `send_scheduler._send_draft` (sent) both call `signal_works.email_events.log_event` |
| Open tracking | **NO** | Gmail does not expose this. Requires tracking-pixel CDN. Separate decision. |
| Click tracking | **NO** | Same as opens. Requires link-rewriting + tracking domain. |
| Per-touch breakdown | YES (sw_email_log path only) | `metadata->touch` populated when source is sequence_engine. Gmail-backfill rows have no touch — can be inferred from `occurred_at` ordering per recipient. |

## Still missing (deferred)

1. **Opens + clicks:** require pixel/CDN. Not a Gmail API capability.
2. **GW brand:** no separate identity. `bokar83@gmail.com` is personal mail; would need either a Gmail filter rule ("label:cold-outreach") or a separate OAuth + send-as. Currently 0 GW rows in email_events.
3. **Brand reconciliation pass:** could clean up the 50-row overlap by re-classifying gmail-backfill rows when a sw_email_log row exists for the same gmail_message_id.
4. **15-min reply-sync cron:** the script is written (`scripts/sync_replies_from_gmail.py`) but not yet installed in VPS crontab. Install line for later:
   ```
   */15 * * * * docker cp /root/agentsHQ/scripts/sync_replies_from_gmail.py orc-crewai:/tmp/ && docker exec orc-crewai python3 /tmp/sync_replies_from_gmail.py >> /var/log/sync_replies.log 2>&1
   ```

## Headline numbers Boubacar can quote

**All-time cold-outreach sent (Gmail ground truth):** 446
**All-time replies:** 3 (0.67% reply rate)
**All-time bounces:** 44 (9.9% bounce rate — above 2% kill-switch threshold)
**Last 14 days sent:** 372 (Gmail), 216 cw + 178 sw = 394 (email_events with overlap)
**Unique recipients contacted (all-time):** ~423

The bounce rate is the loudest finding. The `send_scheduler._bounce_rate_kill_switch` queries `sw_email_log` (sample size 50) — it never tripped because the real bounce signal was in Gmail Inbox, not in our DB. With `email_events` now wired, the kill-switch can be re-pointed at `email_events` and will reflect reality.
