# Phase 1: Skill Audit
# agentsHQ Design Upgrade: "Humanized Standard"

**Date:** 2026-05-02
**Scope:** All frontend, design, animation, and web-artifact skills in agentsHQ/skills/

---

## Skills Audited (14 total)

| Skill | Primary Purpose | Output Format |
|---|---|---|
| frontend-design | Website builds for Catalyst Works / Signal Works clients | React/Next.js via Vercel |
| ui-styling | shadcn/ui + Tailwind component library | React components |
| ui-ux-pro-max | Style selection, UX rules, color/font palettes | Recommendations |
| web-design-guidelines | Vercel Web Interface Guidelines compliance review | Code review |
| design | Routing skill for logo, CIP, slides, banner, social, icons | Various |
| design-system | Three-layer token architecture + slide system | CSS variables, HTML slides |
| slides | HTML presentations with Chart.js | HTML |
| banner-design | Social/ad/print banners, 22 art direction styles | HTML screenshot |
| gsap | Animation reference for HyperFrames | JS animations |
| 3d-website-building | Four-phase 3D scroll-driven website pipeline | Next.js |
| 3d-animation-creator | Scroll-driven animation site from video input | Next.js |
| website-intelligence | Competitive research + site audit + redesign brief | HTML report + site |
| react-best-practices | 69 performance rules for React/Next.js | Code review |
| hyperframes | HTML video composition framework | GSAP timelines |

---

## Key Findings Per Skill

### frontend-design
**Gap rating: HIGH**
- GSAP is referenced but no specific easing values, lerp targets, or spring configurations are mandated. Agent defaults to whatever GSAP tutorial values it learned in training (typically `duration: 1, ease: "power2.out"`: competent but generic).
- The ban list is negative-only. Says what NOT to do but provides no positive archetype system. An agent avoiding all banned patterns still has infinite room to produce mediocre output.
- No scroll-behavior constraints. Smooth scroll, scroll-triggered reveals, and scroll-driven narrative are not specified.
- No archetype selection. Every build starts from the same blank canvas.
- Typography guidance is font-ban-only. No sizing scale, no variable font usage, no editorial hierarchy rules.

### ui-styling
**Gap rating: HIGH**
- shadcn/ui IS the AI-slop default. Every component is deliberately neutral: a starting point, not a finish line. Deploying it without customization produces the exact "AI-slop" look the problem statement names.
- No custom easing curves. Tailwind's default `transition` classes use `cubic-bezier(0.4, 0, 0.2, 1)`: the Material Design curve, recognizable and generic.
- No mathematical spring constants, no lerp values, no scroll behavior.
- The token system is structurally sound but the tokens themselves are not defined. `--color-accent` with no value is a schema, not a design system.

### ui-ux-pro-max
**Gap rating: MEDIUM**
- 50+ styles, 161 palettes, 57 font pairings exist as lists but are not enforced. Agent picks "whatever fits": defaults to the most statistically common combination in training data.
- No decision tree for style selection. Agent is told options exist but has no forcing function to commit to one before writing code.
- Animation rules are MEDIUM priority: lower than performance and touch interaction.

### web-design-guidelines
**Gap rating: LOW**
- Entirely dependent on external URL. If the URL changes, the skill breaks silently.
- Guidelines are Vercel-opinionated: correct for SaaS product UI, not for editorial or narrative sites.
- No visual design coverage: only code compliance.

### design (router skill)
**Gap rating: MEDIUM**
- AI-generated logos as the default path. Gemini image generation produces recognizable AI-style logos.
- No integration with the frontend-design build pipeline for asset handoff.

### design-system
**Gap rating: HIGH**
- Token values are not defined: only the architecture. A named token with no value is not a design system.
- No animation tokens. No `--duration-entrance`, no `--ease-spring`, no `--lerp-scroll`.
- CSS variables only: no export to JS constants for use in framer-motion or GSAP.

### gsap
**Gap rating: HIGH**
- Reference-only skill: no values mandated. An agent reading this knows GSAP exists but has no specific easing curves, duration ranges, or stagger patterns to use.
- No Lenis/smooth scroll integration documented.
- No connection to the frontend-design build pipeline.

### 3d-animation-creator
**Gap rating: HIGH**
- Font stack baked in and not client-configurable. Space Grotesk is a good font but its ubiquity in AI-generated sites is itself an AI-tell.
- Website structure is fixed (11 sections, always the same). This is the "identical centered hero" problem systematized.
- No design archetype system. Same structure for every client.

### website-intelligence
**Gap rating: LOW**
- Correctly enforces using real client assets. The 20-50% different redesign constraint is good.
- No handoff format to frontend-design specifying archetype, typography choices, or motion constraints from the research.

### react-best-practices, hyperframes
**Gap rating: NONE/LOW** for the AI-slop problem.

---

## Five Specific Failure Patterns

### Failure Pattern 1: The Unsigned Transition
Every interactive element uses `transition-all duration-300 ease-in-out`: Tailwind's default. This is Google Material Design's standard easing (cubic-bezier 0.4 0 0.2 1), identifiable to any trained eye. Combined with 300ms duration, it produces the "generic web app" feel.

**Find-replace fix:** Define `--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)` as the mandatory default. Ban `ease-in-out` and `duration-300` explicitly.

### Failure Pattern 2: The Template Section Stack
Hero > Features Grid > Testimonials > CTA. Every build. The 3d-animation-creator skill mandates this as its literal fixed structure. No alternative section archetypes exist.

**Find-replace fix:** Archetype selection system with different section vocabularies per archetype.

### Failure Pattern 3: The Inert Hero
A full-viewport hero with a centered heading, a 60% opacity subheading, and a gradient or image behind. The heading does not move, track the cursor, split on scroll, or respond to input. It sits there. This is the "Word document styled with CSS" problem.

**Find-replace fix:** `<KineticText>` component: mandatory on the hero headline.

### Failure Pattern 4: Space Grotesk + Generic Sans Pairing
The 3d-animation-creator mandates Space Grotesk + Archivo. ui-ux-pro-max lists 57 font pairings but provides no forcing function. The LLM's statistical default is Inter or Plus Jakarta Sans: the fonts appearing most frequently in React starter templates.

**Find-replace fix:** Each archetype gets a mandatory font pair. Inter is banned as a heading font.

### Failure Pattern 5: Flat Depth, No Z-Axis
All elements sit on the same z-plane. No parallax, no layered scroll speeds, no foreground/background separation. The page is a vertical strip of stacked sections with identical scroll velocity.

**Find-replace fix:** `<SmoothScrollProvider>` (lerp: 0.07) and `<ParallaxLayer>` components: mandatory at root and on hero backgrounds.

---

## What Is Missing for the Goal

| Missing Element | Priority |
|---|---|
| Mathematical animation constants (easing curves, spring values, lerp targets) | CRITICAL |
| Archetype selection system with decision logic | CRITICAL |
| Pre-compiled craft components (SmoothScrollProvider, KineticText, MagneticButton) | CRITICAL |
| Positive typography mandates per archetype (not just bans) | HIGH |
| Scroll-behavior specification (Lenis, parallax layers, scroll-driven reveals) | HIGH |
| Builder + critic agent loop with eval rubric | HIGH |
| PDF-specific design upgrade path | HIGH |
| Research-to-build handoff format | MEDIUM |
| Inter/Plus Jakarta ban as heading fonts | MEDIUM |
| Consistent easing ban (ease-in-out, duration-300) | MEDIUM |

---

## Audit Verdict

The current skill stack is **structurally correct but craft-empty.** The plumbing exists (shadcn, Tailwind, GSAP, Framer Motion, design tokens) but none of the values that make output feel human are specified anywhere. The LLM fills every unspecified value with its statistical training default, which is always the most common pattern in its training data, which is always generic.

The solution is not more prompting. It is injecting the craft values as hard constraints so the LLM has no room to default.

---

*Phase 1 complete.*
