# 08 — Sankofa Council Review
# Reserve Works Decision Package
# Generated: 2026-05-05
# Status: SIMULATED — Council infrastructure not invoked from local environment.
# Recommend re-running the real Council on the VPS with this document as input.

---

## Council Inputs

- Phase 1-4 research reports (01-04)
- Fit assessment and capital allocation (05-06)
- Learning roadmap (07)
- Build artifacts: rw_research_agent.py, rw_screening.py, rw_scoring.py
- Verdict under review: DEFER (live capital) / START NOW (paper only)
- Four premises under review: omnidirectional gain, market timing, GEV anchor, asymmetric risk

---

## Voice 1: The Contrarian

The analysis in this package is thorough and the verdict is probably correct, but it contains
a structural error that could produce a much worse outcome than the one it claims to prevent.

The DEFER verdict relies entirely on the premise that Boubacar will follow through on paper
trading after the Phase 1 gate clears. The document even acknowledges the failure mode in
05_fit_assessment.md: "After Phase 1 can become after Phase 2 and then when I have more
capital and then never." It names this risk and then proposes paper trading as the mitigation.
Paper trading is not a mitigation for this risk. It is the behavior that is at risk.

Here is the structural problem. The DEFER verdict creates a condition where doing nothing
costs nothing in the short term. There is no negative consequence to not opening a paper
trading account. There is no external deadline. There is no accountability mechanism.
The documents recommend completing 8 weeks of paper trading before Tier 1 but there is no
mechanism that enforces this or that escalates if it does not happen.

The person reading this package has already spent significant time on this analysis. That
time has discharge value: the thinking happened, the research is done, the decision package
exists. The typical behavior pattern after a thorough analysis is relief followed by
inaction. The analysis substitutes for action. The deck gets filed. The paper trading account
never gets opened.

The build in Phase 3 makes this worse. A sophisticated research agent now exists in the
repository. It cannot run (RW_ENABLED=false). It requires market data providers not yet
integrated. It requires the rw_watchlist to be populated manually. It requires an n8n
workflow built to spec. Every one of these pending steps is a dropout point.

The analysis also misses one failure mode entirely: the capital commitment problem in reverse.
When CW Phase 1 unlocks and cash starts flowing, lifestyle expansion, new business investments,
and scope creep will consume capital at exactly the moment when the DEFER gate clears.

There is also no discussion of what happens if the market moves dramatically between now and
the live capital deployment date. The opportunity described as "available anytime" is actually
regime-dependent.

**The biggest risk I see is:** the DEFER verdict combined with the complexity of the build
creates a high probability of indefinite postponement, meaning the learning outcome (which
is the real value of this project) never materializes regardless of the quality of the analysis.

---

## Voice 2: The First Principles Thinker

Strip away the Kiyosaki framing, the ChatGPT scaffold, the wheel strategy mechanics, and the
agentsHQ build. What is actually being solved here?

The problem is: Boubacar has capital that is currently earning below its potential return.
He wants to change this. He has identified one specific instrument (wheel strategy on
individual equities) as the vehicle. He has read a marketing document that inflated the
expected returns. He has now received corrected projections.

When you rebuild from that problem statement, several things become visible:

The real constraint is not capital. It is time and decision quality.

An open options position is not like a savings account. It requires monitoring. It requires
a decision framework that must be held in working memory: what is my strike, what is my
cost basis, what do I do if the stock moves toward my strike, what is my stop-loss rule.
These are not passive facts. They require periodic retrieval and evaluation.

The first principles question the analysis does not ask is: is the wheel strategy the correct
instrument for the problem, or is it the instrument that was presented first by the PDF?

Consider the alternative. Boubacar has capital earning 4-5% in a high-yield savings account.
He wants to earn more. There are instruments that target 10-15% annualized with near-zero
active management after setup: index ETFs with covered call overlays (JEPI, XYLD), interval
funds, real estate crowdfunding platforms, dividend growth ETFs. These are not as
intellectually interesting as the wheel. But they are closer to "money working while I work
on CW/SW" than the wheel is.

If the honest problem is "deploy idle capital at better returns with minimal management
overhead," the wheel may be right but it is not the only answer, and the analysis treats it
as the only answer because that is what the PDF presented.

**The real question is:** what is the simplest instrument that earns 10-15% on idle capital
with the minimum required weekly decision overhead, given that Boubacar's primary leverage
at this stage is his ability to build CW and SW, not his ability to manage options positions?

---

## Voice 3: The Expansionist

The analysis correctly sizes the wheel strategy as a 10-15 year path to $5K/month from $50K.
That is the right number. But the analysis frames this as the maximum ambition for RW. It is not.

The wheel strategy, practiced consistently for 3-5 years, builds a transferable professional
capability: identifying quality underlyings, reading option chains, managing strike selection,
executing a disciplined income strategy.

The larger play is using this as the foundation for a systematic portfolio management coaching
service. Not a hedge fund. Not a retail advisory. Something in between that Boubacar's
existing consulting framework could support: a systematized financial strategy coaching service
for solopreneur and SMB operators who are in the same position he is now.

The target market is the Signal Works buyer. The SMB owner who has $20K-$100K sitting in a
bank account earning nothing, who wants cash flow but does not have the skill or time to learn
independently, and who does not trust advisors who push mutual funds. This is the exact buyer
Signal Works is already reaching.

A "what to do with your business cash" service that coaches them through year one of the wheel
strategy is a natural extension. This is not Kiyosaki repackaging. It is a legitimate
skill-transfer service with documented methodology.

The market size is larger than Boubacar's personal portfolio income. If 20 SMB owners pay
$2,000/year for financial strategy coaching, that is $40,000/year from one offering. That is
3x the realistic income from a personal $50K wheel account.

The timing works. Boubacar is building the skill now. By the time 18 months pass, he will have
a documented learning journey that is itself a marketing asset. The build artifacts in Phase 3
are directly repurposable as course or coaching infrastructure.

**The bigger play nobody mentioned is:** the wheel strategy skill Boubacar is building is
the curriculum for a financial coaching product targeted at Signal Works buyers who need a
smarter home for their business cash, potentially producing $40K-$80K/year from the same
effort that would otherwise produce $15K-$25K/year from a personal portfolio.

---

## Voice 4: The Outsider

I walked in cold and read this package. Here is what the insiders missed.

You have a pre-revenue consulting business targeting $5K/month by June 2026. You have an
active outbound sales channel. You have a pending vehicle purchase. You have a family.
And you just produced a 40-page research package on stock options, built five Python modules,
wrote a database schema, and spec'd an n8n workflow.

The most expensive thing in this document is not the options capital. It is the 6-12 hours
to produce this analysis, plus the ongoing bandwidth to maintain the agent code, monitor
paper trading, and eventually manage live positions.

From the outside, I notice the research package for the options strategy is more developed than
any piece of research described for CW lead generation or SW conversion. This is a resource
allocation signal. The interesting problem (options mechanics, agent automation) attracted more
investment than the urgent problem (close CW clients, convert SW leads).

The DEFER verdict is correct. But the package underweights the cost of producing it.

The outsider question: what would the equivalent 6-12 hours of effort have produced if
directed at SW outreach or CW prospect research? At $997 setup and $497/month, one closed
client would produce more real income than the expected monthly income from a live wheel
account in year one.

The agent build is clean. But an agent requiring a market data API, manual watchlist,
n8n workflow, and live capital prerequisites before producing any value is a technical
solution to a problem that does not yet exist, built before the prerequisite problems are solved.

Building interesting infrastructure before the revenue exists is a pattern. It produces
good code and delayed income.

**From the outside, the thing you are not seeing is:** the hours spent building the RW agent
are competing with the hours required to close the CW/SW revenue that gates all the other
decisions, and the document meant to defer RW has made it a major focus of this session.

---

## Voice 5: The Executor

I only care about Monday morning. What happens?

The six DEFER prerequisites are listed in a markdown file. There is no mechanism that tracks
whether they are being met. No calendar reminder. No checkpoint agent. No accountability loop.
The six gates exist on paper.

The plan has three actionable items and four deferred items.

Actionable now (this week):
1. Open paper trading account. Specific platform, specific completion state.
2. Add 3-5 tickers to rw_watchlist in PostgreSQL.
3. Read IBKR Campus "Basics of Options" module this weekend.

"Open a paper trading account today" appears in 07_learning_roadmap.md. It does not appear
in the decision artifact (09_decision_artifact.md). If the first concrete action is buried in
page 5 of a learning roadmap, it does not happen.

The decision artifact needs one concrete action with a specific completion state and a
deadline of this week: "By [date], confirm paper trading account is open by logging the
account name and first paper trade in rw_trade_journal."

Without a completion state that is checkable, the action is a resolution, not a plan.

The Expansionist's financial coaching angle is a year-3 idea. Building the skill requires
paper trading. Paper trading requires an account. The account requires 15 minutes on Monday.

**The concrete first step is:** open a paper trading account (thinkorswim or IBKR) before
Friday of this week and sell one simulated cash-secured put on any large-cap stock using
strike criteria from 07_learning_roadmap.md, then log it in rw_trade_journal.
If there is not one, this plan is not ready.

---

## Chairman Synthesis

**Disagreements surfaced:**

The Outsider and Contrarian agree on a meta-level problem: the analysis has consumed
significant effort that should have been directed at CW/SW revenue. They disagree on the
primary risk: the Contrarian focuses on indefinite postponement of RW; the Outsider focuses
on the opportunity cost of building RW infrastructure now.

The First Principles voice raises the most uncomfortable question: is the wheel strategy
the right instrument at all, given the alternative of passive income instruments requiring
less active management? None of the other voices engaged with this directly. The Expansionist
implicitly endorses the wheel strategy by proposing a coaching product built on it. These two
voices are in tension and the Chairman will not collapse it.

The Executor and Contrarian agree on the accountability problem. The plan has no enforcement
mechanism for the paper trading prerequisite. This is a real gap.

The Expansionist's financial coaching angle has merit but zero specificity. "Signal Works
buyers might pay $2,000/year for coaching" is a hypothesis that requires validation, legal
review, and positioning work. It is not a plan. It is a direction worth noting.

**What the Chairman confirms:**

The DEFER verdict for live capital is correct. The research is sound. The Kiyosaki audit is
thorough and necessary. The projected math (10-15% annualized, $400K capital for $5K/month)
is accurate and a significant correction from the PDF's claims.

The build artifacts are clean, deployable, and correctly limited. The kill switch is good
practice. The scoring model and screening logic are conservative and appropriate.

**What the Chairman requires before closing:**

1. The decision artifact (09) must include one specific, checkable action due this week.
   "Open paper trading account by [specific date]" not "open one soon."

2. The First Principles concern about alternative instruments (JEPI, XYLD, dividend ETFs)
   is not resolved in the package. Before Boubacar deploys live capital to the wheel,
   he should explicitly evaluate whether a lower-management instrument achieves 80% of
   the return at 20% of the effort. This is a 2-hour comparison exercise, not a second
   40-page package.

3. The Expansionist's coaching product idea should be noted as a Year 3 hypothesis, not
   acted on now. File it. Revisit after Phase 1 unlock and 12 months of documented
   wheel practice.

4. The Contrarian's concern about capital timing (market may be expensive by Q3 2026
   when live capital gates clear) is valid. Add a VIX/premium availability check to the
   live capital deployment decision: if VIX is below 14 at the time of first live trade,
   reduce position size by 50%.

**Final verdict: DEFER (live capital) / START NOW (paper, this week).**
The disagreements between voices are structural tensions worth noting but do not change
the verdict. The primary urgency remains CW Phase 1 unlock.

The agent build should be kept but not actively developed further until paper trading
is underway. Spending more build time on RW before paper trading starts is the exact
misallocation the Outsider identified.
