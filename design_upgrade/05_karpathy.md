# 05_karpathy.md: Karpathy Principles Review
**Phase 5 of 7 | agentsHQ Design Upgrade: "Humanized Standard"**
*Input: 03_plan.md (as reviewed by 04_sankofa.md)*
*Compiled: 2026-05-02*

---

## The Seven Principles Under Review

The plan is scored against Andrej Karpathy's published principles for building with LLMs. Each principle receives a score of PASS, BORDERLINE, or FAIL, with specific evidence from the plan. A FAIL requires a named structural change.

---

## Principle 1: Prompts are programs. Treat them as modular, composable, testable software.

**Score: BORDERLINE**

**Evidence for PASS:**
The plan does treat skill files as modular programs. `craft-tokens.css`, `craft-tokens.ts`, the craft components, the archetype declaration format, and the eval rubric are all discrete, composable artifacts. The plan separates concerns: tokens are separate from components, which are separate from the orchestrator protocol. The mandatory pre-build sequence is a structured program, not a blob of instructions.

**Evidence against (why BORDERLINE, not PASS):**
The builder agent's instruction layer is embedded in `frontend-design/SKILL.md` as a modified section, not as a standalone testable artifact. If the skill file is large, the mandatory pre-build sequence competes with other instructions for attention. The plan does not specify where in the skill file the mandatory section appears. If it appears at the bottom after 2,000 words of other instructions, the LLM's attention dilution will cause it to miss or underweight the critical constraints.

**Required action:** The mandatory pre-build sequence and archetype declaration block must appear as the FIRST section of the skill file, before any other content. This is not an aesthetic preference: it is attention engineering. The LLM reads top to bottom; front-load the constraints.

---

## Principle 2: Context engineering beats prompt engineering. Right context, right time, right model.

**Score: BORDERLINE**

**Evidence for PASS:**
The plan's four-layer architecture is fundamentally a context engineering strategy. Layer 0 (archetype declaration written to `design_brief.md`) creates a persistent context artifact that the critic agent loads. Layer 1 (craft tokens injected into `globals.css`) embeds context directly in the build artifacts, not just in the agent's working memory. Layer 2 (craft components copied into the project) makes the design constraints machine-readable artifacts, not just prompt text.

**Evidence against (why BORDERLINE, not PASS):**
The plan does not address the multi-turn problem. In a long build session (2+ hours, 20+ turns), the agent's context window compresses. Early instructions: including the archetype declaration and the banned patterns list: get pushed out of the active context window. The craft components are in the build directory but the agent does not re-read them between turns.

The Sankofa Contrarian identified this: "By section 3 of the site, the agent has forgotten the token constraints." This is a context engineering failure, not a prompt failure. The agent read the right things at the start but cannot retain them at the end.

**Required action:** The archetype declaration file (`design_brief.md`) must be re-injected into the agent's context at key checkpoints during the build. Concretely: the builder agent should read `design_brief.md` and the banned patterns list at the start of each major section (hero, features, CTA, footer). This is a 4-line read operation that costs nothing but prevents context-drift failures. Add this to the mandatory pre-build sequence as a recurring checkpoint, not a one-time read.

---

## Principle 3: Generation and verification are asymmetric. Generation is cheap, verification is hard. Build verification into every step.

**Score: PASS**

**Evidence:**
The plan builds verification in at multiple layers:

- Layer 1: The token file itself has inline comments documenting banned values. Verification is embedded in the artifact.
- Layer 3: The critic agent runs the eval rubric after every build, not just at final review.
- The eval rubric distinguishes automatic FAIL criteria (objective, grep-checkable) from human judgment criteria (scored 1-5, threshold 4).
- The Sankofa Council's first required amendment (automated linting for banned strings) is already reflected here: the plan as reviewed explicitly calls for the critic to grep for banned strings before running subjective evaluation.
- The hard cap (3 builder-critic cycles maximum) prevents infinite generation loops by forcing human escalation.

This is the strongest part of the plan from a Karpathy lens. The design explicitly acknowledges that generation is cheap and verification is where value is captured.

**Note:** The Contrarian's point about "component copy verification" is an execution gap in this principle. Adding the component verification step (read `SmoothScrollProvider.tsx` before copying) closes this gap. Mark this as a required amendment in Phase 6.

---

## Principle 4: Keep AI on the leash. No human checkpoint plus no automated check equals risk.

**Score: PASS**

**Evidence:**
The plan has both human and automated checks at every stage:

| Stage | Automated check | Human check |
|---|---|---|
| Token injection | Grep for banned strings in generated code | Builder agent self-check before critic submission |
| Component copy | Verify SmoothScrollProvider.tsx exists (Sankofa amendment) | N/A |
| Build completion | Critic agent runs full eval rubric (10 automatic FAIL criteria) | Human judgment criteria scored 1-5 |
| Loop cap | 3-cycle hard cap; escalates to human at 4 | Human reviews all artifacts if 3 cycles fail |
| Final gate | Automated rubric score | Creative director test (defined in Sankofa amendment) |

The plan also gates on runtime: if the runtime is not Next.js 14+, the build stops immediately. This is a hard automated check before any generation begins.

One gap: the creative director test protocol was flagged as undefined by the Sankofa Contrarian. The plan says "a working creative director would not flag it" but does not say who runs this test or when. Until the test protocol is defined (Sankofa amendment 6), this checkpoint is nominal rather than real. Score stays PASS because the checkpoint is structurally present; the amendment makes it actually executable.

---

## Principle 5: Build the eval first. You cannot improve what you cannot measure.

**Score: PASS**

**Evidence:**
The eval rubric is designed before the deliverables are built. Phase 3 (plan) defines the rubric structure. Phase 7 (deliverables) produces the full rubric document. The plan specifies both automated criteria (10 automatic FAIL items, all grep-checkable) and human judgment criteria (5 items, 1-5 scale, threshold 4).

The eval rubric is also referenced during component design. `KineticText.tsx` exists because the eval rubric requires `<KineticText>` on the hero headline. The eval shaped the implementation, not the reverse. This is the correct order.

**The rubric has measurable thresholds:**
- Automatic FAIL: any of 10 specific patterns found in code
- Human judgment: average score 4.0+ across 5 criteria
- Overall: PASS requires 0 automatic fails AND average human judgment >= 4.0

The improvement loop is closed: build -> eval -> revise (up to 3 cycles) -> escalate or deploy.

**One measurement gap:** The plan does not define a baseline. Without a baseline score for the current agentsHQ output, there is no way to quantify the improvement. This is a minor gap: the creative director test provides a qualitative before/after: but a quantitative baseline (how many of the 10 AI-tells does a typical current build have?) would be useful for the Phase D eval.

---

## Principle 6: LLMs are jagged. Compensate for known weakness with structure, not vibes.

**Score: PASS**

**Evidence:**
The plan's entire architecture is a response to specific, named LLM weaknesses:

| Known weakness | Structural compensation in the plan |
|---|---|
| Defaults to Tailwind indigo for buttons | Explicit CSS variable override; indigo banned from CTA colors |
| Defaults to Inter for all text | Inter banned as heading font; archetype-specific font pairs mandatory |
| Defaults to 3-column symmetric feature grid | 3-column symmetric grid is an automatic FAIL in the eval rubric |
| Defaults to generic `ease-in-out` for all transitions | `ease-in-out` is a banned string; grep catches it post-generation |
| Defaults to 300ms duration | `duration-300` is a banned string; grep catches it |
| Hallucinate GSAP refs and break builds | LLM does not write GSAP: it uses pre-built components |
| Writes happy-path UI only | Error states and empty states are an explicit eval rubric criterion |
| Writes div-first markup | Semantic HTML is an explicit eval rubric criterion |
| Context drift in long sessions | Archetype declaration re-injected at section checkpoints (Sankofa amendment) |

The plan compensates for every known weakness identified in the Phase 1 audit and the Sankofa Council review. This is the cleanest principle alignment in the review.

---

## Principle 7: Vibe coding is a warning, not a destination. Add structure before shipping.

**Score: BORDERLINE**

**Evidence for PASS:**
The plan rejects vibe coding explicitly and by design. The entire "Compiled Craft" architecture is an anti-vibe-coding strategy. Telling the LLM to "be more creative" was the vibe-coding failure mode that the Sankofa Council correctly killed in the Antigravity session. The plan replaces that with exact mathematical constants, exact component APIs, and an eval rubric with objective pass/fail criteria.

**Evidence against (why BORDERLINE, not PASS):**
Two specific places where vibe remains in the plan:

**Vibe 1:** The archetype decision tree (Sankofa amendment 4: simplify to 2 questions + lookup table) still exists in its 5-step form in 03_plan.md. The 5-step tree has judgment calls embedded in steps 3 and 4 ("weight toward" decisions). These are vibes: the agent is told to "weight toward" an archetype based on subjective signals, not a deterministic lookup. Until the tree is simplified to a lookup table (as the Sankofa Outsider recommended), this is vibe-adjacent.

**Vibe 2:** The human judgment criteria in the eval rubric are scored 1-5 with a threshold of 4.0. "Does the layout have a deliberate visual hierarchy beyond centering?" is a judgment call, not a structural check. This is appropriate: some criteria cannot be automated: but the scoring guidelines need to be specific enough that two different critics would give the same score to the same build. Without scoring anchors ("a score of 3 means X; a score of 5 means Y"), the human judgment criteria are vibes dressed up as scores.

**Required actions:**
1. Replace the 5-step decision tree with a 2-question lookup table before Phase 6 refinement.
2. Add scoring anchors to each human judgment criterion in the eval rubric (what does a 3 look like vs. a 5).

---

## Summary Scorecard

| Principle | Score | Key issue |
|---|---|---|
| 1. Prompts are programs | BORDERLINE | Mandatory section must appear first in skill file |
| 2. Context engineering | BORDERLINE | Context drift in multi-turn builds; re-inject declaration at checkpoints |
| 3. Generation vs. verification | PASS | Strongest principle alignment; component copy verification closes the gap |
| 4. AI on the leash | PASS | Both automated and human checks at every stage; creative director test needs operationalization |
| 5. Build the eval first | PASS | Rubric designed before deliverables; measurable thresholds; minor gap: no baseline measurement |
| 6. LLMs are jagged | PASS | Every known weakness has a named structural compensation |
| 7. Vibe coding warning | BORDERLINE | 5-step decision tree has vibe in it; human judgment criteria need scoring anchors |

**FAIL count: 0**

**BORDERLINE count: 3** (Principles 1, 2, 7)

**Overall verdict: BORDERLINE: proceed to Phase 6 (Refinement) with the following required changes:**

1. Mandatory section first in the skill file (Principle 1)
2. Archetype declaration re-injection at section checkpoints (Principle 2)
3. Component copy verification step added to pre-build sequence (Principle 3)
4. Creative director test protocol defined concretely (Principle 4)
5. Baseline measurement added: count AI-tells in one existing build before the new system is applied (Principle 5)
6. Archetype decision tree replaced with 2-question lookup table (Principle 7)
7. Scoring anchors added to human judgment criteria in eval rubric (Principle 7)

All seven changes are surgical. None require re-architecting. The plan's core structure is sound.

---

*Phase 5 complete. Proceeding to Phase 6: Refinement.*
