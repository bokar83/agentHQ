-- Migration 008: pipeline_metrics
-- Per-step instrumentation for the daily morning_runner pipeline.
-- Answers: "yesterday CW sequence ran on 15 leads, 7 succeeded, 8 skipped
-- with reason='thin_text'" via SQL instead of tail-grepping logs.
--
-- Run: docker exec orc-postgres psql -U postgres -d postgres -f /migrations/008_pipeline_metrics.sql
--
-- Reconciliation note (2026-05-12):
--   signal_works/pipeline_metrics.py auto-creates a similar table on import
--   with a slightly different schema (run_date DATE + ts TIMESTAMPTZ instead
--   of just created_at). This migration is the canonical declaration per
--   agent-spec 2026-05-12. If both exist, the schemas are compatible at the
--   columns the writer touches (step, attempted, succeeded, skipped, reason).
--   The next pipeline_metrics.py edit should align column names; until then
--   reads should use whichever columns the deployed _ensure_tables() created.

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id          BIGSERIAL PRIMARY KEY,
    step        TEXT NOT NULL,
    attempted   INTEGER,
    succeeded   INTEGER,
    skipped     INTEGER,
    reason      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS pipeline_metrics_step_created_at_idx
    ON pipeline_metrics (step, created_at DESC);
