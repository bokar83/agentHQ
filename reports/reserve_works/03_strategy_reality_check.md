# 03 — Strategy Reality Check
# Reserve Works Decision Package
# Generated: 2026-05-05

---

## Wheel Mechanics in Plain Terms

The wheel is a two-leg income strategy that cycles between selling puts and selling calls.

**Phase 1 — Cash-Secured Put:**

You identify a stock you are willing to own at price X. You sell a put option with a strike
at or below X, expiring in 30-45 days. You collect a premium immediately. Your brokerage
holds your full cash collateral (strike price times 100 shares per contract) to guarantee
you can buy the shares if the buyer exercises.

Possible outcomes at expiration:
- Stock stays above your strike: option expires worthless, you keep the premium, repeat.
- Stock drops below your strike: you are assigned and must buy 100 shares at the strike.

**Phase 2 — Covered Call (triggered by assignment):**

You now own shares with a cost basis of (strike minus premium received). You sell a call
option against those shares at a strike equal to or above your cost basis, expiring in 30-45
days. You collect another premium.

Possible outcomes at expiration:
- Stock stays below the call strike: option expires worthless, you keep the premium, repeat.
- Stock rises above the call strike: you are called away and must sell your shares at the
  strike. Your total profit is (call strike - put strike) + both premiums collected.

The cycle completes when called away, after which you return to Phase 1.

**What the wheel is not:**

- It is not market-neutral. Both legs are long-delta. Falling stocks hurt.
- It is not a hedge. It has no short leg.
- It is not passive. It requires active monitoring of positions, assignment events, and
  rolling decisions.
- It is not high-frequency. Monthly expirations mean 12 potential trades per position per year.

---

## Realistic Annualized Returns by Regime

All figures are documented from CBOE indices and TastyTrade Research (publicly available at
tastylive.com, searchable archive). CBOE data covers systematic strategies; TastyTrade data
covers individual equity options.

**Normal/low volatility (VIX 12-18), bull or flat:**
- PUT index: 8-12% annualized
- Individual stock wheel: 12-20% annualized before assignments; 8-15% after expected losses
- Best-performing category: dividend stocks with stable earnings (JNJ, ABT, MCD profile)

**Elevated volatility (VIX 20-30), volatile but no crash:**
- PUT index: 12-16% annualized
- Individual stock wheel: 20-35% annualized gross; 12-22% after assignment losses
- Drawdown risk elevated: a single bad assignment can wipe 3-4 months of premium

**High volatility / crash (VIX 30+):**
- PUT index: negative for the crash year, recovery takes 6-18 months
- March 2020: PUT index fell 22% peak-to-trough; recovered in approximately 5 months
- Q4 2008: PUT index fell 26-28%; took approximately 18 months to recover
- Individual stocks in these regimes: highly bifurcated. Quality names recover; sector-
  concentrated or levered names can take 3-5 years or never fully recover

Sources:
- CBOE PUT Index fact sheet (cboe.com/products/benchmarks/put)
- Whaley, R.E. (2002) "Return and Risk of CBOE Buy Write Monthly Index." Journal of Derivatives.
- TastyTrade Research: "Short Puts vs Long Stock" series (20+ peer-reviewed style papers)
- Sinclair, E. "Volatility Trading" 2nd ed. (2013), Chapter 6 systematic short vol strategies

---

## Walk-Through: March 2020 Wheel on a Quality Position

**Setup (late January 2020):**

Target: Apple (AAPL), then trading around $310. Conservative strategy: sell the $270 strike
put (approximately 13% OTM), 45 DTE expiration in mid-March 2020. Premium approximately
$350 per contract. Cash required: $27,000 per contract.

**Event:** COVID market crash. S&P 500 fell 34% peak-to-trough (Feb 19 to March 23, 2020).
AAPL fell from $327 (Feb 12) to $224 (March 23). A 32% decline.

**Result for the $270 strike put:**

- AAPL breached $270 in late February.
- By expiration (mid-March), AAPL was approximately $250.
- Assignment: forced to buy 100 shares at $270. Cash outflow: $27,000.
- Effective cost basis: $27,000 minus $350 premium = $26,650, or $266.50/share.
- Mark-to-market loss at March 23: AAPL at $224. Paper loss = ($266.50 - $224) * 100 = $4,250.

**Phase 2 (covered call after assignment):**

Sell the April $270 call (at-the-money relative to assignment, slightly OTM from current
price). With VIX at 65+, premium is enormous: approximately $1,200 per contract for April
$270 call.

- Cost basis now: $266.50 - $12.00 (call premium) = $254.50.
- AAPL recovered rapidly. By April expiration (April 17), AAPL was approximately $280.
- Called away at $270. Profit: ($270 - $254.50) * 100 = $1,550.

**Total P&L on the cycle:**

Put premium: $350. Called-away profit: $1,550. Total: $1,900 on $27,000 capital.
Return: 7% in approximately 75 days, or approximately 34% annualized.
But this required holding through a $4,250 paper loss at the worst point.

**If AAPL had NOT recovered:**

If AAPL had stayed at $224 (a sustained crash, not a V-shaped recovery), the covered call
strategy would collect $600-800 per month. At $800/month, payback of the $4,250 paper loss
requires 5 months. Full return to profit from entry requires approximately 7 months of
perfect execution with no further declines.

**Key lesson:**

The wheel on AAPL in early 2020 worked because AAPL recovered fast. On a stock that did not
recover (e.g., Carnival Cruise Lines fell 80% in 2020 and took 3+ years to recover), the
same wheel strategy would produce years of covered call income just to get back to breakeven.
Stock selection is not optional. It is the entire strategy.

---

## Capital Efficiency by Tier

**Tier 0 (Paper only, $0 live capital):**

- Time required: 8-12 weeks of consistent practice.
- Skills built: order entry, understanding assignment mechanics, position sizing,
  reading option chains, tracking P&L across legs.
- Gates before Tier 1: 10+ simulated trades completed, at least 2 simulated assignments
  handled, documented trade journal, consistent application of strike selection rules.

**Tier 1 ($5,000-$10,000 live capital, 1-2 contracts):**

On a $25-30 stock (e.g., a utility or consumer staple):
- 1 contract requires $2,500-$3,000 cash collateral.
- Monthly premium at 10-15% OTM: $50-150 per contract.
- Annualized yield: 20-60% of premium notional, or $600-1,800/year on $2,500-3,000 collateral.
- This is learning capital, not income capital. The goal is not income; it is mastery.

**Tier 2 ($25,000 live capital, 3-5 contracts on quality names):**

On quality large-cap stocks ($40-80/share):
- 3-5 contracts on 2-3 different underlyings.
- Monthly premium target: $500-1,500 total.
- Annualized income before assignments: $6,000-18,000. After expected assignment losses
  and capital tied in stock positions: $4,000-12,000.
- Approximately 16-48% annualized on deployed capital.

**Target state ($50,000 live capital, 5-8 contracts, diversified):**

- Monthly income target: $1,500-3,500 in normal conditions.
- Annual income estimate: $18,000-42,000 before adverse events.
- After bad years: $10,000-25,000 in realistic average.
- This is a realistic path to supplemental income. It is not a path to $5,000-$10,000/month
  from $50,000 capital. That would require 10-20% monthly returns sustained without loss.

**To reach $5,000/month consistent income from wheel strategy alone:**

- Capital required at 15% annualized (realistic ceiling for consistent practitioners):
  $400,000 deployed.
- Capital required at 10% annualized (conservative estimate): $600,000 deployed.
- Time to accumulate this via wheel income starting from $50,000: 8-12 years of
  reinvested returns at 15% annualized with no major drawdown years.
- More realistic path: grow primary income channels (CW, SW) and use wheel as capital
  preservation + modest yield strategy while building toward larger capital base.

---

## Why Marketing Beats Execution

The wheel is not hard to understand. It is hard to execute because:

1. **Assignment psychology.** Being forced to buy stock in a falling market feels like
   loss even when the numbers say hold. Most people sell at the bottom of assignment events.

2. **Selection complacency.** After several winning trades, practitioners relax stock
   selection discipline. They pick stocks they "know" rather than stocks that pass filters.

3. **Premium chasing.** Higher premiums come from higher IV, which comes from higher risk.
   Chasing premium leads to selling puts on stocks that subsequently move adversely.

4. **Rolling addiction.** When a position goes against you, rolling (buying back the put
   and selling a farther expiration) feels like managing risk. It often just delays and
   amplifies the loss.

5. **Capital concentration.** The strategy requires full cash collateral per contract.
   With $50,000, you can run 3-5 positions. Diversification is limited. One bad position
   in a highly correlated market hit (all five positions moving against you) is
   existentially damaging.

The marketing version (PDF) omits all five of these failure modes.
