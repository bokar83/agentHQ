-- ============================================================
-- BOUBACAR ORCHESTRATOR — DATABASE SETUP
-- Run once after containers are started
-- Creates all tables needed by all workflows
-- ============================================================

-- Thread memory: persistent conversation per WhatsApp contact
CREATE TABLE IF NOT EXISTS n8n_chat_histories (
  id          SERIAL PRIMARY KEY,
  session_id  TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content     TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Every WhatsApp message in and out — permanent archive
CREATE TABLE IF NOT EXISTS conversation_archive (
  id              SERIAL PRIMARY KEY,
  timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  from_number     TEXT NOT NULL,
  message_id      TEXT,
  message_text    TEXT,
  direction       TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
  is_parallel     BOOLEAN DEFAULT FALSE,
  task_type       TEXT,
  model_used      TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Task queue for task manager
CREATE TABLE IF NOT EXISTS task_queue (
  id           SERIAL PRIMARY KEY,
  task_id      TEXT UNIQUE NOT NULL,
  from_number  TEXT NOT NULL,
  task_text    TEXT NOT NULL,
  task_type    TEXT,
  status       TEXT DEFAULT 'pending'
                 CHECK (status IN ('pending','running','complete','failed')),
  result       TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Auto-SOP change log
CREATE TABLE IF NOT EXISTS sop_changelog (
  id             SERIAL PRIMARY KEY,
  timestamp      TIMESTAMPTZ DEFAULT NOW(),
  trigger_text   TEXT,
  update_content TEXT,
  github_path    TEXT
);

-- Daily security audit trail
CREATE TABLE IF NOT EXISTS security_events (
  id               SERIAL PRIMARY KEY,
  report_date      DATE NOT NULL DEFAULT CURRENT_DATE,
  total_failed     INTEGER DEFAULT 0,
  current_banned   INTEGER DEFAULT 0,
  suspicious_ports INTEGER DEFAULT 0,
  status           TEXT,
  raw_report       TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_session    ON n8n_chat_histories(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_session_ts ON n8n_chat_histories(session_id, id ASC);
CREATE INDEX IF NOT EXISTS idx_conv_from       ON conversation_archive(from_number);
CREATE INDEX IF NOT EXISTS idx_conv_ts         ON conversation_archive(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status    ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_security_date   ON security_events(report_date DESC);

-- Confirm
SELECT 'Tables created: ' || string_agg(table_name, ', ' ORDER BY table_name)
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'n8n_chat_histories','conversation_archive',
    'task_queue','sop_changelog','security_events'
  );
