-- Migration 010: constraints_ai capture columns + idempotency
-- Adds the columns needed for the Constraints AI demo capture follow-up
-- pipeline (3-touch sequence at Day 0/2/4). Additive only — no DROP, no
-- UPDATE of existing rows, no DEFAULT backfill.
--
-- Context: 2026-05-12 — site demo capture form has been silently broken
-- since 2026-05-11 (front-end POSTs to n8n /capture which returns 404).
-- Fix routes the capture through agentsHQ FastAPI POST /api/constraints-capture
-- instead. That endpoint writes a row to Supabase diagnostic_captures
-- (durable artifact) AND inserts a row in leads with sequence_pipeline=
-- 'constraints_ai'. The new columns below carry the demo context into the
-- leads row so the 3 templates (templates/email/constraints_ai_t{1,2,3}.py)
-- can substitute pain_text / response_constraint / response_action.
--
-- Idempotency: front-end generates a UUIDv4 capture_idempotency_key per
-- submit. Unique partial index makes duplicate submits a silent no-op at
-- the DB layer rather than relying on the FastAPI handler to remember.
--
-- Run:
--   docker cp migrations/010_constraints_ai_captures.sql orc-postgres:/tmp/
--   docker exec orc-postgres psql -U postgres -d postgres -f /tmp/010_constraints_ai_captures.sql

ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS pain_text TEXT,
  ADD COLUMN IF NOT EXISTS response_constraint TEXT,
  ADD COLUMN IF NOT EXISTS response_action TEXT,
  ADD COLUMN IF NOT EXISTS capture_idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS leads_capture_idempotency_uniq
  ON leads (capture_idempotency_key)
  WHERE capture_idempotency_key IS NOT NULL;
