# Skill: design-human
**agentsHQ Skill File: "Humanized Standard" Design System**
*This skill replaces ad-hoc design guidance in frontend-design. It is the master design constraint document for all web builds.*

---

## When to Invoke This Skill

Invoke this skill at the start of every web build. It is not optional.

Trigger conditions:
- Any task involving building or modifying a website, landing page, or web application
- Any task involving PDF or slide design output
- Any task where the output will be seen by a client or external stakeholder

---

## What This Skill Does

This skill:
1. Defines the mandatory pre-build sequence
2. Defines the archetype selection system
3. Documents the craft component library (what exists, where to find it, how to use it)
4. Documents the banned patterns list
5. Defines the section checkpoint protocol

This skill does NOT replace `frontend-design/SKILL.md`. It prepends to it. The mandatory content in this skill overrides any conflicting guidance in `frontend-design/SKILL.md`.

---

## MANDATORY PRE-BUILD SEQUENCE

Read and execute in order. These steps are not optional.

### Step 0: Verify Craft Components

Read `skills/frontend-design/components/SmoothScrollProvider.tsx` (first 5 lines).

If the file does not exist:
```
CRAFT COMPONENT VERIFICATION FAILED: Cannot proceed.
Path: skills/frontend-design/components/SmoothScrollProvider.tsx not found.
Escalate to operator.
```

Stop. Do not write any code.

### Step 1: Select Archetype

Answer 2 questions. Look up the result. No 5-step tree. No "weighting."

**Q1: Primary audience:**
- A = Technical / professional
- B = General consumers
- C = Creative industry
- D = Institutional

**Q2: Dominant emotion:**
- 1 = Trust/reliability  2 = Excitement/novelty  3 = Calm/control
- 4 = Awe/immersion     5 = Curiosity/discovery  6 = Comfort/belonging

**Lookup:**

| A1=TRUST_ENTERPRISE | A2=CALM_PRODUCT | A3=CALM_PRODUCT | A4=CINEMATIC_AGENCY |
| A5=DOCUMENTARY_DATA | B1=TRUST_ENTERPRISE | B2=CONVERSION_FIRST | B3=CALM_PRODUCT |
| B6=ILLUSTRATIVE_PLAYFUL | C2=BRUTALIST | C3=CALM_PRODUCT | C4=CINEMATIC_AGENCY |
| D1=TRUST_ENTERPRISE | D5=EDITORIAL_NARRATIVE | D5(data)=DOCUMENTARY_DATA |

**Tiebreaker:** Precise/formal voice -> CALM_PRODUCT or TRUST_ENTERPRISE. Warm/personal voice -> EDITORIAL_NARRATIVE or ILLUSTRATIVE_PLAYFUL. Bold/provocative voice -> BRUTALIST or CINEMATIC_AGENCY.

**Override:** If conversion rate is the primary metric -> CONVERSION_FIRST.

### Step 2: Write design_brief.md

Write this file to the project root before any code:

```
ARCHETYPE DECLARATION
---------------------
Selected archetype: [NAME]
Q1: [A/B/C/D]   Q2: [1-6]
Tiebreaker: [yes/no]   Override: [yes/no]

Typography pair: [heading font] + [body font]
Motion character: [one sentence: what moves, how, at what pace]
Emotional position: [visitor feels X on arrival, Y while scrolling, Z at CTA]
Banned for this build: [3-4 specific patterns from archetype refuse list]

Build checkpoints:
  [ ] Hero:          avoid [banned pattern]
  [ ] Features:      avoid [banned pattern]
  [ ] Social proof:  avoid [banned pattern]
  [ ] CTA:           avoid [banned pattern]
  [ ] Footer:        avoid [banned pattern]
```

### Step 3: Confirm Runtime

This build requires Next.js 14+ with App Router. If not: stop and escalate.

### Step 4: Copy Craft Components

From `skills/frontend-design/components/` to `src/components/craft/`:
- `SmoothScrollProvider.tsx`
- `KineticText.tsx`
- `MagneticButton.tsx`
- `ParallaxLayer.tsx`
- `ScrollReveal.tsx`

Copy `skills/ui-styling/craft-tokens.ts` to `src/lib/craft-tokens.ts`.

### Step 5: Import Craft Tokens

Copy `skills/ui-styling/craft-tokens.css` to `src/app/craft-tokens.css`.

Add as FIRST LINE of `src/app/globals.css`:
```css
@import "./craft-tokens.css";
```

### Step 6: Install Dependencies

```json
"lenis": "^1.1.0",
"gsap": "^3.12.0",
"framer-motion": "^11.0.0"
```

---

## SECTION CHECKPOINT PROTOCOL

Before writing code for each major section, output:
```
Now building: [section name]
Archetype reminder: [archetype]: avoiding [most relevant banned pattern]
Emotional target: [from emotional position in design_brief.md]
```

Re-read `design_brief.md` at each checkpoint. Do not rely on memory of earlier context.

---

## MANDATORY BUILD CONSTRAINTS

### Banned Strings (critic agent greps for these: zero tolerance)
- `ease-in-out`
- `duration-300`
- `ease-linear` (except inside `linear()` spring function definitions)
- `box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1)`
- `rgba(0,0,0,0.1)` as the sole shadow value

### Banned Patterns
- `<div>` where `<button>`, `<article>`, `<nav>`, `<main>`, `<section>`, or `<footer>` applies
- Inter as heading font (h1, h2, h3 must not use Inter)
- The same border-radius value on cards AND buttons AND inputs
- Centered H1 + gradient background + subtitle below (the default hero)
- Any form/list/modal with no error or empty state styling
- `grid-template-columns: repeat(3, 1fr)` with 3 identical children

### Mandatory Components
- `<SmoothScrollProvider>` at application root (except BRUTALIST, TRUST_ENTERPRISE)
- `<KineticText>` on every hero headline (except BRUTALIST)
- `<MagneticButton>` on every primary CTA button (except BRUTALIST)

---

## ARCHETYPE SPECIFICATIONS

### CALM_PRODUCT
```
Fonts:   Geist Sans 700 or Neue Montreal 700 (heading) | Inter 400 or DM Sans 400 (body)
Color:   Near-black bg (~#0f0f11), functional status colors, single gradient accent
Scroll:  Lenis lerp=0.10, ScrollTrigger scrub=1
Spring:  stiffness 300, damping 25 (no overshoot)
Motion:  KineticText motionStyle="calm" (opacity + translateY, no rotation)
Refuse:  Glass morphism, rainbow gradients, mascots, WebGL heroes, decorative motion
```

### EDITORIAL_NARRATIVE
```
Fonts:   Tiempos Text or Playfair Display (heading) | Tiempos Text or Söhne (body)
Color:   Off-white foundation (#f5f2ed), one functional accent
Scroll:  Lenis lerp=0.05, View Transitions for navigation
Motion:  KineticText motionStyle="editorial" (word-by-word reveal), Scrollama + D3 for data steps
Refuse:  Dark mode, glass morphism, icon grids, countdown timers, anything signaling "landing page"
```

### CINEMATIC_AGENCY
```
Fonts:   Clash Display or Neue Montreal 900 (heading) | Neue Montreal 400 or DM Sans 400 (body)
Color:   Dark base, single high-contrast accent moment
Scroll:  Lenis lerp=0.05, ScrollTrigger scrub=2
Motion:  KineticText motionStyle="cinematic" (rotationX:-90, stagger 0.03), ParallaxLayer on hero bg
Hero:    Must fill 100vh, full-bleed media required
Refuse:  3-box feature grids, pricing tables, uniform card radii, Inter at regular weight
```

### BRUTALIST
```
Fonts:   Helvetica Neue 900 or Druk Wide Super (heading) | same grotesque 400 or Courier New (body)
Color:   Pure saturated primaries OR no color; pure white or black bg
Radius:  border-radius: 0 on ALL elements: no exceptions
Motion:  NONE or instant state changes: no transitions, no Lenis, no MagneticButton
Refuse:  Rounded corners, soft shadows, gradients, Lenis, icon libraries, glass morphism
```

### ILLUSTRATIVE_PLAYFUL
```
Fonts:   Nunito 800 or Poppins 700 (heading) | same family 400 (body)
Color:   Warm saturated palette, clear primary + secondary + accent
Scroll:  Lenis lerp=0.10
Spring:  stiffness 150, damping 8 (pronounced bounce: correct for this archetype)
Motion:  KineticText motionStyle="playful", scale(1.05) hover with bouncy spring
Refuse:  Dark mode default, monospace, dense data tables, corporate palettes, enterprise signals
```

### DOCUMENTARY_DATA
```
Fonts:   IBM Plex Sans 600 or DM Sans 600 (heading, chart titles) | same grotesque 400 (body)
Color:   White or #fafafa foundation, 5-7 colorblind-safe chart colors
Scroll:  Lenis lerp=0.07, Scrollama for data steps
Motion:  D3 chart draw-in, CSS scroll-driven animations for indicators, no decorative motion
Special: font-variant-numeric: tabular-nums on ALL numeric data
Refuse:  WebGL, dark mode default, gradient chart fills, motion that does not reveal data
```

### TRUST_ENTERPRISE
```
Fonts:   Freight Display or Neue Haas Grotesk (heading) | Source Serif 4 or Georgia (body)
Color:   Navy or dark teal primary, white secondary, gold or amber accent
Scroll:  NO Lenis, NO scroll animation
Motion:  CSS transitions only: transition: all 0.2s var(--ease-out-expo)
         KineticText motionStyle="calm" for hero ONLY
Refuse:  Dark mode, experimental type, illustration, mascots, neon, startup energy
```

### CONVERSION_FIRST
```
Fonts:   Inter 800 or Neue Montreal 700 (heading) | same sans 400 (body)
Color:   High-contrast CTA button (NOT indigo: must pass WCAG AA 4.5:1)
Scroll:  Lenis lerp=0.10 or disabled
Motion:  CTA hover only (scale 1.02, shadow deepens): no scroll animation before fold
States:  Loading spinner on form submit, checkmark on success: mandatory
Refuse:  Multiple CTAs, hero animation delaying message, dark mode, pre-CTA cognitive load
```

---

## SELF-CHECK BEFORE CRITIC SUBMISSION

Run these checks before handing off:

```bash
grep -r "ease-in-out" src/             # must return 0
grep -r "duration-300" src/            # must return 0
grep -r "SmoothScrollProvider" src/app/layout.tsx   # must return 1+ (unless BRUTALIST/TRUST)
grep -r "KineticText" src/             # must return 1+ (unless BRUTALIST)
grep -r "MagneticButton" src/          # must return 1+ (unless BRUTALIST)
grep -r "craft-tokens.css" src/app/globals.css  # must return 1+
```

Fix any failures before submitting. Do not submit a build you know fails the rubric.

---

## PDF OUTPUT RULES

When the output is a PDF (generated from HTML via headless Chromium print):

1. Import `skills/frontend-design/components/pdf/pdf-base.css` in the PDF template
2. No gradient fills on any element (gradients do not print reliably)
3. No box-shadow on any element (invisible in print)
4. Font size minimum 9pt for all text
5. Body font: Source Serif 4 or Georgia (not Inter for print)
6. Heading font: Same grotesque as the web archetype, but verify it embeds correctly in PDF
7. Chart colors: use colorblind-safe palette, add pattern fills as alternative for B&W printing
8. `font-variant-numeric: tabular-nums` for all numeric data in tables

---

## CRAFT TOKEN CHEAT SHEET

```css
/* Paste anywhere you need quick reference */
--ease-out-expo:    cubic-bezier(0.16, 1, 0.3, 1)
--ease-in-expo:     cubic-bezier(0.7, 0, 0.84, 0)
--duration-micro:   120ms
--duration-fast:    220ms
--duration-base:    380ms
--duration-slow:    600ms
--duration-cinema:  1200ms  /* CINEMATIC archetype only */
--radius-xs: 3px  --radius-sm: 6px  --radius-md: 12px
--radius-lg: 20px --radius-xl: 32px --radius-none: 0px
```

```ts
// Framer Motion springs
stiffness: 400, damping: 30  // button press
stiffness: 300, damping: 25  // modal entry
stiffness: 200, damping: 20  // card hover
stiffness: 100, damping: 15, mass: 1.5  // hero/dramatic
stiffness: 150, damping: 8   // playful/bounce
stiffness: 500, damping: 40  // enterprise/precise
```

```ts
// GSAP easing
"power2.out"   // standard reveals
"power3.out"   // hero entrances
"expo.out"     // cinematic archetype
"back.out(1.1)" // tactile button presses
```

```ts
// Lenis lerp by archetype
EDITORIAL_NARRATIVE: 0.05
CINEMATIC_AGENCY:    0.05
DOCUMENTARY_DATA:    0.07
CALM_PRODUCT:        0.10
ILLUSTRATIVE_PLAYFUL: 0.10
CONVERSION_FIRST:    0.10
BRUTALIST:           none
TRUST_ENTERPRISE:    none
```
