-- 003_router_log.sql
-- Create the router_log table expected by orchestrator/router.py.
--
-- Context: router._router_log_worker() dequeues routing decisions and tries to
-- INSERT them into router_log. Until this migration runs, those writes fail
-- silently (the worker catches the exception, logs at DEBUG, and drops the row).
--
-- Apply on VPS:
--   docker cp orchestrator/migrations/003_router_log.sql \
--     orc-postgres:/tmp/003_router_log.sql
--   docker exec orc-postgres psql -U postgres -f /tmp/003_router_log.sql

CREATE TABLE IF NOT EXISTS router_log (
    id             bigserial PRIMARY KEY,
    ts             timestamptz NOT NULL DEFAULT now(),
    message        text        NOT NULL,
    task_type      text,
    crew           text,
    used_llm       boolean,
    router_version text
);

CREATE INDEX IF NOT EXISTS idx_router_log_ts ON router_log (ts DESC);
CREATE INDEX IF NOT EXISTS idx_router_log_task_type ON router_log (task_type);
