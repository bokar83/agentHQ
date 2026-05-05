# Reserve Works — RW Research Agent v1

## What This Is

A research-only agent that produces weekly wheel strategy candidate lists for
manual review via Telegram. Does not execute trades. Does not select strikes.
Does not act on assignment events.

---

## Current Status

**RW_ENABLED: FALSE (default)**

This agent is staged and ready to deploy but intentionally disabled.

Activation prerequisites:
1. CW Phase 1 unlock ($5K MRR achieved).
2. Carnival purchase complete (liquidity constraint resolved).
3. 8 weeks of paper trading completed with documented trade journal.
4. Minimum 2 simulated assignment events handled end-to-end.
5. $5,000-$10,000 dedicated options capital that is not needed for 12+ months.
6. Boubacar sets RW_ENABLED=true in the .env file on the VPS.

---

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Kill switch: RW_ENABLED env var check |
| `rw_research_agent.py` | CrewAI Agent definition + weekly scan orchestration |
| `rw_screening.py` | Fundamental and options liquidity filters |
| `rw_scoring.py` | Four-dimension scoring (Quality/Liquidity/Risk/Income) |
| `rw_journal_schema.sql` | PostgreSQL tables for watchlist, scan results, trade log |
| `rw_voice_profile.txt` | Conservative family-money analyst voice profile |
| `n8n_trigger_spec.md` | n8n workflow specification for Sunday evening trigger |
| `README.md` | This file |

---

## Deployment Instructions

1. Apply database schema:
   ```bash
   psql $DATABASE_URL -f agents/reserve_works/rw_journal_schema.sql
   ```

2. Populate watchlist (manual step — Boubacar adds initial tickers):
   ```sql
   INSERT INTO rw_watchlist (ticker, sector, notes) VALUES
   ('AAPL', 'Technology', 'Large-cap, liquid options, dividend payer'),
   ('JNJ', 'Healthcare', 'Defensive, consistent earnings, low beta'),
   ('MCD', 'Consumer Discretionary', 'Stable earnings, strong moat');
   ```
   Note: these are examples of the criteria profile, not recommendations.
   Boubacar selects actual tickers based on personal conviction and ongoing research.

3. Set environment variables:
   ```bash
   RW_ENABLED=false     # Keep false until all prerequisites are met
   RW_PAPER_MODE=true   # Always start in paper mode
   ```

4. Build n8n workflow following n8n_trigger_spec.md.

5. When all prerequisites are satisfied, flip the kill switch:
   ```bash
   RW_ENABLED=true
   ```

---

## Test Plan

**Paper mode test (no live capital, safe to run anytime):**
```python
from agents.reserve_works.rw_screening import screen_candidates
from agents.reserve_works.rw_scoring import score_all_candidates

# Minimal test data
candidates = [
    {
        "ticker": "TEST",
        "market_cap_b": 50.0,
        "debt_equity": 0.5,
        "profitable_quarters": 8,
        "days_to_next_earnings": 60,
        "atm_put_oi": 2000,
        "avg_daily_options_volume": 5000,
        "bid_ask_spread_pct": 0.03,
        "beta": 0.85,
        "sector_correlation_to_spy": 0.65,
        "would_own_long_term": True,
        "has_moat_indicator": True,
        "monthly_premium_yield_pct": 0.02,
        "vix_level": 18.0,
        "current_price": 50.0,
    }
]

screened = screen_candidates(candidates)
print(f"Screened: {len(screened)} passed")

scored = score_all_candidates(candidates)
for s in scored:
    print(f"{s.ticker}: {s.total_score}/100 (passed: {s.passed})")
```

---

## Manual vs Automated Boundaries

| Action | Who | Method |
|---|---|---|
| Populate watchlist | Boubacar | Direct SQL INSERT |
| Run weekly scan | Agent (n8n cron) | Automated |
| Review candidates | Boubacar | Telegram notification |
| Select strike and expiration | Boubacar | Manual in brokerage platform |
| Execute trade | Boubacar | Manual in brokerage platform |
| Log trade | Boubacar | SQL INSERT into rw_trade_journal |
| Handle assignment | Boubacar | Manual decision + execution |
| Monthly performance review | Boubacar | Query rw_performance_tracking view |

---

## Integration with select_llm() Routing

The research agent uses:
```python
select_llm("researcher", "moderate")
```

This maps to the existing ROLE_CAPABILITY table in orchestrator/agents.py.
No new model mappings are required. The agent respects the existing two-dimensional
cost gate (capability + max_cost_tier).

---

## Kill Switch

Single config flag: `RW_ENABLED=false` (default).

Effect when false:
- `__init__.py` module-level warning logged.
- `rw_research_agent.run_weekly_scan()` raises RuntimeError immediately.
- n8n workflow Node 2 stops execution.
- No market data fetched. No LLM calls made. No PostgreSQL writes.

To disable at any time: set `RW_ENABLED=false` in the VPS .env file.
The running workflow will respect this on the next trigger. No restart needed.
