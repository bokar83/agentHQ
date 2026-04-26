-- Migration 006: agent_sessions table
-- Tracks active and historical agent sessions in local Postgres.
-- session_id matches agent_conversation_history.session_id.
-- Survives container restarts; populated by session_store.py.

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id    TEXT PRIMARY KEY,
    agent_name    TEXT NOT NULL DEFAULT 'chat',
    from_number   TEXT,
    channel       TEXT NOT NULL DEFAULT 'telegram',
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    turn_count    INTEGER NOT NULL DEFAULT 0,
    meta          JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_from_number
    ON agent_sessions (from_number, last_active_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_name
    ON agent_sessions (agent_name, last_active_at DESC);
