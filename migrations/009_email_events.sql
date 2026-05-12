-- Migration 009: email_events
-- Append-only canonical ledger of every email-related event across CW/SW/GW.
-- Replaces the patchwork of sw_email_log (draft-only), email_jobs (unused),
-- and "ground-truth via Gmail API search" with one immutable source of truth.
--
-- Design notes:
--   * INSERT-only per feedback_immutable_audit_pattern.md. No UPDATE or DELETE.
--   * One row per event. A T1 send that later gets a reply -> two rows.
--   * (brand, gmail_message_id, event_type) is the natural dedup key for
--     idempotent backfill. Unique index enforces it.
--   * occurred_at = when the event happened in the real world (Gmail internalDate)
--   * recorded_at = when we wrote it to this table (for audit of pipeline lag)
--
-- Run: docker cp migrations/009_email_events.sql orc-postgres:/tmp/
--      docker exec orc-postgres psql -U postgres -d postgres -f /tmp/009_email_events.sql

CREATE TABLE IF NOT EXISTS email_events (
    id                BIGSERIAL PRIMARY KEY,
    brand             TEXT NOT NULL,                     -- 'cw' | 'sw' | 'gw' | 'studio'
    pipeline          TEXT,                              -- 'cold_teardown' | 'sequence_t1' | 'sequence_t2' ... optional sub-pipeline
    direction         TEXT NOT NULL,                     -- 'outbound' | 'inbound'
    event_type        TEXT NOT NULL,                     -- 'sent' | 'drafted' | 'delivered' | 'opened' | 'clicked' | 'replied' | 'bounced' | 'spam' | 'unsubscribed' | 'failed'
    to_addr           TEXT NOT NULL,
    from_addr         TEXT NOT NULL,
    subject           TEXT,
    gmail_message_id  TEXT,                              -- Gmail message id (NOT thread id)
    gmail_thread_id   TEXT,                              -- conversation grouping
    body_preview      TEXT,                              -- first ~200 chars; useful on replies
    lead_id           BIGINT,                            -- nullable; not all events have an upstream lead row
    metadata          JSONB,                             -- provider-specific extras (touch number, gmb_opener, etc.)
    occurred_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT email_events_brand_chk      CHECK (brand IN ('cw','sw','gw','studio','unknown')),
    CONSTRAINT email_events_direction_chk  CHECK (direction IN ('outbound','inbound')),
    CONSTRAINT email_events_event_type_chk CHECK (event_type IN
        ('sent','drafted','delivered','opened','clicked','replied',
         'bounced','spam','unsubscribed','failed','dry-run'))
);

-- Hot path indexes
CREATE INDEX IF NOT EXISTS email_events_brand_dir_type_idx
    ON email_events (brand, direction, event_type, occurred_at DESC);
CREATE INDEX IF NOT EXISTS email_events_thread_idx
    ON email_events (gmail_thread_id);
CREATE INDEX IF NOT EXISTS email_events_to_addr_idx
    ON email_events (to_addr);
CREATE INDEX IF NOT EXISTS email_events_occurred_idx
    ON email_events (occurred_at DESC);

-- Dedup key for idempotent backfill: same brand + gmail message id + event
-- can only be inserted once. Allows the backfill to be re-run safely.
-- gmail_message_id may be NULL for synthetic events (failed sends, dry-runs);
-- partial index handles that.
CREATE UNIQUE INDEX IF NOT EXISTS email_events_dedup_idx
    ON email_events (brand, gmail_message_id, event_type)
    WHERE gmail_message_id IS NOT NULL;

-- Dashboard view: per-brand funnel
DROP VIEW IF EXISTS v_email_funnel;
CREATE VIEW v_email_funnel AS
SELECT
    brand,
    COUNT(*) FILTER (WHERE event_type='sent')          AS sent,
    COUNT(*) FILTER (WHERE event_type='drafted')       AS drafted,
    COUNT(DISTINCT to_addr) FILTER (WHERE event_type='sent') AS unique_recipients,
    COUNT(*) FILTER (WHERE event_type='opened')        AS opened,
    COUNT(*) FILTER (WHERE event_type='replied')       AS replied,
    COUNT(*) FILTER (WHERE event_type='bounced')       AS bounced,
    COUNT(*) FILTER (WHERE event_type='clicked')       AS clicked,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE event_type='replied')
      / NULLIF(COUNT(*) FILTER (WHERE event_type='sent'), 0),
      2
    ) AS reply_rate_pct,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE event_type='bounced')
      / NULLIF(COUNT(*) FILTER (WHERE event_type='sent'), 0),
      2
    ) AS bounce_rate_pct,
    MIN(occurred_at) FILTER (WHERE event_type='sent')  AS first_sent_at,
    MAX(occurred_at) FILTER (WHERE event_type='sent')  AS last_sent_at
FROM email_events
GROUP BY brand;

-- Rolling 14-day window — answers "what's volume right now"
DROP VIEW IF EXISTS v_email_funnel_14d;
CREATE VIEW v_email_funnel_14d AS
SELECT
    brand,
    COUNT(*) FILTER (WHERE event_type='sent')          AS sent_14d,
    COUNT(*) FILTER (WHERE event_type='replied')       AS replied_14d,
    COUNT(*) FILTER (WHERE event_type='bounced')       AS bounced_14d,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE event_type='replied')
      / NULLIF(COUNT(*) FILTER (WHERE event_type='sent'), 0),
      2
    ) AS reply_rate_14d_pct
FROM email_events
WHERE occurred_at > NOW() - INTERVAL '14 days'
GROUP BY brand;
