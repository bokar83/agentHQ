-- 004_autonomous_flag.sql
-- Adds the `autonomous` flag and `guard_decision` tag to the per-call ledger.
-- Autonomous-crew spend and guard outcomes are trackable separately from
-- user-initiated spend.
--
-- Context: Phase 0 of the autonomy rollout. See
-- docs/superpowers/specs/2026-04-23-phase-0-autonomy-safety-rails-design.md
--
-- Apply on VPS:
--   docker exec -i agentshq-postgres-1 psql -U postgres -d postgres \
--     < orchestrator/migrations/004_autonomous_flag.sql

ALTER TABLE llm_calls
    ADD COLUMN IF NOT EXISTS autonomous BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE llm_calls
    ADD COLUMN IF NOT EXISTS guard_decision TEXT;
