-- 002_media_generations.sql
-- Per-generation ledger for Kai (kie.ai) media outputs.
-- One row per generation attempt (including failed retries).
-- Populated by orchestrator/kie_media.py _log_to_supabase().
--
-- Apply with:
--   docker exec -i agentshq-postgres-1 psql -U postgres -d postgres < orchestrator/migrations/002_media_generations.sql
-- Or against Supabase SQL editor directly.

CREATE TABLE IF NOT EXISTS media_generations (
    id                  BIGSERIAL PRIMARY KEY,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    task_type           TEXT NOT NULL,
    prompt              TEXT NOT NULL,
    model_used          TEXT,
    rank_used           INT,
    drive_file_id       TEXT,
    drive_url           TEXT,
    local_path          TEXT,
    state               TEXT NOT NULL DEFAULT 'success',
    attempts_json       JSONB,
    quarter             TEXT,
    linked_content_id   TEXT,
    notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_media_generations_created  ON media_generations (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_generations_model    ON media_generations (model_used, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_generations_state    ON media_generations (state, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_generations_content  ON media_generations (linked_content_id) WHERE linked_content_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_media_generations_quarter  ON media_generations (quarter);
