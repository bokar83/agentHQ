# Review Gate - Hormozi Lead-Gen Skill Build

**Status:** AWAITING SHIP-IT FROM BOUBACAR.
**Date:** 2026-04-30
**Branch:** feature/atlas-clickable-notion-links (current; build did not touch this branch's existing files).
**No commits made. No production files modified. No live sequences changed.**

---

## What Was Built

### The Skill (Phase 4)

| File | Purpose | Lines |
|---|---|---|
| [skills/hormozi-lead-gen/SKILL.md](skills/hormozi-lead-gen/SKILL.md) | Brand-agnostic Hormozi lead-gen skill. Codifies $100M Leads + $100M Offers as a runnable procedure. | 455 |

### Research (Phases 1-3)

| File | Purpose | Lines |
|---|---|---|
| [research/hormozi-research-notes.md](research/hormozi-research-notes.md) | Source-anchored Hormozi framework reference. NotebookLM blocked; web research used per spec fallback. | 606 |
| [research/current-state-audit.md](research/current-state-audit.md) | 25-artifact audit of CW + SW lead-gen infrastructure. Severity-rated. | 523 |
| [research/decision-matrix.md](research/decision-matrix.md) | 5-axis scoring (29/50). Verdict: MERGE not REPLACE. Seed-email keep-in-flight call. | 233 |

### Lead-Gen System (Phase 5 - proposed enhancements + 2 new templates)

| File | Type | Purpose | Lines |
|---|---|---|---|
| [lead-gen-system/templates/cold-email-v1.md](lead-gen-system/templates/cold-email-v1.md) | **DIFF** | Enhancement of `templates/email/cold_outreach.py`. Adds Big Fast Value + proof anchor. VE: 5.25 → 6.75. | 139 |
| [lead-gen-system/templates/cw-t3-t4-t5-diffs.md](lead-gen-system/templates/cw-t3-t4-t5-diffs.md) | **DIFFS** | 3 surgical diffs to existing CW T3/T4/T5. Removes implied-client-roster risk. VE: all ≥7.0. | 228 |
| [lead-gen-system/templates/warm-reactivation-v1.md](lead-gen-system/templates/warm-reactivation-v1.md) | **NEW** | Missing warm-outreach kit. Template A (1st touch) + Template B (quarterly value drop) + 10-step process. | 173 |
| [lead-gen-system/templates/lead-magnet-brief-template.md](lead-gen-system/templates/lead-magnet-brief-template.md) | **NEW (brief, build separately)** | CW Margin Bottleneck Diagnostic spec. 7-step Hormozi compliance check. VE: 8.0. | 175 |
| [lead-gen-system/sequences/follow-up-cadence.md](lead-gen-system/sequences/follow-up-cadence.md) | **SPEC** | 8-touch cross-channel sequence design. Extends `skills/outreach/sequence_engine.py`. | 150 |
| [lead-gen-system/scripts/objection-handling.md](lead-gen-system/scripts/objection-handling.md) | **CONSOLIDATION** | CW + SW objection bank with Hormozi-aligned responses. Merges existing SW bank with new CW set. | 198 |
| [lead-gen-system/metrics/success-criteria.md](lead-gen-system/metrics/success-criteria.md) | **SPEC** | Floors before ship. LTGP/CAC math. Per-artifact gating. | 151 |
| [review-gate.md](review-gate.md) | **THIS FILE** | Phase 6 hand-off. | - |

**Total Phase 5 lines: 1,214. All within per-artifact caps.**

---

## Decisions Made and Why

### 1. Verdict: MERGE (not REPLACE, not A/B)

**Score:** 29/50 across 5 axes. Detailed reasoning in [decision-matrix.md](research/decision-matrix.md).

**Why:** The existing CW/SW infrastructure scores Hook 8/10 and Offer 8/10. The gaps are absence-shaped (missing channels, missing CW lead magnet, missing warm system) - additive, not corrective. REPLACE would burn 3-4 weeks of production code and the foundation is good.

**Confidence:** HIGH (per Phase 3 reasoning: direct read of every production cold-email template + sequence engine + morning runner + Hormozi research cross-validated 3+ sources per framework).

### 2. Seed-Email Call: Keep In-Flight, Swap New Leads

**Decision:** Let the 2026-04-29 in-flight CW T1 batch finish its 19-day sequence. Apply Phase 5 enhancement diffs only to leads added 2026-05-12+.

**Confidence:** HIGH for "keep in-flight" (sender reputation argument, no critical brand damage from a 6/10 email). MEDIUM-HIGH for the "swap new leads on 2026-05-12" timing - this aligns with the existing A/B reactivation date but Sankofa flagged a Contrarian view that 240 more sub-floor sends is a real cost. **Boubacar should review and confirm.**

### 3. Skill Scope: 455 lines, 2 worked examples (CW, SW). No hypothetical future venture example.

**Why:** Sankofa Council Pass 1 dropped the hypothetical example as premature abstraction. SKILL.md ships at 455 lines vs original 1200 cap - well-scoped.

**Karpathy WARN:** SKILL.md is 55 lines over Sankofa's revised 400-line target. The overage is in worked examples (Section 11). Acceptable trade-off but logged.

### 4. Phase 5 File Count: 7 files (vs Sankofa's revised 5)

**Karpathy WARN flagged this.** I added back `success-criteria.md` and `objection-handling.md` because the original spec required them. **Boubacar's choice:** keep all 7, or consolidate `success-criteria.md` into review-gate.md and link `objection-handling.md` from `signal_works_plan.md` instead. Both are recoverable in either direction.

### 5. CW T1 Diff Ships at Value Equation 6.75/10 (below 7.0 floor)

**Honest disclosure:** the proposed CW T1 diff scores 6.75/10 on the Value Equation self-check. The skill's own ship floor is 7.0.

**Sankofa Pass 2 disagreed:** Contrarian says hold; Executor says ship with a 200-email retest gate. **Chairman landed on Executor's side.** Boubacar can override.

**Path to 7.0:** add a real client name once SW client #1 closes, OR replace the Apex Tool Group reference with a real services-firm engagement when one closes.

---

## Diagnostic Call: System Design vs. Volume of Execution

**Original audit estimate:** 65% system, 35% volume.
**Sankofa-revised estimate:** 35% system, 65% volume.
**Final synthesized estimate:** ~50/50, contingent on the falsifier test below.

**Reasoning:**
- The Hormozi-shaped gaps in the system (missing warm channel, missing CW lead magnet, single-channel funnel) are real and the skill helps frame them. That's the system half.
- The cold-email channel is already Hormozi-grade structurally. What's missing on the cold side is volume (Rule of 100 not running) and reps. That's the volume half.
- The bottleneck is unknowable until Boubacar sends 3-10 warm messages by hand and we see the reply data.

---

## ⚠️ THE 24-HOUR WARM-DM FALSIFIER (binding test)

**Per the Sankofa Council, this is the gating test for whether the entire Phase 4-5 build was a system upgrade or a delay tactic.**

**Action:** Within 24 hours of this review-gate.md being created, Boubacar sends Template A (from `lead-gen-system/templates/warm-reactivation-v1.md`) to **3 names** from his 1st-degree LinkedIn network. By hand. Real personalization. Real send.

**Outcomes and what they mean:**

| Outcome (24h) | Diagnostic | Next session priority |
|---|---|---|
| 0 messages sent | The volume hypothesis is unfalsified. Build sessions defer to execution sessions until a paying client closes. | Pivot to execution-only |
| 3 sent, 0 replies | The warm-channel hypothesis is weaker than expected. Re-evaluate list quality, personalization depth, or test cold-email lift instead. | Cold-email lift test (the 100-lead enhanced T1 batch) |
| 3 sent, 1+ reply | Warm channel is real and high-leverage. Send 10 more by 5pm next day. List-build to 100. | Scale warm to 100 sends + Margin Bottleneck Diagnostic v1 build |
| 3 sent, 1+ reply BOOKS a call | Warm closes faster than cold. Pause cold expansion; double down on warm. | Run Discovery Call OS v2.0; lock in the close. Capture the close as the first SW or CW client. |

**This test runs even if Boubacar does not say "ship it" on the Phase 4-5 artifacts.** The artifacts can wait. The DM cannot.

---

## Open Questions for Boubacar Before Ship

These need explicit answers before any commit happens:

1. **MERGE verdict:** confirm or override. (Default: confirm.)
2. **Seed-email call:** keep in-flight + swap new leads on 2026-05-12, OR halt now and resume in 48h with the v1 diff? (Default: keep in-flight, lower friction.)
3. **CW T1 diff at 6.75/10:** ship with retest gate (Sankofa Executor view), OR hold for 7.0+ with real client name (Sankofa Contrarian view)? (Default: ship with retest gate.)
4. **Phase 5 file count:** keep all 7 files, OR consolidate `success-criteria.md` + `objection-handling.md`? (Default: keep all 7; they earn their keep at the spec stage.)
5. **SW HTML email vs. `sw_t1.py` ambiguity:** which is the live SW T1 in production? (Phase 2 audit, artifact #8. Severity 4. **Boubacar must clarify before any SW change ships.**)
6. **AI Visibility Score productization (Sankofa Expansionist flag):** ship as public web tool at signal-works.com/score within 7 days? (Not in Phase 5 scope but identified as missed leverage.)
7. **Margin Bottleneck Diagnostic v1 build:** schedule a focused session to build the actual web tool from the brief (1-2 days)? (Sankofa Pass 2 recommends.)

---

## Items Boubacar Must Review Before Deploying Anything

**Before any production change ships:**

1. Read [research/hormozi-research-notes.md](research/hormozi-research-notes.md) Section 12 (Anti-Patterns) - verify alignment with brand voice rules.
2. Read [lead-gen-system/templates/cold-email-v1.md](lead-gen-system/templates/cold-email-v1.md) - confirm the proposed T1 voice matches Boubacar's actual voice. The Big Fast Value paragraph in particular.
3. Read [lead-gen-system/templates/cw-t3-t4-t5-diffs.md](lead-gen-system/templates/cw-t3-t4-t5-diffs.md) - confirm the T4 reframing ("15 years inside services-firm operations (GE, Apex Tool Group, three-continent client work before that)") is factually accurate. **Apex Tool Group reference: confirm or replace.** This is the highest-risk fact-check item.
4. Read [lead-gen-system/templates/warm-reactivation-v1.md](lead-gen-system/templates/warm-reactivation-v1.md) Template A - adjust voice if it doesn't sound like Boubacar.
5. Read [lead-gen-system/sequences/follow-up-cadence.md](lead-gen-system/sequences/follow-up-cadence.md) - confirm the LinkedIn cross-channel layer is realistic given Boubacar's current LinkedIn cadence and account limits.
6. Run [skills/hormozi-lead-gen/SKILL.md](skills/hormozi-lead-gen/SKILL.md) cold on a non-CW non-SW persona (e.g., "redesign Studio's lead-gen") to verify the brand-agnostic claim. (Spec success criterion #3.)

---

## Low-Confidence Items (Named Explicitly)

These are areas where I am NOT confident and want explicit feedback:

1. **The Apollo CW ICP filter vs. SKILL.md Example A's ICP.** Example A says "12-40 employees, recently hired senior leader, margin-anxious in Q4." I did NOT verify this matches what Apollo is currently filtering on. There may be a gap between the skill's prescribed ICP and the running ICP.
2. **The "8 Catalyst Works diagnostic lenses" referenced in the lead-magnet brief.** Phase 1 research surfaced Hormozi's frameworks; Phase 2 mentioned Catalyst Works's 8 lenses (Theory of Constraints, Lean, etc.). I did NOT find a single CW document that lists all 8 lenses with their definitions. The brief references them as if they're documented; **they may be partially in Boubacar's head, not in the codebase.**
3. **The Discovery Call OS v2.0** referenced by `harvest.md` was not located on the filesystem. Severity-3 in the audit. The Phase 5 objection-handling spec assumes it exists; the actual call structure should be cross-referenced once located.
4. **The CW T1 v0 in-flight batch's actual reply data.** Yesterday's launch (2026-04-29) had no measured reply rate at the time of this audit. The 6.75/10 ship floor argument leans on "let's see the v0 data first." That data did not exist when this build was written.
5. **The "AI Visibility Score is licensable" claim** in the Sankofa Expansionist pass. Boubacar's `signal_works_plan.md` mentions white-label at $197/month. I treated this as confirmed; **it's a future-plan, not a tested business model.**
6. **The 8-touch cross-channel cadence's LinkedIn DM acceptance rate floor (40%).** Pulled from third-party industry benchmarks, not from Boubacar's actual LinkedIn data. **Unknown if his account converts at this rate.**

---

## What I Recommend (Sankofa-Synthesized)

**Order of operations, with timing:**

1. **WITHIN 4 HOURS:** Boubacar runs AI Visibility Score on 5 prospects in 5 niches (sanity check before any productization).
2. **WITHIN 8 HOURS:** Boubacar sends Template A to 3 names. **This is the falsifier.**
3. **WITHIN 24 HOURS:** Report back. Outcome shapes next session priority (per the table above).
4. **WITHIN 48 HOURS:** Boubacar makes the call on seed-email handling (keep in-flight vs. halt-and-swap).
5. **WITHIN 7 DAYS:** If warm DMs converted, build Margin Bottleneck Diagnostic v1 web tool (1-2 day focused session).
6. **WITHIN 7 DAYS:** If warm DMs converted, ship AI Visibility Score as public web tool at signal-works.com/score (1 day Vercel deploy).
7. **2026-05-12 onward:** Apply CW T1/T3/T4/T5 enhancement diffs to new leads (alongside existing A/B reactivation date).
8. **NEXT 100-LEAD BATCH:** Layer manual LinkedIn DMs at Day 2 + Day 6 + Day 13 per `follow-up-cadence.md` Phase B. Measure cross-channel lift vs. email-only baseline.

---

## What I Did Not Do (Explicit)

- Did NOT modify `templates/email/cold_outreach.py` or any `cw_t*.py` / `sw_t*.py`.
- Did NOT touch `skills/outreach/sequence_engine.py`.
- Did NOT change `signal_works/morning_runner.py` or its systemd timer.
- Did NOT halt CW auto-send. (Sender reputation argument; Boubacar's call.)
- Did NOT commit anything. The branch is unchanged.
- Did NOT push anything.
- Did NOT modify `MEMORY.md` or any memory file. (None of the discoveries this session warranted a memory write - they're either captured in the deliverables themselves or are skill-content.)
- Did NOT build the Margin Bottleneck Diagnostic web tool. Spec only.
- Did NOT productize the AI Visibility Score as a public web tool. Flagged.
- Did NOT send any warm DMs. That's Boubacar's action.

---

## Final Status

**Phase 1 ✓** Research notes (606 lines, source-anchored).
**Phase 2 ✓** Current-state audit (523 lines, 25 artifacts, severity-rated).
**Phase 3 ✓** Decision matrix (29/50, MERGE verdict, HIGH confidence).
**GATE 1 ✓** Sankofa Council Pass 1 (revised Phase 4-5 scope by 60%).
**Phase 4 ✓** SKILL.md (455 lines, brand-agnostic, 2 worked examples).
**Phase 5 ✓** 7 lead-gen-system files (1,214 lines total, all under caps).
**GATE 2 ✓** Karpathy audit (SHIP, WARN on Principle 2 logged).
**GATE 3 ✓** Sankofa Council Pass 2 (SHIP, recommends 24-hour warm-DM falsifier).
**Phase 6 ✓** This file.

**Awaiting:**
- Boubacar's "ship it" on the Phase 5 enhancement diffs.
- Boubacar's answers to the 7 open questions.
- The 24-hour warm-DM falsifier outcome.

**No commits will happen until all three are resolved.**
