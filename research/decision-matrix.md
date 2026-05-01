# Phase 3: Decision Matrix and Verdict

**Date:** 2026-04-30
**Inputs:** Phase 1 (research/hormozi-research-notes.md), Phase 2 (research/current-state-audit.md)
**Output:** Single forced-close verdict on the existing CW/SW lead-gen system.

---

## Scoring (5 axes, 1-10 each)

### Axis 1: Buyer Trigger Clarity

> Pain named, dream outcome named, time delay realistic, effort honest, likelihood credible.

**Score: 6/10**

**Reasoning:**
- **Pain named:** YES on both brands. CW: "where is your margin actually going?" → bottleneck/handoff/approval-loop pain. SW: "is your business invisible on ChatGPT?" → AI-search invisibility pain. Both pass the falsifiability test.
- **Dream outcome named:** PARTIAL. CW dream is "find and remove the constraint" - abstract, not in prospect's words. SW dream is "be the business AI recommends" - sharper. Neither is grounded in case-study language.
- **Time delay realistic:** YES. CW = 90-min Signal Session. SW = 2-week build, monthly cadence. Both honest.
- **Effort honest:** YES. CW asks for one reply. SW asks for one click on a demo.
- **Likelihood credible:** WEAK. No real client proof on either brand. Boubacar's GE/3-continents biographical authority does work, but it's not "X client got Y outcome in Z time."

**The 4-point penalty is concentrated on dream-outcome specificity and likelihood proof.**

---

### Axis 2: Channel Coverage

> Warm + Cold + Posting + Paid (Core Four).

**Score: 2/10**

**Reasoning:**
- **Warm:** ZERO. No system exists. Boubacar has 15 years of contacts (GE, 3 continents) sitting unmined.
- **Cold:** STRONG. Best-in-class infrastructure (sequence engine, score engine, voice personalizer, niche demos). Running at ~20/day vs Hormozi's 100/day floor.
- **Posting:** NEAR-ZERO. LinkedIn intermittent, no system, no compounding.
- **Paid:** ZERO. (Appropriate - Hormozi says don't run paid until activation order channels 1-3 are live.)

**1 of 4 channels at production grade. 1 of 4 at near-zero. 2 of 4 at zero.**

The penalty here is the largest in the matrix. Hormozi's whole thesis is that the Core Four is a portfolio, not a menu. Single-channel businesses break.

---

### Axis 3: Hook Strength

> Specificity, curiosity, contrarian angle.

**Score: 8/10**

**Reasoning:**
- **CW T1 hook** ("Where is your margin actually going?" → "Most businesses aren't losing margin to bad strategy. They're losing it to one bottleneck...") has all three Hormozi hook qualities: specificity (margin), curiosity (where is it going?), contrarian (not strategy → operations). This would land on Hormozi's top shelf.
- **SW T1 hook** ("Open ChatGPT and type: 'who is the best [niche] in [city]?' If your business is not in the answer, someone ready to hire just called your competitor instead.") is concrete, verifiable in 10 seconds, time-bound. Best of both brands.
- **SW HTML email subject** ("ChatGPT doesn't know [Business Name] exists - your AI score: [X]/100") names the specific business and gives a number - Hormozi-grade.

**The 2-point penalty is for the absence of a hook *bank*.** Hooks are tested via volume, and Boubacar has one hook per brand. Hormozi's Better axis (one test per week per platform) requires a stable of hooks rotating through.

---

### Axis 4: Offer Specificity

> One ICP, one promise, one price logic.

**Score: 8/10**

**Reasoning:**
- **One ICP per brand:** YES on SW (local SMBs in 2 niches: healthcare/pro-services, home services). PARTIAL on CW (mid-market leadership teams, but ICP filter for Apollo seems to be company-size + industry - fuzzy).
- **One promise:** YES on SW ("become the business AI recommends"). PARTIAL on CW (margin/bottleneck/AI strategy bleed into one another in the sequence).
- **One price logic:** YES on both. SW: $500 setup + $497/$797/$997 monthly tiers. CW: $497 Signal Session, $500 SaaS Audit, $20K+ SHIELD. Each priced clearly.

**The 2-point penalty is on CW's offer-stack overlap (Signal Session vs SaaS Audit vs "AI department" SKU sometimes feel like alternatives, sometimes like a stack).** Hormozi: one Grand Slam Offer at a time, anchored.

---

### Axis 5: Follow-Up Depth

> Number of touches, trigger conditions, channel switching.

**Score: 5/10**

**Reasoning:**
- **Number of touches:** SW = 4 (T1-T4 at Day 0/3/7/12). CW = 5 (T1-T5 at Day 0/6/9/14/19). Hormozi's floor: 8 cross-channel.
- **Trigger conditions:** Day-gap based only. No "opens but no reply → switch channel" trigger. No "clicks but no Calendly" trigger. No segmentation by behavior.
- **Channel switching:** ZERO. All touches are email. Hormozi's 8-touch rule explicitly assumes email + LinkedIn + phone rotation.
- **Reactivation:** ZERO. T5 → opt_out → vanish. No quarterly value drops to dormant list.

**The 5-point penalty is on the channel-switching gap (which is shared with Axis 2) and the absence of behavioral triggers.**

---

## Total Score

| Axis | Score | Weight | Weighted |
|---|---:|---|---:|
| 1. Buyer trigger clarity | 6/10 | 1.0 | 6 |
| 2. Channel coverage | 2/10 | 1.0 | 2 |
| 3. Hook strength | 8/10 | 1.0 | 8 |
| 4. Offer specificity | 8/10 | 1.0 | 8 |
| 5. Follow-up depth | 5/10 | 1.0 | 5 |
| **Total** | | | **29 / 50** |

---

## Verdict: **MERGE**

> The Hormozi skill MERGES with the existing CW/SW system. We do NOT replace.

### Why MERGE (not REPLACE)

1. **Foundation is Hormozi-grade where it exists.** Hooks score 8/10. Offers score 8/10. Cold-email infrastructure is genuinely better than what Hormozi shows in his own examples. Replacing would destroy more value than it adds.
2. **Production assets compound on the foundation.** The score engine, voice personalizer, sequence engine, niche demo sites are all leverage that took weeks to build. A skill should ride on top of these, not blow them up.
3. **Yesterday's seed emails are 6/10 Hormozi structurally.** Not strong enough to brag about, not weak enough to kill. MERGE = keep them running, modify next batch.
4. **The real gaps are absence-shaped, not presence-shaped.** Channel coverage is the biggest gap. You cannot fix an absence by replacing a presence - you have to add new channels. That's MERGE work, not REPLACE work.

### Why NOT A/B

1. **A/B implies parallel comparison.** There's no second system to compare against - only Hormozi-aligned modifications to the existing one.
2. **Volume floor too low.** SW + CW combined ship ~20 emails/day. Splitting that into two arms means each arm gets 10/day → no statistical power. A/B testing requires a base flow rate the current system doesn't have. (Per Hormozi's "Better" axis: optimize *after* the Rule of 100 is hitting, not before.)
3. **The current A/B inside `email_builder.py` was correctly paused** - we don't need a *second* A/B layer on top.

### Why NOT REPLACE

1. **Replacement burns 3-4 weeks of production code, copy, demo sites.** The opportunity cost is one missed harvest milestone (R1: first SW contract).
2. **No measured failure to justify replacement.** Reply rates from yesterday's launch are not yet known. You replace what's failing in measurement, not what's "off-pattern."
3. **Replacement would also require re-running the AI Visibility Scorer, re-rendering 19+ HTML emails, re-routing the morning runner.** Multi-day refactor. Not worth it when the foundation is 7/10 already.

---

## Confidence: **HIGH**

**Visibility I used:**
- Direct read of every cold email template in production (`templates/email/cold_outreach.py`, `cw_t2-5.py`, `sw_t1.py`, `signal_works/email_builder.py`, `signal_works/templates/cold_email.txt`).
- Direct read of the orchestration layer (`signal_works/morning_runner.py`, `skills/outreach/sequence_engine.py`).
- Direct read of governing documents (`signal_works/signal_works_plan.md`, `docs/roadmap/harvest.md`, `signal_works/AGENTS.md`).
- Direct read of voice/lint guardrails (`skills/inbound_lead/drafter.py`).
- Hormozi research cross-validated 3+ sources per framework (per Phase 1 source index).

**Visibility I didn't use:**
- I did not read T2-T4 SW templates (`sw_t2.py`, `sw_t3.py`, `sw_t4.py`) - could refine the Severity-3 read on SW follow-up but doesn't change the verdict axis.
- I did not locate Discovery Call OS v2.0 - flagged Severity-3 in audit; doesn't shift the matrix.
- NotebookLM curated material was inaccessible (auth blocker) - third-party Hormozi sources are heavily cross-validated, but the canonical book PDFs from Acquisition.com returned binary blobs.

**Why HIGH not MEDIUM:**
- The verdict is robust to all the missing-visibility items above. None of them would push the matrix below 24/50 (still MERGE territory) or above 35/50 (would shift toward "stay the course, no skill needed" - but the missing-channels gap alone would prevent that).

---

## Specific Call: The Seed Emails Launched Yesterday (CW T1 Apollo batch)

**Status:** Live since 2026-04-29. CW Apollo-sourced leads receive `templates/email/cold_outreach.py` ("Where is your margin actually going?") at T1, then T2-T5 across 19 days. Auto-send is on.

**Hormozi structural score for the seed:** 5.25/10 (per audit, Section 1).

**Cost-of-waiting vs cost-of-changing-now:**

| Action | Cost | Benefit | Risk |
|---|---|---|---|
| **Keep T1 running, modify on next batch** | 0 (in-flight emails complete the 19-day sequence) | Next batch incorporates Phase 5 improvements | Risk: yesterday's batch underperforms; no critical data lost; reply quality is the same diagnostic input either way |
| **Halt T1 mid-flight, swap to Phase-5 v2** | 1-2 days lost momentum + sequence-engine state cleanup | Higher-quality T1 hits the same prospects | Risk: prospects already saw T1 v1; relaunching a different T1 to same address looks erratic; harms sender reputation |
| **Halt T1 only for new leads, keep in-flight running** | <1 day | Cleanest cutover, in-flight prospects ride out their sequence, Phase-5 v2 hits new leads from May onwards | Risk: minimal |

**My call: KEEP IN-FLIGHT, SWAP NEW LEADS to Phase-5 v2 once Phase 5 ships.**

**Why:**
1. **In-flight emails are 6/10 by Hormozi standards.** Not failing. Not ideal. Still net-positive vs no outreach.
2. **Reply data from the in-flight batch is a learning input, not a brand risk.** A 6/10 cold email from a 0-paid-clients consultant is not a brand-damaging artifact. It is an honest first attempt at a Hormozi-aligned hook.
3. **The Phase-5 v2 modifications are surgical:** add 1 line of Big Fast Value to T1, re-frame T4's social proof, add a final value drop to T5. None of these require halting in-flight prospects to take effect. They take effect on the *next* lead added to the queue.
4. **Halt-and-relaunch creates worse optics than ride-it-out.** A prospect who got "Where is your margin actually going?" yesterday and gets "Where is your margin actually going? (v2)" next week sees a sender who can't decide. Worse for trust than the 6/10 baseline.

**Confidence on this seed-email call: HIGH.** I have direct access to the templates, the sequence engine, the morning runner, and the harvest roadmap. The decision is reversible (we can halt at any time if reply data is catastrophically bad), the cost of staying the course is near-zero, and the cost of halting is non-zero (sequence-engine state churn + sender-reputation hit).

---

## Five-Bullet Justification

1. **Score is 29/50 - MERGE territory.** Below 25 = REPLACE. Above 35 = no skill needed. 29 says: solid foundation, real gaps, fix incrementally.
2. **The biggest single gap (Channel Coverage 2/10) is structurally additive, not corrective.** You don't replace cold email to add warm outreach; you add warm outreach alongside cold email. MERGE is the only architectural fit for additive gaps.
3. **The strengths (Hook 8/10, Offer 8/10) compound across channels once Warm and Posting are built.** A strong hook in cold email is the same strong hook in a LinkedIn DM or a posted carousel. MERGE preserves the leverage.
4. **In-flight production cost of REPLACE is one missed harvest.md milestone.** Specifically R1 (first SW contract, target 2026-05-02). The first paid client is worth more than a cleaner system.
5. **The Hormozi skill should be the *organizing layer*, not the *replacement layer*.** Phase 4's SKILL.md will codify the 4-step process, the Value Equation checklist, the Core Four playbooks, the lead magnet rules. Phase 5's templates will plug into the existing sequence engine and morning runner. Nothing in production gets ripped out.

---

## What MERGE Looks Like (handoff to Phases 4 + 5)

**Phase 4 - `skills/hormozi-lead-gen/SKILL.md` (brand-agnostic):**
- The 4-step process as a procedure (Section 3 of research notes).
- The Value Equation as a self-score checklist (Section 2).
- Core Four playbooks: Warm / Cold / Content / Paid.
- 7-step lead magnet creation.
- Hook bank rules (5 hook types, 7 headline elements).
- 8-touch cross-channel cadence.
- 10 anti-patterns as hard refusals.
- Three worked examples (CW, SW, hypothetical future venture).

**Phase 5 - brand-specific artifacts:**
- `lead-gen-system/templates/cold-email-v1.md` - Hormozi-rebuilt CW T1 (adds Big Fast Value + proof point).
- `lead-gen-system/templates/warm-reactivation-v1.md` - the missing warm-outreach template (10-step process from Section 4.1 of research notes).
- `lead-gen-system/templates/lead-magnet-brief-template.md` - the 7-step lead magnet creator (CW needs one; SW already has the score).
- `lead-gen-system/sequences/follow-up-cadence.md` - the 8-touch cross-channel sequence design (replaces the email-only 4/5-touch with email + LinkedIn + phone).
- `lead-gen-system/scripts/objection-handling.md` - the discovery-call objection responses, Hormozi-aligned (some already exist in `signal_works_plan.md`; consolidate + Hormozi-format).
- `lead-gen-system/metrics/success-criteria.md` - explicit floors: 20% open / 5% reply / 1% book / 25% close (warm), 1% reply (cold), LTGP/CAC > 3:1.

**What MERGES into existing infrastructure:**
- Phase 5 cold-email-v1 replaces the *template* in `templates/email/cold_outreach.py` on a future commit (not now; not without explicit ship-it).
- Phase 5 warm-reactivation-v1 becomes a NEW touch type in the sequence engine (additive, no replacement).
- Phase 5 lead-magnet-brief generates a CW-equivalent of the SW score engine (new artifact, no replacement).
- Phase 5 follow-up-cadence design extends `skills/outreach/sequence_engine.py` to support multi-channel (additive, design-only in Phase 5).

**What does NOT get touched:**
- The morning runner (orchestration layer is fine).
- The voice personalizer (already best-in-class).
- The score engine (already best-in-class).
- The niche demo sites (already best-in-class).
- The inbound lead drafter linter (already best-in-class).
- The engagement-ops skill (not in scope).
- In-flight CW T1-T5 emails currently sequencing (per seed-email call above).

---

## Open Questions for Sankofa Council Gate

Before Phase 4 begins, surface these to Sankofa:

1. **Is MERGE the right call, or am I underweighting the cost of the channel-coverage gap?** A council voice may push for "REPLACE the strategic narrowing, even if not the templates." I want explicit dissent on this before locking.
2. **Is the seed-email keep-in-flight call right?** Specifically: is there a hidden brand cost to letting a 6/10 email continue to ~20 fresh CW prospects each weekday for the next ~12 days?
3. **Is the "skill is the organizing layer" framing correct?** Or should the skill be more prescriptive (script-level) rather than principle-level?
4. **Diagnostic question (saved for Phase 6):** is the underlying problem **system design** (skill helps) or **volume of execution** (skill does not help)? My current read is 65/35 system-vs-volume. Sankofa should challenge.

---

## Phase 3 Status: COMPLETE - handing off to Sankofa Gate.
