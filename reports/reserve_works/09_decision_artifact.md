# 09 — Decision Artifact (v2, updated post second-opinion audit)

Reserve Works (RW) — One-Page Summary

Updated: 2026-05-05

---

## Channel: Reserve Works (RW)

**Verdict: DEFER live capital. START paper trading this week.**

Second-opinion audit confirmed verdict. 12 material corrections applied (see CHANGELOG below).

---

## Capital Ceiling and Starting Tier

## Current tier: Tier 0 (Paper Only)

- Capital required: $0
- Platform: Schwab thinkorswim (fastest onboarding) or IBKR
- Kill switch: RW_ENABLED=false (default, correct)

## Live capital ceiling when gates clear

- Tier 1 maximum: $5,000-$10,000 (1 contract, 1 position)
- Tier 2 maximum: $50,000 initial; hard cap 20% of total liquid net worth (never exceeded)
- No live capital before all five Tier 0 gates are cleared

---

## Phase Gates (All Five Required for Tier 1)

| Gate | Measurement |
| --- | --- |
| 1. CW $5K MRR sustained | $5K MRR for 3 consecutive months (not just achieved once) |
| 2. Carnival purchased | Purchase complete and settled |
| 3. Liquid reserve | $25K above operating runway + emergency fund + tax reserve |
| 4. 30 paper trades closed | Journal: 30 trades, including 5 paper assignments with covered-call cycles |
| 5. CPA consultation done | Section 1256, trader status, wash sales, Utah 4.5% flat tax, NIIT |

Earliest realistic Tier 1 date: Q3-Q4 2026 if CW Phase 1 clears on schedule.

During Tier 1, CW Phase 1 must remain intact and not regressing. If CW regresses during Tier 1, all RW positions close and program returns to Tier 0 review.

---

## Weekly Time Budget

**Now through Phase 1 unlock:** 1-2 hours/week. Paper trades and reading only.

**After Phase 1 unlock:** 3 hours/week hard cap. No RW work during CW/SW blocks.

**No exceptions.** If 3 hours cannot be held, the program suspends.

---

## First Action This Week

**By Friday 2026-05-09 (90 minutes total):**

1. Open paper trading account at Schwab thinkorswim (tdameritrade.com). Completion state: login working.
2. Identify one large-cap stock using criteria from 07_learning_roadmap.md.
3. Look at its option chain. Find put 10-15% OTM, 30-45 DTE.
4. Write down the observation using the journal template. Do not execute yet.

This action has a specific completion state. If it does not happen by Friday, the program is theoretical, not real.

---

## First Action Next Month

**By June 2026:**

Complete McMillan *Options as a Strategic Investment* chapters 1-3.
Close 5 paper trades with full journal entries (including at least 1 paper assignment).
Total time budget: 8 hours over the month.

---

## Open Decision (Resolve Within 30 Days)

**Private capital channel (P4) vs public content build with capital prop (P2)?**

These are different programs with different risk profiles and strategic justifications:

- P4 frame: RW is a personal reserve channel funded by CW/SW surplus. Deferred to 2027-2028. Low urgency now.
- P2 frame: RW is built in public. The learning journey is the content. The trades are documented. The losses are the most valuable episodes. This produces a content engine that reaches Signal Works buyers, generates a coaching product, and compounds as IP. Capital is a prop, not the point.

The current analysis does not commit to either. Commit within 30 days.

If P2: the paper trading series starts as public content now (at zero capital cost).
If P4: deferral is firm and the agent sits staged until 2027.

---

## Kill Criteria (Any One Triggers Full Stop)

1. CW Phase 1 fails to unlock or regresses at any point in next 12 months.
2. 3 consecutive months of skipped paper trades or incomplete journal entries.
3. Any live capital deployed before all five Tier 0 gates clear.
4. During Tier 1+: aggregate drawdown exceeds 15% of deployed capital in any rolling 90-day period.
5. Weekly time commitment cannot be held to 3 hours without measurable CW/SW impact.

Any of these converts DEFER to KILL.

---

## Crash Protocol (Pre-Committed, Non-Negotiable)

If multiple positions are assigned simultaneously in a crash:

Monday morning after the crash: sell covered calls at 5-10% above current cost basis on the next monthly expiration. No waiting for recovery. No improvisation. No "let me see if it bounces first."

Pre-commit to this now, while calm, so the crash-week decision is already made.

---

## Scoring Formula (Updated)

Quality 30 / Liquidity 30 / Risk 25 / Income 15 / Behavioral Fit 5.
Minimum passing score: 80. Prefer 85+.

Change from v1: Liquidity raised 25->30 (bid/ask spread destroys yield faster than any other factor). Income reduced 20->15 (chasing income is the primary failure mode). Behavioral Fit added (prior panic or rule violations on a ticker are disqualifying regardless of fundamentals).

Income above 3%/month triggers automatic risk re-review regardless of total score.

---

## Build Status

## RW Research Agent v1: STAGED, NOT DEPLOYED

Location: `agents/reserve_works/`
Kill switch: RW_ENABLED=false (default).
Scoring formula updated to Q30/L30/R25/I15/B5 in rw_scoring.py.

**Do not spend additional build time on RW agent until paper trading is started.**
Next build milestone: after 4-6 weeks of paper trading produce enough manual data to know what the agent should actually do.

---

## Rejected Premises (Confirmed by Second Opinion)

| Premise | Status | Source |
| --- | --- | --- |
| Gain in any direction | FALSE | CBOE PUT Index: -32.7% max drawdown in crash; underperforms S&P in bull years above 10% |
| Market dip coming soon | FALSE as signal | DALBAR QAIB: retail timing underperforms by 2-4% annualized |
| GEV opportunity missed | FALSE as signal | Survivorship bias; hundreds of peers went to zero in same window |
| Inaction is symmetric risk | FALSE | SW expansion at $497/mo: $18K-30K/year. RW on $25K: ~$1K/year. Not symmetric. |
| 150% annual return | FALSE | CBOE benchmark: 9.54% annualized 1986-2018 (Bondarenko 2019) |
| Favorable tax treatment | FALSE for equity options | Short-term gains at ordinary rate + Utah 4.5% flat + potential NIIT |

---

## CHANGELOG: v1 -> v2

Applied 12 corrections from second-opinion audit:

1. Scoring: Liquidity 25->30, Income 20->15, Behavioral Fit 5 added (rw_scoring.py updated)
2. Gate 1: $5K MRR must be sustained 3 consecutive months, not just achieved once
3. Gate 3 added: liquid reserve $25K above runway + emergency + tax reserve
4. Paper trade count: 30 required (was 10), including 5 paper assignments
5. Kill criterion added: 3 consecutive months of skipped trades = quiet kill
6. Open Decision added: P4 vs P2 frame must be resolved within 30 days
7. Projection benchmark: Bondarenko 2019 9.54% cited (was 9-10% range estimate)
8. Tax: Utah confirmed 4.5% flat (was 4.55%); NIIT mention added
9. Crash protocol added: Monday covered-call rule, pre-committed
10. Tier 1 condition added: CW Phase 1 must remain intact during Tier 1
11. Capital gate: hard ceiling at 20% of total liquid net worth at any tier
12. First Principles note added: wheel may be dominated by CW retainer/SW expansion; First Principles voice question not yet resolved

---

## One-Line Summary

Verdict unchanged: defer capital, paper trade by Friday, resolve P2 vs P4 within 30 days.
The second opinion sharpened the gates, corrected the tax framing, and surfaced one
unresolved question that changes the program's character if answered P2.
