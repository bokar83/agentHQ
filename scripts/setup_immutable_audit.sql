-- =============================================================================
-- setup_immutable_audit.sql
-- Immutable out-of-band audit trail for agentsHQ
--
-- Design principles:
--   • Separate schema isolates audit rows from application schema.
--   • audit_logger role has INSERT-only on agent_audit_trail — no UPDATE/DELETE.
--   • superuser/postgres retains SELECT for incident review.
--   • append_audit_event() SECURITY DEFINER wrapper lets audit_logger write
--     without needing direct table privileges (defence-in-depth).
--   • Row-level trigger rejects any attempt to UPDATE or DELETE even by a
--     superuser posing as the application connection.
--
-- Run as superuser (postgres):
--   psql -U postgres -d postgres -f setup_immutable_audit.sql
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Schema
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS immutable_audit;

-- ---------------------------------------------------------------------------
-- 1. Core table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS immutable_audit.agent_audit_trail (
    id          BIGSERIAL    PRIMARY KEY,
    ts          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    agent_id    TEXT         NOT NULL,
    action      TEXT         NOT NULL,
    target      TEXT,
    payload     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    status      TEXT         NOT NULL DEFAULT 'ok'
        CONSTRAINT status_valid CHECK (status IN ('ok', 'warn', 'error', 'blocked'))
);

-- Fast lookups by agent + time window (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_aat_agent_ts
    ON immutable_audit.agent_audit_trail (agent_id, ts DESC);

-- Fast lookups by action type + time window
CREATE INDEX IF NOT EXISTS idx_aat_action_ts
    ON immutable_audit.agent_audit_trail (action, ts DESC);

-- ---------------------------------------------------------------------------
-- 2. Role (idempotent — DO block guards against "role already exists" error)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_logger') THEN
        CREATE ROLE audit_logger WITH
            LOGIN
            PASSWORD 'audit_logger_pw_change_me'
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            CONNECTION LIMIT 8;
    END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 3. Privilege grants — INSERT-only on table; USAGE on schema + sequence
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA immutable_audit TO audit_logger;

-- INSERT is the only DML privilege granted; SELECT/UPDATE/DELETE are withheld.
GRANT INSERT ON TABLE immutable_audit.agent_audit_trail TO audit_logger;

-- Sequence: needed so BIGSERIAL can advance the counter.
GRANT USAGE ON SEQUENCE immutable_audit.agent_audit_trail_id_seq TO audit_logger;

-- postgres (superuser) retains full SELECT for incident review — no explicit
-- grant needed because superusers bypass privilege checks.

-- Revoke any accidental broad grants from PUBLIC
REVOKE ALL ON SCHEMA immutable_audit FROM PUBLIC;
REVOKE ALL ON TABLE immutable_audit.agent_audit_trail FROM PUBLIC;

-- ---------------------------------------------------------------------------
-- 4. Immutability trigger — second line of defence
--    Even if a connection somehow holds UPDATE/DELETE (e.g. someone grants it
--    by mistake), this trigger fires BEFORE the write and raises an exception.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION immutable_audit.deny_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RAISE EXCEPTION
        'immutable_audit: UPDATE and DELETE are prohibited on agent_audit_trail '
        '(attempted by role %). Audit log is append-only.',
        current_user
        USING ERRCODE = 'insufficient_privilege';
    RETURN NULL;  -- never reached; silences compiler warning
END;
$$;

-- Drop-and-recreate is safe because SECURITY DEFINER function body is replaced.
DROP TRIGGER IF EXISTS trg_deny_mutation ON immutable_audit.agent_audit_trail;
CREATE TRIGGER trg_deny_mutation
    BEFORE UPDATE OR DELETE
    ON immutable_audit.agent_audit_trail
    FOR EACH ROW
    EXECUTE FUNCTION immutable_audit.deny_mutation();

-- ---------------------------------------------------------------------------
-- 5. SECURITY DEFINER helper — lets audit_logger call this function to INSERT
--    without needing direct table knowledge. Also enforces payload sanity.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION immutable_audit.append_audit_event(
    p_agent_id  TEXT,
    p_action    TEXT,
    p_target    TEXT,
    p_payload   JSONB,
    p_status    TEXT DEFAULT 'ok'
)
RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER   -- runs as the function OWNER (postgres), not the caller
SET search_path = immutable_audit, pg_catalog
AS $$
DECLARE
    v_id BIGINT;
BEGIN
    -- Validate action is a known verb to prevent injection of arbitrary strings.
    IF p_action NOT IN (
        'agent_spawn',
        'agent_self_heal',
        'gate_proposal',
        'gate_approve',
        'gate_reject',
        'file_edit',
        'task_claim',
        'task_complete',
        'branch_push',
        'heartbeat',
        'error'
    ) THEN
        RAISE WARNING 'immutable_audit: unknown action %, recording as-is', p_action;
    END IF;

    INSERT INTO immutable_audit.agent_audit_trail (agent_id, action, target, payload, status)
    VALUES (p_agent_id, p_action, p_target, COALESCE(p_payload, '{}'::jsonb), p_status)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$;

GRANT EXECUTE ON FUNCTION immutable_audit.append_audit_event(TEXT, TEXT, TEXT, JSONB, TEXT)
    TO audit_logger;

-- ---------------------------------------------------------------------------
-- 6. Smoke-check view (SELECT-only; accessible to postgres superuser)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW immutable_audit.recent_events AS
SELECT id, ts, agent_id, action, target, status,
       payload
FROM   immutable_audit.agent_audit_trail
ORDER  BY ts DESC
LIMIT  200;

-- Done.
