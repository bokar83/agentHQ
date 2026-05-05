# 07 — Learning Roadmap
# Reserve Works Decision Package
# Generated: 2026-05-05

---

## Broker Selection for Paper Trading and Level 2 Options Approval

**Recommended: Interactive Brokers (IBKR) or TD Ameritrade (thinkorswim)**

**IBKR:**
- Paper trading account: free, full simulation including assignment events.
- IBKR Campus: free, high-quality educational content aligned with real brokerage mechanics.
- Options approval: Level 2 (selling covered calls and cash-secured puts) requires
  documented experience or passing their knowledge assessment.
- Platform: slightly complex interface but best execution quality and lowest margin rates.
- Note: IBKR requires a real money account to access paper trading after the initial
  simulation period. Open a real account with minimum deposit ($0 for IBKR Lite) alongside
  the paper account.

**TD Ameritrade / thinkorswim (now Schwab):**
- Paper trading: excellent simulation, integrated with the same platform as live trading.
- Level 2 options approval: straightforward. Answer experience questions honestly.
- Platform: thinkorswim is the industry-standard platform for options analysis.
- IBKR has been absorbed into Schwab; thinkorswim is fully functional as of 2024.

**Avoid for this purpose:** Robinhood (gamified, poor education ecosystem), Webull (options
mechanics simulation is less rigorous), Coinbase (not relevant).

---

## 12-Week Paper Trading Curriculum

**Sources: NO Kiyosaki material. Only:**
- IBKR Campus (ibkrlearn.com) — free video courses
- TastyTrade/TastyLive (tastylive.com) — research archive and free content
- CBOE Education (cboe.com/education) — index methodology, benchmark data
- Schwab options education (schwab.com/options-education)
- Natenberg, S. "Option Volatility and Pricing" 2nd ed. (2014) — the practitioner standard

---

### Weeks 1-2: Foundation

**Objective:** Understand the mechanics without any trade.

Reading/watching:
- IBKR Campus: "Basics of Options" module (approximately 4 hours).
- Understand: strike price, expiration date, premium, intrinsic value, time value.
- Understand: what it means to be assigned. Walk through the assignment mechanics on
  paper with a fictional position before seeing it in simulation.
- TastyLive: "The Skinny on Options" playlist (select the options basics episodes).

**Practice:**
- Open paper account. Do not trade yet. Find 3 stocks you know well (any large-cap name).
- Look at their option chain. Find the current put prices for strikes 10% and 15% below
  the current price, 30-45 days out.
- Write down what you observe. Do not simulate a trade.

**Journal entry format (establish now):**
```
Date:
Underlying:
Current price:
Strike selected (10-15% OTM):
Expiration date (30-45 DTE):
Premium per share:
Cash required for collateral:
Monthly yield on collateral (%):
Why this underlying qualifies: [3 reasons based on fundamental criteria]
```

**Time budget:** 3 hours over 2 weeks.

---

### Weeks 3-4: First Simulated Trades

**Objective:** Execute first paper put sales. Experience the wait.

Reading:
- Natenberg Chapter 1-3: "What is an option?", "Elementary Strategies", "Introduction to
  Theoretical Pricing."
- CBOE education: "Cash-Secured Puts" guide (cboe.com/education).

**Practice:**
- Identify 2 qualifying underlyings using criteria:
  - S&P 500 component or equivalent large-cap (liquid options market).
  - No earnings announcement within 14 days of chosen expiration.
  - Profitable company with positive earnings last 4 quarters.
  - Not in a confirmed downtrend (check simple 20-week moving average).
- Sell 1 paper put contract on each. Log in journal.
- Set a price alert: if the stock falls 5% below your strike, get a notification.
  Do nothing yet. Just observe how you feel.

**Time budget:** 2-3 hours/week.

---

### Weeks 5-6: Monitor and Observe Psychology

**Objective:** Track positions, observe volatility impact on premium value, avoid tinkering.

Reading:
- TastyLive Research: search "45 DTE vs 30 DTE" and read the study.
- Understand theta decay: why options lose value as time passes (even if price is unchanged).

**Practice:**
- Check positions once per day (not more). Log the premium value change.
- If either position is approaching the strike (stock within 5% of strike): DO NOT ROLL.
  Hold the position. Experience the discomfort. This is the most important lesson.
- At expiration, document the outcome. What actually happened vs what you feared would happen.

**Journal addition for monitoring:**
```
Week [n] check:
Underlying current price:
Put current value (if not expired):
Days to expiration:
Decision: Hold / Roll / No action needed
Reasoning:
```

**Time budget:** 1-2 hours/week (monitoring is quick when positions are not near the strike).

---

### Weeks 7-8: First Simulated Assignment

**Objective:** Experience assignment and the covered call transition.

If neither position was assigned naturally, paper-force an assignment scenario:
- Simulate that stock XYZ dropped to your strike price.
- Simulate the assignment: you now own 100 shares at the strike.
- Immediately sell a covered call at the same strike (your cost basis) for the next 30-45 days.
- Log the new position.

Reading:
- TastyLive: "The Wheel Strategy" episodes (search the research archive).
- Understand: what your actual cost basis is after receiving put premium.
- Understand: scenarios where the stock never recovers to your strike and you hold for months.

**Key question to answer in your journal:**
If I owned this stock for 6 months at this cost basis, would I be okay? If the answer is
no, this is not a qualifying underlying.

**Time budget:** 2-3 hours over 2 weeks.

---

### Weeks 9-10: Add a Second Position, Different Sector

**Objective:** Practice diversification within the strategy.

**Practice:**
- Select a second underlying in a different sector from your first.
- Apply all qualifying criteria again. Do not use gut feel.
- Sell a paper put. Now you are managing 2-3 paper positions simultaneously.
- Practice the weekly check routine across all positions.

**Sector diversification rule:**
- Never put two positions in the same sector simultaneously.
- Example: if position 1 is in technology (AAPL), position 2 should be consumer staples,
  utilities, healthcare, or industrials. Not another tech name.

Reading:
- CBOE PUT Index methodology (understand how the benchmark compares to what you are doing).
- Understand: correlation between your positions in a market crash.

**Time budget:** 2-3 hours/week.

---

### Weeks 11-12: Full Cycle Review and Live Capital Gate Assessment

**Objective:** Audit your 12 weeks of paper trading and make the Tier 1 decision.

**Practice:**
- Complete the full journal from week 1 through week 12.
- Calculate your simulated annualized return: (total paper P&L / total collateral deployed)
  * (365 / days elapsed).
- Document every rule violation you made (if any). No self-forgiveness; catalogue them.
- Answer the six Tier 0 advancement gate questions (see 06_capital_allocation.md).
- If all six gates are satisfied AND the capital prerequisites are met (Carnival done, CW
  Phase 1 unlocked, dedicated capital available): proceed to Tier 1.
- If any gate fails: extend paper trading. There is no shame in 16 weeks vs 12 weeks.

**Time budget:** 3-4 hours for the final audit.

---

## Trade Journal Template (Full Version)

```
=== TRADE JOURNAL ENTRY ===
Date opened:
Underlying ticker:
Underlying current price:
52-week range:
Last 4 quarters profitable: Y/N
Upcoming earnings (next 60 days):
Sector:

PUT LEG:
Strike selected:
Strike as % below current price:
Expiration date:
Days to expiration (DTE):
Premium per share:
Total premium (x100):
Cash collateral required:
Yield on collateral (%):

FUNDAMENTAL JUSTIFICATION (3 sentences minimum):
1.
2.
3.

EXIT PLAN (complete before executing):
- If expires worthless: [action]
- If assigned: [action - sell covered call at what strike]
- If stock drops 25%+ below cost basis: [close position]

MONITORING LOG:
[date] price=[x] DTE=[n] action=[hold/roll/none] notes=[...]

OUTCOME:
Date closed:
Final result: Expired worthless / Assigned / Closed early
P&L:
Lessons:
```

---

## Mastery Gates Between Phases

| Phase | Gate Criteria |
|---|---|
| Paper -> Tier 1 | 10 trades, 2 assignments, 6 gates from 06_capital_allocation.md, capital prerequisites met |
| Tier 1 -> Tier 2 | 10 live trades, net positive P&L, 1 live assignment handled, no rule violations, 3-5hr/week sustained |
| Tier 2 -> Scale | 6 months consistent, 15%+ annualized net, zero stop-loss violations, formal tax tracking initiated |

---

## Recommended Reading Priority

1. Natenberg, S. "Option Volatility and Pricing" 2nd ed. (2014) — Chapters 1-6, then 10, 14.
   This is the practitioner standard. Skip nothing.

2. Sinclair, E. "Volatility Trading" 2nd ed. (2013) — Chapters 1-4, 6.
   Academic rigor, real-world application. More advanced than Natenberg but essential.

3. TastyLive Research archive (free at tastylive.com): filter by "short puts" and "wheel."
   These are peer-reviewed style studies, not marketing content.

4. CBOE PUT Index historical data and fact sheets (free at cboe.com).
   Benchmarking your results against PUT gives you an honest performance comparison.

5. IRS Publication 550: Investment Income and Expenses.
   Understand how short-term gains and wash-sale rules work before live trading.
   For Utah: Utah Individual Income Tax instructions (tax.utah.gov).

**Do not re-read Kiyosaki's PDF for strategy guidance.** It is a useful motivational
reframe (cash flow vs capital gains is a legitimate mental model) and a dangerous
source for numerical claims. The wheel mechanics it describes are real; the numbers are not.
