# Reference Document: "Humanized Standard"
**agentsHQ: Builder Agent Runtime Reference**
*This file is loaded by the builder agent at the start of every build.*
*It is a lookup resource, not a sequential instruction set.*

---

## Craft Token Quick Reference

### Easing (use these; use nothing else)
| Token | Value | Use |
|---|---|---|
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Standard entrances, modal opens |
| `--ease-in-expo` | `cubic-bezier(0.7, 0, 0.84, 0)` | Standard exits |
| `--ease-spring-sm` | `linear(...)` | Hover states, small interactive elements |
| `--ease-spring-lg` | `linear(...)` | Cards, larger interactive elements |
| GSAP: `"power2.out"` | | Standard reveals |
| GSAP: `"power3.out"` | | Hero entrances |
| GSAP: `"expo.out"` | | Cinematic/Agency archetype |
| GSAP: `"back.out(1.1)"` | | Tactile button presses |

**BANNED:** `ease-in-out`, `ease`, `linear` (except inside `linear()` spring functions), `duration-300`

### Duration Scale
| Token | Value | Use |
|---|---|---|
| `--duration-micro` | 120ms | Button press, focus ring |
| `--duration-fast` | 220ms | Hover state, small reveals |
| `--duration-base` | 380ms | Modal entry, standard reveal |
| `--duration-slow` | 600ms | Hero entrance, section reveal |
| `--duration-cinema` | 1200ms | Cinematic/Agency archetype ONLY |

### Scroll Values
| Archetype | Lenis lerp | ScrollTrigger scrub |
|---|---|---|
| CALM_PRODUCT | 0.10 | 1 |
| EDITORIAL_NARRATIVE | 0.05 | 1 |
| CINEMATIC_AGENCY | 0.05 | 2 |
| ILLUSTRATIVE_PLAYFUL | 0.10 | 1 |
| DOCUMENTARY_DATA | 0.07 | 0.5 |
| CONVERSION_FIRST | 0.10 | N/A (no scroll animation) |
| BRUTALIST | none | N/A |
| TRUST_ENTERPRISE | none | N/A |

### Spring Physics (Framer Motion)
| Context | stiffness | damping | mass |
|---|---|---|---|
| Button press / UI micro | 400 | 30 | 1 |
| Modal / drawer entry | 300 | 25 | 1 |
| Card hover | 200 | 20 | 1 |
| Hero / dramatic reveal | 100 | 15 | 1.5 |
| Playful / bounce | 150 | 8 | 1 |
| Enterprise / precise | 500 | 40 | 1 |

### Border Radius Scale
| Token | Value | Use |
|---|---|---|
| `--radius-xs` | 3px | Tags, badges |
| `--radius-sm` | 6px | Buttons, inputs |
| `--radius-md` | 12px | Cards |
| `--radius-lg` | 20px | Modals, large cards |
| `--radius-xl` | 32px | Pill elements |
| `--radius-none` | 0px | Brutalist archetype, full-bleed images |

**Rule:** Never use the same radius on cards AND buttons AND inputs. The values must vary.

### Shadow Scale
| Token | Use |
|---|---|
| `--shadow-none` | Flat elements, Brutalist archetype |
| `--shadow-low` | Subtle lift on cards at rest |
| `--shadow-mid` | Hovered cards, active states |
| `--shadow-high` | Dropdowns, floating elements |
| `--shadow-modal` | Modals, tooltips |

**BANNED:** `box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1)` (Tailwind shadow-md applied globally)

---

## Archetype Quick Reference

### CALM_PRODUCT
**Fonts:** Geist Sans 700 or Neue Montreal 700 (heading) + Inter 400 or DM Sans 400 (body) + Geist Mono (code)
**Colors:** Near-black background (~`#0f0f11`), functional status colors, single gradient accent
**Motion:** Lenis 0.10, SplitText motionStyle="calm", Framer spring stiffness 300 damping 25
**Refuse:** Glass morphism, rainbow gradients, mascots, WebGL heroes, decorative motion

### EDITORIAL_NARRATIVE
**Fonts:** Tiempos Text or Playfair Display (heading) + Tiempos Text or Söhne (body)
**Colors:** Off-white foundation (`#f5f2ed`), one functional accent color
**Motion:** Lenis 0.05, SplitText motionStyle="editorial" (word-by-word), View Transitions for navigation
**Refuse:** Dark mode, glass morphism, icon grids, countdown timers, anything signaling "landing page"

### CINEMATIC_AGENCY
**Fonts:** Clash Display or Neue Montreal 900 (heading) + Neue Montreal 400 or DM Sans 400 (body)
**Colors:** Dark or near-black base, single high-contrast accent moment
**Motion:** Lenis 0.05, SplitText motionStyle="cinematic" (rotationX: -90), ScrollTrigger scrub: 2, ParallaxLayer on hero
**Refuse:** 3-box feature grids, pricing tables, uniform card radii, Inter at regular weight

### BRUTALIST
**Fonts:** Helvetica Neue 900 or Druk Wide Super (heading) + same grotesque 400 or Courier New (body)
**Colors:** Pure saturated primaries or no color; pure white or pure black backgrounds
**Motion:** NONE or architectural-scale instant changes; border-radius: 0 everywhere
**Refuse:** Rounded corners, soft shadows, gradient backgrounds, Lenis, icon libraries, glass morphism

### ILLUSTRATIVE_PLAYFUL
**Fonts:** Nunito 800 or Poppins 700 (heading) + Nunito 400 or Poppins 400 (body)
**Colors:** Warm saturated palette with clear primary + secondary + accent
**Motion:** Lenis 0.10, SplitText motionStyle="playful", Framer spring stiffness 150 damping 8
**Refuse:** Dark mode as default, monospace type, dense data tables, corporate blue palettes

### DOCUMENTARY_DATA
**Fonts:** IBM Plex Sans 600 or DM Sans 600 (heading + chart titles) + same grotesque 400 (body)
**Colors:** White or `#fafafa` foundation, colorblind-safe 5-7 color chart palette
**Motion:** Lenis 0.07, D3.js for chart draw-in, Scrollama for data steps, no decorative motion
**Refuse:** WebGL, dark mode as default, gradient fills on charts, motion that does not reveal data
**Special:** `font-variant-numeric: tabular-nums` on ALL numeric data

### TRUST_ENTERPRISE
**Fonts:** Freight Display or Neue Haas Grotesk (heading) + Source Serif 4 or Georgia (body)
**Colors:** Navy or dark teal primary, white secondary, gold or amber accent
**Motion:** CSS transitions only (`transition: all 0.2s var(--ease-out-expo)`), no Lenis, no scroll animation
**Refuse:** Dark mode, experimental typography, illustration, mascots, neon accents, startup energy

### CONVERSION_FIRST
**Fonts:** Inter 800 or Neue Montreal 700 (heading) + same sans 400 (body)
**Colors:** High-contrast CTA button (NOT indigo; must pass WCAG AA 4.5:1 contrast)
**Motion:** CSS hover transitions on CTA only; no scroll animation before fold; loading + success states required
**Refuse:** Multiple CTAs, hero animations that delay message, dark mode, cognitive load before the CTA

---

## The 10 AI-Tells (Quick Reference)

Avoid all of these. The critic agent checks for them.

1. **Indigo-500 Button**: `bg-indigo-500` or `#6366f1` on CTA. Replace with custom brand hex.
2. **Inter on Everything**: Inter as heading font. Replace with archetype-specific font pair.
3. **Three-Box Feature Grid**: `repeat(3, 1fr)` with 3 identical children. Replace with 2+1, timeline, or numbered list.
4. **Uniform Border Radius**: same `rounded-lg` on cards, buttons, and inputs. Vary by element type.
5. **Low-Opacity Shadow**: `shadow-md` (`rgba(0,0,0,0.1)`) applied globally. Use elevation-aware shadows.
6. **Gradient Hero with Centered H1**: `from-purple-900 to-indigo-900` + centered headline. Break the axis.
7. **Icon Monoculture**: all icons from one library at 24px stroke-width 1.5. Mix styles, vary scales.
8. **Missing Error States**: forms with no error styling, lists with no empty state. Implement all states.
9. **Semantic HTML Blindness**: `<div>` instead of semantic elements. Use `<nav>`, `<main>`, `<article>`, `<button>`.
10. **Animation as Decoration**: same `0.5s ease-in-out` fade on every element. Choreograph by hierarchy.

---

## Craft Components API

### `<SmoothScrollProvider lerp={0.07}>`
Wraps the application root. Configures Lenis + GSAP ScrollTrigger proxy.
- lerp: number (see archetype quick reference for correct value)
- Automatically disabled when `prefers-reduced-motion: reduce`
- Do NOT use in BRUTALIST or TRUST_ENTERPRISE builds

### `<KineticText motionStyle="calm" as="h1">`
Animates headline text on scroll entry using SplitText.
- motionStyle: "calm" | "editorial" | "cinematic" | "playful"
- as: any heading element (default "h1")
- className: any Tailwind classes
- Graceful fallback: if SplitText fails, renders with CSS opacity + translateY using `--ease-out-expo`

### `<MagneticButton strength={0.2}>`
Primary CTA button with cursor-tracking magnetic hover and tactile spring press.
- strength: 0.2 (default) to 0.4 (more dramatic)
- onClick: standard button handler
- className: any Tailwind classes for styling (the component handles motion)
- Use for ALL primary action buttons

### `<ParallaxLayer speed={0.3}>`
Scroll-driven parallax offset on any child element.
- speed: 0.2-0.4 (background), 0.5-0.7 (midground)
- Uses GSAP ScrollTrigger scrub for Lenis compatibility
- Do NOT apply to text elements at speed > 0.3 (legibility degrades)

### `<ScrollReveal from="bottom" delay={0}>`
General-purpose scroll-triggered reveal for non-headline content.
- from: "bottom" | "left" | "right" | "fade"
- delay: seconds (use for staggered card grids: 0, 0.1, 0.2)
- Less dramatic than KineticText: for supporting content, not headlines

---

## Semantic HTML Checklist

| Pattern to avoid | Correct element |
|---|---|
| `<div class="nav">` | `<nav>` |
| `<div class="main">` | `<main>` |
| `<div class="card">` | `<article>` |
| `<div class="section">` | `<section>` |
| `<div class="footer">` | `<footer>` |
| `<div onclick="">` | `<button>` |
| `<div role="button">` | `<button>` (usually) |
| Icon-only button | `<button aria-label="[action]">` |
| Decorative image | `<img alt="">` (empty alt) |
| Informative image | `<img alt="[description]">` |

---

## Common Errors Reference

**Error: SplitText not animating**
Cause: SplitText line detection runs on mount. If the component renders server-side, the line count is wrong.
Fix: Wrap KineticText usage in `<ClientOnly>` or use `"use client"` directive.

**Error: Lenis fighting with ScrollTrigger**
Cause: ScrollTrigger is not aware of Lenis's virtual scroll position.
Fix: The SmoothScrollProvider component handles this via `lenis.on("scroll", ScrollTrigger.update)` and `gsap.ticker.add`. If you are not using SmoothScrollProvider, you must wire this manually.

**Error: MagneticButton not responding to hover**
Cause: The parent element has `overflow: hidden` which clips the magnetic range.
Fix: Ensure the MagneticButton's parent has enough padding to allow the magnetic offset (strength * element width) without clipping.

**Error: ParallaxLayer jumping on page load**
Cause: ScrollTrigger calculates positions before images load, resulting in incorrect start positions.
Fix: Call `ScrollTrigger.refresh()` after all images have loaded via `window.addEventListener("load", () => ScrollTrigger.refresh())`.
