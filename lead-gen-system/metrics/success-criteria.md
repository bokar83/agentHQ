# Success Criteria - Hormozi-Aligned Floors

**Type:** Spec - defines floors BEFORE shipping any artifact.
**Hormozi alignment:** YES. Per $100M Leads, every campaign launches with explicit unit-economics math; nothing ships without floors.
**Status:** ACTIVE. These floors govern Phase 5 ship decisions.

---

## Why Floors Matter

Hormozi's hard rule: no campaign launches without LTGP/CAC math. Per Phase 1 research, Section 12, anti-pattern #10. Floors are the falsifiability test. If actuals fall below the floor, kill the artifact. If actuals beat the floor, scale via More-Better-New.

The floors below are derived from:
- Hormozi's published warm-outreach benchmarks (1 paying client / 100 reach-outs).
- Cold-email industry benchmarks (cited as "field-standard," not Hormozi-canonical).
- The current CW/SW unit economics (Signal Session $497, SW Tier 1 $500 setup + $497/mo).

---

## Cold Email Floors (CW + SW)

| Metric | Target | Floor | Kill threshold |
|---|---|---|---|
| Open rate | 40% | 25% | <15% |
| Reply rate (T1-T5 combined) | 8% | 5% | <2% |
| Calendly book rate (out of repliers) | 25% | 15% | <8% |
| Calendly book rate (out of sends) | 2% | 1% | <0.3% |
| Show-up rate (booked → attended) | 80% | 60% | <40% |
| Close rate (attended → paid) | 25% | 10% | <5% |
| Net: paying clients per 100 cold sends | 0.5 | 0.15 | <0.05 |

**Kill rules:**
- If open rate <15% over 100 sends → subject line is broken, hold sequence, fix subject.
- If reply rate <2% → hook is broken or list is wrong, halt new sends, audit ICP.
- If close rate <5% → offer is broken, sales conversation is misaligned, audit Discovery Call OS.

**Re-baseline rule:** if actuals fall in the gap between Floor and Kill threshold, give it 200 more sends before deciding. Statistical noise is real at low volumes.

---

## Warm Outreach Floors

| Metric | Target | Floor | Kill threshold |
|---|---|---|---|
| Reply rate (Template A) | 20% | 10% | <5% |
| Free-offer accept rate (out of repliers) | 25% | 15% | <8% |
| Free-to-paid conversion | 25% | 10% | <5% |
| Net: paying clients per 100 warm reach-outs | 1.25 | 0.5 | <0.15 |

**Kill rules:**
- If warm reply rate <5% → list is wrong (not warm enough) OR personalization is too generic. Re-build list.
- If free-offer accept rate <8% → offer is too high-commitment or too generic. Tighten.
- If free-to-paid <5% → the free deliverable doesn't translate to paid intent. Either upgrade the free deliverable or rethink the upsell.

**Distinction:** warm reply rate floor is HIGHER than cold (10% vs 5%) because warm contacts have a baseline of trust. If they're not replying at warm rates, the list is mis-classified.

---

## Lead Magnet Floors (CW Margin Bottleneck Diagnostic)

| Metric | Target | Floor | Kill threshold |
|---|---|---|---|
| Diagnostic completion rate (start → email submit) | 50% | 30% | <15% |
| Email-open rate on report delivery | 70% | 50% | <30% |
| Calendly book rate from report | 15% | 5% | <2% |
| Net: Signal Sessions booked per 100 magnet starts | 2.5 | 0.5 | <0.1 |

**Kill rules:**
- Completion rate <15% → too many questions or too much friction. Reduce.
- Report-open rate <30% → email subject broken, OR user's email expectation didn't match. Re-write subject.
- Book rate <2% → report doesn't create thirst for the paid offer. Re-design the CTA + the implicit problem-reveal.

---

## Sequence-Wide Floors (the funnel math)

For the full 8-touch sequence to be unit-economics-positive:

```
Cost per cold send (manual operator time + tool cost):  ~$2 / lead
Avg revenue per converted lead (CW Signal Session):     $497
Required conversion rate to break even:                 0.4%
```

**LTGP/CAC requirement (per Hormozi):** ≥3:1.
- LTGP = Signal Session $497 + estimated $1500 SHIELD upsell @ 30% conversion = $897 average LTGP.
- CAC at 0.5% close rate from 100 sends ($200 lead-gen cost) = $400 CAC.
- LTGP/CAC = 2.24:1 → BELOW the 3:1 floor.

**Implication:** at current floors, the cold-email channel is barely net-positive. Fix paths:
1. Increase Signal Session price (CW) - TBD
2. Improve close rate (Discovery Call OS work) - recommended
3. Reduce CAC by increasing reply rate (better hook + cross-channel) - Phase 5 enhancement spec
4. Add upsell density (SHIELD attach rate) - out-of-scope for this skill

**Lock the LTGP/CAC math before launching paid ads.** Hormozi's hard rule.

---

## Phase 5 Artifact Floors (specific)

For each Phase 5 deliverable, the gating floor before ship:

| Artifact | Floor before ship |
|---|---|
| `cold-email-v1.md` (CW T1 enhancement) | Value Equation ≥7/10 self-score (currently 6.75 - almost passes; ship if user accepts) |
| `cw-t3-t4-t5-diffs.md` | All 3 diffs ≥7/10 Value Equation (T3=7.0, T4=7.5, T5=8.25 - all pass) |
| `warm-reactivation-v1.md` | Per warm-floors above; require 100 hand-sends before ship + automate |
| `lead-magnet-brief-template.md` | Build only after warm-DM falsifier test (per Phase 6) |
| `follow-up-cadence.md` | Manual layer first; automate only after ≥30% reply lift over 100-lead batch |

---

## Reporting Cadence

Hormozi's "Better" axis requires data. Set a weekly reporting cadence:

- **Every Monday morning:** pull last 7 days of:
  - Sends (cold + warm + content)
  - Opens / replies / books / closes
  - LTGP / CAC delta vs prior week

- **Every 4 weeks:** Review Floor compliance per artifact above.
- **Every quarter:** revisit floors themselves. Tighten if performance is consistently above; loosen if structurally below.

**Where this lives:** new Notion view in the existing CW/SW tracking, OR a `signal_works/` weekly report. Ideally automated via the morning runner. Not in scope for this Phase 5 ship - flagged for next session.

---

## Anti-Patterns Refused

- Vanity metrics. (Open rate alone is meaningless without reply rate.)
- Floors set after the fact. (Hormozi: lock floors BEFORE you ship, so you don't move them when results disappoint.)
- "It's still early" syndrome. (200 sends is enough signal for kill/keep on most metrics.)
- Reporting without action. (If a floor is breached for 2 consecutive weeks, the artifact must change.)

---

## Output Contract

This spec is itself a Hormozi-grade artifact. Self-check:

- ICP: operators across CW + SW. ✓
- Channel: governs all 4 Core channels. ✓
- Lead magnet: covered. ✓
- Hook: floors include reply-rate-as-hook-test. ✓
- Offer: floors include LTGP/CAC. ✓
- CTA: every artifact has a kill rule. ✓
- Follow-up plan: weekly reporting cadence. ✓
- Success criteria: defined for every metric. ✓
- Anti-patterns refused: 4 listed above. ✓
