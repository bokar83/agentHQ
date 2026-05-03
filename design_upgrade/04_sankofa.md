# 04_sankofa.md: Sankofa Council Review
**Phase 4 of 7 | agentsHQ Design Upgrade: "Humanized Standard"**
*Input: 03_plan.md: The "Compiled Craft" Architecture*
*Compiled: 2026-05-02*

---

## PRE-COUNCIL: Is the Plan Solving the Right Problem at the Right Altitude?

Before the five voices speak, the Council interrogates the framing.

The plan's thesis: agentsHQ produces AI-slop because the LLM fills unspecified values with its statistical training defaults. The solution: inject exact craft values as hard constraints so the LLM has no room to default.

**Framing verdict:** Correct altitude. The plan is not treating symptoms (bad output) by tweaking prompts (Software 1.0). It is restructuring the constraint system so the symptom cannot occur (Software 3.0). The success criterion: a working creative director would not flag these sites as AI-generated within 30 seconds: is measurable and human-gated. The pre-council finds no framing error. The Council may proceed.

---

## Voice 1: The Contrarian

*What kills this? Where does it break under load? What assumption is load-bearing?*

The plan has three load-bearing assumptions. All three need to survive pressure.

**Assumption 1: The LLM will follow the mandatory pre-build sequence.**

The plan instructs the builder agent to copy craft components into the build and import craft-tokens.css before writing code. This is in a SKILL.md file. The agent reads the skill, then writes code. The window between reading the instruction and executing it is where hallucination lives. In a multi-turn build session, the agent will start following instructions, get partway through, and then its attention will drift to the content being built. By section 3 of the site, the agent has forgotten the token constraints and is defaulting to `transition: all 0.3s ease`.

The plan does not address this. There is no mechanism to enforce the constraints at the code-writing layer: only at the instruction-reading layer. The critic agent catches failures after the fact, but this means every build will fail the critic on the first pass, which defeats the purpose of pre-compiled constraints.

**What kills it:** The gap between "instructions read" and "constraints enforced" is where the AI-slop re-enters.

**Required fix:** The eval rubric (which exists) needs to run as a linting pass ON THE GENERATED CODE, not as a subjective review after the fact. The critic agent must grep the generated code for banned strings (`ease-in-out`, `duration-300`, `rgba(0,0,0,0.1)`) before it reads a single line of context. Automated linting catches the mechanical failures; human judgment handles the aesthetic ones.

---

**Assumption 2: GSAP SplitText is free to use.**

The plan states: "SplitText and ScrollTrigger are now free as of GSAP 3.12+ following the Webflow acquisition." This is partially true. GSAP core and ScrollTrigger are free. SplitText was moved to the free tier in late 2024. However, the plan includes a caveat ("Verify current licensing at https://gsap.com/pricing/ before each new project") but then builds the entire kinetic typography system on SplitText. If licensing changes again, or if a client's security policy blocks the GSAP CDN, the KineticText component breaks silently: it renders static text with no animation, which is better than broken UI but still a failure mode not accounted for.

**Required fix:** KineticText needs a graceful fallback. If SplitText fails to register or throws, the component should render the text as-is with a CSS-only fade-in using the custom easing tokens. No dependency on a single vendor for a core user-facing component.

---

**Assumption 3: The creative director test is the exit condition.**

The plan says: "A working creative director shown three sites built using the new system would not flag them as AI-generated within 30 seconds of viewing each." This is the right success criterion. But it is undefined in terms of who, when, and what "flag" means. The plan does not say: how does this test get run? Does Boubacar review it? Is it an external creative director? Is 30 seconds a literal stopwatch or a figure of speech? Without this being operationalized, "pass the creative director test" will be declared by whoever last worked on the build.

**Required fix:** Define the test protocol concretely. Suggested: Boubacar shows 3 sites to 2 people outside agentsHQ (could be other designers, clients, or peers), without saying agentsHQ built them, and asks "who built this?" The test passes when neither person says "AI" within the first 30 seconds of viewing.

---

## Voice 2: The First Principles Thinker

*Strip assumptions. Reframe from zero. What is actually the problem here?*

The plan solves the right problem at a high level but stops short of the root cause at one specific point.

**The actual root cause of AI-slop is not missing constraints. It is missing intent.**

An LLM without constraints generates the statistical average. An LLM with constraints generates the constrained statistical average. The constraints in this plan (exact lerp values, spring constants, banned easing strings) are excellent at removing the worst AI-tells. But they do not inject design intent. They inject design correctness.

The difference: a site can have Lenis lerp 0.07, KineticText on the hero, MagneticButton on the CTA, and still feel like it was assembled from parts rather than conceived as a whole. A human designer brings a point of view: "this brand feels like the founder is whispering a secret to you, so the type should start small and expand." That narrative intent shapes every decision, not just the motion values.

The plan's archetype system gets partway there: "Calm Product" or "Cinematic/Agency" gives the agent a design lane. But the archetype declaration as written is a category selection, not a brief. The agent picks an archetype, copies the components, and builds. It does not synthesize the archetype with the specific client's story.

**First principles reframe:** The missing layer is not between the archetype and the components. It is before the archetype declaration: a one-paragraph design brief that articulates the specific emotional experience the site should create, derived from the client's actual brand and business context.

**Required addition:** The archetype declaration should require a one-sentence emotional positioning statement:

```
Emotional position: [The visitor should feel X when they arrive, Y as they scroll, Z when they reach the CTA]
```

This is the human intent that makes the difference between "assembled correctly" and "conceived with purpose." The builder agent reads this statement and uses it to make judgment calls at every compositional decision point.

---

**The second first-principles question:** Why does this plan ship the components as raw .tsx files copied at build time?

The Antigravity recommendation (and this plan's resolution) is: raw .tsx injection because it is "less fragile than managing npm packages." This is correct for deployment fragility, but it introduces a different problem: version drift. If the SmoothScrollProvider.tsx in the skills directory gets updated, older builds are running the old version. There is no way to know which version of the components any given deployed site is running.

This is not a fatal flaw: it is an accepted tradeoff. But it should be explicit: the raw .tsx injection approach means we are not building a component library. We are building a copy-paste template system. Each build is self-contained and independent. Updates to craft components require re-running the build for existing sites. This is the right tradeoff for now but should be revisited when the component set stabilizes.

---

## Voice 3: The Expansionist

*What bigger play does this unlock? Where does this compound? Where are we playing too small?*

The plan is playing smaller than it needs to in two directions.

**Underplayed upside 1: This is a productizable asset, not just an internal tool.**

The "Compiled Craft" architecture: archetype selection gate, mathematical craft tokens, pre-compiled components, builder-critic loop with eval rubric: is not just a fix for agentsHQ's output quality. It is the core IP of a web design AI that does not produce AI-slop. That is a product that does not currently exist in the market. Every "AI website builder" produces the same indigo-500 gradient hero. None of them have a Compiled Craft layer.

The plan builds this internally and treats it as an agentsHQ infrastructure upgrade. The bigger play: this becomes Signal Works' primary product differentiator, demonstrated to every prospective client before the pitch even starts. "Here are three sites we built with our system. Tell me which ones look AI-generated." This is a sales weapon, not just a quality gate.

**Required addition:** Phase D in the rollout should include at minimum one "showcase build": a site built with the full system, not for a client but for Signal Works itself, demonstrating all 8 archetypes. This becomes the sales proof that replaces cold pitches.

---

**Underplayed upside 2: The eval rubric is a standalone product.**

The 10 AI-tells, the archetype system, the automated linting criteria: these can be packaged as a public "AI Design Audit Tool." Run any website URL through it and get a score: "7 of 10 AI-tells detected." This is a lead generation tool for Signal Works. Prospects self-qualify by running their own site through it and seeing a bad score. Then Signal Works offers to fix it.

This does not require additional engineering beyond what the plan already builds. The eval rubric already exists. Wrapping it in a public URL-input interface is a frontend build, not a research project.

---

**Underplayed upside 3: The archetype system is a client deliverable.**

Currently the archetype declaration is internal: the agent makes the choice, the client sees the output. The bigger play: the archetype selection process is a client-facing deliverable. "We will show you three archetype options for your site, each with a different visual DNA, motion character, and typography mandate. You select one. Then we build." This adds perceived value, reduces scope creep, and pre-aligns expectations. It turns a backend architectural choice into a discovery ritual.

---

## Voice 4: The Outsider

*Does this make sense to someone who has never seen agentsHQ? What is overcomplicated? What is obvious from outside?*

Reading this plan without prior context:

**What lands clearly:**
- The problem is clear: AI builds the same site every time
- The solution is clear: pre-build the craft, constrain the AI to orchestrate it
- The four layers make intuitive sense in sequence (declare, tokenize, build, review)
- The 10 AI-tells are concrete and actionable

**What is overcomplicated:**

The archetype decision tree in Layer 0 has 5 steps with sub-branches. An agent following this tree will produce a declaration. A human reading the declaration will have no intuition for whether the tree was applied correctly. The tree is internally logical but externally opaque.

**Simpler version:** Reduce the decision tree to 2 questions and a tiebreaker:
1. Who is the primary audience? (technical/professional vs. general consumer vs. creative industry vs. institutional)
2. What is the dominant emotion the site must produce? (trust, excitement, curiosity, awe, comfort)
3. Tiebreaker: what is the client's voice style? (precise/formal vs. warm/personal vs. bold/provocative)

Map these three answers to an archetype in a lookup table. 2 questions + lookup table is easier to audit than 5-step decision tree.

---

**What is missing that seems obvious from outside:**

The plan describes what to build but not what to do when the runtime is wrong. The mandatory pre-build sequence says "if the runtime is not Next.js 14+, stop and escalate." But it does not say what "escalate" means. Who gets notified? What does the operator do? Is there a fallback build path (e.g., plain HTML/CSS output for clients who cannot use Next.js)?

From the outside, this looks like a plan that will work well for Next.js clients and silently fail for non-Next.js clients. If agentsHQ serves clients with different tech stacks, this needs to be addressed.

---

**The name "Compiled Craft" is good but needs to be explained once, clearly, in the builder agent's system prompt.** From the outside, "Compiled Craft" sounds technical. The builder agent needs to understand what it means in plain language: "You are an orchestra conductor, not a musician. The musicians (components) are pre-built and mathematically perfect. Your job is to choose the right players for this performance and conduct them in the right sequence. You do not improvise the music."

---

## Voice 5: The Executor

*What ships first? Where does this die in execution? What is the smallest version that produces signal?*

**What ships first:** The token injection pass (Phase A in the rollout).

Write `craft-tokens.css`. Add the import to `globals.css`. Add the ban list to `frontend-design/SKILL.md`. Run one build. Check if `ease-in-out` appears. This can be done in a single session and produces a measurable signal: either the LLM respects the ban or it does not.

If the LLM does not respect the ban after seeing it in the skill file, the critic agent's automated grep catches it. The ban list has exactly this purpose.

---

**Where this dies in execution:**

Three specific execution risks in order of probability:

**Risk 1: Component copy fails silently.** The builder agent is instructed to copy files from `skills/frontend-design/components/` into the build directory. If the agent hallucinates the file paths, or if the target project's directory structure differs from the assumed layout, the copy step fails and the agent writes its own versions of the components: which will be generic GSAP tutorials. The plan has no verification step for "did the files actually get copied?"

**Fix:** Add a step 0 to the mandatory pre-build sequence: verify that `skills/frontend-design/components/SmoothScrollProvider.tsx` exists and read its first 10 lines. If it does not exist, stop immediately. This forces the agent to verify before copying.

**Risk 2: The critic agent sees every build.** The plan says the critic runs the eval rubric on every build. This means every build requires two agent invocations (builder + critic). The current agentsHQ workflow may not be set up for this two-step pipeline. If the critic agent is not wired into the build loop, it will be used inconsistently (only when someone remembers to run it).

**Fix:** The critic agent invocation must be a hook, not a manual step. In the current CrewAI setup, wire the critic agent as a mandatory output_validator on the builder agent's final deliverable. If CrewAI does not support this natively, write a post-build script that runs the automated grep checks (the objective rubric items) and fails the build if any banned string is found.

**Risk 3: Phase A-D rollout takes four weeks and loses momentum.** The plan proposes a 4-week phased rollout. This is reasonable but risks losing momentum if there is no visible win in week 1. The stakeholder (Boubacar) needs to see the difference between a pre-Compiled-Craft build and a post-Compiled-Craft build within the first session.

**Fix:** Run the before/after comparison on day 1. Take one existing agentsHQ build output. Run it through the eval rubric (even informally). Count the AI-tells. Then run a new build with only the Phase A changes (token injection + ban list). Count the AI-tells again. The improvement should be visible even before the craft components are built.

---

## Chairman's Verdict

**VERDICT: REVISE**

The five voices have spoken. Here is where they agreed, where they disagreed, and what must change.

**Where all five voices agreed:**
- The architectural thesis is sound: compiled craft over prompted craft is the right approach.
- The 10 AI-tells and archetype system are the strongest parts of the plan.
- Phase A (token injection) is the right place to start and will produce signal quickly.

**Where voices disagreed:**
- The Contrarian and the Executor both found execution gaps (component copy verification, critic wiring). The Expansionist did not address these: it was focused on upside. The disagreement is between risk mitigation and opportunity capture. Both are valid; the risks must be addressed first.
- The First Principles Thinker found a depth gap (design intent vs. design correctness). The Outsider found a simplicity gap (5-step decision tree). These are related: the decision tree is complex because it is trying to compensate for absent design intent. Simplifying the tree and adding the emotional positioning statement solves both.

**Required amendments before Phase 5 (Karpathy) runs on this plan:**

1. **Add automated linting to the critic agent.** The critic must grep for banned strings before running any subjective evaluation. Banned strings: `ease-in-out`, `duration-300`, `ease-linear`, `rgba(0,0,0,0.1)`, `Inter` in heading selectors, `grid-template-columns: repeat(3`. These are objective failures that do not require judgment.

2. **Add KineticText graceful fallback.** If SplitText fails to register, fall back to a CSS-only opacity + translateY fade using `--ease-out-expo` and `--duration-slow`. The component does not fail; it degrades gracefully.

3. **Add the emotional positioning statement to the archetype declaration.** One sentence: "The visitor should feel X when they arrive, Y as they scroll, Z when they reach the CTA." The builder agent uses this to make compositional judgment calls.

4. **Simplify the archetype decision tree to 2 questions + tiebreaker + lookup table.** Map: audience type + dominant emotion + voice style = archetype. Remove the 5-step branching tree.

5. **Add a component verification step to the pre-build sequence.** Before copying, verify `SmoothScrollProvider.tsx` exists and is readable. If not, halt with a specific error message.

6. **Define the creative director test protocol concretely.** Who runs it, when, what "flag as AI" means, and what happens if it fails.

7. **Wire the critic agent as a mandatory post-build step**, not a manual invocation. Document how to do this in CrewAI or provide a fallback post-build grep script.

**What does NOT need to change:**

The four-layer architecture is correct. The craft component designs are correct. The rollout order (A before B before C before D) is correct. The PDF upgrade path is correct. The ban list is correct and comprehensive.

The plan is close. The amendments are surgical. After they are incorporated into Phase 6 (Refinement), the plan should pass Karpathy with no FAIL items.

---

*Phase 4 complete. Proceeding to Phase 5: Karpathy Principles Review.*
