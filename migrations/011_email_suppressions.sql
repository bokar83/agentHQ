-- Migration 011: email_suppressions
-- Canonical do-not-contact ledger. One row per (email, brand) the moment a
-- prospect asks to stop. Sequence engine joins against this BEFORE sending any
-- touch. Lead-agnostic on purpose: STOP from an address that is not in our
-- leads table (forwarded reply, alias, etc.) must still suppress us.
--
-- Sources:
--   * reply scanner: body matches STOP / UNSUBSCRIBE / "remove me" / "do not
--     contact" / "stop emailing" (case-insensitive, word-bounded)
--   * manual entry: docker exec orc-postgres psql -c "INSERT ..."
--   * future: webhook from any inbound provider
--
-- Once a row is inserted it is NEVER deleted. Reactivation requires explicit
-- human action (set unsuppressed_at, ledger remains for compliance audit).
--
-- Run on VPS:
--   docker cp migrations/011_email_suppressions.sql orc-postgres:/tmp/
--   docker exec orc-postgres psql -U postgres -d postgres -f /tmp/011_email_suppressions.sql

CREATE TABLE IF NOT EXISTS email_suppressions (
    id                  BIGSERIAL PRIMARY KEY,
    email               TEXT NOT NULL,
    brand               TEXT,                          -- 'cw' | 'sw' | 'studio' | NULL = global
    reason              TEXT NOT NULL DEFAULT 'reply_stop',
    source              TEXT NOT NULL DEFAULT 'reply_scanner',
    gmail_message_id    TEXT,
    gmail_thread_id     TEXT,
    body_preview        TEXT,
    matched_pattern     TEXT,                          -- regex/keyword that triggered classification
    lead_id             BIGINT,                        -- optional cross-ref
    suppressed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unsuppressed_at     TIMESTAMPTZ,                   -- non-NULL = manually re-enabled
    notes               TEXT,

    CONSTRAINT email_suppressions_brand_chk CHECK (
        brand IS NULL OR brand IN ('cw','sw','gw','studio')
    ),
    CONSTRAINT email_suppressions_reason_chk CHECK (
        reason IN ('reply_stop','reply_unsubscribe','reply_remove',
                   'manual','bounce_hard','spam_complaint','other')
    )
);

-- One active suppression per (email, brand). Re-running scanner is idempotent.
-- Partial unique allows historical rows (with unsuppressed_at set) to coexist
-- with a new active row for the same email.
CREATE UNIQUE INDEX IF NOT EXISTS email_suppressions_active_unique_idx
    ON email_suppressions (lower(email), COALESCE(brand, 'global'))
    WHERE unsuppressed_at IS NULL;

CREATE INDEX IF NOT EXISTS email_suppressions_email_idx
    ON email_suppressions (lower(email));
CREATE INDEX IF NOT EXISTS email_suppressions_suppressed_at_idx
    ON email_suppressions (suppressed_at DESC);

-- Convenience view: only currently-active suppressions
CREATE OR REPLACE VIEW v_email_suppressions_active AS
SELECT id, email, brand, reason, source, gmail_message_id, gmail_thread_id,
       matched_pattern, lead_id, suppressed_at, notes
FROM email_suppressions
WHERE unsuppressed_at IS NULL;

-- Per-touch breakdown of STOP reactions (analytics for "which touch caused
-- the most opt-outs"). Joins email_suppressions to outbound sent events to
-- learn what touch the prospect last received before unsubscribing.
CREATE OR REPLACE VIEW v_suppressions_by_touch AS
WITH last_outbound AS (
    SELECT DISTINCT ON (to_addr)
        to_addr,
        pipeline,
        occurred_at,
        metadata->>'touch' AS touch
    FROM email_events
    WHERE direction = 'outbound'
      AND event_type IN ('sent','drafted')
    ORDER BY to_addr, occurred_at DESC
)
SELECT
    s.id,
    s.email,
    s.brand,
    s.reason,
    s.suppressed_at,
    o.pipeline AS triggering_pipeline,
    o.touch AS triggering_touch,
    o.occurred_at AS triggering_sent_at
FROM email_suppressions s
LEFT JOIN last_outbound o ON lower(o.to_addr) = lower(s.email)
WHERE s.unsuppressed_at IS NULL;
