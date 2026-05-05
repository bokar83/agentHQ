# 02 — Kiyosaki Premise Audit
# Reserve Works Decision Package
# Generated: 2026-05-05

---

## Purpose

"Rich Trades Smart Trades" is marketing copy. It promotes the wheel strategy and Rich Dad
financial education products. This document audits every numerical claim and credential
assertion in the PDF against verifiable external sources. None of this is personal attack;
it is due diligence on the source material that motivated this project.

---

## Claim 1: "150% Annual Return"

**Source in PDF:** Chapter 4 — "That's $60,000 per year on $40,000 of capital.
That's a 150% annual return." Also: "Five positions...That's $25,000 per month.
$300,000 per year" on $200,000 capital.

**Audit:**

The CBOE PutWrite Index (PUT), which systematically sells one-month at-the-money S&P 500
puts and reinvests collateral in T-bills, has delivered approximately 9-10% annualized since
inception in 1986. This is the academically documented long-run return for a systematic,
diversified put-selling strategy.

The BXM (covered call on S&P 500) has delivered approximately 8-9% annualized over the
same period.

The TastyTrade research archive (publicly available at tastylive.com/shows/research) has
published extensive back-testing of short-put strategies on individual equities. Their
documented results on 45-DTE puts at 30-delta (approximately 10-15% OTM) on liquid large-cap
stocks show:

- Annualized premium yield: 15-25% on notional in favorable volatility environments
  (VIX 18-25).
- Net annualized return after assignment losses and commissions: 10-18% in normal years.
- Catastrophic drawdown years (2008, 2020): significant paper losses requiring months of
  recovery even on quality underlying stocks.

No systematic, audited, multi-year track record for individual retail investors running the
wheel on 5 positions shows 150% annual returns sustained over 3+ years. The figure in the
PDF is an example constructed from a single favorable month extrapolated to a year. It
requires: maximum VIX, perfect stock selection, zero assignment losses, zero commissions,
and immediate reinvestment at the same rate. This is not a return expectation; it is a
marketing ceiling case.

**Verdict: The 150% figure is a ceiling-case example constructed to maximize impressiveness.
Realistic sustainable annual returns are 10-20% in favorable conditions. This is still
attractive but requires accurate framing to make sound capital allocation decisions.**

---

## Claim 2: "85% of Options Expire Worthless"

**Source in PDF:** Chapter 4 — "85% of options expire worthless. The odds are in MY favor."

**Audit:**

The OCC (Options Clearing Corporation) publishes annual statistics on option outcomes.
Typical breakdown for equity options:

- Closed before expiration (trader exits position early): approximately 55-65%
- Expired worthless: approximately 20-25%
- Exercised/assigned: approximately 10-15%

The "85% expire worthless" figure conflates two different things: (a) the observation that
out-of-the-money options, taken as a class, expire worthless most of the time, and
(b) the claim that selling puts is therefore profitable 85% of the time.

These are not equivalent. An option that expires worthless produced a profit of the full
premium. An option that is exercised produces a cost that may exceed many months of
collected premium. One bad assignment on a declining stock (e.g., stock drops from $40
to $25 after you're assigned at a $40 strike) erases 6-10 months of $500/month premiums.

The real metric is expected value: (probability of expiring worthless * premium received)
minus (probability of assignment * average assignment loss). For a quality underlying stock
with conservative strike selection, this expected value is positive and approximately in the
10-20% annualized range documented above.

The "odds are in MY favor" framing is misleading because it conflates outcome frequency
with expected value. The option buyer is paying for insurance with positive expected value
for them in tail scenarios. The put seller profits from the frequency but takes concentrated
tail risk.

Source: OCC Annual Report statistics (theocc.com/market-data); Natenberg "Option Volatility
and Pricing" Chapter 10; Sinclair "Volatility Trading" Chapter 3.

**Verdict: The 85% figure is a partial statistic used to imply systematic edge. The complete
picture requires expected value analysis including assignment scenarios.**

---

## Claim 3: Tax Treatment

**Source in PDF:** Chapter 2 — "The income I generate from selling options is portfolio income.
It's taxed at a lower rate than the money you make at your job."

**Audit:**

This is partially true and potentially misleading for a Utah resident.

**Equity options (individual stock puts and calls) — correct tax treatment:**

- Short-term capital gains (options held less than one year): taxed at ordinary income rates.
- Short-term options on individual equities are almost always taxed as short-term gains
  because the wheel strategy uses monthly (30-60 day) expirations.
- At Boubacar's likely income level, this means federal rates of 22-32%.

**Section 1256 contracts (NOT what the wheel uses):**

Section 1256 applies to regulated futures contracts and index options (SPX, NDX, etc.),
not to options on individual equities (AAPL, GEV, etc.). Index options under Section 1256
receive 60/40 treatment: 60% long-term capital gains rate and 40% short-term, regardless
of holding period. The wheel strategy on individual stocks does NOT qualify.

**Assignment and wash sale rules:**

If you sell a put and get assigned (forced to buy the stock), your cost basis becomes the
strike price minus the premium received. This is correct. However, if you sell the stock
at a loss and immediately re-enter a similar position (e.g., sell another put on the same
stock below your exit price within 30 days), wash-sale rules may defer the loss. This is
a non-trivial bookkeeping requirement.

**Utah state tax:**

Utah has a flat state income tax rate of 4.55% (2024 rate). Short-term capital gains
are taxed at the same rate as ordinary income in Utah. There is no preferential state
treatment for options income.

**Total marginal rate:**

At moderate income: federal 22% + Utah 4.55% = approximately 26-27% marginal on
options premium income. At higher income: federal 32% + Utah 4.55% = approximately
37% marginal.

The PDF's claim that this is "portfolio income taxed at a lower rate" is accurate only
if you hold positions longer than one year (not wheel-compatible) or use index options
(not the PDF's stated strategy). For the actual wheel strategy on individual equities,
the income is short-term gains taxed as ordinary income.

**Verdict: The tax advantage claim is inaccurate for the specific strategy described.
Consult a CPA who knows short options taxation before assuming favorable rates.**

---

## Claim 4: Kiyosaki Credibility Assessment

**The Contrarian question: should this source be trusted?**

Documented facts (publicly verifiable):

- Rich Global LLC, a Kiyosaki-affiliated company, filed Chapter 7 bankruptcy in 2012 after
  losing a $23.7M judgment in favor of Learning Annex (Wall Street Journal, 2012;
  Forbes "Robert Kiyosaki's Company Files For Bankruptcy," August 2012).

- The identity of "Rich Dad" (described as a real mentor) has been disputed. Kiyosaki has
  given inconsistent accounts. Sharon Lechter (co-author) has not publicly confirmed the
  literal accuracy of the character. CBS News (2003) reported extensively on the uncertainty.

- Kiyosaki has made high-profile incorrect predictions: silver crash, dollar collapse, market
  crashes at specific dates. These are widely documented in financial media 2009-2023.

- The Better Business Bureau has received complaints about Rich Dad Education programs
  (the seminar business associated with the brand) regarding upsell pressure tactics.

- The FTC has issued warnings about seminar-based investment education businesses broadly.
  No direct FTC action against Kiyosaki personally as of 2024.

**What this means for the PDF:**

The wheel strategy itself is real, well-documented in academic literature, and taught by
credible practitioners (TastyTrade, CBOE, IBKR Campus, Schwab) who have no financial
incentive to oversell it. Kiyosaki's version of the strategy contains the same core mechanics.
His specific numbers (150%, 85%) are marketing inflations. The source is unreliable for
quantitative claims. The conceptual framework (cash flow vs. capital gains, option premium
as rent) is a legitimate reframe.

**Use the strategy. Discard the numbers. Distrust the credentials.**

---

## Claim 5: The 2008 Anecdote ("I made money every single month")

**Source in PDF:** Multiple references — "During the 2008 crash I sold puts on quality
companies at huge discounts and collected massive premiums...I collected cash while they
panicked."

**Audit:**

This is technically possible but requires strict conditions:

- In Q4 2008, implied volatility (VIX) reached 80+. Put premiums were enormous.
- A wheel practitioner selling deep out-of-the-money puts (20-30% OTM, which was unusual
  distance at that VIX level) could collect substantial premiums.
- However, many "quality companies" of 2008 (Lehman, Bear Stearns, Wachovia, AIG, Citigroup,
  GE Capital) became worthless or near-worthless. "Quality" judgment during the crisis
  was extremely difficult in real time.
- A put seller on Citigroup in September 2008 who was assigned at a $15 strike saw those
  shares fall below $1. No amount of monthly premium covers a 95% loss on assignment.

The 2008 anecdote is plausible if Kiyosaki was selective about underlying stocks and
strike selection. It is presented as if the strategy was trivially safe during a crisis.
It was not. The strategy was viable in 2008 only with extreme care about which companies
to put on.

**Verdict: The anecdote is survivorship-selected. It omits every practitioner who was
assigned on stocks that kept falling. Not fabricated, but not representative.**

---

## Claim 6: "$300K on $200K = 150% per year" Math

From Chapter 4: five positions at $40,000 each = $200,000 capital, each generating $5,000/mo,
equals $25,000/month or $300,000/year.

**The math errors:**

1. $5,000/month per contract on a $40,000 position = 12.5% per month premium yield.
   At 30-45 day expirations, this requires roughly 25-50% implied volatility for at-the-money
   or 5-10% OTM strikes. This is only available during high-volatility regimes (VIX 25+).
   In normal markets (VIX 15-18), the same position generates $1,500-2,500/month.

2. If all five positions get assigned simultaneously (which would happen in a market-wide
   downturn, the exact time when strikes are most likely breached), you have deployed
   $200,000 into equity positions that are now worth less than $200,000. You cannot sell
   the same contracts again until you either sell the stock (possibly at a loss) or
   the stock recovers above your strike.

3. The $300K figure requires continuous monthly compounding with zero assignment events
   across all five positions for 12 consecutive months. Historical base rates for at-the-money
   puts suggest assignment roughly 35-45% of the time. For five positions, at least one
   assignment in any given month is the expected outcome.

**Realistic math:**

On a $40,000 position with conservative 10-15% OTM strikes in a normal VIX environment:
- Monthly premium: $800-1,500 (2-3.75% of notional)
- Annual yield before assignments: 24-45%
- After accounting for occasional assignment events and capital tied in stock positions:
  realistic net annual return 10-18%

On $200,000 in aggregate: $20,000-$36,000 per year, not $300,000 per year.

**Verdict: The $300K projection is off by a factor of 8-15x under realistic conditions.
The actual return profile is attractive (10-18% annualized) but requires realistic framing.**
