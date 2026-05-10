# Session Handoff - SW Email Log + Harvest Diagnosis - 2026-05-10

## TL;DR

Built and deployed `sw_email_log` table in orc-postgres. Wired `sequence_engine.py` to write a row on every T1-T5 draft/send/fail/dry-run. Diagnosed and cleared the profitablepenny/scribd harvest mystery — not a harvest bug. 165 SW T1s drafted this week confirmed via Supabase.

## What was built / changed

- `migrations/007_sw_email_log.sql` — new table in orc-postgres
- `skills/outreach/sequence_engine.py` — `_mark_sent()` + `_log_to_orc_postgres()` added
- Migration run: `docker cp` + `docker exec orc-postgres psql ... -f /tmp/007_sw_email_log.sql`
- Container restarted: `docker compose up -d orchestrator`
- Commit: `91825b1`

## sw_email_log schema

```sql
id           BIGSERIAL PRIMARY KEY
lead_id      BIGINT              -- Supabase leads.id
lead_email   TEXT NOT NULL
touch        INTEGER NOT NULL    -- 1-5
pipeline     TEXT NOT NULL       -- 'sw' | 'cw' | 'studio'
status       TEXT NOT NULL       -- 'drafted' | 'sent' | 'failed' | 'dry-run'
subject      TEXT
gmail_id     TEXT                -- Gmail draft/message ID
created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

Indexes: `created_at DESC`, `(pipeline, touch, created_at DESC)`

Query to check weekly volume going forward:
```sql
SELECT pipeline, touch, status, COUNT(*), DATE_TRUNC('day', created_at) as day
FROM sw_email_log
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY pipeline, touch, status, day
ORDER BY day DESC, pipeline, touch;
```

## SW volume confirmed (Supabase, before this logging was in place)

All-time:
- sequence_touch=1: 217 leads, last email_drafted_at 2026-05-08
- sequence_touch=2: 25 leads, last 2026-04-30
- sequence_touch=0 with email_drafted_at: 174 (old scrape_google_maps_leads inline path)

Last 7 days: **165 T1 drafts** (all touch=1, email_drafted_at in last 7 days)

## Harvest mystery resolved: profitablepenny + scribd

**Not a harvest bug.** Root cause: `enrichment_tool.py` runs Hunter.io domain search on **CW Apollo leads** (not SW GMB leads). "Profitable Penny Accounting" is a legit Apollo CW lead — its website `profitablepenny.com` hit Hunter.io. `es.scribd.com` same pattern. These appear in the orchestrator.log under `signal_works.hunter_client` but they are enrichment-path calls, not SW Serper/GMB calls.

The SW harvest (`topup_leads.py` + `lead_scraper.py` + `expansion_ladder.py`) only queries known niches: dental, hvac, roofing, plumbing, chiropractic, pediatric dentist, electrical, landscaping, auto repair, veterinary, physical therapy, cleaning service — in specific US/CA cities. It cannot produce profitablepenny/scribd.

No fix needed in the niche filter. **Confirmed not a bug.**

## What is NOT done (explicit)

- **M18 HALO** — not started. Target 50 traces by 2026-05-18.
- **Monday VPS cron** — morning_runner runs from `/etc/cron.d/signal-works-morning` (systemd-based per notes), not session-dependent. Confirm cron is still active.
- **CW enrichment Hunter credits** — `enrichment_tool.py` burns Hunter credits on Apollo company domains like profitablepenny.com. Not harmful (Hunter returns "no email") but wastes credits. Low priority; acceptable for now.
- **T2-T5 volume** — only 25 T2s all-time. Pipeline is young. First T2 window opens Day 3 after T1. With 165 T1s this week, T2 wave hits Mon-Tue next week.

## Files changed this session

- `migrations/007_sw_email_log.sql`
- `skills/outreach/sequence_engine.py`

## Commits

- `91825b1` — feat(sw-pipeline): add sw_email_log + wire sequence_engine
