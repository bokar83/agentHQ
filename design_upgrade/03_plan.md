# 03_plan.md: Implementation Plan: "Compiled Craft" Architecture
**Phase 3 of 7 | agentsHQ Design Upgrade: "Humanized Standard"**
*Compiled: 2026-05-02*

---

## Executive Summary

The audit (Phase 1) confirmed that agentsHQ's current skill stack has correct infrastructure but zero craft values. The research (Phase 2) identified 10 specific AI-tells, 8 design archetypes, concrete mathematical constants for motion, and specific font pairings that distinguish human-made from AI-generated output.

This plan implements a "Compiled Craft" architecture, a term drawn from the Antigravity/Sankofa Council research session that preceded this formal process. The core insight: stop asking the LLM to invent elite UI mathematics and instead force it to orchestrate pre-compiled, mathematically correct primitives. The LLM reasons; the craft is pre-built.

---

## Architecture Overview

The system has four layers. Each layer constrains the one below it.

```
Layer 0: Archetype Selection Gate
  The agent declares an archetype before writing a single line of code.
  Archetype determines which tokens, components, and motion patterns are valid.

Layer 1: Mathematical Craft Tokens
  CSS custom properties and JS constants with exact values derived from
  research (lerp targets, spring constants, easing curves, type scales).
  These are not suggestions. They are the only allowed values.

Layer 2: Compiled Craft Components
  Pre-built, tested React/Next.js components that implement the mathematics
  from Layer 1. The builder agent copies these into every build.
  The agent does not write these components. It uses them.

Layer 3: Orchestrator Protocol (Builder + Critic Loop)
  The builder agent assembles components per the archetype constraints.
  The critic agent runs the eval rubric. The loop has a hard cap.
  Human escalation fires when the cap is hit without a passing score.
```

---

## Layer 0: Archetype Selection Gate

### Decision Logic

Before any code is written, the builder agent must declare an archetype. This declaration gates which components, tokens, and motion patterns are permitted.

**Decision tree:**

```
1. What is the client's primary audience?
   - Developers / technical ops / B2B SaaS -> start with CALM PRODUCT
   - Readers / researchers / institutions   -> start with EDITORIAL NARRATIVE
   - General consumers / app users          -> start with ILLUSTRATIVE/PLAYFUL
   - Creative industry / portfolio          -> start with CINEMATIC/AGENCY
   - High-stakes B2B / enterprise buyers    -> start with TRUST/ENTERPRISE
   - Data journalists / researchers         -> start with DOCUMENTARY/DATA
   - Challenger brands / culture            -> start with BRUTALIST
   - Conversion-rate-critical marketing     -> start with CONVERSION-FIRST

2. What is the client's stage?
   - Pre-revenue / early: weight toward PLAYFUL or CINEMATIC
   - Series A+ / proven: weight toward CALM PRODUCT or TRUST/ENTERPRISE
   - Established institution: weight toward EDITORIAL NARRATIVE or TRUST/ENTERPRISE

3. What is the founder's voice?
   - Direct, technical, precise: reinforce toward CALM PRODUCT
   - Warm, personal, narrative: reinforce toward EDITORIAL NARRATIVE or PLAYFUL
   - Bold, provocative: reinforce toward BRUTALIST or CINEMATIC
   - Formal, authoritative: reinforce toward TRUST/ENTERPRISE

4. Is conversion rate the primary success metric?
   - Yes: override to CONVERSION-FIRST regardless of other signals
   - No: proceed with the archetype from steps 1-3

5. Is the primary content data-driven?
   - Yes and narrative is primary: weight toward DOCUMENTARY/DATA
   - No: proceed with archetype from steps 1-4
```

**Output format (required before any build begins):**

```
ARCHETYPE DECLARATION
---------------------
Selected archetype: [NAME]
Primary signal: [which factor from the decision tree drove the selection]
Overrides considered and rejected: [list any archetype that was close and why it was rejected]
Typography pair: [heading font] + [body font]
Motion character: [one sentence describing the motion behavior this build will use]
Banned patterns for this build: [list the 3-4 patterns from the archetype's refuse list]
```

This declaration is written to a file `design_brief.md` in the project root and is loaded by the critic agent as part of its eval.

---

## Layer 1: Mathematical Craft Tokens

### File: `skills/ui-styling/craft-tokens.css`

This file is injected into every build's `globals.css`. It is NOT optional. The builder agent is instructed to import it before any other styles.

```css
/* CRAFT TOKENS: agentsHQ Humanized Standard */
/* Do not override these values without written architectural justification. */

/* Easing */
--ease-out-expo:   cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-expo:    cubic-bezier(0.7, 0, 0.84, 0);
--ease-spring-sm:  linear(0, 0.009, 0.035 2.1%, 0.141, 0.281 6.7%,
                   0.723 12.9%, 0.938 16.7%, 1.017, 1.077, 1.121,
                   1.149 24.3%, 1.159, 1.163, 1.153, 1.128 32.8%,
                   1.051 39.5%, 1.017 43.1%, 0.991, 0.977 51%,
                   0.974 53.8%, 0.975 57.1%, 0.997 69.8%, 1.003 76.9%, 1);
--ease-spring-lg:  linear(0, 0.028, 0.113, 0.264, 0.46, 0.642, 0.789,
                   0.893, 0.956, 0.989, 1.006, 1.014, 1.017, 1.016,
                   1.013, 1.009, 1.006, 1.003, 1.001, 1);

/* Banned: ease-in-out, ease, linear (except in spring definitions), duration-300 */

/* Durations */
--duration-micro:  120ms;   /* button press, focus ring */
--duration-fast:   220ms;   /* hover state, small reveals */
--duration-base:   380ms;   /* modal entry, standard reveal */
--duration-slow:   600ms;   /* hero entrance, section reveal */
--duration-cinema: 1200ms;  /* cinematic/agency archetype only */

/* Banned: 300ms (the generic web app tell) */

/* Scroll */
--lenis-lerp-editorial: 0.05;
--lenis-lerp-standard:  0.07;
--lenis-lerp-product:   0.10;

/* Border Radius: derived scale, not uniform */
--radius-xs:   3px;    /* tags, badges */
--radius-sm:   6px;    /* buttons, inputs */
--radius-md:   12px;   /* cards */
--radius-lg:   20px;   /* modals, large cards */
--radius-xl:   32px;   /* pill elements */
--radius-none: 0px;    /* brutalist archetype, full-bleed images */

/* Banned: using the same radius on cards AND buttons AND inputs */

/* Type Scale: fluid, not fixed */
--text-display-xl: clamp(3.5rem, 8vw, 8rem);    /* cinematic hero only */
--text-display:    clamp(2.5rem, 5vw, 5rem);     /* standard hero headline */
--text-title:      clamp(1.75rem, 3vw, 2.5rem);  /* section titles */
--text-heading:    clamp(1.25rem, 2vw, 1.75rem); /* subsection headings */
--text-body:       1rem;
--text-small:      0.875rem;
--text-caption:    0.75rem;

/* Letter spacing at display sizes */
--tracking-tight:  -0.03em;  /* for grotesque display type */
--tracking-normal: -0.01em;  /* for standard headings */
--tracking-loose:  0.02em;   /* for captions, small text */

/* Shadows: elevation-aware, not uniform */
--shadow-none:   none;
--shadow-low:    0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
--shadow-mid:    0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
--shadow-high:   0 8px 32px rgba(0,0,0,0.12), 0 4px 8px rgba(0,0,0,0.06);
--shadow-modal:  0 24px 64px rgba(0,0,0,0.18), 0 8px 24px rgba(0,0,0,0.08);

/* Banned: box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) (Tailwind shadow-md) applied globally */
```

### File: `skills/ui-styling/craft-tokens.ts`

```typescript
// CRAFT TOKENS: JS/TS constants for Framer Motion and GSAP
// Import this file wherever motion constants are needed.

export const SPRING = {
  // Calm Product: precise, no overshoot
  ui:         { type: "spring", stiffness: 400, damping: 30, mass: 1 },
  modal:      { type: "spring", stiffness: 300, damping: 25, mass: 1 },
  card:       { type: "spring", stiffness: 200, damping: 20, mass: 1 },
  // Cinematic/Agency: dramatic, slow settle
  hero:       { type: "spring", stiffness: 100, damping: 15, mass: 1.5 },
  // Illustrative/Playful: pronounced bounce
  playful:    { type: "spring", stiffness: 150, damping: 8,  mass: 1 },
} as const

export const GSAP_EASE = {
  standard:   "power2.out",
  entrance:   "power3.out",
  tactile:    "back.out(1.1)",
  cinematic:  "expo.out",
  exit:       "power2.in",
} as const

export const SCROLL = {
  scrub_standard:  1,    // hero sequences
  scrub_cinematic: 2,    // feature showcase stacks
  scrub_precise:   0.5,  // image reveals, parallax
  lerp_editorial:  0.05,
  lerp_standard:   0.07,
  lerp_product:    0.10,
} as const

export const STAGGER = {
  char:  0.02,  // character-level: standard headline
  word:  0.05,  // word-level: editorial narrative
  line:  0.08,  // line-level: slow dramatic reveal
  item:  0.1,   // list items, card grids
} as const

// Banned from all builds:
// - ease: "ease-in-out"
// - duration: 0.3 (300ms generic)
// - stagger: 0 (simultaneous reveal)
```

---

## Layer 2: Compiled Craft Components

### Directory: `skills/frontend-design/components/`

These components are the "Iron Man suit." The builder agent does not write them. It copies them from this directory into `src/components/craft/` of every new build.

**Component inventory:**

#### `SmoothScrollProvider.tsx`

Wraps the application. Configures Lenis with the correct lerp value for the declared archetype. Respects `prefers-reduced-motion`. GSAP ScrollTrigger proxy is registered within this component so ScrollTrigger works correctly with Lenis.

```tsx
"use client"
import { useEffect, useRef } from "react"
import Lenis from "lenis"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

interface SmoothScrollProviderProps {
  children: React.ReactNode
  lerp?: number  // default 0.07
}

export function SmoothScrollProvider({ children, lerp = 0.07 }: SmoothScrollProviderProps) {
  const lenisRef = useRef<Lenis | null>(null)

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (prefersReducedMotion) return

    const lenis = new Lenis({ lerp, wheelMultiplier: 1.2, smoothTouch: false })
    lenisRef.current = lenis

    lenis.on("scroll", ScrollTrigger.update)
    gsap.ticker.add((time) => lenis.raf(time * 1000))
    gsap.ticker.lagSmoothing(0)

    return () => {
      lenis.destroy()
      gsap.ticker.remove((time) => lenis.raf(time * 1000))
    }
  }, [lerp])

  return <>{children}</>
}
```

**Archetype lerp mapping (builder agent reads this comment block):**
- CALM_PRODUCT: lerp={0.10}
- EDITORIAL_NARRATIVE: lerp={0.05}
- CINEMATIC_AGENCY: lerp={0.05}
- ILLUSTRATIVE_PLAYFUL: lerp={0.10}
- BRUTALIST: do not use SmoothScrollProvider
- DOCUMENTARY_DATA: lerp={0.07}
- TRUST_ENTERPRISE: do not use SmoothScrollProvider
- CONVERSION_FIRST: lerp={0.10}

---

#### `KineticText.tsx`

Splits text into characters or words and applies a staggered reveal on scroll entry. Reads the archetype prop to determine animation style. Respects `prefers-reduced-motion`.

```tsx
"use client"
import { useEffect, useRef } from "react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import { SplitText } from "gsap/SplitText"

gsap.registerPlugin(ScrollTrigger, SplitText)

type ArchetypeMotion = "calm" | "editorial" | "cinematic" | "playful"

interface KineticTextProps {
  children: string
  as?: keyof JSX.IntrinsicElements
  motionStyle?: ArchetypeMotion
  className?: string
}

const MOTION_CONFIG: Record<ArchetypeMotion, object> = {
  calm:      { y: 20, opacity: 0, duration: 0.5, ease: "power2.out", stagger: 0.015 },
  editorial: { y: 30, opacity: 0, duration: 0.7, ease: "power2.out", stagger: 0.04 },
  cinematic: { y: 60, opacity: 0, rotationX: -90, duration: 0.8, ease: "expo.out", stagger: 0.03 },
  playful:   { y: 40, opacity: 0, scale: 0.8, duration: 0.6, ease: "back.out(1.7)", stagger: 0.02 },
}

export function KineticText({ children, as: Tag = "h1", motionStyle = "calm", className }: KineticTextProps) {
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (prefersReducedMotion) return

    const split = new SplitText(el, { type: motionStyle === "editorial" ? "words,lines" : "chars,words" })
    const units = motionStyle === "editorial" ? split.words : split.chars

    const config = MOTION_CONFIG[motionStyle]

    gsap.from(units, {
      ...config,
      scrollTrigger: { trigger: el, start: "top 85%", toggleActions: "play none none none" },
    })

    return () => split.revert()
  }, [motionStyle])

  return <Tag ref={ref as React.RefObject<any>} className={className}>{children}</Tag>
}
```

---

#### `MagneticButton.tsx`

A button component with cursor-tracking magnetic hover effect and a tactile spring press. The spring values are hardcoded to the research-derived constants. No generic `transition: all 0.3s ease`.

```tsx
"use client"
import { useRef, useState } from "react"
import { motion, useSpring, useTransform } from "framer-motion"
import { SPRING } from "../craft-tokens"

interface MagneticButtonProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
  strength?: number  // 0.2 default, 0.4 for more dramatic pull
}

export function MagneticButton({ children, className, onClick, strength = 0.2 }: MagneticButtonProps) {
  const ref = useRef<HTMLButtonElement>(null)
  const [position, setPosition] = useState({ x: 0, y: 0 })

  const springX = useSpring(position.x, { stiffness: 200, damping: 15 })
  const springY = useSpring(position.y, { stiffness: 200, damping: 15 })

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return
    setPosition({
      x: (e.clientX - rect.left - rect.width / 2) * strength,
      y: (e.clientY - rect.top - rect.height / 2) * strength,
    })
  }

  const handleMouseLeave = () => setPosition({ x: 0, y: 0 })

  return (
    <motion.button
      ref={ref}
      className={className}
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ x: springX, y: springY }}
      whileTap={{ scale: 0.96, transition: SPRING.ui }}
    >
      {children}
    </motion.button>
  )
}
```

---

#### `ParallaxLayer.tsx`

Wraps any element to apply a scroll-driven parallax offset. Speed prop controls the parallax multiplier. Uses GSAP ScrollTrigger for cross-browser consistency and Lenis compatibility.

```tsx
"use client"
import { useEffect, useRef } from "react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

interface ParallaxLayerProps {
  children: React.ReactNode
  speed?: number       // 0.2-0.4 for background, 0.5-0.7 for midground
  className?: string
}

export function ParallaxLayer({ children, speed = 0.3, className }: ParallaxLayerProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (prefersReducedMotion) return

    gsap.to(el, {
      yPercent: -20 * speed * 100,
      ease: "none",
      scrollTrigger: {
        trigger: el,
        start: "top bottom",
        end: "bottom top",
        scrub: SCROLL.scrub_precise,
      },
    })
  }, [speed])

  return <div ref={ref} className={className}>{children}</div>
}

import { SCROLL } from "../craft-tokens"
```

---

#### `ScrollReveal.tsx`

A general-purpose scroll-triggered reveal component. Used for non-headline content (cards, images, body copy sections). Less dramatic than KineticText.

```tsx
"use client"
import { useEffect, useRef } from "react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

interface ScrollRevealProps {
  children: React.ReactNode
  delay?: number
  className?: string
  from?: "bottom" | "left" | "right" | "fade"
}

const FROM_VARIANTS = {
  bottom: { y: 40, opacity: 0 },
  left:   { x: -40, opacity: 0 },
  right:  { x: 40, opacity: 0 },
  fade:   { opacity: 0 },
}

export function ScrollReveal({ children, delay = 0, className, from = "bottom" }: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (prefersReducedMotion) return

    gsap.from(el, {
      ...FROM_VARIANTS[from],
      duration: 0.6,
      delay,
      ease: "power2.out",
      scrollTrigger: { trigger: el, start: "top 85%", toggleActions: "play none none none" },
    })
  }, [delay, from])

  return <div ref={ref} className={className}>{children}</div>
}
```

---

### Required npm dependencies (scoped to builds using craft components)

```json
{
  "lenis": "^1.1.0",
  "gsap": "^3.12.0",
  "framer-motion": "^11.0.0"
}
```

**Note on GSAP:** SplitText and ScrollTrigger are now free as of GSAP 3.12+ following the Webflow acquisition. GSAP Club membership is no longer required. Verify current licensing at https://gsap.com/pricing/ before each new project.

---

## Layer 3: Orchestrator Protocol

### Modified skill: `skills/frontend-design/SKILL.md`

**Core instruction additions to the existing skill:**

```markdown
## MANDATORY PRE-BUILD SEQUENCE

Before writing any code, complete these steps in order:

1. Run the Archetype Selection Gate (see craft-tokens.ts and the decision tree in 03_plan.md).
   Write the ARCHETYPE DECLARATION block to design_brief.md.

2. Confirm the runtime is Next.js 14+ with App Router. If not, stop and escalate.

3. Copy the following files from skills/frontend-design/components/ into src/components/craft/:
   - SmoothScrollProvider.tsx
   - KineticText.tsx
   - MagneticButton.tsx
   - ParallaxLayer.tsx
   - ScrollReveal.tsx
   - ../craft-tokens.ts -> src/lib/craft-tokens.ts

4. Copy skills/ui-styling/craft-tokens.css into src/app/craft-tokens.css
   and add @import "./craft-tokens.css" as the FIRST line of globals.css.

5. Add required npm packages: lenis, gsap, framer-motion (if not already installed).

## MANDATORY BUILD CONSTRAINTS

- EVERY build MUST wrap the application root in <SmoothScrollProvider> with the
  correct lerp value for the declared archetype.
- EVERY hero headline MUST use <KineticText> with the correct motionStyle for
  the declared archetype.
- EVERY primary CTA button MUST use <MagneticButton>.
- ALL transitions MUST use values from craft-tokens.css or craft-tokens.ts.
  The strings "ease-in-out", "duration-300", and "ease" are banned.
- border-radius MUST vary by element type. Using the same radius on cards AND
  buttons AND inputs is a build failure.
- Inter is banned as a HEADING font. It is permitted as a body font only.
- The three-column symmetric feature grid is banned. Use 2+1, timeline, or
  numbered-list alternatives.
- The centered H1 with gradient background hero is banned. Every hero requires
  a compositional decision beyond centering.

## ARCHETYPE-SPECIFIC OVERRIDES

See archetype definitions in 02_research.md Section 5. Each archetype has:
- Typography mandate (exact fonts to use)
- Motion character (which components and what values)
- Refuse list (patterns that are build failures for this archetype)

If the declared archetype is BRUTALIST:
- Do NOT use SmoothScrollProvider
- Do NOT use MagneticButton (plain <button> with no transitions)
- border-radius: 0 on ALL elements
- Animation as a design choice: either none, or architectural-scale movement only

If the declared archetype is TRUST/ENTERPRISE:
- Do NOT use SmoothScrollProvider
- Do NOT use KineticText with cinematic or playful motionStyle
- KineticText with motionStyle="calm" is permitted for hero only
```

---

## Builder + Critic Loop

### Builder Agent

The builder agent's job is constrained to:
1. Declaring an archetype (ARCHETYPE DECLARATION block)
2. Copying craft components into the build
3. Assembling sections using the components and archetype constraints
4. Writing semantic HTML (`<article>`, `<section>`, `<nav>`, `<main>`, `<footer>`)
5. Implementing all three states for every interactive element (default, loading/error, success)
6. Running a self-check against the eval rubric before submitting to the critic

The builder agent does NOT write GSAP animation logic from scratch, does NOT write custom spring physics, and does NOT override craft token values without explicit escalation.

### Critic Agent

The critic agent reads:
1. `design_brief.md` (the archetype declaration)
2. The eval rubric (Layer 3 deliverable, `eval_rubric.md`)
3. The built code

The critic runs the rubric and returns one of three verdicts:
- **PASS**: Build meets all rubric criteria. Proceed to deployment.
- **REVISE**: Build fails 1-2 rubric items. Specific failures listed with line references. Builder agent gets one revision attempt per REVISE verdict.
- **ESCALATE**: Build fails 3+ rubric items, OR the same item fails twice. Human review required.

**Hard cap:** 3 builder-critic cycles maximum. If the build has not passed after 3 cycles, escalate to human with all artifacts and a summary of what failed and why.

---

## Eval Rubric (Summary)

Full rubric is in `design_upgrade/deliverables/eval_rubric.md`. Summary of criteria:

**Automatic FAIL (any one of these is a build failure):**
1. `<SmoothScrollProvider>` not found at application root (except BRUTALIST/TRUST archetypes)
2. Hero headline not wrapped in `<KineticText>`
3. Primary CTA not using `<MagneticButton>`
4. `ease-in-out` or `duration-300` found anywhere in the codebase
5. Inter used as a heading font (`font-family: 'Inter'` in a heading selector)
6. `grid-template-columns: repeat(3, 1fr)` with 3 identical feature children (the three-box grid)
7. All card, button, and input elements using the same border-radius value
8. Box-shadow using `rgba(0,0,0,0.1)` as the only shadow (Tailwind shadow-md applied globally)
9. Form components with no error state styling
10. Non-semantic markup: div used instead of `<button>`, `<article>`, `<nav>` where applicable

**Human judgment criteria (critic agent scores 1-5, threshold 4):**
1. Compositional integrity: does the layout have a deliberate visual hierarchy beyond centering?
2. Typographic differentiation: does the font pairing create genuine personality?
3. Motion choreography: does motion reinforce hierarchy or just decorate?
4. Archetype consistency: does the full build feel like it belongs to the declared archetype?
5. Warmth: would a working creative director say "a thoughtful human designer built this"?

---

## PDF Design Upgrade Path

PDFs are generated from HTML templates using a headless Chromium print pipeline. The AI-slop problem in PDFs is identical to the web problem: default Tailwind, Inter, uniform spacing, gradient fills on charts.

### PDF-specific constraints

**File to create:** `skills/frontend-design/components/pdf/pdf-base.css`

```css
/* PDF BASE: agentsHQ Humanized Standard */
/* Loaded by the PDF generation pipeline for all document outputs */

@media print {
  /* Typography */
  body {
    font-family: "Source Serif 4", "Tiempos Text", Georgia, serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1a1a1a;
  }

  h1, h2, h3 {
    font-family: "Neue Montreal", "DM Sans", Helvetica, sans-serif;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  /* No gradients in print */
  * {
    background-image: none !important;
    background: transparent !important;
  }

  /* Shadows do not print */
  * {
    box-shadow: none !important;
    text-shadow: none !important;
  }

  /* Page breaks */
  h1, h2, h3 { page-break-after: avoid; }
  table, figure { page-break-inside: avoid; }

  /* Color management */
  /* Charts use colorblind-safe palette, pattern fills as alternative */
}
```

**PDF-specific archetype rules:**

| Web archetype | PDF treatment |
|---|---|
| Calm Product | White background, DM Sans headings, Source Serif 4 body, functional color only in charts |
| Editorial Narrative | Off-white (`#faf8f4`) background, editorial serif throughout, generous leading (1.8) |
| Cinematic/Agency | White background, display grotesque headings at large scale, generous margins, photography full-bleed on section pages |
| Documentary/Data | White background, tabular figures throughout, colorblind-safe chart palette, labeled axes in all charts |
| Trust/Enterprise | White background, Garamond or Georgia headings, formal hierarchy, no color except navy accent |

**PDF AI-tells to ban:**
1. `background: linear-gradient(...)` in any element that will print
2. Inter as the body font (replace with Source Serif 4 or Georgia for print readability)
3. `box-shadow` on any element (invisible in print, wastes space)
4. Font size below 9pt for any text
5. Chart color fills using Tailwind defaults (indigo, purple, green without custom palette)

---

## File Paths: All Artifacts to Produce

### Modified skill files:
- `skills/ui-styling/craft-tokens.css` (new)
- `skills/ui-styling/craft-tokens.ts` (new)
- `skills/frontend-design/SKILL.md` (modified: add mandatory pre-build sequence)

### New craft component files:
- `skills/frontend-design/components/SmoothScrollProvider.tsx`
- `skills/frontend-design/components/KineticText.tsx`
- `skills/frontend-design/components/MagneticButton.tsx`
- `skills/frontend-design/components/ParallaxLayer.tsx`
- `skills/frontend-design/components/ScrollReveal.tsx`
- `skills/frontend-design/components/pdf/pdf-base.css`

### Deliverables (Phase 7 outputs):
- `design_upgrade/deliverables/builder_prompt.md`
- `design_upgrade/deliverables/critic_prompt.md`
- `design_upgrade/deliverables/reference_doc.md`
- `design_upgrade/deliverables/build_loop.md`
- `design_upgrade/deliverables/eval_rubric.md`
- `design_upgrade/deliverables/skill_design_human.md`
- `design_upgrade/deliverables/pdf_addendum.md`
- `design_upgrade/deliverables/runbook.md`

---

## Rollout Order

**Phase A (Week 1): Token injection + ban list**
1. Write `craft-tokens.css` and `craft-tokens.ts`
2. Add import to `frontend-design/SKILL.md`
3. Run one test build using only the token constraints (no craft components yet)
4. Verify: `ease-in-out` and `duration-300` do not appear in the generated code
5. Verify: border-radius varies by element type

**Phase B (Week 2): Craft components**
1. Write and test all 5 craft components locally (SmoothScrollProvider, KineticText, MagneticButton, ParallaxLayer, ScrollReveal)
2. Add mandatory pre-build sequence to `frontend-design/SKILL.md`
3. Run one full test build using all craft components
4. Human review: does the scroll feel premium? does the headline entry feel earned?

**Phase C (Week 3): Archetype system + critic loop**
1. Write the archetype decision tree into `frontend-design/SKILL.md`
2. Write the critic agent system prompt
3. Write the full eval rubric
4. Run three test builds: one per archetype (Calm Product, Editorial Narrative, Cinematic/Agency)
5. Human review: Creative director test. Does each build look like a different archetype? Does none of them look AI-generated?

**Phase D (Week 4): PDF pipeline + full eval**
1. Write `pdf-base.css` and PDF archetype rules
2. Run one PDF test build
3. Run the full builder-critic loop on a real client brief
4. Evaluate: did the system ship without human intervention? If not, what broke?

---

## Open Questions (Resolved)

The Antigravity plan left two open questions. Both are resolved here:

**Q: Raw .tsx injection vs. npm package for craft components?**
**A: Raw .tsx injection.** The builder agent copies files from `skills/frontend-design/components/` into `src/components/craft/` at build time. No npm package, no registry, no versioning complexity. If a component needs updating, update it in the skills directory. The copy happens fresh per build.

**Q: Target runtime confirmation?**
**A:** The plan requires Next.js 14+ with App Router. If the web_builder agent outputs a different runtime, the craft components will not work. The mandatory pre-build sequence includes a runtime check with a hard stop if the runtime is not Next.js 14+.

---

*Phase 3 complete. Proceeding to Phase 4: Sankofa Council Review.*
