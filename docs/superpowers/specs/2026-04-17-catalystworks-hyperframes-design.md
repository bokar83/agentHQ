# Catalyst Works × Hyperframes — Site Enhancement Design Spec

**Date:** 2026-04-17
**Status:** Approved for implementation planning
**Working folder:** `output/websites/catalystworks-hyperframes/`
**Source (read-only, never touched):** `output/websites/catalystworks-site/`
**Branch:** `feat/catalystworks-hyperframes`
**Deploy target:** None during build — localhost preview only until Boubacar approves

---

## Scope

Add three Hyperframes animated video integrations to the Catalyst Works landing page. All three concepts are in scope. They are built in the working folder only. The production site and repo are not touched until explicit approval.

---

## Design Constraints

- Site palette stays unchanged: Navy `#071A2E`, Cyan `#00B7C2`, Orange `#FF7A00`, Clay `#B47C57`, Mist `#F3F6F9`
- Font stays Inter — no new fonts
- All Hyperframes compositions use the existing kente/Adinkra visual language from prior sessions
- `prefers-reduced-motion` wraps all animation — accessibility preserved
- No layout shifts on any section: existing copy, CTAs, and form elements stay in their exact positions
- Single-file HTML — no build tools, no frameworks, consistent with existing site architecture
- GSAP loaded from CDN (already used pattern in Hyperframes compositions)

---

## Concept A — The Living Hero

**Placement:** Hero section background, behind all existing copy

**What it is:** The static grid texture (`grid-texture` div) is replaced by a `<canvas>` element running a Hyperframes-style infinite loop. The loop plays mute, no controls, no interaction.

**Animation content (47s loop, then repeat):**
- Star field: ~120 particles, slow drift, seeded PRNG (no Math.random)
- Africa continent outline: SVG path, stroke-dasharray draw animation, gold on black, traces itself every ~20s
- Kente stripe: 4px animated gradient strip along the very bottom edge of the hero, cycling Navy/Cyan/Orange/Clay
- Single gold dot seed frame at start and end for seamless repeat

**Technical approach:**
- Canvas element positioned `absolute`, `inset: 0`, `z-index: 1`
- All existing hero content stays at `z-index: 2` (already set)
- `requestAnimationFrame` loop drives star field; GSAP drives Africa trace and kente stripe
- Canvas is `aria-hidden="true"` — decorative, not interactive
- `prefers-reduced-motion`: canvas hidden, original grid texture shown as fallback

**Files changed in working folder:**
- `index.html` — replace `div.grid-texture` with `canvas#hero-canvas`; add inline script block for canvas animation

---

## Concept B — Diagnostic in Motion

**Placement:** New section inserted between `#how` (How It Works) and `#who` (Who It's For)

**What it is:** A full-width dark section (`background: var(--carbon)`) containing a 60-second Hyperframes explainer video panel on the right and explanatory copy on the left. The video shows the diagnostic process visually.

**Section ID:** `#diagnostic-video`

**Video content (60s, then loop):**
- Scene 1 (0-12s): Problem stated as text, building word by word. "The real problem is rarely the one in front of you."
- Scene 2 (12-28s): 8 lens labels orbit a central glow, one by one, each fading in as it locks into position
- Scene 3 (28-44s): One lens brightens, "constraint" word emerges from center, other lenses fade
- Scene 4 (44-55s): Clean output card builds: named constraint, three signals, one action
- Scene 5 (55-60s): Brand lockup fade, dissolve back to start

**Layout:**
- Two-column grid: `1fr 1fr`, matching the `signal-grid` pattern already on the page
- Left: eyebrow label ("The Method, Visualized") + h2 + 3 bullet points explaining what the viewer is watching
- Right: video panel in a `carbon`-background card with orange top border (matching `signal-card` pattern)
- Video panel is a `<div>` containing the Hyperframes `<canvas>` — not a `<video>` element
- Mobile: stacks to single column, video panel above copy

**Files changed in working folder:**
- `index.html` — new section HTML inserted between `#how` and `#who`; new CSS block for `#diagnostic-video`; new script block for video animation
- Nav links updated to include `#diagnostic-video` anchor if nav is updated

---

## Concept C — Boubacar, Thinking

**Placement:** Within the existing `#about` section, below the bio paragraph and above the clay quote block

**What it is:** A 45-second philosophy reel, contained in a card that sits below the bio. It plays on a dark card with clay left border (matching `about-quote` pattern). Auto-plays on scroll into view, loops silently.

**Video content (45s, then loop):**
- Scene 1 (0-10s): "Observe." builds, then "Diagnose." then "Remove." — each word in a different weight
- Scene 2 (10-20s): Sankofa proverb word-by-word: "It is not wrong to go back for what you forgot." Gold highlight on key words (already built in showoff composition)
- Scene 3 (20-32s): Career arc — five city names appear one at a time with a thin connecting line: Conakry → Dubai → Paris → Lagos → New York. Gold trail.
- Scene 4 (32-45s): "20 years. 4 languages. One method." — dissolve to brand lockup, clay tone

**Layout:**
- Full-width card within the about grid's right column
- Card styling: `background: rgba(180,124,87,0.04)`, `border: 1px solid var(--clay-border)`, `border-left: 3px solid var(--clay)`, `border-radius: 8px`, `padding: 0`, `overflow: hidden`
- Canvas fills the card, aspect ratio 16:9, `width: 100%`
- Small caption below: "Playing automatically · No sound" in `text-dim` style
- Scroll-triggered autoplay via `IntersectionObserver` (same pattern used for `.fade-in` on the page)
- Mobile: full-width card, stacks naturally below bio

**Files changed in working folder:**
- `index.html` — new canvas card inserted inside `#about` section; new CSS; new script block

---

## Shared Technical Notes

**GSAP version:** 3.12.5 from CDN — same as all other Hyperframes compositions
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
```

**PRNG:** mulberry32 seeded function for all random values — no `Math.random()` anywhere

**Canvas sizing:** All canvas elements use `devicePixelRatio` scaling for retina clarity

**Reduced motion fallback:**
```css
@media (prefers-reduced-motion: reduce) {
  .hf-canvas { display: none; }
  .hf-fallback { display: block; }
}
```

**Script organization:** Each concept gets its own clearly delimited `<script>` block with a comment header. No minification. Easy to remove or disable individually.

**No external video files:** All animation is canvas/GSAP — no MP4, no WebM, no `<video>` elements. Zero load time cost beyond GSAP CDN (already ~60KB gzip).

---

## Build Sequence

1. Create git branch `feat/catalystworks-hyperframes` from current main
2. Concept A (hero canvas) — build and verify in localhost
3. Concept B (diagnostic section) — build and verify
4. Concept C (about reel) — build and verify
5. Full page review: scroll, mobile, reduced-motion, all three concepts together
6. Present final result to Boubacar at localhost
7. No push to any branch until Boubacar approves

---

## Success Criteria

- [ ] Original `catalystworks-site/` folder is byte-for-byte unchanged
- [ ] All three animations play correctly in Chrome on first load
- [ ] `prefers-reduced-motion` disables all animation, page remains fully functional
- [ ] No layout shift on any existing section
- [ ] Mobile (375px) renders correctly for all three concepts
- [ ] Page loads without console errors
- [ ] Existing CTAs, modal, and form still work

---

## Out of Scope

- Audio
- Any changes to copy, pricing, or offer text
- Pushing to GitHub or Hostinger
- Changing the production site in any way
