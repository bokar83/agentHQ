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

**No HTML/CSS before this skill completes. Every time. No exceptions.**

Applies to: new sites, redesigns, section updates, single-page tweaks,
clones, demo sites, and app UIs.

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

If all five checks are written and pass, proceed. If any are missing or fail, stop and resolve before touching HTML.

---

## FAILURE MODE GALLERY

These are real outputs that failed the Volta standard. Never ship anything that looks like these:

- **The Resume Template**: sticky nav, hero with left text + right image, 3-column card grid for services, testimonials carousel, contact form, footer. BANNED.
- **The Bootstrap Reskin**: same skeleton as above but with a different font and accent color. Still BANNED. Boubacar can feel the skeleton through any costume.
- **The Figma Export**: technically correct, visually dead. No motion, no cursor, no life. Looks finished but does not feel alive. BANNED.
- **The "Clean" Cop-out**: "this business needs something clean and minimal" used as justification for a skeleton site. Clean is a design choice. Skeleton is not clean, it is lazy. BANNED.
- **The Blob Swap**: took a previous site, changed the blob color from cobalt to teal, added "sky blue accent." Still the same skeleton. Still BANNED.
- **The Rushed First Pass**: wrote HTML before completing all five self-verification checks. Got called out. Had to rebuild. Wasted time, burned trust. BANNED behavior.

If your output could appear in a Wix template gallery, it has failed.

---

## MANDATORY: Read a reference site before writing code

Before writing the first `<` character, you MUST open and read at minimum the first 150 lines of ONE of these reference sites:

```
workspace/demo-sites/volta-studio/index.html         (926 lines — cinematic dark, agency)
workspace/demo-sites/thepointpediatricdentistry/index.html  (923 lines — storybook blob, kids dental)
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

## Cinematic Baseline

Every site gets at least 3 of these. More is better. Pull back if asked.

- [ ] **Custom cursor**: dot + lagging ring, explicit colors, no blend mode
- [ ] **GSAP SplitText** on hero heading: chars or lines fly in with stagger
- [ ] **ScrollTrigger stagger** on cards, rows, or list items
- [ ] **Clip-path reveal** OR **scrub parallax** on at least one section
- [ ] **Magnetic buttons**: GSAP mousemove + elastic.out on leave
- [ ] **Wavy SVG section dividers**: never hard horizontal lines between sections
- [ ] **Particle trail** OR **CSS marquee** OR **morphing SVG blob**
- [ ] **Pinned horizontal scroll** OR **full-bleed cinematic section** (at least one)

GSAP plugins free as of v3.13: SplitText, ScrambleText, MorphSVG, DrawSVG.
CDN: `https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/`

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
| Playfair Display + Inter | Classic, trustworthy, CW-adjacent |
| Space Grotesk + Syne | Modern, geometric, technical |
| Cormorant Garamond + Source Sans | Luxury, boutique, high-end |
| Unbounded + DM Sans | Bold, statement, geometric |
| Syne + DM Sans | Cinematic dark, agency, confident |
| Amatic SC + Nunito | Hand-drawn, artisan, warm |

---

## Color Story Rotation

Avoid repeating a story within 3 builds.

| Story | Anchors | Notes |
|---|---|---|
| Cobalt + yellow + mint | #1B3F8B + #FFD447 + #B8F0D8 | Playful, bold |
| Cinematic dark + neon green | #0a0a0a + #7BFF6A | Agency, luxury |
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
+ OG image (1200x630)
+ Any image the client has not provided

### How to generate

Invoke the `kie_media` skill. Use `generate_image()` from `orchestrator/kie_media.py`:

```python
from orchestrator.kie_media import generate_image

result = generate_image(
    prompt="...",          # detailed prompt -- see format below
    aspect_ratio="16:9",   # hero: 16:9 | card: 1:1 | OG: 1.91:1
    task_type="text_to_image",
)
# result["local_path"] -> use this path in the HTML src
# result["drive_url"]  -> backup
```

Kie picks the best model automatically (ranked registry). Budget auto-approved up to $0.20/image.

### Prompt format for site images

```
[Style adjective] [subject], [lighting], [color palette matching site], [composition], [mood]
No text. No watermarks. Photorealistic / Illustration / etc.
```

Example for a pediatric dentist hero:
> "Bright, inviting dental office waiting room with colorful children's toys, warm natural light, soft blues and yellows, wide angle, welcoming and playful mood. No text. No people. Photorealistic."

### Rules

+ Generate images **before** writing the HTML that references them. Never write `src=""` placeholders.
+ Match the color palette of the site (include accent color in prompt)
+ OG image: always 1200x630, include site name as text overlay in a second pass if needed
+ If generation fails after the Kie retry ladder, use a CSS gradient as fallback. Never ship a broken img tag.

---

## Step 5: Pre-launch checklist (live deploys)

- [ ] Favicon wired
- [ ] OG image 1200x630px
- [ ] sitemap.xml present
- [ ] robots.txt present
- [ ] GA4 wired
- [ ] HTTP 200 verified on every image URL before embed
- [ ] No placeholder text or broken links
- [ ] Schema.org JSON-LD present
- [ ] Forms wired (Formspree for static)
- [ ] GitHub push in same session as build

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
