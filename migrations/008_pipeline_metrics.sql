-- Migration 008: pipeline_metrics canonical schema + sw_email_log.recycle column
-- =====================================================================
-- Per-step instrumentation for the daily morning_runner pipeline, plus a
-- recycle flag on sw_email_log so analytics can distinguish primary outbound
-- from Step 5b T-advance recycle volume without changing the status enum.
--
-- Run: docker exec orc-postgres psql -U postgres -d postgres -f /migrations/008_pipeline_metrics.sql
--
-- Schema notes:
--   pipeline_metrics is also auto-created on import by
--   signal_works/pipeline_metrics.py with the same column set
--   (run_date + ts + step + counters + reason). This migration is the
--   canonical declaration; columns match the writer so log_step() works
--   whether or not the writer ran first.

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id          BIGSERIAL PRIMARY KEY,
    run_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    step        TEXT NOT NULL,
    attempted   INTEGER NOT NULL DEFAULT 0,
    succeeded   INTEGER NOT NULL DEFAULT 0,
    skipped     INTEGER NOT NULL DEFAULT 0,
    reason      TEXT,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes: run_date+step for daily rollups, step+created_at DESC for
-- "last N runs of step X" queries (per migration spec 2026-05-12).
CREATE INDEX IF NOT EXISTS pipeline_metrics_run_date_step_idx
    ON pipeline_metrics (run_date, step);
CREATE INDEX IF NOT EXISTS pipeline_metrics_step_created_at_idx
    ON pipeline_metrics (step, created_at DESC);

-- sw_email_log.recycle: boolean flag set by morning_runner Step 5b after a
-- recycle pass. Default FALSE so all existing rows and all normal sends keep
-- their current semantics. Recycle analytics filter on `AND recycle = TRUE`;
-- dashboards filtering on status IN ('sent','drafted') stay unchanged.
ALTER TABLE sw_email_log
    ADD COLUMN IF NOT EXISTS recycle BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS sw_email_log_recycle_idx
    ON sw_email_log (recycle, created_at DESC)
    WHERE recycle = TRUE;
