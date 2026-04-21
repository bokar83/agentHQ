-- 001_llm_calls.sql
-- Per-call LLM ledger. One row per OpenRouter completion.
-- Populated by orchestrator/usage_logger.py via OpenRouter /api/v1/generation.
-- Apply on local VPS Postgres (the same DB as council_runs and conversation history).
--
-- Apply with:
--   docker exec -i agentshq-postgres-1 psql -U postgres -d postgres < orchestrator/migrations/001_llm_calls.sql

CREATE TABLE IF NOT EXISTS llm_calls (
    id                   BIGSERIAL PRIMARY KEY,
    generation_id        TEXT UNIQUE NOT NULL,
    ts                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    project              TEXT,
    agent_name           TEXT,
    task_type            TEXT,
    crew_name            TEXT,
    session_key          TEXT,
    council_run_id       TEXT,
    model                TEXT NOT NULL,
    tokens_prompt        INT NOT NULL DEFAULT 0,
    tokens_completion    INT NOT NULL DEFAULT 0,
    tokens_cached_read   INT NOT NULL DEFAULT 0,
    tokens_cached_write  INT NOT NULL DEFAULT 0,
    cost_usd             NUMERIC(10,6) NOT NULL DEFAULT 0,
    latency_ms           INT,
    finish_reason        TEXT,
    error                TEXT
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_ts          ON llm_calls (ts DESC);
CREATE INDEX IF NOT EXISTS idx_llm_calls_project_ts  ON llm_calls (project, ts DESC);
CREATE INDEX IF NOT EXISTS idx_llm_calls_agent_ts    ON llm_calls (agent_name, ts DESC);
CREATE INDEX IF NOT EXISTS idx_llm_calls_council     ON llm_calls (council_run_id) WHERE council_run_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_llm_calls_session     ON llm_calls (session_key, ts DESC) WHERE session_key IS NOT NULL;
