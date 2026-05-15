-- 011_auto_wire_state.sql
-- Phase 4 absorb auto-wire crew tracking. Two tables:
--   hermes_auto_wire_state    -- daily 3/day rate-limit counter (America/Denver day key)
--   hermes_auto_wire_lineage  -- per-branch lineage back to absorb_queue.id

CREATE TABLE IF NOT EXISTS hermes_auto_wire_state (
    day TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    last_branch TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hermes_auto_wire_lineage (
    id SERIAL PRIMARY KEY,
    absorb_queue_id INTEGER NOT NULL REFERENCES absorb_queue(id),
    branch_name TEXT NOT NULL,
    target_path TEXT NOT NULL,
    commit_sha TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    ts_created TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts_pushed TIMESTAMPTZ,
    error TEXT
);

CREATE INDEX IF NOT EXISTS hermes_auto_wire_lineage_aq_idx
    ON hermes_auto_wire_lineage (absorb_queue_id);

COMMENT ON TABLE hermes_auto_wire_state IS
  'Phase 4 absorb auto-wire: per-day rate limit counter. Default cap 3/day America/Denver.';
COMMENT ON TABLE hermes_auto_wire_lineage IS
  'Phase 4 absorb auto-wire: one row per branch shipped or attempted, links back to absorb_queue.id.';
COMMENT ON COLUMN hermes_auto_wire_lineage.status IS
  'pending | pushed | failed';
