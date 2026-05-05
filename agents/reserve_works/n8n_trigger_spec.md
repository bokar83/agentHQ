# n8n Trigger Specification — Reserve Works Weekly Scan
# Reserve Works Decision Package
# Generated: 2026-05-05

---

## Overview

This n8n workflow triggers the RW research agent weekly and routes candidate
output to Telegram for Boubacar's manual review. No automatic trade execution
occurs at any stage.

---

## Prerequisites

Before implementing this workflow:
1. RW_ENABLED=true in environment (currently false, set after all prerequisites met).
2. rw_journal_schema.sql applied to local PostgreSQL.
3. rw_watchlist table populated with at least 5 initial tickers manually.
4. Boubacar has completed 8 weeks of paper trading and all Tier 0 gates.

---

## Trigger

**Type:** Schedule (Cron)
**Schedule:** Sunday 7:00 PM Mountain Time (01:00 UTC Monday)
**Rationale:** Sunday evening gives time to review before Monday market open.
US equity markets are closed Sunday; all data is end-of-week snapshots.

**Cron expression:** `0 1 * * 1` (1:00 AM UTC every Monday)

---

## Workflow Nodes

### Node 1: Cron Trigger
- Type: Cron
- Expression: `0 1 * * 1`
- Timezone: America/Denver

---

### Node 2: Kill Switch Check
- Type: IF
- Condition: `$env.RW_ENABLED === "true"`
- On FALSE: Send Telegram message "RW scan skipped: RW_ENABLED=false" to Boubacar.
  Stop workflow.
- On TRUE: Continue.

---

### Node 3: Read Watchlist from PostgreSQL
- Type: PostgreSQL
- Operation: SELECT
- Query:
  ```sql
  SELECT ticker FROM rw_watchlist WHERE active = true ORDER BY ticker;
  ```
- Credentials: local PostgreSQL (same connection as agentsHQ db.py)
- Output: list of ticker strings

If 0 tickers returned: Send Telegram message "RW scan: watchlist is empty. Add tickers
to rw_watchlist table." Stop workflow.

---

### Node 4: Fetch Market Data (Placeholder — Manual Fill Required)
- Type: HTTP Request (or manual data fetch node)

**IMPORTANT:** This node requires a market data API. Options:
- Alpha Vantage (free tier, limited): fundamental data, no options chains.
- Unusual Whales API (paid): options-specific, OI, IV, volume.
- Yahoo Finance via yfinance Python library (unofficial, free): adequate for paper mode.
- Polygon.io (paid tier): best for systematic use with options data.

For paper trading phase: use manual data entry or yfinance library via Python node.
For live trading phase: Polygon.io Starter plan ($29/month) is recommended.

**Data required per ticker:**
- current_price: float
- market_cap_b: float (billions)
- debt_equity: float
- profitable_quarters: int (last 4 quarters, count how many were profitable)
- days_to_next_earnings: int
- atm_put_oi: int (open interest on nearest-expiry, 10-15% OTM put)
- avg_daily_options_volume: int
- bid_ask_spread_pct: float
- beta: float
- monthly_premium_yield_pct: float (estimated from put premium / (strike * 100))
- vix_level: float (current VIX)

---

### Node 5: Run RW Research Agent (Python)
- Type: Execute Command or Python node
- Command: invoke rw_research_agent.run_weekly_scan() with watchlist and market data
- Environment variables required: RW_ENABLED, RW_PAPER_MODE, OPENROUTER_API_KEY
- Output: list of candidate dicts with telegram_text field

---

### Node 6: Save Scan Results to PostgreSQL
- Type: PostgreSQL
- Operation: INSERT for each candidate into rw_scan_results
- Include scan_date, ticker, all scores, telegram_sent=false

---

### Node 7: Format Telegram Message
- Type: Function (transform node)
- Logic: join all candidate telegram_text outputs with separator lines
- If no candidates passed: message = "RW weekly scan complete. No candidates cleared
  screening this week. No action needed."
- Always append: "Total watchlist tickers scanned: [n]. Candidates cleared: [m]."

---

### Node 8: Send to Telegram
- Type: Telegram
- Chat: Boubacar's personal Telegram ID (same as agentsHQ notifier.py target)
- Message: formatted output from Node 7
- On success: update rw_scan_results SET telegram_sent=true for this scan_date

---

### Node 9: Error Handler (attached to all nodes)
- On any error: send Telegram message "RW scan failed at [node name]: [error]"
- Do NOT retry automatically. Retry requires manual investigation.

---

## Manual Approval Gate

After Telegram notification, Boubacar reviews and:
- If interested in a candidate: reviews the candidate's option chain in brokerage platform.
- Decides strike, expiration, and number of contracts manually.
- Executes the trade manually in the brokerage platform.
- Logs the trade in rw_trade_journal via direct PostgreSQL INSERT or a Telegram-triggered
  log command (future feature).

There is no automated path from scan result to trade execution. This is by design.

---

## Kill Switch (Single Config Flag)

Set `RW_ENABLED=false` in the environment (VPS .env file) to disable all RW activity:
- Node 2 catches this and stops the workflow before any market data is fetched.
- rw_research_agent.py raises RuntimeError immediately if RW_ENABLED=false.
- No partial scans are possible.

To re-enable: set `RW_ENABLED=true`. The workflow resumes on the next scheduled trigger.

---

## Cost Ceiling

The RW agent uses the "researcher/moderate" LLM tier from select_llm().
Estimated per-scan cost: $0.01-$0.05 depending on watchlist size and model routing.
Weekly cost at 10 tickers: approximately $0.20-$0.50/month.
This is within any reasonable cost ceiling.

---

## Paper Mode vs Live Mode

`RW_PAPER_MODE=true` (default):
- All Telegram notifications are prefixed with [PAPER].
- Scan results in rw_scan_results are marked as paper mode.
- No behavioral difference; it is a labeling flag for the journal.

`RW_PAPER_MODE=false` (only after Tier 0 prerequisites complete):
- Notifications are prefixed with [LIVE - MANUAL APPROVAL REQUIRED].
- No other behavioral change. Live execution is always manual.
