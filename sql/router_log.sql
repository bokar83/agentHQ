-- router_log: telemetry for every classify_task() call
-- Run this once in the Supabase SQL editor for project jscucboftaoaphticqci.
-- The orchestrator writes to this table fire-and-forget; missing table = no-op.

CREATE TABLE IF NOT EXISTS router_log (
    id              BIGSERIAL PRIMARY KEY,
    message         TEXT        NOT NULL,
    task_type       TEXT        NOT NULL,
    crew            TEXT        NOT NULL,
    used_llm        BOOLEAN     NOT NULL DEFAULT FALSE,
    router_version  TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS router_log_created_at_idx ON router_log (created_at DESC);
CREATE INDEX IF NOT EXISTS router_log_task_type_idx  ON router_log (task_type);
