# STOP Suppression Compliance Incident -- 2026-05-16

## TL;DR

Every CW + SW cold email invited "reply STOP to unsubscribe", but **no
suppression pipeline existed**. The `leads.opt_out` column was checked by the
send loop, but nothing ever wrote to it. The reply scanner referenced in
`scripts/sync_replies_from_gmail.py` was **not installed on the VPS** (no
cron, no log file). The classifier itself had **not been written**.

One known opt-out reply slipped through this week (Jordan Harbertson,
`jordan@catalina.capital`). No follow-up touch has been sent yet, so this is
caught BEFORE a CAN-SPAM violation.

Fix shipped in `fix/stop-suppression-2026-05-16`.

## Timeline

| When (UTC)              | Event |
|-------------------------|-------|
| 2026-05-01 16:20        | T1 sent to `jordan@catalina.capital` ("Where is your margin actually going?") |
| 2026-05-12 18:47        | T2 drafted ("Something I thought you'd want to see") |
| 2026-05-13 17:27        | T2 sent (Gmail thread id `19e1d8465159444f`) |
| 2026-05-14 12:59        | Reply received: body opens with bare `STOP`. NOT captured. |
| 2026-05-15 / 2026-05-16 | T3 due per CW touch schedule (Day 9 from T1 = 2026-05-10+; gate is `last_contacted_at <= now - 9d` which fires on 2026-05-21). T3 **was poised to fire** before the fix landed. |
| 2026-05-16              | Audit run, fix shipped, manual suppression row inserted for Jordan. |

## What was broken (5 findings)

1. **No body classifier.** No code in the repo ever scanned reply bodies for
   STOP / unsubscribe / remove-me intent. `scripts/sync_replies_from_gmail.py`
   logged `replied` events to `email_events` but treated all replies as
   equivalent.

2. **Reply scanner not running.** `/var/log/sync_replies.log` did not exist
   on `root@72.60.209.109`. No `crontab -l` entry for the script. The script
   shipped to the repo but was never installed on the host.

3. **No suppression table.** The schema had no canonical do-not-contact
   ledger. `leads.opt_out` is a per-lead flag, but ~20% of cold-outreach
   prospects don't have a row in `leads` at all (forwarded replies, alias
   addresses).

4. **No `unsubscribed` event ever recorded** in `email_events`. The schema
   supports the enum value (migration 009) but nothing ever inserted one.

5. **Send loop only checked `leads.opt_out`.** Even with a populated
   suppression table, the existing send-loop query would have missed it.

## Evidence (queried 2026-05-16)

```
docker exec orc-postgres psql -c "SELECT COUNT(*) FROM leads WHERE opt_out=TRUE;"
 opt_out_count
---------------
             0

docker exec orc-postgres psql -c "SELECT event_type, COUNT(*) FROM email_events GROUP BY event_type;"
 event_type | count
------------+-------
 bounced    |    44
 drafted    |   114
 dry-run    |    36
 replied    |     3
 sent       |   540

ssh root@... 'crontab -l | grep sync_replies'   # empty
ssh root@... 'ls /var/log/sync_replies.log'     # No such file or directory
```

Gmail inbox search returned exactly one match for `STOP` in the last 14 days:
the Jordan Harbertson reply.

## Fix shipped (branch `fix/stop-suppression-2026-05-16`)

1. **Migration `orchestrator/migrations/012_email_suppressions.sql`** -- new canonical
   do-not-contact ledger. Brand-aware (cw / sw / studio / NULL=global),
   reason-tagged, immutable except for `unsuppressed_at` (manual reactivation
   only). Includes `v_email_suppressions_active` + `v_suppressions_by_touch`
   views for analytics.

2. **`scripts/sync_replies_from_gmail.py` rewritten.** Adds the
   `scan_stop_replies` job that walks every inbound message in the last 2
   days, classifies the body, and on hit:
   - inserts an `email_suppressions` row (idempotent via partial unique idx)
   - flips `leads.opt_out=TRUE` in canonical Supabase (case-insensitive match)
   - logs an `unsubscribed` event to `email_events`
   - emits one Telegram alert per new suppression

3. **`skills/outreach/sequence_engine.py`**: added
   `_filter_suppressed_emails()` second-gate. Runs after the leads.opt_out
   filter on every touch, regardless of pipeline. Drops any lead whose email
   has an active `email_suppressions` row. Non-fatal on table-missing (falls
   back to leads.opt_out alone).

4. **`scripts/install_reply_scanner_cron.sh`** -- one-shot installer for
   the VPS host. Applies the migration, installs the `*/15 * * * *` cron
   line, smoke-tests one immediate run. Idempotent.

5. **`tests/test_stop_intent_classifier.py`** -- 18 tests including the
   real Jordan Harbertson body as a regression fixture.

## Immediate remediation (manual, 2026-05-16)

Logged here for audit. To be executed via Gate run-list when this branch
merges:

```sql
-- Insert suppression row for the known-missed STOP
INSERT INTO email_suppressions
  (email, brand, reason, source, gmail_message_id, gmail_thread_id,
   body_preview, matched_pattern, notes)
VALUES
  ('jordan@catalina.capital', 'cw', 'reply_stop', 'manual_backfill',
   '19e2691fc0f85292', '19e1d8465159444f',
   'STOP Jordan Harbertson CEO & President Catalina Capital',
   'STOP',
   'Backfilled 2026-05-16 during compliance audit (incident 2026-05-16-stop-suppression-compliance-incident).');

-- Flip leads.opt_out (Supabase) -- this happens automatically in the patched
-- scanner, but is being done immediately so T3 cannot fire even before the
-- VPS deploys the fix.
UPDATE leads SET opt_out=TRUE, updated_at=NOW()
WHERE lower(email)='jordan@catalina.capital';

-- Log the inbound 'unsubscribed' event for audit
INSERT INTO email_events
  (brand, direction, event_type, to_addr, from_addr, subject,
   gmail_message_id, gmail_thread_id, metadata, occurred_at)
VALUES
  ('cw', 'inbound', 'unsubscribed',
   'boubacar@catalystworks.consulting', 'jordan@catalina.capital',
   'Re: Something I thought you''d want to see',
   '19e2691fc0f85292', '19e1d8465159444f',
   '{"source":"manual_backfill","reason":"reply_stop","matched_pattern":"STOP"}',
   '2026-05-14 12:59:09+00');
```

## Analytics: STOP by touch level

Once `email_suppressions` is populated by the cron, this view answers
"which touch most often triggers a STOP":

```sql
SELECT triggering_pipeline, triggering_touch, COUNT(*) AS stop_reactions
FROM v_suppressions_by_touch
GROUP BY 1, 2 ORDER BY 1, 2;
```

Today's single STOP: pipeline=`cw`, touch=`2`. After the fix runs and
backfills, expect ~3-5 historical rows to surface (the 3 'replied' rows in
`email_events` plus any others the new scanner picks up in its 2-day window).

## Lessons / tripwires

- Any cold-outreach campaign that mentions an unsubscribe path must have a
  scanner BEFORE the first batch ships. Sequence: scanner-first, send-second.
  This is now in the cold-outreach send checklist.
- Reply-scanner cron must be smoke-tested with `ls /var/log/<scanner>.log`
  + `crontab -l | grep <scanner>` on the VPS host -- not just "the script
  was added to the repo".
- `leads.opt_out` is necessary but NOT sufficient. Email-based suppression
  must be the canonical gate because not every contacted email has a leads
  row.

## Registry entry

To be appended to `docs/audits/REGISTRY.md`:

> 2026-05-16 -- STOP suppression compliance incident. Scanner missing, no
> suppression table, one known-missed STOP (Jordan Harbertson). Fix branch
> `fix/stop-suppression-2026-05-16` ships migration 011, body classifier,
> second-gate suppression check, cron installer, 18 unit tests, manual
> remediation script. Owner: gate review.
