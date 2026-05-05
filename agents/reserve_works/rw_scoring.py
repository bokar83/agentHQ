"""
rw_scoring.py — Candidate scoring for Reserve Works.

Implements a four-dimension scoring model. Candidates below the minimum
score threshold are excluded from the output list.

Scoring dimensions (total 100 points):
  Quality        (30 pts): fundamental soundness of the underlying business.
  Liquidity      (30 pts): options market depth and ease of entry/exit.
  Risk           (25 pts): downside scenario analysis and assignment comfort.
  Income         (15 pts): current premium yield relative to capital requirement.
  Behavioral Fit  (5 pts): operator familiarity with the name (prior trades, emotional history).

Why these weights (updated per second-opinion audit, 2026-05-05):
  Quality is weighted highest because assignment on a bad business is the
  primary failure mode for the wheel strategy.

  Liquidity is raised from 25 to 30. A wide bid/ask spread on a thin options
  market destroys the theoretical premium yield at execution more reliably than
  any other single factor. Illiquid options chains are the fastest way to lose
  the economic argument for the wheel.

  Risk is unchanged at 25.

  Income is reduced from 20 to 15. Chasing income is the most common mistake.
  High premiums signal high risk. Income should confirm a position that already
  qualifies on the first three dimensions, not override them.

  Behavioral Fit (new, 5 pts): whether the operator has wheeled this name before
  and how it went. A name that triggered panic or rule violations in the past is
  a liability regardless of the fundamental score.

Minimum passing score: 80/100.
Candidates below 80 are excluded. Expose reasoning to Boubacar for manual override.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

MINIMUM_SCORE = int(os.environ.get("RW_MIN_SCORE", "80"))


@dataclass
class ScoredCandidate:
    ticker: str
    quality_score: float           # 0-30
    liquidity_score: float         # 0-30
    risk_score: float              # 0-25
    income_score: float            # 0-15
    behavioral_fit_score: float    # 0-5
    total_score: float
    passed: bool
    score_notes: dict              # dimension -> reasoning string


def score_quality(
    profitable_quarters: Optional[int],
    market_cap_b: Optional[float],
    debt_equity: Optional[float],
    has_moat_indicator: bool,
    sector_stability_rating: Optional[int],  # 1-5, 5 = most stable
) -> tuple[float, str]:
    """
    Score fundamental quality. Max 30 points.

    Components:
      - Consecutive profitable quarters: 0-10 pts
      - Market cap size: 0-5 pts
      - Debt/equity: 0-8 pts
      - Moat indicator (dividend history, brand, switching costs): 0-7 pts
    """
    score = 0.0
    notes = []

    # Consecutive profitable quarters (0-10 pts)
    q = profitable_quarters or 0
    if q >= 8:
        score += 10
        notes.append(f"8+ profitable quarters: 10pts")
    elif q >= 4:
        score += 7
        notes.append(f"{q} profitable quarters: 7pts")
    elif q >= 2:
        score += 4
        notes.append(f"{q} profitable quarters: 4pts")
    else:
        notes.append(f"{q} profitable quarters: 0pts")

    # Market cap (0-5 pts): larger = more liquid and harder to manipulate
    mc = market_cap_b or 0
    if mc >= 100:
        score += 5
        notes.append("Mega-cap (100B+): 5pts")
    elif mc >= 50:
        score += 4
        notes.append("Large-cap (50-100B): 4pts")
    elif mc >= 10:
        score += 2
        notes.append("Mid-large-cap (10-50B): 2pts")
    else:
        notes.append(f"Sub-10B cap: 0pts")

    # Debt/equity (0-8 pts): lower is better for assignment survival
    de = debt_equity
    if de is None:
        score += 4
        notes.append("D/E unknown: 4pts (neutral)")
    elif de <= 0.3:
        score += 8
        notes.append(f"Low D/E ({de:.2f}): 8pts")
    elif de <= 0.8:
        score += 6
        notes.append(f"Moderate D/E ({de:.2f}): 6pts")
    elif de <= 1.5:
        score += 3
        notes.append(f"Elevated D/E ({de:.2f}): 3pts")
    else:
        notes.append(f"High D/E ({de:.2f}): 0pts")

    # Moat indicator (0-7 pts)
    if has_moat_indicator:
        score += 7
        notes.append("Moat indicator present: 7pts")
    else:
        notes.append("No moat indicator: 0pts")

    return score, " | ".join(notes)


def score_liquidity(
    atm_put_oi: Optional[int],
    avg_daily_options_volume: Optional[int],
    bid_ask_spread_pct: Optional[float],  # spread as % of mid-price
) -> tuple[float, str]:
    """
    Score options market liquidity. Max 25 points.

    Components:
      - ATM put open interest: 0-10 pts
      - Average daily options volume: 0-8 pts
      - Bid/ask spread width: 0-7 pts
    """
    score = 0.0
    notes = []

    oi = atm_put_oi or 0
    if oi >= 5000:
        score += 10
        notes.append(f"OI {oi}: 10pts")
    elif oi >= 1000:
        score += 7
        notes.append(f"OI {oi}: 7pts")
    elif oi >= 500:
        score += 4
        notes.append(f"OI {oi}: 4pts")
    else:
        notes.append(f"OI {oi}: 0pts")

    vol = avg_daily_options_volume or 0
    if vol >= 10000:
        score += 8
        notes.append(f"ADV {vol}: 8pts")
    elif vol >= 2000:
        score += 5
        notes.append(f"ADV {vol}: 5pts")
    elif vol >= 500:
        score += 2
        notes.append(f"ADV {vol}: 2pts")
    else:
        notes.append(f"ADV {vol}: 0pts")

    spread = bid_ask_spread_pct
    if spread is None:
        score += 3
        notes.append("Spread unknown: 3pts (neutral)")
    elif spread <= 0.02:
        score += 7
        notes.append(f"Spread {spread:.1%}: 7pts")
    elif spread <= 0.05:
        score += 5
        notes.append(f"Spread {spread:.1%}: 5pts")
    elif spread <= 0.10:
        score += 2
        notes.append(f"Spread {spread:.1%}: 2pts")
    else:
        notes.append(f"Wide spread {spread:.1%}: 0pts")

    return score, " | ".join(notes)


def score_risk(
    days_to_earnings: Optional[int],
    beta: Optional[float],
    sector_correlation_to_spy: Optional[float],
    would_own_long_term: bool,
) -> tuple[float, str]:
    """
    Score downside risk and assignment safety. Max 25 points.

    Components:
      - Earnings window safety: 0-8 pts
      - Beta (price volatility relative to S&P 500): 0-7 pts
      - Sector correlation: 0-5 pts
      - "Would own this long-term" judgment: 0-5 pts (binary, Boubacar confirms)
    """
    score = 0.0
    notes = []

    dte = days_to_earnings
    if dte is None:
        score += 4
        notes.append("Earnings date unknown: 4pts (caution)")
    elif dte >= 45:
        score += 8
        notes.append(f"Earnings {dte} days out: 8pts")
    elif dte >= 30:
        score += 5
        notes.append(f"Earnings {dte} days out: 5pts")
    elif dte >= 14:
        score += 2
        notes.append(f"Earnings {dte} days out: 2pts")
    else:
        notes.append(f"Earnings {dte} days out (INSIDE BLACKOUT): 0pts")

    b = beta or 1.0
    if b <= 0.7:
        score += 7
        notes.append(f"Low beta {b:.2f}: 7pts")
    elif b <= 1.0:
        score += 5
        notes.append(f"Near-market beta {b:.2f}: 5pts")
    elif b <= 1.3:
        score += 3
        notes.append(f"Moderate beta {b:.2f}: 3pts")
    else:
        notes.append(f"High beta {b:.2f}: 0pts")

    corr = sector_correlation_to_spy
    if corr is None:
        score += 2
        notes.append("Sector correlation unknown: 2pts (neutral)")
    elif corr <= 0.5:
        score += 5
        notes.append(f"Low correlation {corr:.2f}: 5pts")
    elif corr <= 0.7:
        score += 3
        notes.append(f"Moderate correlation {corr:.2f}: 3pts")
    else:
        notes.append(f"High correlation {corr:.2f}: 0pts")

    if would_own_long_term:
        score += 5
        notes.append("Boubacar confirms would own long-term: 5pts")
    else:
        notes.append("Would NOT own long-term: 0pts (disqualifying flag)")

    return score, " | ".join(notes)


def score_income(
    monthly_premium_yield_pct: Optional[float],
    annualized_yield_pct: Optional[float],
    vix_level: Optional[float],
) -> tuple[float, str]:
    """
    Score premium income attractiveness. Max 15 points (reduced from 20).

    Rationale for reduction: chasing income is the most documented failure mode
    for retail wheel traders. Premium above ~2%/month almost always signals risk
    the score does not fully capture. Income weight reduced; liquidity weight raised.

    Components:
      - Monthly premium yield (premium / cash collateral): 0-9 pts
      - VIX adjustment: 0-6 pts. Normal VIX (15-25) = highest score because
        premium is sustainable. Crisis VIX (35+) = 0 pts because new positions
        should not be opened during crash conditions.

    Note: income is the LAST dimension scored, on purpose. High income on a low-quality
    name is a trap. Anything above 3%/month triggers automatic risk re-review.
    """
    score = 0.0
    notes = []

    mpy = monthly_premium_yield_pct or 0
    if mpy > 0.03:
        score += 6
        notes.append(f"Monthly yield {mpy:.1%}: 6pts (HIGH -- TRIGGER RISK RE-REVIEW)")
    elif mpy >= 0.02:
        score += 9
        notes.append(f"Monthly yield {mpy:.1%}: 9pts")
    elif mpy >= 0.01:
        score += 6
        notes.append(f"Monthly yield {mpy:.1%}: 6pts")
    elif mpy >= 0.008:
        score += 3
        notes.append(f"Monthly yield {mpy:.1%}: 3pts")
    else:
        notes.append(f"Monthly yield {mpy:.1%}: 0pts (below 0.8% threshold)")

    vix = vix_level or 18
    if 15 <= vix <= 25:
        score += 6
        notes.append(f"VIX {vix:.0f} normal range: 6pts (sustainable yield)")
    elif vix < 15:
        score += 3
        notes.append(f"VIX {vix:.0f} low: 3pts (premium compressed)")
    elif vix <= 35:
        score += 3
        notes.append(f"VIX {vix:.0f} elevated: 3pts (premium high but crash risk elevated)")
    else:
        score += 0
        notes.append(f"VIX {vix:.0f} crisis level: 0pts (do not open new positions)")

    return score, " | ".join(notes)


def score_behavioral_fit(
    prior_trades_on_ticker: int,
    prior_trades_profitable_pct: Optional[float],
    triggered_panic_or_rule_violation: bool,
) -> tuple[float, str]:
    """
    Score operator familiarity and behavioral history with this specific ticker.
    Max 5 points.

    A ticker that previously triggered emotional decision-making or rule violations
    is a liability regardless of its fundamental score. The best wheel candidates
    are names the operator can hold through volatility without behavioral drift.
    """
    score = 0.0
    notes = []

    if triggered_panic_or_rule_violation:
        notes.append("Prior rule violation or panic on this ticker: 0pts (automatic flag)")
        return 0.0, " | ".join(notes)

    if prior_trades_on_ticker == 0:
        score += 2
        notes.append("No prior trades on this ticker: 2pts (neutral, first exposure)")
    elif prior_trades_on_ticker >= 3:
        pct = prior_trades_profitable_pct or 0
        if pct >= 0.7:
            score += 5
            notes.append(f"{prior_trades_on_ticker} prior trades, {pct:.0%} profitable: 5pts")
        elif pct >= 0.5:
            score += 3
            notes.append(f"{prior_trades_on_ticker} prior trades, {pct:.0%} profitable: 3pts")
        else:
            score += 1
            notes.append(f"{prior_trades_on_ticker} prior trades, {pct:.0%} profitable: 1pt")
    else:
        score += 2
        notes.append(f"{prior_trades_on_ticker} prior trades (too few for signal): 2pts")

    return score, " | ".join(notes)


def score_candidate(candidate: dict) -> ScoredCandidate:
    """
    Score a single candidate dict. Required keys match rw_screening.py output plus
    additional fields:
      - would_own_long_term: bool (Boubacar confirms before final scoring)
      - beta: float
      - sector_correlation_to_spy: float
      - monthly_premium_yield_pct: float
      - vix_level: float
      - avg_daily_options_volume: int
      - bid_ask_spread_pct: float
      - has_moat_indicator: bool
      - sector_stability_rating: int (1-5)
      - prior_trades_on_ticker: int (0 if new)
      - prior_trades_profitable_pct: float | None
      - triggered_panic_or_rule_violation: bool
    """
    q_score, q_notes = score_quality(
        profitable_quarters=candidate.get("profitable_quarters"),
        market_cap_b=candidate.get("market_cap_b"),
        debt_equity=candidate.get("debt_equity"),
        has_moat_indicator=candidate.get("has_moat_indicator", False),
        sector_stability_rating=candidate.get("sector_stability_rating"),
    )
    l_score, l_notes = score_liquidity(
        atm_put_oi=candidate.get("atm_put_oi"),
        avg_daily_options_volume=candidate.get("avg_daily_options_volume"),
        bid_ask_spread_pct=candidate.get("bid_ask_spread_pct"),
    )
    r_score, r_notes = score_risk(
        days_to_earnings=candidate.get("days_to_next_earnings"),
        beta=candidate.get("beta"),
        sector_correlation_to_spy=candidate.get("sector_correlation_to_spy"),
        would_own_long_term=candidate.get("would_own_long_term", False),
    )
    i_score, i_notes = score_income(
        monthly_premium_yield_pct=candidate.get("monthly_premium_yield_pct"),
        annualized_yield_pct=candidate.get("annualized_yield_pct"),
        vix_level=candidate.get("vix_level"),
    )
    b_score, b_notes = score_behavioral_fit(
        prior_trades_on_ticker=candidate.get("prior_trades_on_ticker", 0),
        prior_trades_profitable_pct=candidate.get("prior_trades_profitable_pct"),
        triggered_panic_or_rule_violation=candidate.get("triggered_panic_or_rule_violation", False),
    )

    total = q_score + l_score + r_score + i_score + b_score
    passed = total >= MINIMUM_SCORE

    if not passed:
        logger.info(
            f"[SCORE] {candidate['ticker']} scored {total:.1f} < {MINIMUM_SCORE} threshold"
        )

    return ScoredCandidate(
        ticker=candidate["ticker"],
        quality_score=q_score,
        liquidity_score=l_score,
        risk_score=r_score,
        income_score=i_score,
        behavioral_fit_score=b_score,
        total_score=total,
        passed=passed,
        score_notes={
            "quality": q_notes,
            "liquidity": l_notes,
            "risk": r_notes,
            "income": i_notes,
            "behavioral_fit": b_notes,
        },
    )


def score_all_candidates(candidates: list[dict]) -> list[ScoredCandidate]:
    """
    Score all candidates. Return only passing candidates sorted by total score descending.
    """
    scored = [score_candidate(c) for c in candidates]
    passing = [s for s in scored if s.passed]
    passing.sort(key=lambda s: s.total_score, reverse=True)
    logger.info(
        f"[SCORE] {len(passing)}/{len(scored)} candidates scored >= {MINIMUM_SCORE}"
    )
    return passing
