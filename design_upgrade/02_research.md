# 02_research.md: Design System Research
**Phase 2 of 7 | agentsHQ Design Upgrade: "Humanized Standard"**
*Compiled: 2026-05-02*

---

## Section 1: Reference Sites

### 1. Linear: https://linear.app

**The human move:** Every status indicator uses functional color (green for "On track," red for "At risk") rather than decorative color. The palette serves information first, aesthetics second.

**Technical pattern:** Inter UI at weights 600 and 800, tight letter-spacing (~-0.02em) at large sizes. Status colors live in CSS custom properties, swapped at the component level. Modular section architecture: each feature block follows a strict heading / description / visual-demo rhythm.

**Copy it when:** B2B SaaS targeting developers or ops teams. Trust earned through precision.

**Refuse it when:** Consumer-facing, lifestyle, or needs warmth. Precision reads as cold to non-technical audiences.

Sources: [typ.io/s/2jmp](https://typ.io/s/2jmp), [LogRocket analysis](https://blog.logrocket.com/ux-design/linear-design/)

---

### 2. Stripe: https://stripe.com

**The human move:** The animated gradient hero is implemented in WebGL via a fragment shader using Fractal Brownian Motion layering Simplex noise, then transformed with `skewY(-12deg)` via CSS. The motion is mathematically alive in a way a CSS keyframe gradient is not.

**Technical pattern:** Pure JavaScript WebGL ("minigl" library, zero dependencies). The shader uses `sin()` and `cos()` applied to UV coordinates with time-based offsets. GPU handles the load at 60fps.

**Copy it when:** Payment infrastructure, enterprise SaaS, any client where "technical credibility" is a brand pillar.

**Refuse it when:** Consumer apps, nonprofits, mobile-primary experiences. WebGL tanks Lighthouse scores.

Sources: [Kevin Hufnagl breakdown](https://kevinhufnagl.com/how-to-stripe-website-gradient-effect/), [Bram.us tutorial](https://www.bram.us/2021/10/13/how-to-create-the-stripe-website-gradient-effect/)

---

### 3. Vercel: https://vercel.com

**The human move:** Vercel uses its own typeface (Geist Sans / Geist Mono) created with Basement Studio, signaling that the company is a design system company, not just a hosting company. The SVG node-activity animation communicates scale without a single number.

**Technical pattern:** Geist Sans (geometric, Swiss-inspired) for all UI and marketing copy. Dark-mode-first, CSS variables for theme switching. Responsive image delivery with dual SVG variants (light/dark) via media queries.

**Copy it when:** Developer tooling, infrastructure products, any SaaS whose users will notice type quality. Geist is open source.

**Refuse it when:** Non-technical audiences. Geist's Swiss precision can feel impersonal for consumer brands.

Sources: [Vercel Geist font page](https://vercel.com/font), [Geist GitHub](https://github.com/vercel/geist-font)

---

### 4. Resend: https://resend.com

**The human move:** Maximum signal, minimum surface area. A near-empty dark canvas with a single code snippet and one CTA. The restraint itself communicates confidence. Deliberate brand statement, not budget-limited design.

**Technical pattern:** Dark background (~`#0a0a0a`), monospace for code examples, minimal body copy in Inter at regular weight, generous line-height. No image carousels, no animated heroes.

**Copy it when:** Dev tools, APIs, CLI products where the developer audience interprets decoration as noise.

**Refuse it when:** Any client who needs to explain what they do. Minimal works only when the product is already understood by the visitor.

---

### 5. Raycast: https://raycast.com

**The human move:** The glass-morphism keyboard rendering uses `backdrop-filter: blur(10px)`, `background: rgba(17, 25, 40, 0.75)`, and subtle `saturate` filters. This is physically plausible rendering rather than arbitrary transparency.

**Technical pattern:** Layered depth: gradient background, glass-effect overlay elements, and sharp UI components on top create three planes of depth without WebGL. Progressive disclosure manages feature density.

**Copy it when:** Productivity apps, desktop apps, premium consumer tools. Effective for Mac-first or developer-adjacent audiences.

**Refuse it when:** Enterprise B2B dashboards, editorial sites, data journalism.

---

### 6. Anthropic: https://www.anthropic.com

**The human move:** The font pairing is the differentiator. Styrene A/B (Commercial Type) handles headlines; Tiempos Text (Klim Type Foundry) handles body copy. Both are premium editorial typefaces with visible personality. This distances the brand from the cold techno-aesthetic of most AI companies.

**Technical pattern:** Neutral color system: off-white and warm beige rather than pure white, dark charcoal rather than pure black. Ample padding (64px+ section gaps).

**Copy it when:** Research organizations, AI companies, policy institutions, any client whose brand promise involves trust and long-term thinking.

**Refuse it when:** Consumer products or any client who needs to generate immediate excitement.

Sources: [type.today Anthropic profile](https://type.today/en/journal/anthropic), [Abduzeedo analysis](https://abduzeedo.com/seamlessly-crafting-ai-branding-and-visual-identity-anthropic)

---

### 7. Locomotive Agency: https://locomotive.agency

**The human move:** The loading animation is a brand moment, not a delay screen. Every page uses full-funnel scroll architecture: the user flows from awareness to conversion as they scroll, mirroring the agency's own methodology.

**Technical pattern:** Locomotive Scroll (their open-source library) provides the smooth-scroll narrative. Infinite CSS marquee for client logos. Scroll-triggered section reveals via IntersectionObserver.

**Copy it when:** Agency or studio portfolios where process narrative is the product.

**Refuse it when:** Product SaaS landing pages, e-commerce, or mobile-heavy contexts.

---

### 8. Active Theory: https://activetheory.net

**The human move:** Active Theory V6 adds AI chat and multiplayer to the portfolio. The site does not describe the studio's capabilities; it demonstrates them live. The portfolio is itself interactive work.

**Technical pattern:** Custom WebGL framework (Hydra, their own toolset). Portfolio navigation is a 3D interactive environment.

**Copy it when:** Creative studios, games companies, entertainment brands for whom immersion is the product.

**Refuse it when:** SaaS, e-commerce, mobile-first, SEO-dependent sites. WebGL portfolios lose ~5 Lighthouse performance points and are invisible to crawlers without SSR.

Sources: [CSS Design Awards](https://www.cssdesignawards.com/sites/active-theory-v6/45015), [Awwwards Annual 2024](https://annuals.awwwards.com/site-nominees/active-theory-v6)

---

### 9. Resn: https://resn.co.nz [LOW CONFIDENCE: site returned minimal HTML]

**The human move:** Resn is known for experimental browser-based experiences that treat the browser as an art medium. Their work features unexpected interaction models (dragging, physics, unconventional scroll) and deliberately breaks grid conventions.

**Copy it when:** Experiential campaigns, cultural institutions, entertainment brands where the experience is the deliverable.

**Refuse it when:** Any client with a conversion-rate objective. Experimental interaction models increase cognitive load and reduce conversion.

---

### 10. The Pudding: https://www.pudding.cool

**The human move:** Custom illustrated stickers replace conventional filter tabs. The stickers function as navigation but feel like editorial curation. This signals "publication with opinions," not a content platform.

**Technical pattern:** Scrollama.js handles scroll-driven story triggers via IntersectionObserver. D3.js handles data visualization within scroll steps.

**Copy it when:** Editorial and data journalism projects. Scrollytelling stack (Scrollama + D3) is right for any project where visualization changes in response to narrative progress.

**Refuse it when:** Product SaaS or marketing pages. Scrollytelling demands full attention and fights with sidebar CTAs.

Sources: [Pudding/Scrollama introduction](https://pudding.cool/process/introducing-scrollama/), [D3+Scrollama guide](https://pudding.cool/process/how-to-implement-scrollytelling/)

---

### 11. Bloomberg Graphics: https://www.bloomberg.com/graphics [LOW CONFIDENCE: site returned 403]

**The human move:** Massive display type that nearly breaks the grid, bespoke color palettes per story (not a single brand palette), and data visualization custom-built for each narrative rather than reusing chart templates.

**Technical pattern:** D3.js for bespoke chart rendering, often combined with Scrollama. Each graphic is a standalone application embedded in an article wrapper. Responsive SVG via `viewBox` scaling.

**Copy it when:** Data journalism, annual reports, investor decks that need to read as editorial rather than corporate.

**Refuse it when:** Any project needing a reusable component library. The approach has high per-story cost.

---

### 12. Codrops / Tympanus: https://tympanus.net/codrops/

**Purpose:** A techniques library surfacing implementation patterns behind award-winning effects. Key current techniques: WebGPU fragment shaders, Three.js with custom GLSL, GSAP `easeReverse`, scroll-driven 3D world navigation.

**Use it:** Before implementing any WebGL, shader, or complex GSAP pattern. Codrops usually has a working demo with annotated source.

**Skip it:** Do not cargo-cult Codrops demos into production without performance profiling. Many demos are proof-of-concept only.

---

### 13. GSAP Showcase: https://gsap.com/showcase/

**Technical patterns documented:** ScrollTrigger for scroll-scrubbed narratives, SplitText for kinetic typography, MorphSVG for shape transitions, Flip for layout-aware state changes, Observer for gesture-driven interactions. DrawSVG, MotionPath, ScrambleText, Draggable.

**When to use GSAP over CSS:** When animation timing must be synchronized across multiple elements in a timeline. For single-element hover transitions, CSS is sufficient and lighter.

---

## Section 2: Designers

### 1. Jony Ive: LoveFrom, formerly Apple

**Core principles:**
1. Minimalism as a tool for bringing order to chaos, not aesthetic reduction for its own sake.
2. Manufacturing obsession embedded in design from the start. Material decisions communicate before any text is read.
3. Consequence awareness: designers are responsible for unintended outcomes, not only stated intent.
4. Every design decision serves understanding, not appearance.
5. Minimalism should "sincerely elevate the species": the ambition is genuine improvement of experience, not aesthetic tidiness.

**Visual signatures:** Chamfered edges, proportionally-derived radii (not generic `border-radius: 8px`), material depth without decorative surface texture, generous whitespace as composition.

**Business contexts:** Premium hardware, productivity software, luxury physical goods, any product competing on refinement rather than feature count.

Sources: [LoveFrom philosophy (Tapflare)](https://tapflare.com/articles/jony-ive-lovefrom-design-philosophy), [MacRumors interview May 2025](https://www.macrumors.com/2025/05/09/jony-ive-reflects-on-culture-products-and-warning/)

---

### 2. Dieter Rams: Braun, Vitsoe

**Core principles (distilled for screen design):**
1. Good design is honest: it does not make a product appear more valuable than it is.
2. Good design is long-lasting: it avoids being fashionable and never appears antiquated.
3. Good design is as little design as possible: less but better, concentrating on essential aspects.
4. Good design makes a product understandable: it clarifies structure and uses self-explanatory form.

**Visual signatures:** Strict grid discipline. Helvetica and Akzidenz Grotesk. Function-derived form. No decorative elements that do not serve information.

**Business contexts:** SaaS tools, B2B dashboards, consumer electronics brands, any product where "built to last" is a competitive claim.

Sources: [Vitsoe Good Design](https://www.vitsoe.com/us/about/good-design), [IxDF Ten Principles](https://ixdf.org/literature/article/dieter-rams-10-timeless-commandments-for-good-design)

---

### 3. Paula Scher: Pentagram

**Core principles:**
1. Typography as image: letterforms are the primary illustrative component, not a label applied to a visual.
2. Serious play: intuition and "solvable mistakes" over rigid data-driven grids.
3. Environmental integration: 2D design scales into 3D architectural space.
4. Expressionist typography: the look of type must match the content's emotional register.

**Visual signatures:** Massive type that acts as landscape. Layered letterforms at different scales. High contrast between display and body weight. Color deployed boldly.

**Business contexts:** Cultural institutions, urban brands, organizations whose identity must read at architectural scale.

Sources: [Pentagram/Paula Scher](https://www.pentagram.com/about/paula-scher), [inkbotdesign analysis](https://inkbotdesign.com/paula-scher/)

---

### 4. Massimo Vignelli

**Core principles:**
1. Semantic correctness, syntactic consistency, pragmatic understandability.
2. Visual power, intellectual elegance, timelessness: design is not decoration.
3. Grid discipline: all design organized by a column-row grid; whitespace is part of the grid.
4. Strict typeface economy: Vignelli worked from a palette of four typefaces. More typefaces signal lack of conviction.

**Visual signatures:** Helvetica at varied weights as the primary expressive tool. Asymmetric layouts with deliberate tension. Clean color coding via functional palette (the NYC subway lines).

**Business contexts:** Transit systems, institutional identity systems, any organization communicating at scale across print, environmental, and digital simultaneously.

Sources: [Vignelli Canon PDF (RIT)](https://www.rit.edu/vignellicenter/sites/rit.edu.vignellicenter/files/documents/The%20Vignelli%20Canon.pdf), [UX Collective analysis](https://uxdesign.cc/the-vignelli-canon-a-design-classic-from-the-last-of-the-modernists-74d6e7dc0169)

---

### 5. Stefan Sagmeister

**Core principles:**
1. Beauty is functional: high-quality aesthetics improve user engagement, trust, and business performance.
2. The body as medium: the most visceral communication uses physical material; the message is inseparable from the medium.
3. Handwriting when content is personal; the register mismatch is the point.
4. Sabbatical as innovation engine: every seven years, a full year of non-commercial research.

**Visual signatures:** Typographic interventions in physical space. Typography secondary to the experience of encountering it.

**Business contexts:** Cultural brands, music industry, luxury goods, any client whose brief allows the medium to be the message. Anti-fit for interfaces and SaaS.

Sources: [Sagmeister studio](https://sagmeister.com/answers/), [inkbotdesign analysis](https://inkbotdesign.com/stefan-sagmeister/)

---

### 6. Jessica Walsh: &Walsh

**Core principles:**
1. Find the weird: every brand has a distinctive, unusual quality. Design amplifies it rather than sanding it down.
2. Brand therapy over brand templates: start with actual personality, not a category template.
3. Anti-blanding: homogenization of brand identity is a failure mode, not safety. Distinctiveness is functional.
4. Beauty and functionality are not opposites.

**Visual signatures:** Vivid saturated color palettes. Experimental typography that bends or overlaps. Photography combined with illustration, hand-lettering, and 3D elements.

**Business contexts:** Consumer brands competing on personality, fashion and beauty, food and beverage, entertainment, cultural campaigns.

Sources: [It's Nice That, Nov 2024](https://www.itsnicethat.com/articles/air-jessica-walsh-manifesto-creative-industry-sponsored-content-111124), [Sevenvault analysis](https://sevenvault.com/2024/01/25/jessica-walshs-10-rules-for-outstanding-branding-design/)

---

### 7. Tobias van Schneider: House of van Schneider

**Core principles:**
1. Start with WHY: all design values determined before visual decisions are made.
2. Minimalism with bold choices: clean layouts, one deliberately bold decision per piece.
3. Long-term design systems over quick trends.
4. Das Gesamtkunstwerk: every touchpoint as part of one unified creative statement.

**Visual signatures:** Large-scale photography and illustration paired with restrained typography. Monochromatic palettes punctuated by a single contrast element.

**Business contexts:** Consumer tech, audio/music brands, automotive, luxury. Strong fit for any brand whose product is primarily experienced rather than read about.

Sources: [vanschneider.com](https://vanschneider.com/), [Das Gesamtkunstwerk essay, June 2024](https://vanschneider.com/blog/das-gesamtkunstwerk/)

---

### 8. Mathieu Triay: BBC R&D

**Core principles:**
1. Prototype before polishing: sketch first, move to screen only to test interactions.
2. Restraint in digital: every element must earn its presence. Pilcrow symbols (¶) as section separators.
3. Content-first navigation: links and anchors rather than button components. Document-like structure.
4. Experimental without spectacle: unusual interaction models serve a design argument, not visual flash.

**Visual signatures:** Text-first layout with typographic symbols as navigational markers. Monochromatic. Design that reads more like a printed publication than a website.

**Business contexts:** Editorial products, cultural institutions, public media, research organizations.

Sources: [mathieutriay.com](https://www.mathieutriay.com/), [Creative Lives in Progress](https://www.creativelivesinprogress.com/article/mathieu-triay)

---

## Section 3: Technical Patterns Inventory

### 1. Lenis Smooth Scroll

**What it does:** Replaces native scroll with momentum-based linear interpolation. The page lags slightly behind scroll input and eases into rest. Results in "buttery" or "luxury" scrolling.

**Lerp value guide:**
- `0.05`: Very slow, cinematic pacing. Editorial and agency portfolio work.
- `0.07`: Standard premium production value. **Default choice.**
- `0.1`: Near-native speed with light smoothing. SaaS products where scroll accuracy matters.
- `0.5+`: Effectively no difference from native scroll.

**Caution:** Always disable Lenis when `prefers-reduced-motion` matches.

**Archetype fit:** Calm Product, Editorial Narrative, Cinematic/Agency.

Source: [Lenis GitHub](https://github.com/darkroomengineering/lenis)

---

### 2. GSAP ScrollTrigger

**Scrub value guide:**
- `scrub: true`: Direct 1:1 tracking. Use for progress indicators.
- `scrub: 0.5`: Responsive and smooth. Use for image reveals and parallax.
- `scrub: 1`: Standard premium narrative scroll. Use for hero sequences.
- `scrub: 2`: Cinematic pacing. Use for feature showcase stacks.

**Trigger point convention:** `start: "top 80%"` is the standard entry trigger. `start: "top top"` for full-viewport pins.

**Archetype fit:** All archetypes. ScrollTrigger is the foundation of narrative scroll.

Source: [GSAP ScrollTrigger docs](https://gsap.com/docs/v3/Plugins/ScrollTrigger/)

---

### 3. Framer Motion Spring Physics

**Parameter combinations by feel:**

| Feel | Stiffness | Damping | Mass | Use case |
|---|---|---|---|---|
| Snappy UI (button press) | 400 | 30 | 1 | Micro-interactions |
| Standard modal entry | 300 | 25 | 1 | Dialogs, drawers |
| Gentle card hover | 200 | 20 | 1 | Card lifts, tooltips |
| Heavy/dramatic reveal | 100 | 15 | 1.5 | Hero elements |
| Bouncy/playful | 150 | 8 | 1 | Illustrative/Playful archetype |

Defaults (stiffness 100, damping 10, mass 1) produce noticeable bounce: usually too much for professional product UIs.

**Archetype fit:** Calm Product (stiffness 250+, damping 25+), Illustrative/Playful (stiffness 150, damping 8), Cinematic (mass 1.5).

Source: [Framer Motion transitions](https://www.framer.com/motion/transition/)

---

### 4. CSS Scroll-Driven Animations

**Key concepts:**
- `animation-timeline: scroll()`: ties animation to scroll container progress. Use for progress bars, parallax backgrounds.
- `animation-timeline: view()`: ties animation to element visibility within viewport. Use for element entry/exit.
- `animation-range: entry 0% entry 30%`: fires during the first 30% of the element's entry into view.

**Browser support (2026):** Chrome/Edge full, Firefox flagged, Safari 2025. Use `@supports` guard with GSAP fallback.

**Archetype fit:** Calm Product, Documentary/Data.

Source: [MDN scroll-driven animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations)

---

### 5. View Transitions API

**What it does:** Animates between DOM states or page navigations with browser-native crossfade or custom CSS. The key technique: give the same `view-transition-name` to an element in both old and new state. The browser morphs position, size, and content automatically.

**Browser support (2026):** Chrome, Edge, Safari (2025), Firefox (partial). Over 85% coverage.

**Archetype fit:** Editorial Narrative, Calm Product.

Source: [Chrome Developers: View Transitions 2025](https://developer.chrome.com/blog/view-transitions-in-2025)

---

### 6. GSAP SplitText for Kinetic Typography

**Standard hero headline entry:**
```js
gsap.from(split.chars, {
  opacity: 0, y: 40, rotationX: -90,
  stagger: 0.02, ease: "power2.out", duration: 0.6
})
```

**Technique variations:**
- Stagger reveal by char (stagger: 0.02): standard premium headline entry
- Wave effect via stagger by word: slower reveals with narrative weight
- ScrambleText: random character substitution resolving to final text

**Caution:** Call `split.revert()` before responsive reflow. SplitText line detection breaks on resize without this.

**Archetype fit:** Cinematic/Agency (dramatic, slow stagger), Editorial Narrative (word-by-word), Calm Product (opacity + translateY only, no rotation).

Source: [GSAP SplitText docs](https://gsap.com/docs/v3/Plugins/SplitText/)

---

### 7. CSS `linear()` Easing

**What it does:** Approximates spring animation physics in CSS: overshoot, bounce, elastic settle: without JavaScript. No bundle weight.

**Generation tool:** [CSS Spring Easing Generator (kvin.me)](https://www.kvin.me/css-springs). Open Props library provides named presets: `--ease-spring-1` through `--ease-spring-5`.

**Browser support:** Chrome 113+, Firefox 112+, no Safari (2026). Use `@supports` guard with cubic-bezier fallback.

**Archetype fit:** Calm Product (spring-1 or spring-2: gentle overshoot), Illustrative/Playful (spring-4 or spring-5: pronounced bounce).

Source: [Josh W. Comeau: CSS linear()](https://www.joshwcomeau.com/animation/linear-timing-function/)

---

### 8. SVG Path Morphing

**What it does:** Animates the `d` attribute of an SVG path between two shapes. GSAP MorphSVG automatically adds anchor points to normalize path complexity. No manual point matching required.

**Performance:** Keep point counts under 200 for smooth 60fps. Simplify complex paths in Figma before export.

**Archetype fit:** Cinematic/Agency (abstract shape transitions), Illustrative/Playful (playful icon state changes), Calm Product (subtle icon morphs on toggle states).

Source: [GSAP MorphSVG docs](https://gsap.com/docs/v3/Plugins/MorphSVGPlugin/)

---

### 9. WebGL / Three.js

**When WebGL is warranted:** The site's primary value proposition is a 3D product. The brand identity is inherently spatial. The hero animation cannot be achieved with CSS or SVG. Desktop audience with GPU performance assumed.

**When WebGL is overkill:** Conversion-rate-critical landing pages (~5 Lighthouse point loss). Mobile-first or performance-sensitive audiences. SEO-dependent pages. When the 3D is decorative, not functional.

**Archetype fit:** Cinematic/Agency only.

---

### 10. CSS Parallax with `transform` and Scroll Position

**Performance rules:**
- Always use `translate3d()` not `translateY()`: forces GPU layer compositing
- Never animate `top`, `left`, `margin`, or `position`: triggers layout reflow
- Use `will-change: transform` on parallax layers (sparingly)
- Bind to requestAnimationFrame or CSS compositor, not scroll events directly

**Speed multiplier guide:** Background layer: 0.2-0.4x. Midground: 0.5-0.7x. Foreground: 1.1-1.3x.

**Archetype fit:** Editorial Narrative, Cinematic/Agency. Use sparingly in Calm Product (single layer, 0.3x max).

Source: [CSS Tricks: Parallax with scroll-driven animations](https://css-tricks.com/bringing-back-parallax-with-scroll-driven-css-animations/)

---

## Section 4: The 10 AI-Tells

Sources: [prg.sh analysis](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website), [DEV Community](https://dev.to/alanwest/why-every-ai-built-website-looks-the-same-blame-tailwinds-indigo-500-3h2p), [925studios guide](https://www.925studios.co/blog/ai-slop-web-design-guide)

---

**Tell 1: The Indigo-500 Button**
- Signal: `background-color: #6366f1` (Tailwind `bg-indigo-500`) or `from-indigo-500 to-purple-600` gradient on primary CTAs.
- Why it reads as AI: Tailwind's default indigo palette was the statistically most common button color in training data. LLMs predict the most probable token; this is the most probable button color.
- Human replacement: A custom brand hex derived from a mood board, not a Tailwind default. Override via `--color-primary: #your-hex`. If using Tailwind, choose warm amber, cool teal, or neutral stone instead of indigo.

**Tell 2: Inter on Everything**
- Signal: `font-family: 'Inter', sans-serif` globally at a single weight (400 regular + 600 semibold), no serif counterpart.
- Why it reads as AI: Inter is the highest-frequency font in GitHub repos and Tailwind tutorials.
- Human replacement: A deliberate pairing with purpose. Geist Sans for developer-facing, Styrene + Tiempos for research orgs, Editorial New + Inter for editorial-product hybrids. If Inter is used, pair it with a display serif for headlines.

**Tell 3: The Three-Box Feature Grid**
- Signal: Three equal columns, each with a Heroicons/Lucide icon (24px, same weight), short heading, 2-3 lines of body copy at `grid-template-columns: repeat(3, 1fr)` with `gap: 2rem`.
- Why it reads as AI: The single most common feature section pattern in Tailwind landing page templates.
- Human replacement: Break symmetry. Use a 2+1 layout, horizontal timeline, numbered list with large numerals, or before/after split. Replace icon + text with video or live demos.

**Tell 4: Uniform Border Radius**
- Signal: `border-radius: 0.5rem` (8px) or `border-radius: 0.75rem` (12px) applied uniformly to every card, button, image, and input.
- Why it reads as AI: This is the Tailwind default (`rounded-lg`) applied everywhere.
- Human replacement: Derive radii proportionally. Small elements (buttons, badges): 4px. Cards: 12-16px. Large image containers: 0px (edge-to-edge) or 24px+ (deliberately large). Never the same value on all elements.

**Tell 5: The Low-Opacity Shadow**
- Signal: `box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1)` (Tailwind `shadow-md`) on every card.
- Why it reads as AI: This exact value is the Tailwind `shadow-md` default.
- Human replacement: Vary by elevation. Consider colored shadows that echo brand color. Or eliminate shadows entirely and use border + background contrast.

**Tell 6: The Gradient Hero with Centered H1**
- Signal: Full-width hero with `from-purple-900 to-indigo-900` gradient, white centered H1 at 48-64px, subtitle, and two buttons (primary CTA + secondary ghost). Everything centered.
- Why it reads as AI: The default SaaS hero template replicated across millions of Tailwind-based projects.
- Human replacement: Offset headline to 60% of viewport width. Use a full-bleed image with text overlay. Make the background a live WebGL gradient or actual photo. Break the center axis. Introduce vertical rhythm with the headline spanning multiple visual layers.

**Tell 7: Icon Monoculture**
- Signal: All icons from a single library (Heroicons, Lucide, Phosphor), all at 24px, all at `stroke-width: 1.5`, all in the same color as body text.
- Why it reads as AI: Icon libraries are the easiest path for an LLM. One library at one size at one color requires no visual decision-making.
- Human replacement: Treat icons as illustration elements. Mix styles. Scale deliberately (16px inline, 32px feature sections, 64px hero icons). Apply brand color. Or replace with custom SVG illustrations.

**Tell 8: Missing Error States and Empty States**
- Signal: Forms with no visible validation feedback, no required field indicators, no error message styling. Lists with no empty-state component.
- Why it reads as AI: LLMs generate the happy-path UI. Conditional states are statistically less common in training data.
- Human replacement: Design and implement all three states for every interactive element: default, loading/pending, error/empty, success.

**Tell 9: Semantic HTML Blindness**
- Signal: `<div class="card">` instead of `<article>`. `<div class="nav">` instead of `<nav>`. `<div onclick="">` instead of `<button>`. No ARIA labels on icon-only buttons.
- Why it reads as AI: LLMs trained on div-heavy tutorials default to div-first markup.
- Human replacement: Use semantic elements throughout. Add `aria-label` to all icon-only buttons. `role` attributes where semantic element does not exist.

**Tell 10: Animation as Decoration**
- Signal: Scattered `opacity: 0` to `opacity: 1` fade-ins on every section via IntersectionObserver, all at the same timing (`0.5s ease-in-out`), no relationship between animation and content hierarchy.
- Why it reads as AI: The most common scroll animation pattern in Tailwind + GSAP tutorials. Applied uniformly, it adds motion without narrative purpose.
- Human replacement: Choreograph with intent. Hero headline: dramatic SplitText stagger. Supporting content: subtle translateY with longer delay. Charts: draw-in sequenced to reading order. Navigation: no animation. Motion must reinforce hierarchy.

---

## Section 5: Archetype Definitions

### Archetype 1: Calm Product

**When to use:** B2B SaaS, developer productivity, fintech, project management, analytics. Professional audiences skeptical of marketing, needing trust before commitment. Stage: Series A or later, moving from early adopter to mainstream.

**Visual DNA:** Near-black background (~`#0f0f11`), 8px grid, 16/24px padding units, status color system (functional greens/ambers/reds), single gradient accent as brand signature.

**Typography mandate:** Heading: Inter 700 or Geist Sans 600 at -0.02em letter-spacing, or Neue Montreal / DM Sans. Body: Inter 400, 14-16px, 1.5 line-height. Mono: Geist Mono or JetBrains Mono.

**Motion character:** GSAP ScrollTrigger `scrub: 1` for hero sequences. Framer Motion stiffness 300, damping 25 for UI interactions. Lenis lerp 0.07-0.1. No decorative animation.

**Reference sites:** https://linear.app, https://vercel.com, https://resend.com

**Refuse:** Glass morphism, rainbow gradients, illustrated mascots, heavy WebGL heroes, motion that does not communicate a state change.

---

### Archetype 2: Editorial Narrative

**When to use:** Long-form journalism, research organizations, think tanks, conference sites, public institutions. Audiences that read rather than scan.

**Visual DNA:** Off-white foundation (`#f5f2ed` to `#faf8f4`), premium font pairing as primary visual differentiator, generous leading (line-height 1.7-1.9 for body copy), minimal color: one functional accent.

**Typography mandate:** Heading: Tiempos Text (Klim), Canela (CSTM Fonts), GT Super (Grilli Type), or Playfair Display (open source). Body: Tiempos Text or a humanist sans like Söhne for contrast. Captions: small-caps or narrower sans at 11-12px.

**Motion character:** View Transitions API for page navigation. Scrollama + D3 for data-driven story steps. CSS scroll-driven animations for section entry. Lenis lerp 0.05.

**Reference sites:** https://www.pudding.cool, https://www.anthropic.com

**Refuse:** Dark mode, glass morphism, icon grids, countdown timers, any element that signals "landing page."

---

### Archetype 3: Cinematic / Agency

**When to use:** Creative studios, production companies, luxury brands, entertainment properties, experiential campaigns. The site functions as a portfolio piece.

**Visual DNA:** Full-viewport hero (video, WebGL, or high-resolution photography edge-to-edge), cinematic aspect ratios (16:9 or 2.39:1), type at architectural scale (headlines at 40-60% of viewport height), dark base punctuated by single high-contrast color moment.

**Typography mandate:** Heading: Clash Display, Syne, Neue Montreal at 900 weight, Editorial New, or bespoke custom type. Body: Neue Montreal 400 or DM Sans 400. No monospace.

**Motion character:** GSAP SplitText stagger 0.03-0.05, `rotationX: -90` on chars for headline entry. ScrollTrigger `scrub: 2` for slow dramatic sequences. Lenis lerp 0.05. WebGL only when brand warrants it.

**Reference sites:** https://activetheory.net, https://locomotive.agency

**Refuse:** Three-box feature grids, pricing tables, uniform card radii, Inter at regular weight, any pattern that signals SaaS.

---

### Archetype 4: Brutalist

**When to use:** Independent creators, culture publications, challenger brands, music, fashion brands positioning against the mainstream. Audiences who read "professional-looking" as "corporate" and "corporate" as "untrustworthy."

**Visual DNA:** Raw grid or deliberately broken grid (intentional misalignment as statement), high-contrast typography at extreme weights (900) against pure white or black, pure saturated primaries (not pastels, not gradients) or no color, visible structure: borders and grid lines shown rather than hidden.

**Typography mandate:** Heading: Helvetica Neue 900, Druk Wide Super, or GT America Compressed Black. Body: same grotesque at regular weight, or a slab serif (Courier New). `border-radius: 0` on all elements.

**Motion character:** No animation, or deliberate anti-animation (instant state changes, no transitions). If scroll animation exists, it feels architectural: large movements, no easing. The absence of smooth motion is a design choice.

**Refuse:** Rounded corners, soft shadows, gradient backgrounds, smooth scroll with lerp, icon libraries, glassmorphism, any element that prioritizes comfort over provocation.

---

### Archetype 5: Illustrative / Playful

**When to use:** Consumer apps for non-technical audiences, wellness and personal growth, creator tools, gaming-adjacent products, brands whose personality is a competitive advantage. Stage: early-stage consumer, community products.

**Visual DNA:** Custom illustration system (not stock photography, not icon libraries), warm saturated palette with clear primary + secondary + accent, organic shapes (pill buttons, blob backgrounds, hand-drawn borders), low density: each section has one primary visual.

**Typography mandate:** Heading: Nunito 800, Poppins 700, Plus Jakarta Sans 800, or a display font with personality (Recoleta, Fraunces). Body: Nunito 400, Poppins 400, or Plus Jakarta Sans 400. No serif, no monospace.

**Motion character:** Framer Motion stiffness 150, damping 8: pronounced bounce is appropriate. GSAP SplitText for playful reveals. Lenis lerp 0.1. Hover states with scale(1.05) and bouncy spring.

**Reference sites:** https://www.pudding.cool (illustrated navigation), https://andwalsh.com

**Refuse:** Dark mode as default, monospace type, dense data tables, high-contrast minimalism, corporate blue palettes, anything signaling enterprise.

---

### Archetype 6: Documentary / Data

**When to use:** Data journalism, research visualization, financial reporting, scientific communication, public health, policy analysis. Audiences skeptical of visual manipulation who need to trust the underlying numbers.

**Visual DNA:** White or very light gray foundation (`#fafafa`), typography-forward (data and labels are the primary visual element), chart color system: 5-7 discrete colors, colorblind-safe (avoid red-green pairings), generous white space around data visualizations.

**Typography mandate:** Heading: IBM Plex Sans 600, DM Sans 600, or Inter 600 for chart titles. Body: same grotesque at regular weight, or Tiempos Text for narrative sections. Data labels: `font-variant-numeric: tabular-nums` for all numeric data. Axes and captions: 11-13px, 0.02em letter-spacing.

**Motion character:** D3.js for chart draw-in animations. Scrollama for scroll-triggered data steps. CSS scroll-driven animations for progress indicators. No decorative motion: every animation reveals or explains a data point.

**Reference sites:** https://www.pudding.cool, https://observablehq.com

**Refuse:** WebGL, dark mode as default (reduces chart legibility), gradient fills on charts (implies false data interpolation), motion that does not reveal data.

---

### Archetype 7: Trust / Enterprise

**When to use:** Consulting firms, legal services, financial advisors, insurance, enterprise software, healthcare B2B. High-stakes decision-makers who equate visual conservatism with professional reliability.

**Visual DNA:** Navy or dark teal primary, white secondary, gold or amber accent, photography of real people in real work contexts, conservative grid (12-column, 1200px max-width, 24px gutter), no visual tricks.

**Typography mandate:** Heading: Freight Display, Garamond Premier Pro, or Neue Haas Grotesk. Body: Source Serif 4 or Georgia 400 for reading-heavy pages; Inter 400 for UI sections. No display type, no decorative letterforms.

**Motion character:** CSS transitions only: `transition: all 0.2s ease-out` for hover states. No scroll animation, no kinetic typography, no parallax. If Framer Motion required: stiffness 500, damping 40, fast and precise, no overshoot.

**Refuse:** Dark mode, experimental typography, motion that reads as "trying too hard," illustration, mascots, neon accents, anything implying startup energy.

---

### Archetype 8: Conversion-First / Growth

**When to use:** E-commerce, subscription products, marketplaces, PLG SaaS. Primary success metric is conversion rate.

**Visual DNA:** High-contrast CTA button (not indigo: warm orange, saturated green, or custom brand color at 4.5:1 contrast), social proof above the fold (logos, testimonials, live counter), price anchoring visible without scrolling, single-column mobile-first layout.

**Typography mandate:** Heading: Inter 800, Neue Montreal 700, or DM Sans 700, sized to fill 70-80% of mobile viewport width at H1 level. Body: same sans at 400, 16-18px for mobile readability. Price and CTA text: 700 weight, 2px+ larger than body.

**Motion character:** CSS transitions on CTA hover only (scale 1.02, box-shadow deepens). No scroll animation that delays content. No parallax. Lenis disabled or at lerp 0.1. Loading spinner on form submit. Checkmark on success.

**Refuse:** Multiple competing CTAs, hero animations that delay the primary message, dark mode (lower conversion documented in e-commerce), any element adding cognitive load before the CTA.

---

## Source Index

**Reference sites:** [typ.io/s/2jmp](https://typ.io/s/2jmp) | [LogRocket/Linear](https://blog.logrocket.com/ux-design/linear-design/) | [Kevin Hufnagl/Stripe](https://kevinhufnagl.com/how-to-stripe-website-gradient-effect/) | [Bram.us/Stripe](https://www.bram.us/2021/10/13/how-to-create-the-stripe-website-gradient-effect/) | [Vercel/Geist](https://vercel.com/font) | [type.today/Anthropic](https://type.today/en/journal/anthropic) | [Abduzeedo/Anthropic](https://abduzeedo.com/seamlessly-crafting-ai-branding-and-visual-identity-anthropic) | [CSS Design Awards/Active Theory](https://www.cssdesignawards.com/sites/active-theory-v6/45015) | [Pudding/Scrollama](https://pudding.cool/process/introducing-scrollama/)

**Designers:** [LoveFrom/Tapflare](https://tapflare.com/articles/jony-ive-lovefrom-design-philosophy) | [MacRumors/Ive 2025](https://www.macrumors.com/2025/05/09/jony-ive-reflects-on-culture-products-and-warning/) | [Vitsoe/Good Design](https://www.vitsoe.com/us/about/good-design) | [Pentagram/Scher](https://www.pentagram.com/about/paula-scher) | [Vignelli Canon PDF](https://www.rit.edu/vignellicenter/sites/rit.edu.vignellicenter/files/documents/The%20Vignelli%20Canon.pdf) | [It's Nice That/Walsh](https://www.itsnicethat.com/articles/air-jessica-walsh-manifesto-creative-industry-sponsored-content-111124) | [vanschneider.com](https://vanschneider.com/) | [mathieutriay.com](https://www.mathieutriay.com/)

**Technical patterns:** [Lenis GitHub](https://github.com/darkroomengineering/lenis) | [GSAP ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/) | [Framer Motion](https://www.framer.com/motion/transition/) | [MDN/scroll-driven](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations) | [CSS Spring Generator](https://www.kvin.me/css-springs) | [Josh W. Comeau/linear()](https://www.joshwcomeau.com/animation/linear-timing-function/) | [GSAP SplitText](https://gsap.com/docs/v3/Plugins/SplitText/) | [GSAP MorphSVG](https://gsap.com/docs/v3/Plugins/MorphSVGPlugin/)

**AI-tell sources:** [prg.sh](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website) | [DEV Community/Tailwind](https://dev.to/alanwest/why-every-ai-built-website-looks-the-same-blame-tailwinds-indigo-500-3h2p) | [925studios](https://www.925studios.co/blog/ai-slop-web-design-guide)

---

*Phase 2 complete. Proceeding to Phase 3: Plan.*
