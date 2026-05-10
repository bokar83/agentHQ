-- Migration 007: sw_email_log
-- Per-touch send/draft log in orc-postgres for SW/CW/studio pipelines.
-- Answers: "how many T1s went out this week?" without reading Gmail.
-- Run: docker exec orc-postgres psql -U postgres -d postgres -f /migrations/007_sw_email_log.sql

CREATE TABLE IF NOT EXISTS sw_email_log (
    id           BIGSERIAL PRIMARY KEY,
    lead_email   TEXT NOT NULL,
    lead_id      BIGINT,              -- Supabase leads.id (may be NULL for legacy runs)
    touch        INTEGER NOT NULL,    -- 1-5
    pipeline     TEXT NOT NULL,       -- 'sw' | 'cw' | 'studio'
    status       TEXT NOT NULL,       -- 'drafted' | 'sent' | 'failed' | 'dry-run'
    subject      TEXT,
    gmail_id     TEXT,                -- Gmail draft/message ID returned by API
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS sw_email_log_created_at_idx ON sw_email_log (created_at DESC);
CREATE INDEX IF NOT EXISTS sw_email_log_pipeline_touch_idx ON sw_email_log (pipeline, touch, created_at DESC);
