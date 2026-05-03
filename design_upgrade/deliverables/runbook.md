# Implementation Runbook: "Humanized Standard"
**agentsHQ: Design Upgrade Rollout Guide**
*Read this before touching any skill files. Execute phases in order.*

---

## What This Runbook Does

This runbook walks through the 4-phase rollout of the Compiled Craft architecture into agentsHQ's production skill stack. Each phase has a clear goal, specific steps, and a measurable verification gate before the next phase begins.

**Do not skip phases.** Each phase builds on the previous. Attempting Phase C without Phase B's craft components will produce a build that crashes on the first use of KineticText.

---

## Before You Begin: Baseline Measurement

Run this before any changes:

1. Take one recent agentsHQ web build output (any live client site or internal build)
2. Run it through the eval rubric (`eval_rubric.md`): Phase 1 checks only
3. Count how many of the 12 automated checks fail
4. Record in `design_upgrade/test_log.md`:

```
BASELINE MEASUREMENT
--------------------
Date: [today]
Build: [name of the build used for baseline]
Phase 1 failures: [count] of 12
Specific failures: [list]
Notes: [anything notable]
```

This number becomes the benchmark. After Phase C, run the same rubric on a new build and compare.

---

## Phase A: Token Injection + Ban List

**Goal:** Eliminate the most common AI-tells from all new builds by injecting exact craft token values and explicitly banning the generic defaults.

**Estimated time:** 1 focused session (2-3 hours)

### Steps

**Step A1: Create craft-tokens.css**

Create `skills/ui-styling/craft-tokens.css` with the content from [03_plan.md Layer 1].

**Step A2: Create craft-tokens.ts**

Create `skills/ui-styling/craft-tokens.ts` with the content from [03_plan.md Layer 1].

**Step A3: Update frontend-design/SKILL.md**

At the VERY TOP of the skill file (before any existing content), add:

```markdown
## MANDATORY: READ THIS BEFORE ANY OTHER SECTION

This build uses the Humanized Standard Compiled Craft system.
Before writing any code, read and execute the MANDATORY PRE-BUILD SEQUENCE
in `skills/frontend-design/deliverables/skill_design_human.md`.

BANNED STRINGS (critic agent greps for these: zero tolerance):
- ease-in-out
- duration-300
- rgba(0,0,0,0.1) as the only shadow value
- grid-template-columns: repeat(3, 1fr) with 3 identical children
- Inter in h1, h2, or h3 selectors
```

**Step A4: Run a test build**

Prompt the builder agent to build a simple 3-section marketing page for a fictional B2B SaaS client. Give it no other design guidance: let the constraints do the work.

**Step A5: Verify**

Run the Phase 1 automated checks:
```bash
bash scripts/post_build_check.sh ./src
```

Expected improvement: checks 1.1 (ease-in-out), 1.2 (duration-300), 1.10 (Inter heading) should pass.

**Phase A Gate:** Phase 1 failure count must be lower than the baseline. If it is not, diagnose why the agent is not respecting the ban list before proceeding.

---

## Phase B: Craft Components

**Goal:** Build the 5 pre-compiled craft components that the builder agent will use in all future builds. Test each component individually before wiring it into the build pipeline.

**Estimated time:** 1-2 focused sessions (4-6 hours)

### Steps

**Step B1: Create the components directory**

```
mkdir -p skills/frontend-design/components/
mkdir -p skills/frontend-design/components/pdf/
```

**Step B2: Write each component**

Create these files with the content from [03_plan.md Layer 2]:
- `skills/frontend-design/components/SmoothScrollProvider.tsx`
- `skills/frontend-design/components/KineticText.tsx`
- `skills/frontend-design/components/MagneticButton.tsx`
- `skills/frontend-design/components/ParallaxLayer.tsx`
- `skills/frontend-design/components/ScrollReveal.tsx`

Create the PDF stylesheet:
- `skills/frontend-design/components/pdf/pdf-base.css`

**Step B3: Local component test**

Create a test Next.js project locally:
```bash
npx create-next-app@latest craft-test --typescript --tailwind --app
```

Copy all 5 components into `craft-test/src/components/craft/`.
Copy `craft-tokens.ts` into `craft-test/src/lib/craft-tokens.ts`.
Copy `craft-tokens.css` into `craft-test/src/app/craft-tokens.css`.
Add the import to `globals.css`.
Install: `npm install lenis gsap framer-motion`

Build a minimal test page using all 5 components.

**Step B4: Verify components in browser**

Check each component manually:
- SmoothScrollProvider: does the scroll feel different from native? (lerp = 0.07, should feel "buttery")
- KineticText: does the hero headline animate on scroll entry? does it degrade gracefully with no animation if you trigger the reduced-motion media query?
- MagneticButton: does the button track the cursor? does it spring back on mouseleave?
- ParallaxLayer: does the background move at a slower rate than the foreground on scroll?
- ScrollReveal: do supporting content elements fade in with a translateY on scroll entry?

**Step B5: Add mandatory pre-build sequence to skill file**

Add the MANDATORY PRE-BUILD SEQUENCE from `skill_design_human.md` to the top of `frontend-design/SKILL.md` (after the ban list added in Phase A).

**Phase B Gate:** All 5 components work correctly in the test build. A human looking at the test page says "this feels like a premium website." If any component does not work, fix it before proceeding to Phase C.

---

## Phase C: Archetype System + Critic Loop

**Goal:** Wire the archetype selection system and the builder-critic loop. Run three test builds: one per archetype: and validate that each one feels distinctly different from the others.

**Estimated time:** 2-3 focused sessions (6-10 hours)

### Steps

**Step C1: Add archetype system to skill file**

Add the ARCHETYPE SPECIFICATIONS from `skill_design_human.md` to `frontend-design/SKILL.md`.
Add the SECTION CHECKPOINT PROTOCOL.
Add the SELF-CHECK BEFORE CRITIC SUBMISSION.

**Step C2: Set up the critic agent**

Create the critic agent using the system prompt from `critic_prompt.md`.

Wire it into the build pipeline per the CrewAI pattern in `build_loop.md`. If CrewAI wiring is not yet possible, save `scripts/post_build_check.sh` from `build_loop.md` and run it manually after each build.

**Step C3: Run test build 1: CALM_PRODUCT**

Client brief: "A B2B project management SaaS targeting engineering teams at Series B startups. The founder is technical and values precision. The site should feel calm, controlled, and trustworthy. No fluff."

Run the full builder-critic loop. Record the verdict and cycle count.

**Step C4: Run test build 2: EDITORIAL_NARRATIVE**

Client brief: "A research organization publishing reports on AI policy. The audience is policy makers and journalists. The site should feel serious, authoritative, and worth reading carefully."

Run the full builder-critic loop. Record the verdict and cycle count.

**Step C5: Run test build 3: CINEMATIC_AGENCY**

Client brief: "A creative production studio that makes brand films and experiential campaigns for luxury consumer brands. The site is their portfolio. It needs to feel like the work itself."

Run the full builder-critic loop. Record the verdict and cycle count.

**Step C6: Creative Director Test (first run)**

Show all three test builds to 2 external reviewers (anyone outside agentsHQ). Follow the protocol from `06_refinement.md` Amendment 4. Record results in `design_upgrade/test_log.md`.

**Phase C Gate:** At least 2 of 3 test builds pass the builder-critic loop within 2 cycles. The creative director test: neither reviewer says "AI" for at least 2 of the 3 sites. If the gate is not met, diagnose the specific failure and fix before Phase D.

---

## Phase D: PDF Pipeline + Full Production Eval

**Goal:** Wire the PDF design system into the PDF generation pipeline and run the full system on a real client brief.

**Estimated time:** 1-2 focused sessions (3-5 hours)

### Steps

**Step D1: Wire pdf-base.css into the PDF generation pipeline**

In the HTML template used for PDF generation, add:
```html
<link rel="stylesheet" href="pdf-base.css" media="print">
```

Or if using a server-side rendering approach:
```css
@import url('./pdf-base.css');
```

Verify the import loads correctly when generating a PDF.

**Step D2: Test PDF output**

Generate a PDF from an existing agentsHQ HTML report. Open it.

Check:
- Body font is readable (Source Serif 4 or Georgia, not Inter)
- No blank areas where gradients used to appear
- No extra whitespace from removed box-shadows
- Numeric columns align correctly (tabular figures)
- Charts are readable without color (if printed in B&W)
- No text below 9pt

**Step D3: Run on a real client brief**

Take the next Signal Works client brief that comes through the pipeline. Run the full system:
1. Builder agent with Compiled Craft components
2. Critic agent with full eval rubric
3. PDF generation with pdf-base.css

Measure: how many builder-critic cycles did it take? What was the final score?

**Step D4: Post-launch eval**

After the site launches, run the creative director test one more time. This is the "live site" version: the actual deployed URL, not a localhost build. Record in `test_log.md`.

**Phase D Gate:** A real Signal Works client site passes the builder-critic loop within 3 cycles and passes the creative director test. If it does not, the specific failures become the input for the next refinement pass.

---

## Rollback Plan

If the Compiled Craft system causes a build to fail catastrophically (components crash, skill file is corrupted, etc.):

1. The skill files are version-controlled. Roll back `frontend-design/SKILL.md` with `git revert`.
2. The craft components are in `skills/frontend-design/components/`: removing this directory reverts the system to the pre-craft-component state.
3. The `craft-tokens.css` import in `globals.css` can be commented out in the project being built without affecting the skill files.

**The rollback path does not destroy any data.** The craft components remain in the skills directory; they are simply not used in the rolled-back build.

---

## Maintenance

### Adding a New AI-Tell to the Rubric

When a new AI-tell is discovered (e.g., a new Tailwind default that appears in multiple builds):

1. Add it to `eval_rubric.md` Phase 1 Banned String Checks
2. Add it to the BANNED STRINGS list in `skill_design_human.md`
3. Add the corresponding grep check to `scripts/post_build_check.sh`
4. Log it in `design_upgrade/test_log.md` with the date discovered and the first build it appeared in

### Updating Craft Components

If a component needs to be updated (new lerp values, new spring constants, new archetype added):

1. Update the component file in `skills/frontend-design/components/`
2. Update the corresponding constants in `craft-tokens.ts` and `craft-tokens.css`
3. Update the quick reference in `reference_doc.md` and `skill_design_human.md`
4. Run one test build to verify the update works
5. **Note:** Existing deployed builds are not automatically updated. They use the copy that was made at build time.

### Adding a New Archetype

1. Define the archetype in `02_research.md` Section 5 format
2. Add it to the lookup table in `skill_design_human.md`
3. Add archetype-specific component rules to `builder_prompt.md` and `skill_design_human.md`
4. Add archetype-specific eval handling to `critic_prompt.md`
5. Build one test site using the new archetype before adding it to production

---

## Quick Reference: File Map

| File | Purpose | When to read |
|---|---|---|
| `design_upgrade/01_audit.md` | Skill audit findings | Diagnosing why a build is producing AI-slop |
| `design_upgrade/02_research.md` | Reference sites, designers, technical patterns | Adding new archetypes or updating motion values |
| `design_upgrade/03_plan.md` | Full architecture spec | Understanding why the system is designed the way it is |
| `design_upgrade/04_sankofa.md` | Sankofa Council review | Understanding the risks and tradeoffs |
| `design_upgrade/05_karpathy.md` | Karpathy principles scorecard | Adding new features to the system |
| `design_upgrade/06_refinement.md` | All amendments from Sankofa + Karpathy | Understanding why specific decisions were made |
| `deliverables/builder_prompt.md` | Builder agent system prompt | Wiring the builder agent |
| `deliverables/critic_prompt.md` | Critic agent system prompt | Wiring the critic agent |
| `deliverables/reference_doc.md` | Runtime quick reference | Agent reads this at build time |
| `deliverables/build_loop.md` | Loop pseudocode + CrewAI wiring | Wiring the build pipeline |
| `deliverables/eval_rubric.md` | Full scoring rubric | Critic agent evaluation |
| `deliverables/skill_design_human.md` | Master skill file | Front-loading skill file constraints |
| `deliverables/pdf_addendum.md` | PDF-specific design rules | PDF generation builds |
| `deliverables/runbook.md` | This file | Rollout |
| `skills/ui-styling/craft-tokens.css` | Math constants in CSS | Every web build |
| `skills/ui-styling/craft-tokens.ts` | Math constants in TypeScript | Every web build |
| `skills/frontend-design/components/*.tsx` | Pre-compiled craft components | Every web build |
| `design_upgrade/test_log.md` | Test results over time | Diagnosing regressions |
