-- Atlas M26: milestones source-of-truth table
CREATE TABLE IF NOT EXISTS milestones (
    id          SERIAL PRIMARY KEY,
    codename    TEXT NOT NULL,
    mid         TEXT NOT NULL,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'queued',
    blocked_by  TEXT,
    eta         TEXT,
    notes       TEXT,
    shipped_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(codename, mid)
);
CREATE INDEX IF NOT EXISTS milestones_codename_idx ON milestones(codename);
CREATE INDEX IF NOT EXISTS milestones_status_idx   ON milestones(status);
COMMENT ON TABLE milestones IS 'Atlas M26: live roadmap milestone source of truth. Written by Telegram /shipped, webchat, and agents via flip_milestone().';
COMMENT ON COLUMN milestones.codename IS 'atlas|echo|compass|studio|harvest';
COMMENT ON COLUMN milestones.mid      IS 'Milestone ID as shown in roadmap: M1, M2.5b, R1, etc';
COMMENT ON COLUMN milestones.status   IS 'shipped|active|blocked|queued|deferred|descoped';
