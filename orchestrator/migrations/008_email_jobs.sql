CREATE TABLE IF NOT EXISTS email_jobs (
    id         SERIAL PRIMARY KEY,
    to_addr    TEXT NOT NULL,
    subject    TEXT NOT NULL,
    body_text  TEXT NOT NULL,
    send_at    TIMESTAMPTZ NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    sent_at    TIMESTAMPTZ,
    error_msg  TEXT
);
