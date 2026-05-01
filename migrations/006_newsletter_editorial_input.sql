CREATE TABLE IF NOT EXISTS newsletter_editorial_input (
  week_start_date date PRIMARY KEY,
  reply_text text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT NOW(),
  chat_id text NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_newsletter_editorial_input_received_at
  ON newsletter_editorial_input (received_at);
