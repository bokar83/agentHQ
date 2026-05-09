# Session Handoff - Reserve Works Decision Package - 2026-05-05

## TL;DR

Full Reserve Works (RW) wheel strategy decision package built, audited by second opinion (Claude Chat), and corrected with 12 material updates. Verdict confirmed: DEFER live capital, START paper trading by 2026-05-09. Memory saved. Agent build staged at agents/reserve_works/ with kill switch active.

## What was built / changed

- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/01_pre_council_framing.md -- 4 premises tested, 3 fail
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/02_kiyosaki_premise_audit.md -- PDF numbers refuted
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/03_strategy_reality_check.md -- real mechanics + 2020 walk-through
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/04_north_star_math.md -- corrected projection (8-12 yrs to $5K/mo)
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/05_fit_assessment.md -- DEFER verdict with reasoning
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/06_capital_allocation.md -- tier gates + stop-loss rules
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/07_learning_roadmap.md -- 12-week paper curriculum + journal template
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/08_sankofa_council_review.md -- 5 voices + chairman (simulated)
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/09_decision_artifact.md -- one-page summary (v2, post-audit)
- d:/Ai_Sandbox/agentsHQ/reports/reserve_works/sankofa_raw/ -- 5 individual voice files
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/__init__.py -- kill switch
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/rw_research_agent.py
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/rw_screening.py
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/rw_scoring.py -- updated Q30/L30/R25/I15/B5 post-audit
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/rw_journal_schema.sql
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/rw_voice_profile.txt
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/n8n_trigger_spec.md
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/README.md
- d:/Ai_Sandbox/agentsHQ/agents/reserve_works/scripts/projection_model.py -- verified working
- C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\project_reserve_works_state.md
- C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\feedback_rw_kiyosaki_numbers_wrong.md
- d:/Ai_Sandbox/agentsHQ/docs/handoff/2026-05-05-reserve-works-decision-package.md

## Decisions made

- Verdict: DEFER live capital. No live trading before 5 Tier 0 gates clear (earliest Q3 2026).
- Paper trading: green-lit immediately, thinkorswim, by 2026-05-09.
- Scoring formula locked: Q30/L30/R25/I15/B5 (Behavioral Fit added; Income reduced).
- Kill switch default: RW_ENABLED=false. Never flip before all gates clear.
- Crash protocol pre-committed: Monday covered-call rule, no improvisation.
- Tier 1 condition: CW Phase 1 must remain intact during live trading.
- Hard capital ceiling: 20% of total liquid net worth at any tier.
- Kiyosaki numbers rejected: 150% return false, 85% false, tax advantage false.
- Bondarenko 2019 (CBOE PUT Index 9.54% annualized) is the planning benchmark.

## What is NOT done

- Real Sankofa Council invocation (VPS-side): simulated locally. Recommend re-running council.py with 08 as input when at VPS.
- n8n workflow: spec written, not built. Build after paper trading starts.
- rw_watchlist: not populated. Boubacar must add tickers manually.
- Market data provider: not selected. yfinance for paper phase; Polygon.io Starter ($29/mo) for live.
- Open Decision: P2 (public content build) vs P4 (private capital channel). Must resolve by 2026-06-04.
- First Principles question unresolved: is wheel dominated by CW retainer / SW expansion as income vehicle?

## Open questions

1. P2 vs P4: is RW a public content series or a private capital channel? Decide by June 4.
2. First Principles (Sankofa voice 2): should Boubacar evaluate JEPI/XYLD/dividend ETFs vs wheel before live capital? 2-hour comparison exercise, not done.
3. Expansionist angle: build-in-public financial coaching product for SW buyers. Year-3 hypothesis. Filed, not actioned.

## Next session must start here

1. Confirm: did Boubacar open thinkorswim paper account by 2026-05-09? If yes, log first trade observation. If no, assess why.
2. Resolve P2 vs P4 decision (due 2026-06-04). One sentence answer.
3. If P2: outline the public content format (newsletter, Twitter thread series, Notion doc?).
4. If P4: park RW, do not touch agent until Q3 2026 gates review.
5. Next active project: Hotel Club de Kipe rebuild (see hotelclubkipe-rebuild-prompt.md -- already in docs/handoff/).

## Files changed this session

All new (none modified from pre-existing):
- reports/reserve_works/ (9 reports + 5 sankofa_raw files)
- agents/reserve_works/ (8 files + scripts/projection_model.py)
- docs/handoff/2026-05-05-reserve-works-decision-package.md
- memory/project_reserve_works_state.md
- memory/feedback_rw_kiyosaki_numbers_wrong.md
- memory/MEMORY.md (2 lines appended)
