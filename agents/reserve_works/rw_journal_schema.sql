-- rw_journal_schema.sql
-- Reserve Works PostgreSQL schema
-- Run against the agentsHQ local Postgres instance (same as db.py conventions).
-- All tables use IF NOT EXISTS for safe re-runs.

-- ─────────────────────────────────────────────────────────────────────────────
-- rw_watchlist: stocks being monitored for wheel strategy candidacy.
-- Populated manually by Boubacar. Agent reads; never writes to this table.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS rw_watchlist (
    id              SERIAL PRIMARY KEY,
    ticker          TEXT NOT NULL UNIQUE,
    sector          TEXT,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS rw_watchlist_active
    ON rw_watchlist (active);


-- ─────────────────────────────────────────────────────────────────────────────
-- rw_scan_results: weekly scan output from rw_research_agent.
-- One row per ticker per scan run. Agent writes; Boubacar reads.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS rw_scan_results (
    id                  SERIAL PRIMARY KEY,
    scan_date           DATE NOT NULL,
    ticker              TEXT NOT NULL,
    total_score         NUMERIC(5,2),
    quality_score       NUMERIC(5,2),
    liquidity_score     NUMERIC(5,2),
    risk_score          NUMERIC(5,2),
    income_score        NUMERIC(5,2),
    passed              BOOLEAN NOT NULL DEFAULT FALSE,
    current_price       NUMERIC(10,2),
    suggested_strike_lo NUMERIC(10,2),
    suggested_strike_hi NUMERIC(10,2),
    monthly_yield_pct   NUMERIC(6,4),
    cash_required       NUMERIC(12,2),
    fail_reasons        TEXT,
    score_notes         JSONB,
    telegram_sent       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS rw_scan_results_date_ticker
    ON rw_scan_results (scan_date, ticker);

CREATE INDEX IF NOT EXISTS rw_scan_results_passed
    ON rw_scan_results (passed, scan_date DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- rw_trade_journal: manual trade log populated by Boubacar.
-- Agent never writes to this table. Boubacar enters trades after manual review.
-- This is the source of truth for performance tracking.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS rw_trade_journal (
    id                  SERIAL PRIMARY KEY,

    -- Position identification
    ticker              TEXT NOT NULL,
    leg_type            TEXT NOT NULL CHECK (leg_type IN ('put', 'call')),
    paper_mode          BOOLEAN NOT NULL DEFAULT TRUE,

    -- Trade entry
    open_date           DATE NOT NULL,
    expiration_date     DATE NOT NULL,
    strike              NUMERIC(10,2) NOT NULL,
    contracts           INTEGER NOT NULL DEFAULT 1,
    premium_per_share   NUMERIC(8,4) NOT NULL,
    total_premium       NUMERIC(12,2) GENERATED ALWAYS AS (premium_per_share * contracts * 100) STORED,
    cash_collateral     NUMERIC(12,2) NOT NULL,
    underlying_price_at_open NUMERIC(10,2),

    -- Trade outcome
    close_date          DATE,
    outcome             TEXT CHECK (outcome IN ('expired', 'assigned', 'called_away', 'closed_early', NULL)),
    underlying_price_at_close NUMERIC(10,2),
    realized_pl         NUMERIC(12,2),
    notes               TEXT,

    -- Metadata
    scan_result_id      INTEGER REFERENCES rw_scan_results(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS rw_trade_journal_ticker_open
    ON rw_trade_journal (ticker, open_date DESC);

CREATE INDEX IF NOT EXISTS rw_trade_journal_paper_mode
    ON rw_trade_journal (paper_mode, open_date DESC);

CREATE INDEX IF NOT EXISTS rw_trade_journal_open_positions
    ON rw_trade_journal (close_date)
    WHERE close_date IS NULL;


-- ─────────────────────────────────────────────────────────────────────────────
-- rw_performance_tracking: monthly performance summary.
-- Populated by a summary function run at month-end, or manually.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS rw_performance_tracking (
    id                      SERIAL PRIMARY KEY,
    period_month            DATE NOT NULL UNIQUE,  -- first day of the month
    paper_mode              BOOLEAN NOT NULL,
    total_premium_collected NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_realized_pl       NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_assignment_losses NUMERIC(12,2) NOT NULL DEFAULT 0,
    trades_opened           INTEGER NOT NULL DEFAULT 0,
    trades_expired_worthless INTEGER NOT NULL DEFAULT 0,
    trades_assigned         INTEGER NOT NULL DEFAULT 0,
    trades_called_away      INTEGER NOT NULL DEFAULT 0,
    avg_monthly_yield_pct   NUMERIC(6,4),
    capital_deployed        NUMERIC(12,2),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS rw_performance_tracking_period
    ON rw_performance_tracking (period_month DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- Helper view: open positions with days-to-expiration
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW rw_open_positions AS
SELECT
    j.id,
    j.ticker,
    j.leg_type,
    j.paper_mode,
    j.open_date,
    j.expiration_date,
    (j.expiration_date - CURRENT_DATE) AS dte,
    j.strike,
    j.contracts,
    j.premium_per_share,
    j.total_premium,
    j.cash_collateral,
    j.underlying_price_at_open,
    j.notes
FROM rw_trade_journal j
WHERE j.close_date IS NULL
ORDER BY j.expiration_date ASC;
