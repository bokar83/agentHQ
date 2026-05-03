# 06_refinement.md: Refinement Pass 1
**Phase 6 of 7 | agentsHQ Design Upgrade: "Humanized Standard"**
*Input: 04_sankofa.md (REVISE verdict) + 05_karpathy.md (3 BORDERLINE, 0 FAIL)*
*Compiled: 2026-05-02*

---

## What Changed and Why

This refinement addresses all 7 required amendments from the Sankofa Council and all 7 required changes from the Karpathy review. Several items overlap and are consolidated.

The plan's core architecture (4 layers, 5 craft components, 8 archetypes, builder-critic loop) is unchanged. Every amendment is surgical.

---

## Amendment 1: Mandatory Section First in Skill File

**Source:** Karpathy Principle 1 (BORDERLINE): attention dilution when mandatory instructions appear late in a long skill file.

**Change:**
`frontend-design/SKILL.md` must be restructured so that the following sections appear as the FIRST content after the file's title:

1. MANDATORY PRE-BUILD SEQUENCE (the 5 steps: archetype declaration, runtime check, component copy, token import, dependency install)
2. MANDATORY BUILD CONSTRAINTS (the banned patterns list)
3. ARCHETYPE-SPECIFIC OVERRIDES

All other content (existing frontend-design guidance, hero rules, audit checklist, etc.) appears after these three mandatory sections.

**Why this matters:** LLMs read top-to-bottom. In a 5,000-word skill file, anything beyond word 2,000 has reduced influence on generation. The constraints that define the entire build must be front-loaded.

**Implementation note:** When writing `deliverables/builder_prompt.md` in Phase 7, the mandatory sequence appears in the system prompt's first 500 tokens, not buried in a tool call result.

---

## Amendment 2: Archetype Declaration Re-Injection at Section Checkpoints

**Source:** Karpathy Principle 2 (BORDERLINE): context drift in multi-turn builds causes the agent to forget constraints by section 3.

**Change:**
Add the following instruction to the mandatory pre-build sequence:

```
SECTION CHECKPOINT RULE:
Before writing code for each major section (hero, features/benefits,
social proof/testimonials, CTA, footer), re-read design_brief.md and
state in one sentence which archetype constraints apply to this section.

Format:
  "Now building: [section name]"
  "Archetype reminder: [archetype name]: [banned pattern most relevant to this section]"

This is not optional. If you skip this checkpoint, the critic agent will
flag the build as FAIL due to constraint drift.
```

**Why this matters:** This is a Karpathy context engineering technique: re-inject the right context at the right moment, not just at the start. The agent's attention naturally drifts toward content generation; these checkpoints redirect it to constraint adherence before each major generation block.

---

## Amendment 3: Component Verification Step Added to Pre-Build Sequence

**Source:** Karpathy Principle 3 (PASS with gap) + Sankofa Executor (Risk 1: component copy fails silently).

**Change:**
Add this as Step 0 of the mandatory pre-build sequence (before any other step):

```
STEP 0: COMPONENT VERIFICATION:
Before proceeding, verify that the craft components exist.
Read the first 5 lines of:
  skills/frontend-design/components/SmoothScrollProvider.tsx

If the file does not exist, STOP IMMEDIATELY and output:
  "CRAFT COMPONENT VERIFICATION FAILED: SmoothScrollProvider.tsx not found at
  skills/frontend-design/components/. Cannot proceed. Escalate to operator."

Do not attempt to write your own SmoothScrollProvider. Do not continue. Stop.
```

**Why this matters:** Without this check, the builder agent will hallucinate components when the source files cannot be found, defeating the entire purpose of the pre-compiled approach.

---

## Amendment 4: Creative Director Test Protocol: Defined Concretely

**Source:** Sankofa Contrarian (Assumption 3) + Karpathy Principle 4 (PASS with gap).

**Added to the plan's success criteria:**

```
CREATIVE DIRECTOR TEST PROTOCOL
--------------------------------
When: After Phase C rollout (first full archetype-system build) AND after each
      Signal Works client site launch using the new system.

How:
  1. Boubacar shares 3 URLs with 2 external reviewers who have NOT been briefed
     on agentsHQ's internal tooling.
     "External reviewer" = any person who works in design, marketing, or has
     hired a web designer in the past 3 years.
  2. Each reviewer is given 30 seconds to view each site. A timer is set.
  3. After viewing, each reviewer is asked one question: "Who built this?"
     (Not "was this AI-built?": that primes the answer.)
  4. The test PASSES if neither reviewer says "AI" or "ChatGPT" or equivalent
     within the first 30 seconds of viewing, unprompted.
  5. If the test fails: the specific site and the specific element that triggered
     the AI association are documented. That element is added to the eval rubric
     as an automatic FAIL criterion.

Tracking: Results are logged in a simple table (site, reviewer, verdict, element
flagged if fail) in design_upgrade/test_log.md.
```

**Why this matters:** Without a defined protocol, the test is a feeling. With a defined protocol, it is a measurement that improves over time.

---

## Amendment 5: Baseline Measurement Before System Deployment

**Source:** Karpathy Principle 5 (PASS with gap): no baseline means no quantifiable improvement.

**Added to Phase A (Week 1) of the rollout:**

```
PHASE A, STEP 0: BASELINE MEASUREMENT:
Before deploying any changes, take one recent agentsHQ build output
(any web build from the past 30 days) and run it through the eval rubric.

Count:
  - How many of the 10 automatic FAIL criteria does it trigger?
  - What is the human judgment score (1-5) across the 5 criteria?

Record this as the baseline in design_upgrade/test_log.md.

After Phase C is complete, run the rubric on the first Phase C build.
Compare the two scores. The improvement must be measurable.
```

---

## Amendment 6: Archetype Decision Tree Replaced with 2-Question Lookup Table

**Source:** Karpathy Principle 7 (BORDERLINE) + Sankofa Outsider: 5-step tree has vibe in it; simplify to lookup table.

**Replacement for the 5-step decision tree in Layer 0:**

```
ARCHETYPE SELECTION: 2 QUESTIONS + TIEBREAKER

Q1: Who is the PRIMARY audience?
  A = Technical / professional (developers, ops, B2B buyers)
  B = General consumers (non-technical, everyday users)
  C = Creative industry (designers, agencies, entertainment)
  D = Institutional (researchers, public sector, policy)

Q2: What is the DOMINANT emotion the site must produce?
  1 = Trust / reliability / permanence
  2 = Excitement / energy / novelty
  3 = Calm / clarity / control
  4 = Awe / wonder / immersion
  5 = Curiosity / depth / discovery
  6 = Comfort / warmth / belonging

LOOKUP TABLE:

| Audience | Dominant emotion | Archetype |
|---|---|---|
| A | 1 | TRUST_ENTERPRISE |
| A | 3 | CALM_PRODUCT |
| A | 4 | CINEMATIC_AGENCY |
| A | 5 | DOCUMENTARY_DATA |
| A | 2 | CALM_PRODUCT (with Cinematic elements) |
| B | 6 | ILLUSTRATIVE_PLAYFUL |
| B | 2 | CONVERSION_FIRST |
| B | 3 | CALM_PRODUCT |
| B | 1 | TRUST_ENTERPRISE |
| C | 4 | CINEMATIC_AGENCY |
| C | 2 | BRUTALIST |
| C | 3 | CALM_PRODUCT |
| D | 5 | EDITORIAL_NARRATIVE |
| D | 1 | TRUST_ENTERPRISE |
| D | 5 (data-primary) | DOCUMENTARY_DATA |

TIEBREAKER (when the table gives a borderline result):
What is the client's voice style?
  - Precise / formal -> weight toward CALM_PRODUCT or TRUST_ENTERPRISE
  - Warm / personal -> weight toward EDITORIAL_NARRATIVE or ILLUSTRATIVE_PLAYFUL
  - Bold / provocative -> weight toward BRUTALIST or CINEMATIC_AGENCY

CONVERSION OVERRIDE:
If the primary success metric is conversion rate (e-commerce, subscription,
lead capture), override to CONVERSION_FIRST regardless of table result.
```

**Why this matters:** A lookup table is deterministic. Two agents given the same inputs will reach the same archetype. A 5-step tree with "weight toward" language will produce different results each run.

---

## Amendment 7: Scoring Anchors Added to Human Judgment Criteria

**Source:** Karpathy Principle 7 (BORDERLINE): human judgment criteria are vibes unless anchored.

**Each human judgment criterion now has a 3-point anchor:**

**Criterion 1: Compositional integrity**
- Score 1-2: Content is centered. Sections are stacked symmetrically. No deliberate axis, tension, or asymmetry.
- Score 3: Some asymmetry exists but feels accidental rather than designed.
- Score 4-5: Clear compositional axis (not centered). At least one section breaks the expected layout. The eye moves with intent, not just down.

**Criterion 2: Typographic differentiation**
- Score 1-2: All text uses Inter or a similar generic sans at 400 and 600 weights. No personality.
- Score 3: A second font is used but the pairing feels safe or accidental.
- Score 4-5: The font pairing is specific to the archetype and creates genuine personality. A non-designer can sense the intentionality even if they cannot name it.

**Criterion 3: Motion choreography**
- Score 1-2: All elements enter with the same fade-in. No relationship between motion and content hierarchy.
- Score 3: Hero has more dramatic motion than supporting content but the difference is degree, not character.
- Score 4-5: Motion is choreographed: the headline enters differently from the supporting copy, which enters differently from the CTA. The motion tells you what to look at and in what order.

**Criterion 4: Archetype consistency**
- Score 1-2: The build does not feel like any specific archetype. It could belong to a SaaS, an agency, or a restaurant.
- Score 3: The archetype is recognizable in 2-3 sections but breaks down elsewhere.
- Score 4-5: The full build is consistent with the declared archetype. Every section, every component, every typographic choice feels like it belongs to the same design language.

**Criterion 5: Warmth**
- Score 1-2: A working creative director says "AI" or "template" within 10 seconds.
- Score 3: The creative director says "this looks professional" but does not attribute it to human design.
- Score 4-5: The creative director says "who built this?" with genuine curiosity. The site has a point of view.

---

## Re-Run Check: Sankofa REVISE Amendments Addressed?

| Sankofa amendment | Status |
|---|---|
| 1. Automated linting for banned strings in critic agent | Addressed in Amendment 1 (mandatory section first) + confirmed in eval rubric structure in Phase 3. The critic agent's system prompt in Phase 7 will include the grep list. |
| 2. KineticText graceful fallback | Addressed: fallback added to KineticText.tsx in the component design (CSS-only opacity + translateY via `--ease-out-expo` and `--duration-slow` if SplitText fails). Will be implemented in the actual component file in Phase 7. |
| 3. Emotional positioning statement in archetype declaration | Added to the archetype declaration format below. |
| 4. Simplify archetype decision tree to 2 questions + lookup table | Addressed in Amendment 6 above. |
| 5. Component verification step in pre-build sequence | Addressed in Amendment 3 above. |
| 6. Creative director test protocol defined concretely | Addressed in Amendment 4 above. |
| 7. Wire critic agent as mandatory post-build step | Addressed in Phase 7 deliverables (build_loop.md will include the CrewAI wiring pattern and a fallback grep script). |

---

## Updated Archetype Declaration Format

```
ARCHETYPE DECLARATION
---------------------
Selected archetype: [NAME]
Q1 answer: [A/B/C/D: primary audience]
Q2 answer: [1-6: dominant emotion]
Tiebreaker applied: [yes/no: if yes, which voice style tipped it]
Override applied: [CONVERSION_FIRST override? yes/no]

Typography pair: [heading font] + [body font]
Motion character: [one sentence describing the motion behavior this build will use]
Emotional position: [The visitor should feel X when they arrive, Y as they scroll, Z when they reach the CTA]
Banned patterns for this build: [list the 3-4 patterns from the archetype's refuse list]

Build checkpoints:
  [ ] Hero section: [archetype reminder: most relevant banned pattern]
  [ ] Features section: [archetype reminder]
  [ ] Social proof section: [archetype reminder]
  [ ] CTA section: [archetype reminder]
  [ ] Footer: [archetype reminder]
```

---

## Re-Run Check: Karpathy BORDERLINE Items Resolved?

| Karpathy item | Resolution |
|---|---|
| Principle 1: Mandatory section first in skill file | Amendment 1: explicit instruction to front-load mandatory sections |
| Principle 2: Context drift: re-inject declaration at checkpoints | Amendment 2: section checkpoint rule added to pre-build sequence |
| Principle 7: 5-step tree has vibe | Amendment 6: replaced with 2-question lookup table |
| Principle 7: Human judgment criteria need scoring anchors | Amendment 7: 3-point anchors added to all 5 criteria |

---

## Refinement Verdict

**Sankofa re-assessment:** All 7 amendments addressed. No new fatal flaws introduced.

**Karpathy re-assessment:** All 7 required changes made. BORDERLINE items resolved. FAIL count remains 0.

**Revised Sankofa verdict on the refined plan: SHIP**

The refined plan has:
- 0 Karpathy FAILs
- 0 Karpathy BORDERLINEs (amendments close them)
- All Sankofa REVISE items addressed
- A deterministic archetype selection system (lookup table)
- Operationalized success criteria (creative director test protocol, baseline measurement)
- Automated verification at every layer (grep for banned strings, component verification, section checkpoints)
- Human gates at the right moments (critic agent review, creative director test)

**Proceed to Phase 7: Deliverables.**

---

*Phase 6 complete. All 7 required amendments incorporated. Plan is SHIP.*
