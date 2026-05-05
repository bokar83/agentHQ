"""
rw_screening.py — Stock universe filtering for Reserve Works.

Applies fundamental and options-liquidity filters to produce a candidate
list suitable for the wheel strategy.

What this module does:
- Filter by market cap (large-cap only, >= $10B).
- Filter by options open interest (minimum liquidity threshold).
- Filter out upcoming earnings within the earnings_blackout_days window.
- Apply basic fundamental quality checks.

What this module does NOT do:
- Recommend strike prices.
- Execute trades.
- Access brokerage APIs.

All output is a list of tickers with scores for manual review.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

# Earnings blackout: do not allow a position whose nearest standard monthly
# expiration falls within this many days of the earnings date.
EARNINGS_BLACKOUT_DAYS = int(os.environ.get("RW_EARNINGS_BLACKOUT_DAYS", "14"))

# Minimum options open interest for the nearest-expiry ATM put.
# Ensures the options market is liquid enough for fair fills.
MIN_OPTIONS_OI = int(os.environ.get("RW_MIN_OPTIONS_OI", "500"))

# Minimum market cap in billions (USD).
MIN_MARKET_CAP_BILLIONS = float(os.environ.get("RW_MIN_MARKET_CAP_BILLIONS", "10.0"))

# Maximum debt/equity ratio. Higher = more financial risk on assignment.
MAX_DEBT_EQUITY = float(os.environ.get("RW_MAX_DEBT_EQUITY", "2.0"))

# Minimum consecutive profitable quarters required.
MIN_PROFITABLE_QUARTERS = int(os.environ.get("RW_MIN_PROFITABLE_QUARTERS", "4"))


@dataclass
class ScreeningResult:
    ticker: str
    passed: bool
    market_cap_b: Optional[float] = None
    debt_equity: Optional[float] = None
    profitable_quarters: Optional[int] = None
    days_to_earnings: Optional[int] = None
    options_oi: Optional[int] = None
    fail_reasons: list[str] = field(default_factory=list)


def screen_ticker(
    ticker: str,
    market_cap_b: Optional[float],
    debt_equity: Optional[float],
    profitable_quarters: Optional[int],
    days_to_next_earnings: Optional[int],
    atm_put_oi: Optional[int],
) -> ScreeningResult:
    """
    Apply all filters to a single ticker. Returns a ScreeningResult with
    pass/fail and the specific reasons for any failure.

    All inputs are floats/ints provided by the caller (rw_research_agent.py).
    This function has no external dependencies; it is pure filtering logic.
    """
    fail_reasons: list[str] = []

    if market_cap_b is not None and market_cap_b < MIN_MARKET_CAP_BILLIONS:
        fail_reasons.append(
            f"Market cap ${market_cap_b:.1f}B below minimum ${MIN_MARKET_CAP_BILLIONS}B"
        )

    if debt_equity is not None and debt_equity > MAX_DEBT_EQUITY:
        fail_reasons.append(
            f"Debt/equity {debt_equity:.2f} above maximum {MAX_DEBT_EQUITY}"
        )

    if profitable_quarters is not None and profitable_quarters < MIN_PROFITABLE_QUARTERS:
        fail_reasons.append(
            f"Only {profitable_quarters} consecutive profitable quarters; need {MIN_PROFITABLE_QUARTERS}"
        )

    if days_to_next_earnings is not None and days_to_next_earnings < EARNINGS_BLACKOUT_DAYS:
        fail_reasons.append(
            f"Earnings in {days_to_next_earnings} days; inside {EARNINGS_BLACKOUT_DAYS}-day blackout"
        )

    if atm_put_oi is not None and atm_put_oi < MIN_OPTIONS_OI:
        fail_reasons.append(
            f"ATM put OI {atm_put_oi} below minimum {MIN_OPTIONS_OI}"
        )

    passed = len(fail_reasons) == 0

    return ScreeningResult(
        ticker=ticker,
        passed=passed,
        market_cap_b=market_cap_b,
        debt_equity=debt_equity,
        profitable_quarters=profitable_quarters,
        days_to_earnings=days_to_next_earnings,
        options_oi=atm_put_oi,
        fail_reasons=fail_reasons,
    )


def screen_candidates(candidates: list[dict]) -> list[ScreeningResult]:
    """
    Screen a list of candidate dicts against all filters.

    Each dict in candidates must contain:
        ticker: str
        market_cap_b: float | None
        debt_equity: float | None
        profitable_quarters: int | None
        days_to_next_earnings: int | None
        atm_put_oi: int | None

    Returns only the passed candidates in results, sorted by ascending debt/equity.
    Logs failed candidates with reasons.
    """
    results = []
    for c in candidates:
        result = screen_ticker(
            ticker=c["ticker"],
            market_cap_b=c.get("market_cap_b"),
            debt_equity=c.get("debt_equity"),
            profitable_quarters=c.get("profitable_quarters"),
            days_to_next_earnings=c.get("days_to_next_earnings"),
            atm_put_oi=c.get("atm_put_oi"),
        )
        if not result.passed:
            logger.info(
                f"[SCREEN] {result.ticker} FAILED: {'; '.join(result.fail_reasons)}"
            )
        results.append(result)

    passed = [r for r in results if r.passed]
    passed.sort(key=lambda r: (r.debt_equity or 999))
    logger.info(
        f"[SCREEN] {len(passed)}/{len(candidates)} candidates passed screening"
    )
    return passed
