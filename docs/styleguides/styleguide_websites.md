# Website Style Guide — Catalyst Works Consulting

**Version:** 1.0
**Last updated:** 2026-03-29
**For:** Boubacar Barry, Founder — Catalyst Works Consulting

---

## 1. Design Philosophy

A Catalyst Works website should feel like walking into a well-prepared briefing room — not a startup's landing page, not a Big Four consulting firm's institutional website. It combines the visual authority of the Coastal Clarity palette with copy that sounds like a person, not a product.

The target visitor is a VP, Director, or C-suite executive who is either actively searching for a solution to an organizational problem, or has been referred. They make fast judgments. The site earns credibility in the first 5 seconds or loses it.

**Three visual principles:**
1. Space communicates confidence. Use generous whitespace — crowding looks like desperation.
2. Clarity before beauty. If the user doesn't know what Catalyst Works does within 10 seconds, the design failed.
3. Warmth inside the structure. The color system (Clay, warm golds) prevents the site from reading as cold or institutional.

---

## 2. Color System

Primary palette for all web contexts: **Coastal Clarity**

### Full Color System

| Token name | Hex | Usage |
|---|---|---|
| `--color-primary` | `#00B7C2` | Primary actions, active states, links, highlights |
| `--color-primary-dark` | `#008F99` | Hover state on primary elements |
| `--color-primary-light` | `#E6F9FA` | Primary color tints, selected states, tag backgrounds |
| `--color-base` | `#071A2E` | Dark section backgrounds, hero backgrounds, nav bar |
| `--color-base-lighter` | `#0D2A45` | Secondary dark sections, footer, code blocks |
| `--color-accent` | `#FF7A00` | CTAs (use at ≤10% of colored elements), attention states |
| `--color-accent-hover` | `#E06900` | Hover state on accent CTAs |
| `--color-clay` | `#B47C57` | Decorative warmth elements, borders on testimonials, human-context icons |
| `--color-mist` | `#F3F6F9` | Page background (light sections), card backgrounds |
| `--color-white` | `#FFFFFF` | Card surfaces, modal backgrounds, input fields |
| `--color-carbon` | `#1E222A` | All body text on light backgrounds |
| `--color-carbon-muted` | `#5A6272` | Secondary text, captions, placeholders |
| `--color-carbon-subtle` | `#9AA3B2` | Tertiary text, disabled states |
| `--color-divider` | `#DDE2EA` | Horizontal rules, borders, table dividers |

### Color Usage Rules
- **Never** use `--color-accent` (`#FF7A00`) as a background for large sections — accent only on buttons, tags, and small UI elements (≤10% of the colored surface area on any page)
- **No red tones** anywhere in the interface — not for errors, warnings, or any UI state
- Error states: use `#CC6600` (deep amber) instead of red
- Clay (`#B47C57`) is decorative — never use it as a primary text color or primary button color
- Dark sections (hero, footer, feature bands): use `--color-base` (`#071A2E`)
- Light sections (content areas, cards): use `--color-mist` (`#F3F6F9`) or `--color-white`

---

## 3. Typography Stack

### Font Families

**Primary (headings, UI labels, navigation):** Inter
- Source: `https://fonts.google.com/specimen/Inter`
- Load weights: 400, 500, 600, 700, 800
- CSS: `font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;`
- Google Fonts import: `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');`

**Secondary (body text, long-form copy):** Source Serif 4
- Source: `https://fonts.google.com/specimen/Source+Serif+4`
- Load weights: 400, 600
- CSS: `font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif;`
- Use for: service page body copy, about page narrative sections, article/blog content

**Monospace (optional, for technical content only):** JetBrains Mono
- CSS: `font-family: 'JetBrains Mono', 'Courier New', monospace;`

### Type Scale (Desktop)

| Token | Size | Weight | Line Height | Letter Spacing | Font | Usage |
| --- | --- | --- | --- | --- | --- | --- |
| `--text-display` | 56–64px | 800 | 1.1 | -1.5px | Inter | Hero main headline |
| `--text-h1` | 40–48px | 800 | 1.2 | -1.5px | Inter | Page titles |
| `--text-h2` | 30–36px | 700 | 1.25 | -0.5px | Inter | Section headers |
| `--text-h3` | 22–26px | 600 | 1.3 | -0.5px | Inter | Subsection headers |
| `--text-h4` | 18px | 600 | 1.4 | 0 | Inter | Card titles, feature names |
| `--text-body-lg` | 18px | 400 | 1.65 | 0 | Source Serif 4 | Long-form body, about page |
| `--text-body` | 16px | 400 | 1.6 | 0 | Inter | Standard body, card content |
| `--text-body-sm` | 14px | 400 | 1.5 | 0 | Inter | Secondary copy, captions |
| `--text-label` | 12px | 500 | 1.4 | +1.2px (uppercase) | Inter | Eyebrow tags, section labels — ALWAYS uppercase |
| `--text-caption` | 11px | 400 | 1.4 | 0 | Inter | Fine print, timestamps |

**Letter-spacing rules (critical for premium feel):**

- Display + H1: `letter-spacing: -0.03em` (−1.5px at 48px) — tight tracking signals confidence
- H2 + H3: `letter-spacing: -0.015em` — slightly tighter than default
- Labels/eyebrows: `letter-spacing: 0.1em` — wide-spaced uppercase only
- Body text: always `letter-spacing: 0` — never touch body tracking

### Mobile Type Scale
Scale down display and h1 proportionally: display → 36–40px, h1 → 28–32px. H2 and below remain the same. Letter-spacing values stay the same — do NOT adjust for mobile.

---

## 4. Spacing System

**Base unit:** 8px

All spacing values are multiples of 8px.

| Token | Value | Usage |
|---|---|---|
| `--space-1` | 8px | Icon padding, tight inline gaps |
| `--space-2` | 16px | Button padding (vertical), list item gap |
| `--space-3` | 24px | Card internal padding, form field gap |
| `--space-4` | 32px | Section element gap, sidebar gap |
| `--space-5` | 40px | Component top/bottom padding (tight sections) |
| `--space-6` | 48px | Card padding (generous), feature block gap |
| `--space-8` | 64px | Section padding (standard) |
| `--space-10` | 80px | Section padding (generous) |
| `--space-12` | 96px | Hero section padding, major visual separations |
| `--space-16` | 128px | Page-level separation between major sections |

### Grid
- **Max content width:** 1200px
- **Content column width:** 760px (for prose-heavy pages)
- **Narrow column:** 600px (for articles, case studies)
- **Gutter:** 24px (desktop), 16px (tablet), 16px (mobile)

---

## 5. Component Standards

### Buttons

**Primary button (accent CTA):**
```
Background: #FF7A00
Text: #FFFFFF
Font: Inter 600, 16px
Padding: 14px 28px
Border-radius: 4px
Hover: background #E06900, subtle box-shadow
Focus: 2px outline #00B7C2, 2px offset
```
Use for: one primary action per page — "Book a call", "Start the conversation", "Download"

**Secondary button:**
```
Background: transparent
Text: #00B7C2
Border: 1.5px solid #00B7C2
Font: Inter 600, 16px
Padding: 13px 27px
Border-radius: 4px
Hover: background #E6F9FA
```
Use for: secondary actions — "Learn more", "View services", "Read case study"

**Ghost button (dark background version):**
```
Background: transparent
Text: #FFFFFF
Border: 1.5px solid rgba(255,255,255,0.5)
Hover: border-color #FFFFFF, background rgba(255,255,255,0.08)
```
Use on: hero sections, dark feature bands

**Button rules:**
- One primary (accent) button per section — never two orange buttons side by side
- CTAs should say what happens, not what the user should do: "Book a call" not "Click here"
- No rounded-pill buttons (border-radius stays at 4px) — pill buttons feel like SaaS, not consulting

---

### Cards

**Service card (light section):**
```
Background: #FFFFFF
Border: 1px solid #DDE2EA
Border-radius: 8px
Padding: 32px
Box-shadow: 0 2px 8px rgba(7,26,46,0.06)
Hover: box-shadow 0 8px 24px rgba(7,26,46,0.12), translateY(-2px)
Transition: all 200ms ease-out
```
Header: Inter 600, 20px, `#1E222A`
Body: Inter 400, 15px, `#5A6272`
Accent detail: 3px left border in `#00B7C2`

**Feature card (dark section — preferred for landing pages):**
```
Background: rgba(0,183,194,0.06)
Border: 1px solid rgba(0,183,194,0.15)
Border-radius: 8px
Padding: 28px 24px
Icon circle: 36x36px, background rgba(0,183,194,0.15), icon #00B7C2
Hover: border-color rgba(0,183,194,0.35), background rgba(0,183,194,0.1)
Transition: all 200ms ease-out
```
Header: Inter 700, 16px, `#FFFFFF`, letter-spacing 0
Body: Inter 400, 14px, `rgba(255,255,255,0.55)`

**Testimonial / quote card (dark section):**
```
Background: #071A2E
Border: 1px solid rgba(180,124,87,0.3)
Border-radius: 8px
Padding: 28px 24px
Avatar circle: 40x40px, background #B47C57, initials white Inter 600
```
Quote text: Inter 400 italic, 15px, `rgba(255,255,255,0.8)`, line-height 1.65
Name: Inter 600, 14px, `#00B7C2`
Role: Inter 400, 13px, `#B47C57`

**Testimonial / quote card (light section):**
```
Background: #F3F6F9
Border-left: 4px solid #B47C57
Padding: 32px
Border-radius: 0 8px 8px 0
```
Quote text: Source Serif 4 italic, 18px
Attribution: Inter 500, 14px, `#5A6272`

**Stat / KPI card:**
```
Background: #071A2E
Padding: 32px 24px
Border-radius: 8px
Number: Inter 700, 48px, #00B7C2
Label: Inter 500, 14px, rgba(255,255,255,0.7)
```

---

### Navigation

**Desktop nav:**
- Background: `#071A2E` (always dark — not transparent, not white)
- Logo: left-aligned
- Nav links: Inter 500, 15px, `rgba(255,255,255,0.8)`, hover → `#FFFFFF`
- Active: `#00B7C2` underline (2px, offset 4px)
- CTA button: right-aligned, accent primary button style
- Height: 72px
- Sticky: yes, with `backdrop-filter: blur(8px)` and 90% opacity on scroll

**Mobile nav:**
- Hamburger icon: top right
- Full-screen overlay: `#071A2E` background
- Links: Inter 600, 24px, white, stacked vertically with 24px gap
- CTA: full-width accent button at bottom of menu

---

### Hero Section

```
Background: #071A2E (full width)
Min-height: 80vh (desktop), 60vh (mobile)
Padding: 96px top/bottom (desktop), 64px (mobile)
Layout: 2-column grid (text left 55%, visual right 45%) on desktop
        Single column on mobile
```

**Hero text hierarchy:**

1. Eyebrow tag: Inter 500, 12px, `#00B7C2`, `letter-spacing: 0.1em`, uppercase — "AI STRATEGY CONSULTING"
2. Headline: Inter 800, 56px, `#FFFFFF`, `letter-spacing: -0.03em` — the diagnosis or the promise
3. Subhead: Inter 400, 20px, `rgba(255,255,255,0.7)`, `letter-spacing: 0` — one sentence of proof or context
4. CTA group: Primary accent button + ghost secondary button, side by side (stacked on mobile)

**Hero visual options:**
- Abstract geometric pattern using Primary color at low opacity (recommended default)
- Photography: single person in a serious professional context (dark-toned, not bright stock photo energy)
- No: Generic skylines, puzzle pieces, handshakes, or abstract "teamwork" imagery

---

### CTA Section (mid-page and end-of-page)
```
Background: #00B7C2 (primary) OR #071A2E (base dark)
Padding: 80px (desktop), 56px (mobile)
Max-width: 760px (centered)
```
Headline: Inter 700, 36px
Body: Inter 400, 18px, 80% opacity
Button: accent primary (on dark bg) or ghost white (on primary bg)

---

## 6. Animation & Interaction Standards

Source: UI/UX Pro Max — validated for executive consulting landing pages

### Timing

| Token | Value | Use for |
| --- | --- | --- |
| `--transition-fast` | 150ms ease-out | Hover color/border changes, button states |
| `--transition-base` | 200ms ease-out | Card lifts, opacity fades, nav highlights |
| `--transition-enter` | 300ms ease-out | Elements entering the viewport (scroll fade-in) |
| `--transition-exit` | 200ms ease-in | Elements leaving (modals closing) |

**Rules:**

- Enter animations: `ease-out` — fast start, soft landing (feels responsive)
- Exit animations: `ease-in` — soft start, fast end (feels dismissive, not laggy)
- Exit duration ≈ 60–70% of enter duration
- Never animate `width`, `height`, `top`, `left` — use `transform` and `opacity` only
- Always include `@media (prefers-reduced-motion: reduce)` — disable all transitions

### Scroll Fade-In (Intersection Observer)

All below-fold sections animate in on scroll:

```css
.fade-in {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 300ms ease-out, transform 300ms ease-out;
}
.fade-in.visible {
  opacity: 1;
  transform: translateY(0);
}
```

Stagger cards/items by 60ms per item. Max stagger delay: 300ms total.

### Hover States

- Cards: `translateY(-2px)` + border-color brightens — never shift layout bounds
- Buttons: background darkens 10–15% — no size change
- Links: color shifts to `#FFFFFF` or `#00B7C2` depending on background — no underline in nav

---

## 7. Mobile-First Breakpoints

| Name | Breakpoint | Target |
|---|---|---|
| `xs` (base) | 0–479px | Small phones |
| `sm` | 480–767px | Large phones |
| `md` | 768–1023px | Tablets |
| `lg` | 1024–1279px | Small laptops |
| `xl` | 1280–1535px | Standard desktop |
| `2xl` | 1536px+ | Large screens |

**Development order:** Write all styles mobile-first (min-width queries, not max-width). Design review at 375px, 768px, 1280px.

**Critical mobile rules:**
- No horizontal scrolling at any breakpoint
- Touch targets: minimum 44px × 44px
- Font-size: minimum 16px on mobile (prevents browser zoom)
- Navigation always accessible via mobile menu — never hidden

---

## 7. Image and Icon Standards

### Photography Direction
All photography for Catalyst Works should pass this test: "Does this look like a person who knows what they're doing, or a stock photo of business?"

**Use:**
- Single-person portraits with clear, direct eye contact
- Real environments: offices, meetings, Africa-relevant contexts (markets, cities, boardrooms)
- Dark-toned or desaturated images that don't fight the dark navy palette
- Candid moments with a documentary quality
- Black and white photography when the content is serious/historical

**Never use:**
- Generic stock handshakes, team high-fives, or "diverse group around laptop"
- Bright white studio shots (too clinical against the navy palette)
- Cheesy motivational imagery (arrows going up, puzzle pieces, lightbulbs)
- Images where the person is looking at a phone or laptop as the main subject
- Any image that requires a caption explaining why it's relevant

### Image treatment on dark backgrounds
- Apply an overlay of `rgba(7, 26, 46, 0.4)` to integrate photos with the dark navy palette
- Alternatively: convert to duotone using `#071A2E` as shadow and `#00B7C2` as highlight

### Icons
- **Icon set:** Phosphor Icons (MIT license, 6 weights available) or Lucide Icons
- **Style:** Line weight — "Regular" (1.5px stroke equivalent)
- **Size:** 20px (inline UI), 24px (feature callout), 32–40px (hero/section icons)
- **Color:** `#00B7C2` on dark backgrounds, `#1E222A` on light backgrounds, `#B47C57` for warmth-context icons
- **Never:** Filled/solid icon sets, emoji icons, multi-color illustrative icons

---

## 8. Voice and Copy Standards for Web

### Headlines
The job of a headline is to make the next sentence necessary. It should state the benefit, the diagnosis, or the claim — not describe the page.

**Headline formulas that work:**
- The Diagnosis: "Your org chart changed. Your decision rights didn't."
- The Direct Claim: "Organizational clarity, built to last past the consultant's exit."
- The Specific Outcome: "Teams that know exactly who decides what — and why."
- The Contrast: "Not strategy frameworks. Working systems."

**Avoid:**
- "Welcome to Catalyst Works" (zero information)
- "Empowering organizations to achieve their full potential" (says nothing)
- "Your trusted partner in transformation" (every competitor says this)

### Subheads
One sentence. What the section delivers or what the visitor should understand after reading it. Not a repeat of the headline in different words.

### CTAs (Buttons and Links)
Match the action to the verb:
- Booking a call: "Book a discovery call" — not "Get started" or "Contact us"
- Learning more: "See how it works" — not "Click here" or "Read more"
- Downloading something: "Download the framework" — not "Submit"

### Microcopy (Form labels, error messages, helper text)
- Form labels: short, direct, no colons. "Your email" not "Email address:"
- Error messages: state what to do, not what went wrong. "Use a work email address" not "Invalid email format"
- Confirmation messages: specific. "Your message is on its way. Boubacar typically responds within 24 hours." not "Thank you for your submission."

### Body copy
Write at 9th-grade reading level. Short sentences. No jargon without a same-sentence explanation. When a paragraph is 4 lines long, ask if it can be 2.

---

## 9. Page Structure Templates

### Landing Page Structure

```
1. Nav bar (sticky, dark)
2. Hero section
   - Eyebrow tag + headline + subhead + CTA
   - Visual right (abstract or portrait)
3. Trust bar (logos of clients, "As seen in" media, or 3 KPI stats)
4. Problem / framing section
   - The specific problem Catalyst Works solves, stated plainly
   - 2-column: narrative left, supporting visual right
5. Services overview
   - 3-column card grid (service name, one-line description, link)
6. How it works / Process
   - 3-step horizontal timeline or numbered list with descriptions
7. Case study / Proof section
   - One detailed case study OR 2 shorter testimonials
8. About teaser (Boubacar)
   - Photo left, 3-sentence bio right, link to full about page
9. CTA section (full-width, dark background)
10. Footer
```

---

### Service Page Structure

```
1. Nav bar
2. Service hero
   - Narrow layout, centered
   - Service name (H1) + one-sentence description
   - Who this is for (one line, specific role/situation)
3. The problem this service solves
   - Narrative format, not bullets
4. The approach
   - How Catalyst Works does this differently (specific, not generic)
   - 3–4 step process or phases
5. What's included
   - Card grid or detailed list — specific deliverables
6. Case study or example outcome
7. Pricing or engagement model (if public)
8. FAQ section (4–6 questions)
9. CTA: "Start the conversation"
10. Footer
```

---

### About Page Structure

```
1. Nav bar
2. About hero
   - Portrait photo (left or center)
   - Name, title, one-sentence professional identity
3. Origin / story section
   - Where Boubacar comes from — professional and personal
   - Specific, not generic: what shaped the lens he brings to the work
4. The philosophy
   - What Catalyst Works believes about organizational change
   - In Boubacar's voice, not corporate-speak
5. Expertise and experience
   - Industries, geographies, scale of organizations
   - Presented as evidence, not a brag list
6. Recognition or media (if applicable)
7. CTA: "Let's talk"
8. Footer
```

---

## 10. What Makes a Catalyst Works Site Feel Like Catalyst Works

A Catalyst Works site is not like a Big Four firm (institutional, impersonal, generic) and not like a solo freelancer's portfolio (informal, hobbyist-feeling). It occupies a specific positioning: boutique, expert, direct.

### The signals that create that feeling

**Typography and space:** The generous whitespace and Inter's clean geometry signal premium positioning without luxury-brand pretension. Text breathes. Nothing competes.

**The navy base:** Dark backgrounds in hero, nav, and footer sections. This immediately separates the site from the white-background-with-blue-accents template look. The darkness communicates depth and seriousness.

**Specificity in the copy:** Every headline and subhead should contain a specific word that a generic competitor couldn't use without lying. "12 countries" — not "global." "Decision rights" — not "accountability." This is the single most important factor.

**Clay as humanity:** The `#B47C57` clay color appears as the border on testimonials, as the warmth accent in icon sets, in personal story sections. It signals that there's a real human behind the brand. It should appear on every page in at least one place.

**Photography with presence:** One real portrait of Boubacar, present on multiple pages (about, homepage, footer). Not a headshot — a working photo. Looking at camera or looking at something with focus. Full presence.

**CTAs that sound like invitations, not funnels:** "Start the conversation" and "Book a discovery call" — not "Get your free audit now" or "Transform your organization today."

### The test

If a designer swapped the Catalyst Works logo for a generic Big Four logo and the page still made sense — the design failed. The copy, color, and specificity should be inseparable from the brand.
