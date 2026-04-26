-- Migration 007: agent_config table
-- Key-value runtime config store for agentsHQ.
-- Overrides env vars without requiring a container restart.
-- Populated by agent_config.py set_config().

CREATE TABLE IF NOT EXISTS agent_config (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note       TEXT
);
