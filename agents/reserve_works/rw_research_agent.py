"""
rw_research_agent.py — Reserve Works research agent.

CrewAI Agent that:
1. Reads the watchlist from PostgreSQL (rw_watchlist table).
2. Fetches fundamental and options data for each ticker.
3. Applies rw_screening.py filters.
4. Applies rw_scoring.py scoring.
5. Returns a candidate list formatted for Telegram review.

Hard constraints (enforced in code, not just documentation):
- NEVER places trades.
- NEVER accesses brokerage APIs.
- NEVER selects strike prices (produces strike range suggestions for manual selection only).
- ALL output requires Boubacar's manual approval before any action.
- Kill switch: if RW_ENABLED=false in environment, agent raises immediately.

LLM usage: SPOT tier for analysis (not FULL - this is structured data work, not
frontier reasoning). Follows select_llm() routing from orchestrator/agents.py.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Kill switch check ──────────────────────────────────────────────────────────
RW_ENABLED = os.environ.get("RW_ENABLED", "false").lower() == "true"
RW_PAPER_MODE = os.environ.get("RW_PAPER_MODE", "true").lower() == "true"

if not RW_ENABLED:
    logger.warning(
        "[RW] Reserve Works agent is DISABLED. "
        "Set RW_ENABLED=true in environment to activate."
    )

# ── Conditional CrewAI imports (only if enabled and deps available) ────────────
# The agent module can be imported and inspected even when disabled.
# CrewAI/litellm are only invoked when the run() function is called.

def _get_llm():
    """
    Resolve the LLM using select_llm() from the orchestrator.
    Uses "researcher" role at "moderate" complexity = SPOT tier equivalent.
    Raises ImportError if orchestrator is not on the Python path.
    """
    # Add orchestrator to path if not already present
    orc_path = Path(__file__).parent.parent.parent / "orchestrator"
    if str(orc_path) not in sys.path:
        sys.path.insert(0, str(orc_path))
    from agents import select_llm  # noqa: F401 - orchestrator agents.py
    return select_llm("researcher", "moderate")


def build_rw_research_agent():
    """
    Build and return the RW Research CrewAI Agent.
    Raises RuntimeError if RW_ENABLED is false.
    """
    if not RW_ENABLED:
        raise RuntimeError(
            "RW_ENABLED=false. Refusing to build agent. "
            "Set RW_ENABLED=true after all prerequisites are met."
        )

    from crewai import Agent

    llm = _get_llm()

    return Agent(
        role="Reserve Works Research Analyst",
        goal=(
            "Analyze a watchlist of stocks against the wheel strategy screening criteria "
            "and produce a ranked candidate list for manual review. "
            "Output is a structured report, not a trade recommendation. "
            "You never suggest specific strike prices or expiration dates — "
            "those decisions belong to the human operator."
        ),
        backstory=(
            "You are a disciplined options research analyst focused on the wheel strategy. "
            "You apply conservative, evidence-based screening criteria derived from CBOE "
            "benchmark data and academic research on short-premium strategies. "
            "You have zero tolerance for premium-chasing on low-quality names. "
            "Your job is to find the 2-3 best candidates from a watchlist each week and "
            "explain why they qualify — or why everything failed screening. "
            "You are skeptical of high premiums on volatile names. "
            "You treat every candidate as if Boubacar will be assigned tomorrow and must "
            "hold the stock for 6 months. If that scenario is uncomfortable, you flag it. "
            "You never fabricate data. If a data point is missing, you say so explicitly."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
        max_iter=3,
    )


def format_candidate_for_telegram(
    ticker: str,
    total_score: float,
    current_price: Optional[float],
    suggested_strike_range: Optional[tuple[float, float]],
    monthly_yield_pct: Optional[float],
    cash_required: Optional[float],
    score_notes: dict,
    paper_mode: bool = True,
) -> str:
    """
    Format a scored candidate for Telegram notification.

    This function produces human-readable output only. It does not
    trigger any brokerage action. Boubacar reads this and decides
    whether to act, and if so, what specific strikes to use.
    """
    mode_tag = "[PAPER]" if paper_mode else "[LIVE - MANUAL APPROVAL REQUIRED]"
    strike_text = (
        f"${suggested_strike_range[0]:.0f}-${suggested_strike_range[1]:.0f}"
        if suggested_strike_range
        else "range not computed"
    )
    yield_text = f"{monthly_yield_pct:.1%}/mo" if monthly_yield_pct else "N/A"
    cash_text = f"${cash_required:,.0f}" if cash_required else "N/A"

    lines = [
        f"{mode_tag} RW Candidate: {ticker} | Score: {total_score:.0f}/100",
        f"Price: ${current_price:.2f}" if current_price else "Price: N/A",
        f"Strike range (10-15% OTM suggestion): {strike_text}",
        f"Est. monthly premium yield: {yield_text}",
        f"Cash collateral required (1 contract): {cash_text}",
        "",
        "Scoring breakdown:",
        f"  Quality:   {score_notes.get('quality', 'N/A')}",
        f"  Liquidity: {score_notes.get('liquidity', 'N/A')}",
        f"  Risk:      {score_notes.get('risk', 'N/A')}",
        f"  Income:    {score_notes.get('income', 'N/A')}",
        "",
        "ACTION REQUIRED: Review above and decide manually.",
        "Do not act on this output automatically.",
    ]

    return "\n".join(lines)


def run_weekly_scan(watchlist_tickers: list[str], market_data: dict) -> list[dict]:
    """
    Orchestrate the weekly candidate scan.

    Parameters:
        watchlist_tickers: list of ticker symbols from the rw_watchlist table.
        market_data: dict mapping ticker -> data dict with the fields required
                     by rw_screening.py and rw_scoring.py. Caller is responsible
                     for populating this from a market data provider.

    Returns:
        List of formatted output dicts for Telegram notification.

    This function performs no I/O itself. Caller handles DB read and Telegram send.
    This design keeps the agent testable without live brokerage or Telegram connections.
    """
    if not RW_ENABLED:
        raise RuntimeError("RW_ENABLED=false. Scan aborted.")

    from rw_screening import screen_candidates
    from rw_scoring import score_all_candidates

    logger.info(f"[RW] Starting weekly scan for {len(watchlist_tickers)} tickers")

    # Build candidate list from market data
    candidates = []
    for ticker in watchlist_tickers:
        data = market_data.get(ticker, {})
        if not data:
            logger.warning(f"[RW] No market data for {ticker}, skipping")
            continue
        candidates.append({"ticker": ticker, **data})

    # Phase 1: screening
    passed_screen = screen_candidates(candidates)
    if not passed_screen:
        logger.info("[RW] No candidates passed screening this week.")
        return []

    # Phase 2: scoring
    scored = score_all_candidates([
        {**c.__dict__, "ticker": c.ticker} for c in passed_screen
        if c.passed
    ])

    # Phase 3: format for Telegram
    outputs = []
    for s in scored:
        raw = market_data.get(s.ticker, {})
        price = raw.get("current_price")
        if price:
            low_strike = round(price * 0.85, 0)
            high_strike = round(price * 0.90, 0)
            strike_range = (low_strike, high_strike)
            cash_required = high_strike * 100
        else:
            strike_range = None
            cash_required = None

        text = format_candidate_for_telegram(
            ticker=s.ticker,
            total_score=s.total_score,
            current_price=price,
            suggested_strike_range=strike_range,
            monthly_yield_pct=raw.get("monthly_premium_yield_pct"),
            cash_required=cash_required,
            score_notes=s.score_notes,
            paper_mode=RW_PAPER_MODE,
        )
        outputs.append({
            "ticker": s.ticker,
            "score": s.total_score,
            "telegram_text": text,
        })

    logger.info(f"[RW] Scan complete. {len(outputs)} candidates ready for review.")
    return outputs
