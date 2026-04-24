-- 005_autonomy_memory.sql
-- Phase 1 of autonomy rollout: episodic memory + approval queue.
-- Two additive tables on local Postgres. No backfill. No FK constraints.
--
-- Spec: docs/superpowers/specs/2026-04-24-phase-1-episodic-memory-and-approval-queue-design.md
--
-- Apply on VPS:
--   docker exec -i orc-postgres psql -U postgres -d postgres \
--     < orchestrator/migrations/005_autonomy_memory.sql

CREATE TABLE IF NOT EXISTS approval_queue (
    id                       BIGSERIAL PRIMARY KEY,
    ts_created               TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts_decided               TIMESTAMPTZ,
    crew_name                TEXT NOT NULL,
    proposal_type            TEXT NOT NULL,
    payload                  JSONB NOT NULL,
    telegram_msg_id          BIGINT,
    status                   TEXT NOT NULL DEFAULT 'pending',
    decision_note            TEXT,
    boubacar_feedback_tag    TEXT,
    edited_payload           JSONB,
    task_outcome_id          BIGINT
);

CREATE INDEX IF NOT EXISTS idx_approval_queue_status_ts
    ON approval_queue (status, ts_created DESC);

CREATE INDEX IF NOT EXISTS idx_approval_queue_telegram_msg
    ON approval_queue (telegram_msg_id)
    WHERE telegram_msg_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS task_outcomes (
    id                       BIGSERIAL PRIMARY KEY,
    ts_started               TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts_completed             TIMESTAMPTZ,
    crew_name                TEXT NOT NULL,
    task_signature           TEXT NOT NULL,
    plan_summary             TEXT,
    result_summary           TEXT,
    total_cost_usd           NUMERIC(10,6) NOT NULL DEFAULT 0,
    success                  BOOLEAN,
    approval_queue_id        BIGINT,
    boubacar_feedback        TEXT,
    llm_calls_ids            BIGINT[] NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_task_outcomes_ts
    ON task_outcomes (ts_started DESC);

CREATE INDEX IF NOT EXISTS idx_task_outcomes_crew_ts
    ON task_outcomes (crew_name, ts_started DESC);

CREATE INDEX IF NOT EXISTS idx_task_outcomes_signature
    ON task_outcomes (task_signature);
