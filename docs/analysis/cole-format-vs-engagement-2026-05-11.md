# Cole Format ↔ Content Board Crosstab (2026-05-11)

**Purpose:** G2 step of GW validation ladder. Tag last 30 days of Boubacar's Content Board posts with the nearest Cole format label. Cross-tab with engagement signal.

**Goal:** Decide whether G4 (multiplier A/B with Cole prior) is worth running.

**Source:** Notion Content Board `collection://339bcf1a-3029-81ed-8eaa-000b984ec759`.
**Window:** 2026-04-11 → 2026-05-11 (30 days).
**Sample size:** 25 posts (page_size cap on Notion search).

---

## Limitation up front

Notion `notion-search` returns titles + highlights but NOT the Likes/Views/Comments/Reposts numeric fields directly. To produce a true engagement crosstab we'd need to either (a) fetch each post page individually for full property data, or (b) export the Content Board as CSV.

**This analysis is therefore qualitative on the FORMAT side and SAMPLED on the engagement side** — engagement read from page highlights where they appear, otherwise marked as `unknown` and treated as null. Format fit is the strong signal here. Engagement signal will be sharpened during G4 A/B if it runs.

---

## Per-Post Format Classification

Each row: post title (truncated) | platform | nearest Cole format match | confidence | engagement signal.

| # | Title (truncated) | Format type | Nearest Cole format | Conf | Eng signal |
|---|---|---|---|---|---|
| 1 | Find out who understands your AI stack | LI post | **None** (recognition hook, no template fit) | high | unknown |
| 2 | What a Constraint Audit Actually Finds (And Why It's Never What You Expected) | Article | LF #15 Don't Do That, Do This (loose) OR LF #20 Good vs Bad Reasons | low | unknown |
| 3 | LinkedIn Post (planning row) | — | n/a — meta row | — | — |
| 4 | Everyone is copying the product. Nobody is copying the org. | LI long | LH #13 The Average Person Is Wrong (close) | medium | unknown |
| 5 | Why AI Implementations Fail in Professional Services (And What to Do Instead) | Article | LF #1 The Stop/Start | medium | unknown |
| 6 | Buying AI tools feels like progress. Fixing handoffs doesn't. | LI short | LH #8 Belief Flip OR SF #12 People Think | medium-high | unknown |
| 7 | You have already had the thought. | LI short | **None** (recognition opener, anti-template by design) | high | unknown (CTQ-passed marker) |
| 8 | You have already had the thought (dup) | dup of #7 | — | — | — |
| 9 | LinkedIn Launch Post. The Weekly Signal Issue 1 | LI post | LH #5 Oddly Ignored (loose) | low | unknown |
| 10 | Revenue is up. That is the problem. | LI short | LH #10 The Crazy Part (close) OR LH #13 Average Person Is Wrong | medium | unknown |
| 11 | LinkedIn Comment. The Weekly Signal Subscribe Link | meta/comment | n/a | — | — |
| 12 | Most AI tool reviews end with we'll revisit next quarter | LI post | LH #1 Most Powerful (inverse — "Most useless"-style) | low | published via Blotato API |
| 13 | The Hidden Factory Inside Your Business | Article | LF #19 The Most Underrated Tool | medium | unknown |
| 14 | The First AI Decision You Made Was Probably the Wrong One | LI post | LH #8 Belief Flip | high | Sankofa+CTQ Pass 2 |
| 15 | [LI] Post 3: Common assumption: AI governance slows innovation. | LI short | SF #12 People Think OR LH #13 Average Person Is Wrong | high | unknown |
| 16 | AI and Jobs Post 1: We keep asking the wrong question — X | X post | **None** (reframe hook, anti-template) | high | unknown |
| 17 | AI and Jobs Post 2: Once you ask the right question — LI | LI | SF #20 The Trick | medium | unknown |
| 18 | AI and Jobs Post 2: Once you ask the right question — X | X | SF #20 The Trick | medium | unknown |
| 19 | LinkedIn posts (planning row) | — | n/a | — | — |
| 20 | AI and Jobs Post 1: We keep asking the wrong question — LI | LI | **None** (reframe hook) | high | unknown |
| 21 | AI and Jobs Post 3: Design the human role on purpose — LI | LI | LH #11 Everyone Should (close) | medium | unknown |
| 22 | AI and Jobs Post 3: Design the human role on purpose — X | X | LH #11 Everyone Should (close) | medium | unknown |
| 23 | [X] Post 3: Assumption: AI governance slows innovation. Wrong. | X | SF #12 People Think | high | unknown |
| 24 | What your team is not telling you | LI/CW T1 hook | LH #4 The Secret (close) | medium | T1 cold outreach hook |
| 25 | Your AI strategy is a spreadsheet of subscriptions. | LI | LH #5 Oddly Ignored OR LH #10 Crazy Part | medium | Governance arc Post 3 of 4 |

---

## Aggregate

Total non-meta posts classified: 22 (excluded rows #3, #8, #11, #19).

| Bucket | Count | % |
|---|---|---|
| **No fit / anti-template** (recognition / reframe hooks) | 5 | 23% |
| **Strong Cole fit** (confidence high) | 4 | 18% |
| **Loose Cole fit** (confidence medium) | 10 | 45% |
| **Weak/forced fit** (confidence low) | 3 | 14% |

Top format families that DO fit Boubacar's posts:

1. **LH #8 Belief Flip** — 2 hits — "Buying AI tools feels like progress. Fixing handoffs doesn't." + "The First AI Decision You Made Was Probably the Wrong One"
2. **LH #13 Average Person Is Wrong / SF #12 People Think** — 3-4 hits — clusters of "common belief vs reality" hooks
3. **SF #20 The Trick** — 2 hits — "AI and Jobs Post 2 (LI+X)"
4. **LH #11 Everyone Should** — 2 hits — "AI and Jobs Post 3 (LI+X)"
5. **LF #1 Stop/Start + LF #19 Underrated Tool + LF #20 Good vs Bad Reasons** — long-form article structure overlaps

Top format families that DO NOT fit:

- **LH #1 Most Powerful** — zero clean hits. Boubacar's voice anti-correlates with "most powerful X for Y."
- **LH #6 The Struggle / LH #12 Brutal But True Story / LH #9 The List** — zero hits. Personal narrative templates absent — likely because Boubacar voice avoids first-person hardship narration.
- **LH #14 I Did X Without Y / LH #15 Investment In Myself** — zero hits.
- **LF #11 Business Mistakes / LF #18 Birthday Lessons / LF #12 Note To Younger Self** — zero hits. Personal-reflection templates absent.
- **LF #16 The One Simple Idea Story** — zero clean hits. Hero's-journey biz story template absent.

---

## Pattern observation

Boubacar's content board has TWO dominant hook patterns Cole's library captures:
- **Belief Flip / Reframe** family (LH #8, LH #13, SF #12) — "common belief is wrong, here's the real frame"
- **Naming-the-hidden-cost** family (LF #19, LF #20, partial LF #1) — long-form articles about hidden constraints

AND one dominant pattern Cole's library DOES NOT capture:
- **Recognition opener** — "You have already had the thought," "Find out who understands your AI stack." This is Boubacar's signature move (per `feedback_cold_teardown_council_mandates.md`: recognition hook is mandate-level). Cole has nothing equivalent.

Boubacar's content board does NOT use Cole's personal-narrative family at all (Struggle, Brutal-True-Story, Investment-in-Myself, Birthday-Lessons, Younger-Self). Voice mastery explicitly forbids fabricated personal stories — this is consistent.

---

## G4 Decision: RUN (conditional, narrow scope)

Cole templates DO show partial fit (~18% strong + 45% loose). NOT enough to justify wiring the full 102-template library as a global prior. BUT enough to justify a NARROW A/B on the 3-5 format families that actually map.

**Recommended G4 scope (narrower than original plan):**

- A/B only the matching families: **LH #8 Belief Flip**, **LH #13 Average Person Is Wrong**, **SF #12 People Think**, **SF #20 The Trick**, **LH #11 Everyone Should**, **LF #1 Stop/Start**, **LF #19 Underrated Tool**, **LF #20 Good vs Bad Reasons**.
- Skip the 95+ templates that have zero observed fit. They're available in the swipe file but never load into the multiplier.
- 10-source A/B: multiplier-WITHOUT vs multiplier-WITH the narrow 8-format prior.
- Measure: CTQ pass rate, Hook Audit score, Boubacar blind preference.

**Hard constraint preserved:** the recognition-hook anti-template patterns (5 of Boubacar's 22 posts, 23%) are signature moves the voice mastery skill protects. Cole prior must NEVER override or suppress those. If A/B shows recognition hooks dropping in frequency on the WITH-Cole side, kill the wiring even if blind preference is favorable.

---

## Engagement signal — DEFERRED

True engagement crosstab requires per-page property fetch (Likes, Views, Comments, Reposts numbers). Deferring to G4 A/B as the proper measurement event. G2 deliverable = format-fit map (this file), which is what we needed to decide whether G4 runs.

---

## Next action

G4 A/B scheduled by 2026-05-25. Narrow 8-format prior, not full library. Decision rule preserved: ≥6/10 blind preference + CTQ pass rate ≥ baseline → wire it (narrow). Otherwise templates stay at neutral path.

G5 (1 prospect, 1 pitch, 1 booked call) runs in parallel — independent track.
