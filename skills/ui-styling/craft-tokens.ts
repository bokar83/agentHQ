/**
 * CRAFT TOKENS: agentsHQ Humanized Standard
 * TypeScript/JavaScript constants for Framer Motion and GSAP.
 *
 * Import in any file that needs motion constants:
 *   import { SPRING, GSAP_EASE, SCROLL, STAGGER, DURATION } from "@/lib/craft-tokens"
 *
 * Copy this file to src/lib/craft-tokens.ts at build time.
 */

// ============================================================
// FRAMER MOTION SPRING CONFIGURATIONS
// ============================================================

export const SPRING = {
  // Calm Product: precise, no overshoot: for professional product UIs
  ui:         { type: "spring" as const, stiffness: 400, damping: 30, mass: 1 },
  modal:      { type: "spring" as const, stiffness: 300, damping: 25, mass: 1 },
  card:       { type: "spring" as const, stiffness: 200, damping: 20, mass: 1 },

  // Cinematic/Agency: dramatic, slow settle: for hero elements
  hero:       { type: "spring" as const, stiffness: 100, damping: 15, mass: 1.5 },

  // Illustrative/Playful: pronounced bounce: correct for this archetype
  playful:    { type: "spring" as const, stiffness: 150, damping: 8,  mass: 1 },

  // Trust/Enterprise: fast, precise, zero overshoot
  enterprise: { type: "spring" as const, stiffness: 500, damping: 40, mass: 1 },

  // Magnetic button tracking
  magnetic:   { type: "spring" as const, stiffness: 200, damping: 15, mass: 1 },
} as const

// ============================================================
// GSAP EASING STRINGS
// ============================================================

export const GSAP_EASE = {
  standard:   "power2.out",    // standard reveals, content entries
  entrance:   "power3.out",    // hero entrances, section titles
  cinematic:  "expo.out",      // Cinematic/Agency archetype: dramatic
  tactile:    "back.out(1.1)", // tactile button presses, interactive elements
  exit:       "power2.in",     // elements leaving viewport
  anticipate: "back.in(1.7)",  // wind-up before motion
} as const

// ============================================================
// SCROLL CONFIGURATION
// ============================================================

export const SCROLL = {
  // Lenis lerp by archetype
  lerp: {
    editorial:  0.05, // EDITORIAL_NARRATIVE: cinematic, magazine-feel pacing
    cinematic:  0.05, // CINEMATIC_AGENCY: slow, deliberate, premium
    standard:   0.07, // DOCUMENTARY_DATA: default production value
    product:    0.10, // CALM_PRODUCT, ILLUSTRATIVE_PLAYFUL, CONVERSION_FIRST
  },

  // GSAP ScrollTrigger scrub values
  scrub: {
    precise:    0.5,  // image reveals, parallax layers
    standard:   1,    // hero sequences (standard premium narrative)
    cinematic:  2,    // feature showcase stacks, cinematic archetype
  },

  // Lenis wheelMultiplier: keep at 1.2 for consistent cross-platform feel
  wheelMultiplier: 1.2,
} as const

// ============================================================
// GSAP STAGGER VALUES
// ============================================================

export const STAGGER = {
  char:  0.02,  // character-level: standard headline entry
  word:  0.05,  // word-level: editorial narrative archetype
  line:  0.08,  // line-level: slow dramatic reveal
  item:  0.1,   // list items, card grids
} as const

// ============================================================
// DURATION CONSTANTS (mirrors craft-tokens.css)
// ============================================================

export const DURATION = {
  micro:   0.12,  // 120ms: button press, focus ring
  fast:    0.22,  // 220ms: hover state, small reveals
  base:    0.38,  // 380ms: modal entry, standard reveal
  slow:    0.6,   // 600ms: hero entrance, section reveal
  cinema:  1.2,   // 1200ms: Cinematic/Agency archetype only
} as const

// ============================================================
// PARALLAX SPEED MULTIPLIERS
// ============================================================

export const PARALLAX = {
  background: 0.3,  // slowest: furthest back layer (0.2-0.4 range)
  midground:  0.6,  // middle layer (0.5-0.7 range)
  foreground: 1.2,  // fastest: in front of content (1.1-1.3 range)
} as const

// ============================================================
// ARCHETYPE MOTION PROFILES
// Convenience bundles: pass the whole profile to the component
// ============================================================

export type ArchetypeName =
  | "CALM_PRODUCT"
  | "EDITORIAL_NARRATIVE"
  | "CINEMATIC_AGENCY"
  | "BRUTALIST"
  | "ILLUSTRATIVE_PLAYFUL"
  | "DOCUMENTARY_DATA"
  | "TRUST_ENTERPRISE"
  | "CONVERSION_FIRST"

export const ARCHETYPE_MOTION: Record<ArchetypeName, {
  lenis_lerp: number | null
  scrub: number
  kineticText_style: "calm" | "editorial" | "cinematic" | "playful" | "none"
  spring: typeof SPRING[keyof typeof SPRING]
  use_smooth_scroll: boolean
}> = {
  CALM_PRODUCT: {
    lenis_lerp:        0.10,
    scrub:             SCROLL.scrub.standard,
    kineticText_style: "calm",
    spring:            SPRING.modal,
    use_smooth_scroll: true,
  },
  EDITORIAL_NARRATIVE: {
    lenis_lerp:        0.05,
    scrub:             SCROLL.scrub.standard,
    kineticText_style: "editorial",
    spring:            SPRING.card,
    use_smooth_scroll: true,
  },
  CINEMATIC_AGENCY: {
    lenis_lerp:        0.05,
    scrub:             SCROLL.scrub.cinematic,
    kineticText_style: "cinematic",
    spring:            SPRING.hero,
    use_smooth_scroll: true,
  },
  BRUTALIST: {
    lenis_lerp:        null,
    scrub:             0,
    kineticText_style: "none",
    spring:            SPRING.enterprise,
    use_smooth_scroll: false,
  },
  ILLUSTRATIVE_PLAYFUL: {
    lenis_lerp:        0.10,
    scrub:             SCROLL.scrub.standard,
    kineticText_style: "playful",
    spring:            SPRING.playful,
    use_smooth_scroll: true,
  },
  DOCUMENTARY_DATA: {
    lenis_lerp:        0.07,
    scrub:             SCROLL.scrub.precise,
    kineticText_style: "calm",
    spring:            SPRING.modal,
    use_smooth_scroll: true,
  },
  TRUST_ENTERPRISE: {
    lenis_lerp:        null,
    scrub:             0,
    kineticText_style: "calm",
    spring:            SPRING.enterprise,
    use_smooth_scroll: false,
  },
  CONVERSION_FIRST: {
    lenis_lerp:        0.10,
    scrub:             0,
    kineticText_style: "calm",
    spring:            SPRING.ui,
    use_smooth_scroll: true,
  },
} as const

// ============================================================
// BANNED VALUES: reference only, do not use these
// The critic agent greps for these strings in generated code.
// ============================================================

// BANNED_EASING: "ease-in-out", "ease-linear", "linear" (outside spring defs)
// BANNED_DURATION: "duration-300", 0.3 (as transition duration in framer-motion)
// BANNED_SHADOW: "rgba(0,0,0,0.1)" as the sole shadow value
// BANNED_FONT: "Inter" in h1/h2/h3 selectors
// BANNED_GRID: "repeat(3, 1fr)" with 3 identical children
