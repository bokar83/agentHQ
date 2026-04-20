CREATE TABLE IF NOT EXISTS inbound_lead_enrichment (
  email           TEXT PRIMARY KEY,
  first_booking   TEXT NOT NULL,
  enriched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_booking    TEXT NOT NULL,
  last_meeting_at TIMESTAMPTZ,
  status          TEXT NOT NULL CHECK (status IN ('enriched', 'partial', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_inbound_lead_enrichment_enriched_at
  ON inbound_lead_enrichment (enriched_at);
