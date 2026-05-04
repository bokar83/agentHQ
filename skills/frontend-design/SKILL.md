---
name: frontend-design
description: >
  Use when creating, updating, or reviewing any website, landing page, or
  HTML/CSS artifact. Must run before writing any code. Applies the Volta
  design standard (cinematic, distinctive, business-type-matched) and enforces
  the banned default skeleton. Trigger on any website build, redesign, section
  update, clone, demo site, or UI artifact request.
---

# Frontend Design Skill

---

## ⛔ COMPILED CRAFT SYSTEM: READ THIS BEFORE EVERYTHING ELSE

This skill uses the **Humanized Standard Compiled Craft architecture**.
Before writing a single line of HTML, CSS, or JavaScript, execute the
mandatory pre-build sequence below. It is not optional. The critic agent
greps for violations after every build.

### STEP 0: Verify Craft Components Exist

Read the first 5 lines of `skills/frontend-design/components/SmoothScrollProvider.tsx`.

If the file does not exist, output this and STOP:
```
CRAFT COMPONENT VERIFICATION FAILED: SmoothScrollProvider.tsx not found at
skills/frontend-design/components/. Cannot proceed. Escalate to operator.
```

Do not write your own SmoothScrollProvider. Stop completely.

### STEP 1: Select Archetype (2 questions + lookup, no tree)

**Q1: Primary audience:**
- A = Technical / professional (developers, ops, B2B buyers)
- B = General consumers (non-technical, everyday users)
- C = Creative industry (designers, agencies, entertainment)
- D = Institutional (researchers, public sector, policy)

**Q2: Dominant emotion the site must produce:**
- 1 = Trust / reliability / permanence
- 2 = Excitement / energy / novelty
- 3 = Calm / clarity / control
- 4 = Awe / wonder / immersion
- 5 = Curiosity / depth / discovery
- 6 = Comfort / warmth / belonging

**Lookup table:**

| A1 = TRUST_ENTERPRISE | A2 = CALM_PRODUCT | A3 = CALM_PRODUCT | A4 = CINEMATIC_AGENCY |
| A5 = DOCUMENTARY_DATA | B1 = TRUST_ENTERPRISE | B2 = CONVERSION_FIRST | B3 = CALM_PRODUCT |
| B6 = ILLUSTRATIVE_PLAYFUL | C2 = BRUTALIST | C3 = CALM_PRODUCT | C4 = CINEMATIC_AGENCY |
| D1 = TRUST_ENTERPRISE | D5 = EDITORIAL_NARRATIVE | D5(data) = DOCUMENTARY_DATA |

**Tiebreaker:** Precise/formal voice -> CALM_PRODUCT or TRUST_ENTERPRISE. Warm/personal -> EDITORIAL_NARRATIVE or ILLUSTRATIVE_PLAYFUL. Bold/provocative -> BRUTALIST or CINEMATIC_AGENCY.

**Override:** If conversion rate is the primary metric -> CONVERSION_FIRST regardless of table.

### STEP 2: Write design_brief.md to project root

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
  [ ] Hero:         avoid [most relevant banned pattern]
  [ ] Features:     avoid [banned pattern]
  [ ] Social proof: avoid [banned pattern]
  [ ] CTA:          avoid [banned pattern]
  [ ] Footer:       avoid [banned pattern]
```

### STEP 3: Confirm Runtime

This build requires **Next.js 14+ with App Router**. If not: stop and escalate.

### STEP 4: Copy Craft Components

From `skills/frontend-design/components/` to `src/components/craft/`:
- SmoothScrollProvider.tsx
- KineticText.tsx
- MagneticButton.tsx
- ParallaxLayer.tsx
- ScrollReveal.tsx

Copy `skills/ui-styling/craft-tokens.ts` to `src/lib/craft-tokens.ts`.

### STEP 5: Import Craft Tokens

Copy `skills/ui-styling/craft-tokens.css` to `src/app/craft-tokens.css`.

Add as **FIRST LINE** of `src/app/globals.css`:
```css
@import "./craft-tokens.css";
```

### STEP 6: Install Dependencies

```json
"lenis": "^1.1.0",
"gsap": "^3.12.0",
"framer-motion": "^11.0.0"
```

---

## ⛔ MANDATORY BUILD CONSTRAINTS

### Banned Strings: critic agent greps for these, zero tolerance

- `ease-in-out`: anywhere in CSS or JS/TS
- `duration-300`: Tailwind class or CSS value
- `ease-linear`: except inside `linear()` spring function definitions
- `box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1)`: Tailwind shadow-md applied globally
- `rgba(0,0,0,0.1)` as the sole shadow value on any element

### Banned Patterns

- `<div>` where `<button>`, `<article>`, `<nav>`, `<main>`, `<section>`, or `<footer>` applies
- Inter as a heading font (h1, h2, h3 must NOT use Inter)
- The same border-radius value on cards AND buttons AND inputs
- Centered H1 + gradient background + subtitle below it (the default hero)
- Any form, list, or modal with no error state or empty state styling
- `grid-template-columns: repeat(3, 1fr)` with 3 identical children (3-box grid)

### Mandatory Components

- `<SmoothScrollProvider>` at application root (exception: BRUTALIST, TRUST_ENTERPRISE)
- `<KineticText>` on every hero headline (exception: BRUTALIST)
- `<MagneticButton>` on every primary CTA button (exception: BRUTALIST)

---

## ⛔ SECTION CHECKPOINT RULE

Before writing code for each major section, output:
```
Now building: [section name]
Archetype reminder: [archetype]: avoiding [most relevant banned pattern for this section]
Emotional target: [from emotional position in design_brief.md]
```

Re-read `design_brief.md` at each checkpoint. Do not rely on memory from earlier context.

---

## ARCHETYPE SPECIFICATIONS

### CALM_PRODUCT
- **Fonts:** Geist Sans 700 or Neue Montreal 700 (heading) + Inter 400 or DM Sans 400 (body) + Geist Mono (code)
- **Colors:** Near-black bg (~`#0f0f11`), functional status colors (green/amber/red), single gradient accent
- **Scroll:** Lenis `lerp={0.10}`, ScrollTrigger `scrub: 1`
- **Spring:** stiffness 300, damping 25: no overshoot
- **Motion:** KineticText `motionStyle="calm"` (opacity + translateY, no rotation)
- **Refuse:** Glass morphism, rainbow gradients, mascots, WebGL heroes, decorative motion

### EDITORIAL_NARRATIVE
- **Fonts:** Tiempos Text or Playfair Display (heading) + Tiempos Text or Söhne (body)
- **Colors:** Off-white foundation (`#f5f2ed`), one functional accent color only
- **Scroll:** Lenis `lerp={0.05}`, View Transitions API for page navigation
- **Motion:** KineticText `motionStyle="editorial"` (word-by-word reveal), Scrollama + D3 for data steps
- **Refuse:** Dark mode, glass morphism, icon grids, countdown timers, anything signaling "landing page"

### CINEMATIC_AGENCY
- **Fonts:** Clash Display or Neue Montreal 900 (heading) + Neue Montreal 400 or DM Sans 400 (body)
- **Colors:** Dark or near-black base, single high-contrast accent moment
- **Scroll:** Lenis `lerp={0.05}`, ScrollTrigger `scrub: 2`
- **Motion:** KineticText `motionStyle="cinematic"` (rotationX: -90, stagger 0.03), ParallaxLayer on hero bg
- **Hero:** Must fill 100vh with full-bleed media (video or high-res photo)
- **Refuse:** 3-box feature grids, pricing tables, uniform card radii, Inter at regular weight

### BRUTALIST
- **Fonts:** Helvetica Neue 900 or Druk Wide Super (heading) + same grotesque 400 or Courier New (body)
- **Colors:** Pure saturated primaries OR no color; pure white or black backgrounds
- **Radius:** `border-radius: 0` on ALL elements: no exceptions
- **Motion:** NONE, or instant state changes only: no Lenis, no MagneticButton, no KineticText
- **Refuse:** Rounded corners, soft shadows, gradients, smooth scroll, icon libraries, glass morphism

### ILLUSTRATIVE_PLAYFUL
- **Fonts:** Nunito 800 or Poppins 700 (heading) + same family 400 (body)
- **Colors:** Warm saturated palette with clear primary + secondary + accent
- **Scroll:** Lenis `lerp={0.10}`
- **Spring:** stiffness 150, damping 8: pronounced bounce is correct for this archetype
- **Motion:** KineticText `motionStyle="playful"`, scale(1.05) hover with bouncy spring
- **Refuse:** Dark mode default, monospace type, dense data tables, corporate blue palettes

### DOCUMENTARY_DATA
- **Fonts:** IBM Plex Sans 600 or DM Sans 600 (heading, chart titles) + same grotesque 400 (body)
- **Colors:** White or `#fafafa` foundation, 5-7 colorblind-safe discrete chart colors
- **Scroll:** Lenis `lerp={0.07}`, Scrollama for data steps
- **Motion:** D3 chart draw-in, CSS scroll-driven animations, no decorative motion
- **Special:** `font-variant-numeric: tabular-nums` on ALL numeric data
- **Refuse:** WebGL, dark mode default, gradient chart fills, motion that does not reveal data

### TRUST_ENTERPRISE
- **Fonts:** Freight Display or Neue Haas Grotesk (heading) + Source Serif 4 or Georgia (body)
- **Colors:** Navy or dark teal primary, white secondary, gold or amber accent
- **Scroll:** NO Lenis, NO scroll animation
- **Motion:** CSS transitions only: `transition: all 0.2s var(--ease-out-expo)`. KineticText `motionStyle="calm"` for hero only.
- **Refuse:** Dark mode, experimental type, illustration, mascots, neon accents, startup energy

### CONVERSION_FIRST
- **Fonts:** Inter 800 or Neue Montreal 700 (heading) + same sans 400 (body)
- **Colors:** High-contrast CTA (NOT indigo: must pass WCAG AA 4.5:1 contrast ratio)
- **Scroll:** Lenis `lerp={0.10}` or disabled
- **Motion:** CTA hover only (scale 1.02, shadow deepens): no scroll animation before fold
- **States:** Loading spinner on form submit, checkmark on success: mandatory
- **Refuse:** Multiple CTAs, hero animation delaying message, dark mode, pre-CTA cognitive load

---

## SELF-CHECK BEFORE CRITIC SUBMISSION

Run these before handing off:
```bash
grep -r "ease-in-out" src/           # must return 0
grep -r "duration-300" src/          # must return 0
grep -r "SmoothScrollProvider" src/app/layout.tsx  # must return 1+ (unless BRUTALIST/TRUST_ENTERPRISE)
grep -r "KineticText" src/           # must return 1+ (unless BRUTALIST)
grep -r "MagneticButton" src/        # must return 1+ (unless BRUTALIST)
grep -r "craft-tokens.css" src/app/globals.css  # must return 1+
```

Fix any failures before submitting. Do not submit a build you know fails the rubric.

---

**No HTML/CSS before this skill completes. Every time. No exceptions.**

Applies to: new sites, redesigns, section updates, single-page tweaks,
clones, demo sites, and app UIs.

---

## ⛔ HARD RULE: The hero section is the close

The hero section closes the client AND the client's clients. For Catalyst Works
sites, the hero is what convinces the visitor to call. For Signal Works pitch
sites, the hero is what convinces the prospect we know what we're doing. The
hero gets the most design attention, the most reference research, and the
strictest sign-off process. **Locked 2026-05-01 after the Elevate hero
substitution incident.** See `memory/feedback_hero_is_the_close.md`.

**Five sub-rules, all non-negotiable:**

1. **Video over still imagery whenever possible.** Drone footage, time-lapse
   builds, walk-throughs, founder-to-camera, before/after transforms. Static
   images are the fallback, not the default. Reasons: motion holds attention
   5-7× longer; signals premium production value; aligns with 2026 trends
   (see `memory/reference_web_design_trends.md`).

2. **If video isn't available, pick the single most representative still** : 
   the one shot that summarizes what the business does. NEVER substitute a
   smaller-but-different image to optimize a Lighthouse score. If file size
   is the problem, **compress the approved asset, don't swap it.** Use WebP
   + JPG fallback via CSS `image-set()` for backgrounds, `<picture>` for
   `<img>` tags. The Elevate rebuild ships `hero-roof.webp` (454KB) +
   `hero-roof.jpg` (304KB) compressed from a 1.2MB source: same image,
   3× smaller.

3. **Asset-level hero changes need explicit operator sign-off.** Once a design
   is approved, the hero image, video, copy, fonts, and any other front-and-center
   asset cannot be changed without operator confirmation, even when an automated
   signal (Lighthouse, accessibility audit, contrast checker) says it should
   be. Code-level fixes (focus rings, ARIA, schema, contrast tokens that don't
   change the look) are fine to apply silently. Asset changes are not.

4. **Lead with hero changes in any report.** If the hero gets touched, that
   change goes at the top of the next user-facing message: not buried in a
   list. Reporting bar: surface the change in the first 3 lines, not the 30th.

5. **Default hero patterns by business type:**
   + **Roofer / contractor / builder:** drone footage of completed roof or
     active build, looped silently, autoplay deferred until idle for LCP.
     Static fallback = drone still.
   + **Dentist / orthodontist / pediatric dental:** founder smile-with-team
     or clean modern operatory walk-through. Static fallback = founder portrait.
   + **HVAC / plumber / electrician:** tech-in-uniform working on equipment,
     or before/after thermal imagery. Static fallback = uniformed tech still.
   + **Lawyer / advisor / consultant:** founder in their office or speaking
     on a stage. Static fallback = sharp founder portrait.
   + **SaaS / tech:** product walk-through screencast OR animated illustration
     of the core flow. Static fallback = product hero shot.
   + **Restaurant / hospitality:** kitchen close-up or service shot. Static
     fallback = signature dish or interior.

**The bar:** if the prospect's hero doesn't beat the best 3 reference sites
in the niche on first impression, redesign it. The hero is not a section. It
is the close.

---

## ⛔ HARD RULE: Regenerate OG images after every copy or branding change

Many sites keep an `og-image.html` source template that renders to `og-image.jpg`
(or `.png`) for social shares. The HTML is the source of truth; the JPG/PNG is
what LinkedIn, Twitter, and Slack actually load. **They drift.**

**Symptom:** You update site copy (price, duration, headline). The HTML
template is current, but the image file on disk is months stale. Anyone
sharing the URL on LinkedIn sees the OLD price / OLD copy in the share card.

**Real incident 2026-05-01:** catalystworks.consulting `og-image.jpg` was
showing "$350 / 60 minutes" for a Signal Session that has cost $497 / 90 min
for months. The HTML had been edited at some point but the JPG was rendered
2026-04-03 (pre v3-WOW redesign). Every LinkedIn share for ~30 days carried
wrong price.

**How to apply:**

When you change ANY of: price, headline, duration, brand colors, founder
name/photo, eyebrow text, CTA URL, OR any text that appears in the OG
image template: you MUST regenerate the OG image file in the same commit.

**Regen pattern (Playwright + local server, no extra tooling):**

1. Serve the site locally: `python3 -m http.server 8743` from the site dir
   (run in background).
2. `mcp__plugin_playwright_playwright__browser_resize` to width 1200, height 630.
3. `browser_navigate` to `http://127.0.0.1:8743/og-image.html`.
4. `browser_take_screenshot` with `type: 'jpeg'`, `fullPage: false`: saves
   to `.playwright-mcp/og-image-new.jpg` or repo root.
5. `mv` the new file over the old `og-image.jpg`. Backup the old one if
   you want, but don't commit the backup.
6. `git add og-image.html og-image.jpg` together. Commit message names both.
7. Stop the local server.

**Verify:** open the new JPG and read the text manually. If it still says
the old price/copy, the source HTML wasn't updated either: fix it and
re-render before committing.

**Cache-busting:** social platforms cache OG images aggressively. After
deploy, prime the cache via Twitter/LinkedIn debuggers (or just append a
`?v=2` query param to the og:image URL in the HTML head: file path stays
the same, but social scrapers see a new URL).

---

## Stay at the forefront: and create new trends

Boubacar's directive (locked 2026-05-01): *"We will need to be following trends
for website building and stay at the forefront of them and ourselves go ahead
and create new trends."*

Before designing any hero or major section, **read `memory/reference_web_design_trends.md`**.
That memory tracks Awwwards / Godly / Linear / Cofolios / Land-book as the
trend-following sources, plus the current snapshot of what's hot (cinematic
video heroes, scroll-driven scrub, glassy translucent layers, bento grids,
ticker strips, cursor glow, etc.).

The "lead, don't follow" mandate: **ship at least one element per build that
the next 50 contractors in the niche won't have for 12-18 months.** Examples:

- Schema.org structured data (most contractors haven't even heard of it)
- Scroll-driven scrubbed video on contractor sites
- AI-search-optimized FAQ blocks
- Voice-search-optimized H1/H2 phrasing
- Calendly-replacement embedded scheduling in the hero CTA itself

Document trend-leading elements in the engagement-ops or roadmap entry so we
can claim credit when the niche catches up.

---

## The Volta Standard

`workspace/demo-sites/volta-studio/index.html` is the reference bar for
**quality of thinking and craft**, not for visual style.

The Volta site is dark, neon, cinematic, and packed with motion. That is
right for a creative agency. It would be wrong for a pediatric dentist,
a bakery, a law firm, or a real estate developer. Do NOT apply Volta's
aesthetic to every site. Apply Volta's *level of intentionality* to every site.

**What Volta demonstrates that every site must match:**

1. **Research before design.** Volta's dark cinematic style was chosen
   because it fits a creative agency's emotional register. For every new
   site, ask: what does premium look like *for this specific category*?
   What do the best sites in this niche do? What would surprise and delight
   a visitor who usually sees template sites in this space?

2. **Distinctive layout skeleton.** Volta does not use sticky-nav + split-hero
   + card-grid. Neither should any other site, but the alternative must fit
   the business, not just be "different for different's sake."

3. **At least one interaction that makes you feel the site.** Volta has a
   particle trail, a morphing blob, a pinned horizontal scroll. A kids'
   dentist might have floating tooth animations and a morphing blob hero.
   A restaurant might have a full-bleed video section with a parallax food
   reveal. A law firm might have a slow, weighty clip-path entrance and
   a typographic hero. The *form* is different every time. The *intention*
   : that the site feels alive and considered. That is the constant.

4. **No rubber-stamping.** The biggest failure mode is shipping the same
   skeleton with Volta's neon green swapped for a different accent color.
   That is still a template. The skeleton, the interaction vocabulary, the
   font personality, and the emotional register must all be derived from the
   specific business and its audience.

**Boubacar's rule:** Default to ambitious. Pull back if asked.
Never the reverse. "I'd rather pull you back than push you further."

The question before every build: *if this business had a $50K design budget,
what would the agency they hired produce?* Build that. Not the $500 version.

---

## THE GOAL: AVOID AI SLOP

This skill exists to prevent AI-generated visual slop. Every other rule serves that one goal. The most important target is **Signal Works demos and client builds**: those sites ARE the agency's portfolio. A prospect judging whether to hire Signal Works to "build me a site that doesn't look AI-generated" is judging the demo they see. If that demo reads as AI-generated within 5 seconds, the agency loses the prospect, regardless of how good the cinematic motion is.

**Signal Works builds get a stricter floor than internal builds:** must score `/design-audit` ≥17/20 with anti-patterns ≥3/4 before going live. No exceptions.

---

## PROJECT CONTEXT PERSISTENCE (PRODUCT.md + DESIGN.md)

Every multi-session project (demo site, client site, lead magnet, internal tool) gets two files at the project root that LOCK strategic + visual decisions across sessions:

- `<project-root>/PRODUCT.md`: register (brand vs product), what this is, who it's for, three voice words, anti-references, audience reflexes to reject, success criterion, failure mode
- `<project-root>/DESIGN.md`: locked typography, palette, spacing scale, type scale, motion vocabulary, interaction primitives, anti-pattern compliance checklist

### When to use this protocol

- Building any site / artifact that will span more than one session
- Building any Signal Works demo, client site, or lead magnet (always: these are `register=brand`)
- Iterating on an existing project (load both files first to avoid drift)

### Protocol

**At session start, before anything else:**

1. Look for `PRODUCT.md` and `DESIGN.md` at the project root
2. If they exist: READ THEM. They override defaults. Do not re-derive design from scratch.
3. If they don't exist AND this is a multi-session build: CREATE THEM before writing HTML
   - Templates: `~/.claude/skills/frontend-design/templates/PRODUCT.md.template` + `DESIGN.md.template`
   - Copy template → fill in by interviewing user (or reading existing brand.md, engagement notes, prior audit)
   - **Never synthesize PRODUCT.md from the user's original prompt alone.** Ask 2-3 specific questions per round, minimum one round of real user answers before drafting.
   - DESIGN.md is created AFTER PRODUCT.md: the design decisions derive from the strategic context, not the other way round.

**During build:**

- Cite the relevant section of DESIGN.md when making a visual decision (e.g. "DESIGN.md locks display font as Spectral 700, using that for hero")
- If you want to deviate from DESIGN.md mid-session: STOP. Surface the deviation to user. Get explicit approval before changing the file or the build.

**At session end:**

- Update DESIGN.md if any locked decision changed during the session (with user approval)
- Update build log entry in `workspace/demo-sites/build-log.md` (if applicable)
- The next session loads PRODUCT.md + DESIGN.md fresh and continues from there

### Why this matters

Without persisted context, every new session starts from defaults. Defaults are AI-slop. Three sessions on the same project produce three different visual directions. The user gets frustrated. The work regresses. Persistence prevents this.

### Catalyst Works projects

CW projects already have `docs/styleguides/styleguide_master.md` v1.1 + `styleguide_websites.md` v1.1 as their global DESIGN.md equivalent. PRODUCT.md per CW project is still useful for register, voice words, anti-references, success criterion. Create one for any CW project that has its own positioning (e.g. `boubacarbarry-site/PRODUCT.md`, `humanatwork-site/PRODUCT.md`).

---

## CRAFT REFERENCE LIBRARY

When you need craft knowledge beyond the rules in this skill (typography reasoning, color contrast theory, motion principles, spatial logic, microcopy guidelines, cognitive load management), load the relevant file from `~/.claude/skills/frontend-design/reference/`:

- `typography.md`: picking fonts, type scales, vertical rhythm
- `color-and-contrast.md`: palette construction, OKLCH, accessibility
- `spatial-design.md`: whitespace, grids, asymmetric layout
- `motion-design.md`: easing curves, scroll triggers, reduced-motion
- `interaction-design.md`: hover, focus, click affordances
- `responsive-design.md`: breakpoints, fluid type, touch targets
- `ux-writing.md`: buttons, errors, empty states, microcopy
- `cognitive-load.md`: what to cut, hide, hierarchy-rank
- `heuristics-scoring.md`: design quality dimensions

See `reference/README.md` for when to load each one. Don't load all 9 every time: pick the 1-2 that match the question you're answering.

### Specialized contexts (defer to ui-styling)

For shadcn-substrate decisions (component sources, theming, blocks, agent UIs), defer to `ui-styling` per the canonical-home rule:

+ **Agent / chat / tool-call UIs** (Atlas chat, Studio operator panels, MCP-app surfaces): see `skills/ui-styling/references/shadcn-agent-ui.md`. Start from 21st.dev Agent Elements, then apply the Volta standard on top.
+ **Branded theme generation** for any build: see `skills/ui-styling/references/shadcn-theming.md` (tweakcn-first workflow).
+ **Structured business PDFs** (invoice, statement, SOW): see `skills/ui-styling/references/shadcn-pdf.md` (pdfx lane).

---

## ABSOLUTE BANS (Impeccable-derived)

These are not preferences. They are training-data tells that mark a site as AI-generated within 5 seconds. Refuse and rewrite.

1. **Side-stripe colored borders**: `border-left` or `border-right` >1px as a colored accent on cards, blocks, sections, or quotes. The "1-3px colored line on the side of a card" is the universal AI tell. Use spacing, weight, or asymmetric layout for hierarchy instead.

2. **Gradient text**: `background-clip: text` + linear-gradient. Always tacky, always reads as AI. Use a single bold color or a typographic moment instead.

3. **Glassmorphism as default**: `backdrop-filter: blur()` on most surfaces, frosted nav bars, blurred translucent cards. Acceptable as a single rare moment. Never as a system.

4. **Hero-metric template**: giant number + small label + supporting stats grid + accent line. The "$9,660 ANNUAL BLEED" pattern. Replace with editorial typography where the number IS the moment, not boxed inside a card.

5. **Identical card grids**: 3-6 cards in a row with the same icon, heading, body. Whether the cards have side-stripes, hover lifts, or gradient backgrounds, the *grid of identical cards* is the tell. Use kinetic lists, asymmetric editorial grids, depth-reveals, or feature-film stacks instead.

6. **Modal as primary CTA path**: popups for booking, signup, or any action that should be inline. Modals for confirmations are fine. Modals as the main conversion mechanism are slop.

7. **Em-dashes**: `: ` and `--` in body copy. Use commas, colons, semicolons, or rewrite. Em-dashes in AI-generated text are the #1 written tell. (This rule is enforced by `scripts/check_no_em_dashes.py` at commit time too.)

8. **Bounce easing as default**: `cubic-bezier` overshoot on every interaction. Bounce should be rare and intentional. Default to `ease-out` or `cubic-bezier(0.22, 1, 0.36, 1)` for entrances.

9. **Category-reflex palettes**: if a stranger could guess the business category from the palette/theme alone, it is training-data slop. Reject and reframe. Examples (all banned as defaults):
   - Dental → blue/white/sky-blue + tooth mascot
   - Law → navy + gold + serif
   - Healthcare → white + teal + smiling person
   - Crypto → neon-on-black
   - Agency / creative studio → cinematic dark + neon green or orange accent
   - SaaS / consulting → navy + cyan + orange CTA
   - Roofer / HVAC / contractor → dark + orange + industrial display sans

If the palette would look "right" for any business in the category, it is right for none. The whole point of design is to feel specific.

10. **Reflex-reject fonts**: Refuse these picks. They are training-data defaults. Find an alternative from a real catalog (Pangram Pangram, Future Fonts, Klim, Velvetyne, Production Type, Grilli Type) or, for free options, use Google Fonts but pick something that does NOT appear on this list.

| Banned font | Why |
|---|---|
| Inter | The #1 reflex sans. Every AI-generated SaaS site. |
| DM Sans | The #2 reflex sans. Replaced Inter as the default in 2024. |
| DM Serif Display / DM Serif Text | Default "elegant" pick for AI. |
| Plus Jakarta Sans | Default "friendly modern" pick. |
| Space Grotesk / Space Mono | Default "technical/startup" pick. |
| Syne | Default "agency confident" pick. |
| Outfit | Default "modern friendly" pick. |
| Instrument Sans / Instrument Serif | Default "editorial modern" pick. |
| Fraunces | Default "warm serif" pick. |
| Newsreader / Lora / Crimson / Crimson Pro / Crimson Text | Default "literary" picks. |
| Playfair Display | Default "luxury" pick: most overused serif of 2018-2025. |
| Cormorant / Cormorant Garamond | Default "premium serif" pick. |
| IBM Plex Sans / Plex Serif / Plex Mono | Default "we read Hacker News" pick. |
| Source Serif 4 | Default "considered serif" pick. |

**Picks that are NOT on the reject list and are good defaults for free Google Fonts:**
- **Spectral** (Production Type): display serif, editorial weight
- **Public Sans** (USWDS): neutral sans with character
- **Fraunces is banned** but if you need a contemporary serif, try **Roboto Slab** or **Bitter** for body
- **Unbounded**: display sans, industrial register (used carefully)
- **Fredoka / Baloo 2**: playful, kid-friendly (rotation, not default)
- **Bricolage Grotesque**: modern editorial sans, distinctive
- **Gloock / Big Shoulders Display**: bold display
- **Cabinet Grotesk / Erode / Satoshi** (Fontshare, free): premium look, not reflex

---

## FONT SELECTION PROCEDURE (Impeccable-derived)

When picking a font for any new build, follow this procedure. Skip and you will reach for Inter or DM Sans by default.

### Step A: Three concrete brand-voice words

Not "modern" or "elegant." Concrete physical-object words.

> Bad: "modern, friendly, professional"
> Good: "warm and mechanical and opinionated"
> Good: "weighty, hand-set, like a serious magazine cover"
> Good: "scrappy, punk-zine, photocopier-pressed"

### Step B: List your three reflex picks

Write down the three fonts you reach for first. Be honest.

### Step C: Reject any reflex pick that's on the ban list

Cross-reference Step B against the ban list above. If any of your three are banned, reject them. They are reflexes precisely because the AI training corpus has those fonts on millions of sites.

### Step D: Browse a real catalog

Open one of:
- pangrampangram.com
- futurefonts.xyz
- klim.co.nz
- velvetyne.fr
- productiontype.com
- grillitype.com
- fontshare.com (free Indian Type Foundry catalog)

Look for the brand-as-physical-object words from Step A. Pick something that fits.

### Step E: Cross-check

If your final pick equals your original reflex pick (Step B), start over. You rationalized your way back to the default.

### Step F: For Catalyst Works builds

**For any CW-branded artifact, ALWAYS load the source-of-truth typography file FIRST:**

> `D:\Ai_Sandbox\agentsHQ\docs\styleguides\CURRENT_TYPOGRAPHY.md`

This file is the single canonical source for which fonts are active on CW work. Hard-coding font names in this skill goes stale within months: read CURRENT_TYPOGRAPHY.md every time. As of 2026-04-29 it locks Spectral + Public Sans + JetBrains Mono, but check the file for the latest.

Then load the relevant artifact-type styleguide:
- Website / app: `docs/styleguides/styleguide_websites.md` (currently v1.1)
- PDF / consulting report: `docs/styleguides/styleguide_pdf_documents.md` (currently v2.2)
- Master rules (voice, anti-patterns, color): `docs/styleguides/styleguide_master.md` (currently v1.1)

These styleguides DEFER to CURRENT_TYPOGRAPHY.md for fonts and contain only artifact-specific layout rules (cover page geometry, gold bar, button specs, etc). When CURRENT_TYPOGRAPHY.md and a styleguide conflict on fonts, **CURRENT_TYPOGRAPHY.md wins**: it's the latest source of truth.

---

## COLOR SELECTION PROCEDURE

Same logic as fonts: rotation tables encode reflexes. Use procedure.

### Step A: Anchor the palette in something specific to THIS business

Not "the category palette." Something specific. The actual location's light. The actual texture of the materials they sell. The actual interior of their office. A photograph from the client. The cover of a book that captures the register.

### Step B: Reject category-reflex palettes (see ban #9)

If the palette you reached for is the category default, reject it. A pediatric dentist does NOT have to be navy + sky-blue + coral. A roofer does NOT have to be dark + orange. A consultant does NOT have to be navy + cyan.

### Step C: Pick 3 anchor colors max + 1 neutral

More than 4 colors is decoration, not a system. Each color has a job:
- Surface (background)
- Ink (text)
- Accent (CTA, focal moments: used sparingly)
- Optional: secondary accent OR ornament (for warmth, like CW's clay)

### Step D: One of the colors should surprise

If all 4 colors are predictable for the brief, the palette is generic. One of them should be a choice nobody else in the category would make, anchored in Step A.

---

## DESIGN_PREFLIGHT (mandatory output before first `<` character)

Before writing any HTML, output this exact line in your response:

```
DESIGN_PREFLIGHT: skeleton=pass build_log=pass agency=pass volta_floor=pass interactions=pass photos=pass reflex_check=pass category_reflex=pass register=brand|product
```

Each token must be `pass` (not just present: actually verified). If you cannot honestly write `pass` for a token, the build is not ready. The tokens map to the verification checks A-F below + the new reflex/category checks. `register=brand` if the design IS the product (Signal Works demos, agency portfolio, brand-led builds). `register=product` if design serves the product (CW landing, lead magnets, internal tools).

If this string is missing from the output, the skill did not run. The build must restart.

---

## HARD RULES

### 1. The banned skeleton

This layout combination is BANNED:

> sticky-nav + split-hero + ribbon-bar + alternating-2col-sections +
> card-grid + CTA-box + footer

Changing fonts and colors does NOT make this a different design.
Boubacar can feel the skeleton through any costume. If you catch yourself
building this, stop. Change at least 3 structural elements before proceeding.

### 1b. The services section is NEVER a card grid

This is the single most common failure. A services section with 3-6 boxes/cards in a row or grid is the banned skeleton, regardless of how the cards are styled. The word `svc-card`, `service-card`, or `card-grid` in a services section is a red flag. Use one of these instead:

+ **Kinetic list**: full-width numbered list items that slide or fan in on scroll, no cards
+ **Editorial grid**: asymmetric layout where service items have wildly different sizes (one large, two small, one full-width)
+ **Depth-reveal**: 3D perspective cards that start face-down and rotate to reveal on scroll (CSS `rotateY` + ScrollTrigger)
+ **Horizontal scroll lane**: services revealed left-to-right in a pinned horizontal scroll section
+ **Feature film**: each service gets its own full-viewport section, stacked vertically, revealed with clip-path

If you are about to write `<div class="service-card">` or `<div class="svc-card">`, stop. Use one of the above patterns instead.

### 2. No same skeleton twice

Check `workspace/demo-sites/build-log.md` before designing. Avoid
repeating the same layout archetype, font pairing, or color story used in
the previous 3 builds.

### 3. Business-type match

Research what premium looks like for THIS specific business category.
A kids dentist is not a law firm is not a restaurant is not a SaaS.
Each has its own emotional register, layout language, and interaction
vocabulary. Spend 2 minutes thinking about the category before picking
an archetype.

### 4. Custom cursor: no mix-blend-mode ever

`mix-blend-mode: difference` and `mix-blend-mode: exclusion` make the
cursor invisible on dark backgrounds. They are BANNED on cursor elements.
Always use explicit colors with no blend mode.

```css
/* CORRECT */
#cursor {
  background: #7BFF6A; /* explicit color, no mix-blend-mode */
}

/* BANNED */
#cursor {
  background: white;
  mix-blend-mode: difference; /* invisible on dark backgrounds */
}
```

### 5. Self-verification before writing any code : mandatory (cannot be skipped)

Before the first `<` character, you must produce ALL of the following. Missing any item means the skill has not run. Do not proceed.

**A. Anti-banned-skeleton check (explicit):**
Write out your planned section order, e.g.:
> "My sections: full-viewport blob hero / horizontal scroll reviews / wavy-divider services / stat counters / FAQ accordion / minimal footer"

Then check each against the banned skeleton:

- Does it start with sticky-nav + split-hero? If yes, STOP. Redesign.
- Does it use alternating-2col-sections? If yes, STOP. Replace with something from the archetype table.
- Does it use a generic card-grid for services? If yes, STOP. Use depth-reveal, kinetic list, or editorial grid instead.

**B. Build log check (explicit):**
Read `workspace/demo-sites/build-log.md`. Write out the last 3 archetypes used. Confirm yours is not a repeat.
> "Last 3 archetypes: [A], [B], [C]. My archetype: [X]. No repeat confirmed."

**C. $50K agency question (explicit):**
Write one sentence: what would a top-tier agency produce for this specific business category that would make a visitor stop scrolling?
> "For a [business type], the $50K agency move is: [specific, concrete answer (not 'a premium feel').]"

**D. Volta line count check:**
`workspace/demo-sites/volta-studio/index.html` is 926 lines. `workspace/demo-sites/thepointpediatricdentistry/index.html` is 923 lines. Your output must be at minimum 800 lines. A site under 800 lines is not at Volta quality. If you are under, you have skipped animations, schema, or sections.

**E. Interaction inventory (explicit):**
List the 3+ cinematic interactions you will implement before you start:
> "Interactions: [1], [2], [3]"
These must be specific (e.g. "GSAP SplitText on H1 with chars stagger 0.04s" not "hero animation"). Vague descriptions mean the skill did not run.

**F. Photo plan (explicit): NEW:**
Before writing a single `<img>` tag, state every photo slot the site needs and where each image comes from.
> "Photos: hero (Kie prompt: '...'), team (Kie prompt: '...'), before/after pair (Kie prompts: '...' / '...')"
Unverified Unsplash hotlinks are banned. See IMAGE RULES below.

If all six checks are written and pass, proceed. If any are missing or fail, stop and resolve before touching HTML.

---

## FAILURE MODE GALLERY

These are real outputs that failed the Volta standard. Never ship anything that looks like these:

- **The Resume Template**: sticky nav, hero with left text + right image, 3-column card grid for services, testimonials carousel, contact form, footer. BANNED.
- **The Bootstrap Reskin**: same skeleton as above but with a different font and accent color. Still BANNED. Boubacar can feel the skeleton through any costume.
- **The Figma Export**: technically correct, visually dead. No motion, no cursor, no life. Looks finished but does not feel alive. BANNED.
- **The "Clean" Cop-out**: "this business needs something clean and minimal" used as justification for a skeleton site. Clean is a design choice. Skeleton is not clean, it is lazy. BANNED.
- **The Blob Swap**: took a previous site, changed the blob color from cobalt to teal, added "sky blue accent." Still the same skeleton. Still BANNED.
- **The Rushed First Pass**: wrote HTML before completing all five self-verification checks. Got called out. Had to rebuild. Wasted time, burned trust. BANNED behavior.
- **The Emoji Icon**: used emoji characters as decorative service icons instead of CSS shapes, SVG, or generated images. BANNED on any client-facing site.
- **The Hotlink Gamble**: grabbed an Unsplash URL, tested that it returned HTTP 200, and embedded it without knowing what the photo shows. This produced a Monster Energy drink on a children's dental site, a chef on a roofing site, and a caulk gun in a "crew" section. HTTP 200 is not content verification. BANNED.

If your output could appear in a Wix template gallery, it has failed.

---

## MANDATORY: Read a reference site before writing code

Before writing the first `<` character, you MUST open and read at minimum the first 150 lines of ONE of these reference sites:

```
workspace/demo-sites/volta-studio/index.html         (926 lines: cinematic dark, agency)
workspace/demo-sites/thepointpediatricdentistry/index.html  (923 lines: storybook blob, kids dental)
```

Choose the one closest in spirit to the business you are building. Read it. Note:
- How the hero is structured (not a split-hero with left text + right image)
- How GSAP is initialized and used
- How ScrollTrigger is wired
- How the custom cursor is built (no mix-blend-mode)
- How many CSS variables are defined up front
- How the noise texture overlay is done (Volta)
- How section transitions are handled (wavy SVGs, clip-path, marquee)

This is not optional. It is the technical calibration step. The reference sites are the floor, not the ceiling.

---

## MANDATORY: Live competitive research before writing code

After reading the reference site, **before writing any HTML**, research what premium looks like in the wild for the specific business category. This is how you avoid building a pediatric dental site that looks like every other pediatric dental site.

### Step 1: Trigger the website-intelligence skill first

The `website-intelligence` skill already exists in the stack. It scrapes real sites, analyzes them, and produces a design brief. **It should run before frontend-design, not after.** If you are building for a known business category (dental, roofing, HVAC, law, restaurant, etc.), invoke it first:

```
/website-intelligence [business category] [city]
```

If the user has provided a client URL, pass that too. The output tells you what the competition looks like and where the opportunity is to be distinctive.

### Step 2: Firecrawl search for premium examples

If website-intelligence has not already run, use Firecrawl search to find 2-3 real premium sites in the category. Extract what makes them distinctive: not what they have in common (that is what to avoid).

```python
from firecrawl import FirecrawlApp
app = FirecrawlApp()
results = app.search("best [category] website design award winning [city]", limit=5)
```

For each result, extract:
- Hero structure (what is the first thing you see: image, type, video, illustration?)
- Color palette (what 2-3 colors dominate?)
- What trust signals appear above the fold
- Any interaction or animation that is memorable
- What they do that generic sites in this category do NOT do

### Step 3: Write a one-paragraph competitive brief

Before touching HTML, write this out:
> "The best [category] sites I found do [X]. The generic sites all do [Y]. My site will stand out by doing [Z], which none of them do."

This is not optional. It is the research output that feeds the $50K agency question (check C) and the design brief (Step 3). Without it, the $50K question is a guess. With it, it is a specific, informed decision.

### What to look for by category

| Category | What premium sites do | What generic sites do |
|---|---|---|
| Pediatric dental | Illustrated hero, mascot characters, warm bright photography of real children, playful font | Stock photo of dentist, blue/white clinical palette, card grid services |
| Roofing | Aerial photography of completed roofs, before/after proof sections, bold stats | Generic house photo, "call us" hero, list of services in boxes |
| HVAC | Seasonal mood photography, emergency response urgency, trust badge wall | Same contractor template as roofing |
| Restaurant | Full-bleed food photography, ambient video, reservation CTA above fold | Grid of menu items, phone number hero |
| Law firm | Weighty serif typography, monochrome photography, slow dramatic entrances | Smiling lawyer stock photo, blue and gold |
| Real estate | Immersive property photography, map integration, neighborhood lifestyle shots | Listing grid, generic skyline |

---

## Cinematic Baseline

Every site gets at least 3 of these. More is better. Pull back if asked.

- [ ] **Custom cursor**: dot + lagging ring, explicit colors, no blend mode
- [ ] **Char-split animation** on hero heading: use DOM splitChars() helper (NOT SplitText CDN: Club plugin, will 404 and kill all JS)
- [ ] **ScrollTrigger stagger** on cards, rows, or list items
- [ ] **Clip-path reveal** OR **scrub parallax** on at least one section
- [ ] **Magnetic buttons**: GSAP mousemove + elastic.out on leave
- [ ] **Wavy SVG section dividers**: never hard horizontal lines between sections
- [ ] **Particle trail** OR **CSS marquee** OR **morphing SVG blob**
- [ ] **Pinned horizontal scroll** OR **full-bleed cinematic section** (at least one)
- [ ] **Real photos in every image slot**: no emoji substitutes, no CSS gradient placeholders, no empty boxes

**GSAP CDN: FREE plugins only (public cdnjs):**
`gsap.min.js`, `ScrollTrigger.min.js`, `Draggable.min.js`, `Flip.min.js`, `Observer.min.js`, `TextPlugin.min.js`, `EasePack.min.js`
CDN: `https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/`

**NEVER load from public CDN: Club GSAP members only:**
SplitText, MorphSVG, DrawSVG, ScrambleText, MotionPathHelper, Physics2D

Loading a Club plugin from cdnjs returns 404. The variable is undefined. `gsap.registerPlugin(ScrollTrigger, SplitText)` throws and **kills the entire script block**: cursor, animations, accordions, everything stops working. CSS still loads so the page looks fine but is fully non-interactive. This is silent and extremely hard to diagnose.

**For char/word animation without SplitText:** use the DOM walker pattern:
```js
function splitChars(el) {
  const chars = [];
  const walk = (node) => {
    if (node.nodeType === 3) {
      const frag = document.createDocumentFragment();
      for (const ch of node.textContent) {
        if (ch === ' ' || ch === '\n') { frag.appendChild(document.createTextNode(' ')); }
        else {
          const outer = document.createElement('span');
          outer.style.cssText = 'display:inline-block;overflow:hidden;';
          const inner = document.createElement('span');
          inner.style.display = 'inline-block';
          inner.textContent = ch;
          outer.appendChild(inner); frag.appendChild(outer); chars.push(inner);
        }
      }
      node.parentNode.replaceChild(frag, node);
    } else if (node.nodeType === 1) { Array.from(node.childNodes).forEach(walk); }
  };
  Array.from(el.childNodes).forEach(walk);
  return chars;
}
// Usage: gsap.from(splitChars(document.querySelector('h1')), { y:80, opacity:0, stagger:0.025 })
```

---

## Layout Archetypes

Rotate, do not repeat within 3 builds.

| Archetype | Best for | Key structural move |
|---|---|---|
| Storybook blob | Kids, family, wellness | Morphing SVG blob hero, organic shapes, no hard edges |
| Bold editorial | Legal, finance, B2B | Oversized asymmetric type, unexpected negative space |
| Warm boutique | Spa, restaurant, artisan | Texture, photography-led, no cards, no grid |
| Kinetic typographic | Tech, agency, startup | Text IS the hero, SplitText, motion-driven |
| Cinematic dark | Creative agency, luxury, film | Dark bg, particle trail, horizontal scroll, full-bleed |
| Magazine front page | Media, multi-service, portfolio | Multiple content lanes, editorial hierarchy |
| Immersive full-bleed | Real estate, architecture, travel | Image/video fills viewport, content overlays |
| Single-scroll narrative | Personal brand, portfolio, story | One long story, no section breaks, no nav |

---

## Font Rotation

Avoid repeating a pairing within 3 builds.

| Pairing | Personality |
|---|---|
| Fredoka + Baloo 2 + Amatic SC | Playful, rounded, kids |
| DM Serif Display + DM Sans | Editorial, premium, clean |
| Fraunces + Nunito | Warm serif, boutique, kids-adjacent |
| Playfair Display + Inter | Classic, trustworthy, CW-adjacent |
| Space Grotesk + Syne | Modern, geometric, technical |
| Cormorant Garamond + Source Sans | Luxury, boutique, high-end |
| Unbounded + DM Sans | Bold, statement, geometric: industrial |
| Syne + DM Sans | Cinematic dark, agency, confident |
| Amatic SC + Nunito | Hand-drawn, artisan, warm |

---

## Color Story Rotation

Avoid repeating a story within 3 builds.

| Story | Anchors | Notes |
|---|---|---|
| Cobalt + yellow + mint | #1B3F8B + #FFD447 + #B8F0D8 | Playful, bold |
| Cinematic dark + neon green | #0a0a0a + #7BFF6A | Agency, luxury |
| Cinematic dark + orange | #0D0D0D + #F4600C | Industrial, trade contractor |
| Navy + sky blue + coral + gold | #0B1F3A + #5BC8F5 + #FF6B6B + #F5C842 | Kids, bright, warm |
| Deep forest + gold | #1a2e1f + #c4956a | Premium local |
| Burnt sienna + ivory | #a0522d + #fdf8f0 | Restaurant, artisan |
| Plum + blush + cream | #4a1a6b + #f4b8cc | Boutique, spa |
| Black + yellow | #0a0a0a + #FFD447 | Editorial, bold |
| Warm red + cream + dark brown | #c0392b + #fdf8f3 + #2c1a0e | Local, trusted |
| Sage + cream | AVOID for demos | Overused, CW-adjacent |
| Navy + coral | BANNED for demos | Too close to default CW palette |

---

## Step 1: Project type

Is this Catalyst Works / Boubacar personal brand output?

- **Yes:** Step 2A
- **No:** Step 2B

---

## Step 2A: Catalyst Works output

Load before writing any code:
```
docs/styleguides/styleguide_master.md
docs/styleguides/styleguide_websites.md
```

Non-negotiables: `#071A2E` navy + `#B47C57` clay + `#00B7C2` action.
Plus Jakarta Sans headlines. Inter body. First element is a specific
claim, not a category description.

The Volta cinematic baseline still applies to CW sites; they should
feel alive, not static.

---

## Step 2B: Non-CW output

1. Pick an archetype from the rotation table that fits the business type
   AND has not been used in the last 3 builds.
2. Pick a font pairing and color story from the rotation tables.
3. Check `workspace/demo-sites/build-log.md` to verify no repeat.
4. Run the ui-ux-pro-max design system query for the specific business
   category if the build log does not already have relevant prior art.

---

## Step 3: Design brief (mandatory, spoken aloud before code)

> "Reference archetype: [name]. Font: [pairing]. Color: [story].
> 3 constraints: [1], [2], [3]. Anti-patterns avoided: [list]."

No brief = skill did not run.

---

## Step 4: Mobile first

375px first. Then 1280px. Then 768px. Verify all three.

---

## Image Generation via Kie

When building a site and the right image does not exist in the project assets, **do not use placeholder images, stock photo URLs, or Unsplash hotlinks.** Generate the image using Kie.

### When to generate

+ Hero background / full-bleed section image
+ Team photo placeholder (client-branded illustration, not a real face)
+ Service illustration or icon set
+ Before/after pairs (matched scene, same angle, condition changes only)
+ OG image (1200x630)
+ Any image the client has not provided

### How to generate

Invoke the `kie_media` skill. Use `generate_image()` from `orchestrator/kie_media.py`:

```python
from orchestrator.kie_media import generate_image

result = generate_image(
    prompt="...",          # detailed prompt: see format below
    aspect_ratio="16:9",   # hero: 16:9 | card: 1:1 | OG: 1.91:1
    task_type="text_to_image",
)
# result["local_path"] -> use this path in the HTML src
# result["drive_url"]  -> backup
```

Kie picks the best model automatically (ranked registry). Budget auto-approved up to $0.20/image.

**If the orchestrator import fails locally** (missing modules), call the API directly:

```python
from dotenv import load_dotenv
load_dotenv()
import os, requests, time

KEY = os.getenv('KIE_AI_API_KEY')
headers = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

r = requests.post('https://api.kie.ai/api/v1/gpt4o-image/generate',
    headers=headers,
    json={'prompt': '...', 'aspect_ratio': '16:9'},
    timeout=30)
task_id = r.json()['data']['taskId']

for _ in range(40):
    time.sleep(8)
    r2 = requests.get(f'https://api.kie.ai/api/v1/gpt4o-image/record-info?taskId={task_id}',
        headers={'Authorization': f'Bearer {KEY}'}, timeout=15)
    d = r2.json()['data']
    if d.get('status') == 'SUCCESS':
        url = d['response']['resultUrls'][0]
        img = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        with open('output/websites/<site>/img/<name>.png', 'wb') as f:
            f.write(img.content)
        break
```

Save images to `output/websites/<site>/img/` and reference with relative paths (`src="img/name.png"`).
Never hotlink the Kie temp URL: it expires.

### Prompt format for site images

Build every prompt from these six fields in order. All six are required.

```
[COMPOSITION ANCHOR] [SUBJECT] [LIGHTING + MOOD] [COLOR PALETTE] [BACKGROUND MODE] [ANTI-SLOP PROHIBITION]
No text. No watermarks. Photorealistic.
```

**COMPOSITION ANCHOR** - how the frame is structured. Pick one per image; vary across sections:
- `Wide-angle centered, subject fills lower two-thirds` (hero, cinematic)
- `Left-third subject, right-two-thirds open space` (editorial split)
- `Full-bleed background, text safe zone lower-left` (overlay sections)
- `Close macro crop, subject fills frame edge-to-edge` (detail / feature)
- `Overhead flat-lay` (product, service icons)
- `Eye-level documentary` (team, process, trust)

**BACKGROUND MODE** - what sits behind the subject. Vary across sections; never use the same mode twice in a row:
- `Solid surface + subject in foreground` (clean, minimal)
- `Full-bleed cinematic with tonal overlay` (hero, atmosphere)
- `Editorial side-image, subject occupies 60% of frame` (split sections)
- `Soft radial vignette, subject centered` (premium, luxury)
- `Subtle texture / paper / material surface` (editorial, warm)

**HERO SCALE** - choose once per page, apply consistently:
- Giant Statement: large subject, dominant first impression, high visual tension
- Mid Editorial: balanced subject/space, cinematic but not screen-filling
- Mini Minimalist: restrained, confident negative space, subject small and precise

**ANTI-SLOP PROHIBITION** - one per prompt, matched to site type:
- Service / trades: `No stock-photo clichés, no posed handshakes, no generic hard-hat scenes`
- Professional services: `No purple-blue AI gradients, no floating orbs, no generic office smiles`
- Restaurant / hospitality: `No oversaturated food lighting, no white-plate-on-white-background`
- Healthcare: `No sterile corridor clichés, no stock stethoscope props`
- Agency / creative: `No glassmorphism blobs, no neon edge glow, no generic dashboard UI panels`
- Real estate: `No drone shot of generic suburb, no empty white room with hardwood floors`

**Examples:**

Hero for a roofing company (Giant Statement, full-bleed):
```
Full-bleed cinematic with tonal overlay, skilled roofer silhouetted against golden-hour sky installing dark shingles on steep-pitch roof, warm amber and deep charcoal tones matching site palette, dramatic underlit clouds, image fills frame with text safe zone lower-left. No stock-photo clichés, no posed hard-hat scenes. No text. No watermarks. Photorealistic.
```

Feature section for a pediatric dental practice (Mid Editorial, editorial split):
```
Left-third subject right-two-thirds open space, cheerful child in dental chair relaxed and smiling, bright warm natural light from window left, soft blues and warm yellows matching site palette, editorial side-image style, calm welcoming mood. No oversaturated clinical lighting, no generic stock smiles. No text. No watermarks. Photorealistic.
```

Before/after pair for roofing (matched scene, same composition both shots):
```
Before: Overhead flat-lay, old asphalt shingle roof with missing shingles and moss stains, overcast flat light, muted grey-brown palette, documentary realism. No text. No watermarks. Photorealistic.
After: Overhead flat-lay, brand new charcoal shingle roof clean perfect installation sharp ridgeline, same angle same lens same focal length as before image, sunny warm light, rich charcoal matching site accent. No text. No watermarks. Photorealistic.
```

### Rules

+ Generate images **before** writing the HTML that references them. Never write `src=""` placeholders.
+ Match the color palette of the site (include accent color in prompt).
+ Before/after sliders need matched pairs: same scene, same angle, same lighting. Generate both via Kie.
+ **HTTP 200 is NOT content verification.** Before embedding any image, describe what it shows and confirm it matches the business. A 350KB JPEG of a Monster Energy can passes every HTTP check. Describe the content, not the status.
+ If generation fails after the Kie retry ladder, use a CSS gradient as fallback. Never ship a broken `<img>` tag.

---

## Step 5: Pre-launch checklist (live deploys)

- [ ] **Run `skills/frontend-design/references/design-audit.md` against all visible sections - fix flagged items before declaring done**

- [ ] Favicon wired
- [ ] OG image 1200x630px
- [ ] sitemap.xml present
- [ ] robots.txt present
- [ ] GA4 wired
- [ ] All images verified for content appropriateness (not just HTTP 200)
- [ ] All images saved locally in `img/`, referenced with relative paths
- [ ] No placeholder text or broken links
- [ ] Schema.org JSON-LD present (LocalBusiness + FAQPage minimum)
- [ ] FAQ includes AI visibility question ("Is [business] visible on ChatGPT/Perplexity?")
- [ ] Forms wired (Formspree for static)
- [ ] GitHub push in same session as build
- [ ] Vercel deploy confirmed live
- [ ] **`/design-audit <path>` ran and scored ≥15/20 with anti-patterns ≥3/4** (HARD GATE)
- [ ] **For Signal Works builds: ≥17/20 with anti-patterns ≥3/4** (stricter floor: these ARE the agency's portfolio)
- [ ] No items from the 10-pattern absolute bans list present
- [ ] No reflex-reject fonts used (or styleguide explicitly mandates one: note in build-log)

### Post-build: invoke /design-audit

After build is complete and before declaring "done," invoke the `design-audit` skill on the artifact:

```
/design-audit <path-to-html-or-pdf>
```

This produces a scored audit at `workspace/design-audits/<artifact>-audit.md`. If the score is below the gate, fix the flagged P0/P1 issues, re-render, and re-audit. Do not skip this step. The audit is the only objective check on whether the build escapes AI slop.

### Live micro-adjust (optional, for refinement)

If the audit flags issues that are aesthetic (font choice, color balance, spacing rhythm) rather than structural, run:

```
node scripts/design-live.mjs <path-to-html>
```

This opens the file in a browser with a side panel for swapping fonts/colors/spacing in real time. Tweak, accept, the file is rewritten. See `scripts/design-live.mjs` for usage.

---

## KNOWN PITFALLS (learned the hard way)

These are bugs that have shipped and caused user pain. Add to this list every time a new one is found.

### 1. NEVER hide H2/heading text by default with `transform: translateY(110%)` waiting for GSAP/IntersectionObserver

This is the GSAP split-line bug discovered on the Elevate Roofing build (2026-04-30). The pattern was:

```html
<h2><span class="split-line"><span>Recent work</span></span></h2>
```

```css
.split-line span { transform: translateY(110%); }  /* hidden by default */
```

```js
gsap.fromTo('.split-line span', { yPercent: 110 }, { yPercent: 0, scrollTrigger: { ... once: true }});
```

**Failure modes:**

- GSAP CDN times out or fails → headline invisible forever
- ScrollTrigger trigger missed on fast scroll → headline never animates in
- Reduced-motion query matched but JS path didn't reset → headline stays hidden
- Slow connection → headline invisible for 2-3 seconds on every section

The user's screenshot showed entire empty columns where H2s should be. Looked like a layout bug; was actually a JS-dependent display bug.

**The fix (use ALL of these):**

1. **Gate the hide behind a `.js-ready` class** added by your IIFE entry point:
   ```js
   document.documentElement.classList.add('js-ready');
   ```
   ```css
   .js-ready .split-line span { transform: translateY(110%); }
   /* without JS, the text is always visible */
   ```

2. **Better: use `gsap.from()`** (animates FROM a state) instead of CSS-default-hidden. The rendered DOM is always the final state; GSAP merely transitions through the start state. If GSAP fails, the final state is what shows.

3. **Best: don't split-line H2s at all unless animation is absolutely required.** A visible static heading beats an animated invisible one. The Elevate fix was to rip out all `.split-line` wrappers and use direct `<h2 class="section-h2">` elements with `gsap.from()` reveals applied to the whole element.

### 2. Cache-bust CSS/JS during iteration

When the user says "I don't see your changes," 95% of the time it is browser cache, not code. Add a unix-timestamp `?v=` query string to every `<link>` and `<script>` tag and bump it via Python regex sweep across all pages on every CSS/JS change:

```python
import re, glob, time
ver = str(int(time.time()))
for p in glob.glob('site/**/*.html', recursive=True):
    raw = open(p, encoding='utf-8').read()
    new = re.sub(r'(/css/[a-z]+\.css|/js/[a-z]+\.js)\?v=\d+', r'\1', raw)
    new = new.replace('/css/site.css"', f'/css/site.css?v={ver}"')
    new = new.replace('/js/site.js"',  f'/js/site.js?v={ver}"')
    if new != raw:
        open(p, 'w', encoding='utf-8', newline='\n').write(new)
```

Without this, every "fix" reads as "no change" to the user staring at a cached browser.

### 3. No meta-commentary in visitor-facing copy

Lines that read as designer notes that escaped into production. Examples caught on Elevate:

- *"Three real reviews from real clients. Rod by name in every one."*: describes the page, not for the visitor
- *"01 / Stack"* margin labels using designer-jargon ("Stack" wasn't anywhere in the section)
- *"Don't just take our word for it"*: defensive cliché that calls attention to the section being a reviews section
- *"06 / Said"*: the word doesn't make sense in context, sounds like a file directory name

The fix: every line of copy must answer "would a visitor find value in reading this?" If it sounds like designer commentary about what the page is doing, cut it. Use plain section labels ("Reviews", "Where we work") not clever ones.

### 4. Em-dash scrub before declaring done

Boubacar's hard rule: no `: ` or `: ` site-wide. They're the #1 AI-tell in written copy. Run a sweep before every "done" claim:

```python
import re, glob
for p in glob.glob('site/**/*.html', recursive=True) + glob.glob('site/**/*.css', recursive=True) + glob.glob('site/**/*.js', recursive=True):
    raw = open(p, encoding='utf-8').read()
    new = raw.replace(': ', ' - ').replace(': ', ', ').replace(': ', ' - ').replace(': ', '-')
    if new != raw:
        open(p, 'w', encoding='utf-8', newline='\n').write(new)
```

Caught 12-166 instances per scrub on Elevate. Watch out for JS string fallbacks (e.g. cost-tool placeholder `'- pick a project above -'` will get clobbered to `',  pick a project above , '` if the scrubber runs on bare `-` characters: only scrub the unicode em-dash and en-dash).

### 5. Mobile hero crowding from oversized type clamp

The default `--t-h1` clamp can hit 8.2rem (~131px) at large viewports, which forces the H1 to wrap into 5-6 vertical lines on a 380-1900px screen and crowd whatever is behind it (video, image). The Elevate fix:

- Define a SEPARATE `--hero-h1` clamp ceiling lower than `--t-h1` (e.g. `clamp(2.6rem, 1.8rem + 4vw, 6.2rem)`)
- Don't use hard `<br>` tags in the H1: let `max-width` control wrapping
- Add a localized scrim under the headline (linear-gradient with blur) so the type stays readable when video shows through
- On `max-width: 480px`, drop the clamp floor again and tighten line-height to 0.95

### 6. Use the client's REAL logo. Always.

Per `feedback_redesign_familiar_not_foreign.md`: never improvise a text-based logotype as a stand-in for a client's actual logo. The client immediately recognizes their own logo and immediately doesn't recognize a stylized text version. Render their actual PNG via:

```html
<img src="/assets/media/logo-wordmark.png" alt="ClientName" class="brand-logo">
```

```css
.brand-logo {
  height: 28px; width: auto;
  filter: brightness(0) invert(1);  /* white on dark surfaces; flip for light */
}
```

If their logo is dark-text-on-transparent (Picsart background-removed PNGs are common), `filter: brightness(0) invert(1)` flips to white. For light sections, scope the filter via `mix-blend-mode` on the parent or swap to a light variant.

### 7. mix-blend-mode scope must be tight

`mix-blend-mode: difference` on the whole `.site-header` will invert EVERY child including borders on `.nav-cta` buttons → the button border looks like a broken dark box on light sections. Scope blend modes to text-only elements (`.brand`, `.nav-links`, `.nav-toggle`) and give the CTA pill its own explicit color treatment.

---

## Red flags: stop if you think any of these

- "I'll load the reference after I get the structure down": stop, load first
- "This is just a small update": still run the skill
- "The colors and fonts are different so it's a different design": wrong.
  The skeleton is the tell. Boubacar can feel it through any costume.
- "This looks clean and professional": clean and professional is not
  the bar. Volta is the bar.
- "The user hasn't asked for animations": add them anyway. Pull back if asked.
- "This business type needs something simple": simple does not mean
  the same skeleton as every other site. Simple can be a single-scroll
  narrative or a bold editorial with one color. Simple is a design choice,
  not a skeleton choice.
- "I tested the image URL and it returned 200": HTTP status is not content
  verification. Describe what the image shows before embedding it.
- "I'll use emoji as icons for now": no. Generate icons or use CSS shapes.
  Emoji are never shipped on client-facing sites.
- "I'll add real photos later": photos are part of the build, not a follow-up
  task. Plan and generate them in the photo plan (check F) before writing HTML.
