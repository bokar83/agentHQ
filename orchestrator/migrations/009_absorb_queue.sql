-- 009_absorb_queue.sql
-- Ingress queue for the absorb_crew agent. Distinct from approval_queue:
-- approval_queue is the human-review queue. absorb_queue is the agent's
-- inbox of artifacts to evaluate. Big-surface PROCEED verdicts get pushed
-- from absorb_queue into approval_queue for human ack; everything else
-- writes silently to docs/reviews/absorb-log.md on host fs.

CREATE TABLE IF NOT EXISTS absorb_queue (
    id              SERIAL PRIMARY KEY,
    ts_received     TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts_processed    TIMESTAMPTZ,
    source          TEXT NOT NULL,
    url             TEXT NOT NULL,
    submitted_by    TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    artifact_kind   TEXT,
    verdict         TEXT,
    leverage        TEXT,
    placement       TEXT,
    dossier         JSONB,
    raw_content     TEXT,
    error           TEXT,
    approval_queue_id INTEGER REFERENCES approval_queue(id)
);

CREATE INDEX IF NOT EXISTS absorb_queue_status_idx
    ON absorb_queue (status, ts_received);
CREATE INDEX IF NOT EXISTS absorb_queue_url_idx
    ON absorb_queue (url);

COMMENT ON COLUMN absorb_queue.source IS 'telegram | cc | scout-x | scout-reddit | scout-gh | scout-hn';
COMMENT ON COLUMN absorb_queue.status IS 'pending | processing | done | failed';
COMMENT ON COLUMN absorb_queue.verdict IS 'PROCEED | ARCHIVE-AND-NOTE | DONT_PROCEED';
COMMENT ON COLUMN absorb_queue.placement IS 'enhance | extend | new_skill | new_tool | new_agent | satellite | replace_existing | archive';
