-- 010_scout_state.sql
-- Per-source state for absorb_scout adapters: cursor for incremental fetch,
-- mute flag for auto-mute when Phase 0 fail-rate goes high, simple counters
-- for the auto-mute decision and the dashboard.

CREATE TABLE IF NOT EXISTS scout_state (
    source              TEXT PRIMARY KEY,
    cursor              TEXT,
    last_run_at         TIMESTAMPTZ,
    last_enqueued_count INTEGER NOT NULL DEFAULT 0,
    muted               BOOLEAN NOT NULL DEFAULT FALSE,
    muted_reason        TEXT,
    muted_at            TIMESTAMPTZ,
    total_enqueued      INTEGER NOT NULL DEFAULT 0,
    total_phase0_fail   INTEGER NOT NULL DEFAULT 0
);

COMMENT ON TABLE scout_state IS
  'One row per scout source (reddit-r-ClaudeAI, github-trending-ai-agents, etc.). Auto-mute fires when total_phase0_fail / total_enqueued > 0.8 with total_enqueued >= 25.';

COMMENT ON COLUMN scout_state.cursor IS
  'Source-specific incremental marker: RSS guid, HN max_id, github stargazers_count snapshot, etc.';
