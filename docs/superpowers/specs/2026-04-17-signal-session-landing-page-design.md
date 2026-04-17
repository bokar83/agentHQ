# Signal Session Landing Page — Design Spec

**Date:** 2026-04-17
**Status:** Approved for implementation
**URL:** `catalystworks.consulting/ai-data-audit`
**File:** `output/websites/catalystworks-site/ai-data-audit.html`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A premium, conversion-first landing page for the Signal Session ($497 AI posture diagnostic) that ranks for professional services AI data risk queries and drives direct bookings via Calendly.

**Architecture:** Single HTML file with embedded CSS and vanilla JS. GSAP loaded via CDN. Matches the existing catalystworks.consulting design system exactly. Mobile-first (375px base), then 768px tablet, then 1280px desktop.

**Tech Stack:** HTML5, CSS custom properties, Inter + Plus Jakarta Sans + JetBrains Mono (Google Fonts), GSAP 3 + ScrollTrigger (CDN), GA4 (G-TBW90RVMM1), no framework, no build step.

---

## Brand System (Non-Negotiable)

```css
--navy:        #071A2E;   /* hero, nav, footer, dark sections */
--navy-darker: #0D1117;   /* GSAP section only */
--carbon:      #1E222A;   /* body text on light, gated download bg */
--cyan:        #00B7C2;   /* eyebrows, links, ghost btn border */
--cyan-hover:  #008F99;
--orange:      #FF7A00;   /* CTAs only, orange divider, risk tape dots */
--orange-hover:#E06900;
--clay:        #B47C57;   /* card borders, testimonial borders, warmth */
--mist:        #F3F6F9;   /* light section backgrounds */
--white:       #FFFFFF;   /* card surfaces */
--carbon-body: #1E222A;   /* body text on light */
--carbon-muted:#5A6272;   /* secondary text */
--amber:       #CC6600;   /* warning badges only — never red */
```

**Typography rules:**
- `Plus Jakarta Sans` (600/700/800) — ALL headlines, H1 through H3, card headings, price display, anchor stat
- `Inter` (400/500/600) — body copy, eyebrow labels, button labels, captions, fine print
- `JetBrains Mono` (400) — data callouts, price figure in hero strip, numbered item prefixes, source citations, badge text

**Hard rules:**
- No em dashes anywhere — not in copy, not in code comments
- No Inter at headline scale
- No shadow on every card (shadow only on primary CTA button)
- No three rounded boxes in a row
- No red tones — use `#CC6600` amber for warnings
- No generic CTAs — every button label is specific to this page
- No framework jargon — "AI governance", "compliance framework", "zero trust" never appear in copy

---

## Page Architecture (Finalized)

| # | Section | Background | Notes |
|---|---|---|---|
| 1 | Nav | `#071A2E` | Fixed, 68px, blur |
| 2 | Hero | `#071A2E` | Editorial C style |
| 3 | Risk tape | `#071A2E` | Scrolling marquee |
| 4 | Problem block | `#F3F6F9` | 3-4 sentences |
| 5 | What It Is | `#071A2E` | Plain English |
| 6 | Split panel | `#F3F6F9` | Prose left, diagnostic mock card right, testimonial below card |
| 7 | GSAP posture summary | `#0D1117` | Animated output reveal |
| 8 | Price block | `#071A2E` | $497, anchor stat above |
| 9 | SHIELD block | `#071A2E` | No price, text link CTA |
| 10 | Credibility block | `#F3F6F9` | 3-stat founder track record (replaces testimonials until real ones exist) |
| 11 | Gated download | `#1E222A` | Before footer, email only |
| 12 | FAQ | `#F3F6F9` | 3 questions, FAQPage schema |
| 13 | Footer | `#071A2E` | |

---

## SEO Requirements

**Slug:** `/ai-data-audit` (not `/governance` — weak, matches no search intent)

**Meta title:** `AI Data Exposure Audit for Professional Services Firms | Catalyst Works`

**Meta description:** `Find out which AI tools in your firm can access client data. The Signal Session is a 45-minute diagnostic with a written posture summary delivered in 24 hours. $497.`

**Canonical:** `https://catalystworks.consulting/ai-data-audit`

**H1:** The editorial hero headline (keeps conversion copy)

**H2s that target queries (in order of appearance):**
- Problem block: "AI Tools and Client Data Risk for Professional Services Firms"
- What It Is: "A 45-Minute Diagnostic. Eleven Questions. One Written Summary."
- GSAP section: "See the Output Before You Book"
- Price: "One Session. One Summary. One Fee."

**Schema markup:**
1. `Service` schema — name, provider, price ($497), description, duration (PT45M)
2. `FAQPage` schema — 3 questions (see FAQ section below)
3. `BreadcrumbList` — Home > AI Data Audit

**GA4:** Use existing `G-TBW90RVMM1` tag. Add event tracking for: Calendly CTA clicks, SHIELD inquiry link clicks, email form submissions.

---

## Section Specs

### 1. Nav

- `position: fixed`, `top: 0`, `z-index: 100`, full viewport width
- `height: 68px`, `background: rgba(7,26,46,0.92)`, `backdrop-filter: blur(16px)`
- `border-bottom: 1px solid rgba(255,255,255,0.06)`
- Inner: `max-width: 1100px`, `margin: 0 auto`, `padding: 0 24px`, flex row, space-between
- Logo left: "Catalyst Works" — Plus Jakarta Sans 700, 18px, `#FFFFFF`
- Right: ghost button
  - Label: "Book a Signal Session"
  - Style: `border: 1.5px solid #00B7C2`, `color: #00B7C2`, Inter 600 14px, `padding: 10px 22px`, `border-radius: 4px`
  - Hover: `background: rgba(0,183,194,0.08)`
- Mobile 375px: logo 16px, button label "Book Session"

---

### 2. Hero

- `background: #071A2E`, `min-height: 100vh`
- Padding: `calc(68px + 96px)` top, `80px` bottom
- Inner: `max-width: 1100px`, `margin: 0 auto`, `padding: 0 24px`
- Text column: `max-width: 760px`, `margin: 0 auto`, centered

**Eyebrow:**
- Text: "AI POSTURE DIAGNOSTIC"
- Inter 500, 13px, `letter-spacing: 0.12em`, `text-transform: uppercase`, `color: #00B7C2`
- Before eyebrow: `content: ''`, 22px wide, 1px tall, `background: #00B7C2`, inline-flex
- `margin-bottom: 24px`

**H1 (single element, two visual parts):**
```html
<h1>
  You have AI tools touching client data.
  <em>Most firms can name three. The average is twenty.</em>
</h1>
```
- Part 1: Plus Jakarta Sans 800, 64px (desktop) / 38px (mobile), `#FFFFFF`, `letter-spacing: -0.03em`, `line-height: 1.08`
- `<em>`: Plus Jakarta Sans 600 italic, 56px (desktop) / 32px (mobile), `#B47C57`, `line-height: 1.15`
- `margin-bottom: 32px`
- Tablet 768px: Part 1 52px, em 44px

**Founder credential (one line, below H1):**
- Text: "Boubacar Barry has mapped AI exposure across firms in four continents — most could not name their own tools."
- Inter 400, 15px, `#F3F6F9` at `opacity: 0.55`, `margin-bottom: 24px`
- Max-width: 580px

**Orange divider:**
- `width: 64px`, `height: 3px`, `background: #FF7A00`, `margin: 0 0 32px 0`, left-aligned

**Subhead:**
- Text: "Find out exactly which AI tools have access to your client data — and what to do about it first."
- Inter 400, 20px (desktop) / 17px (mobile), `line-height: 1.6`, `#F3F6F9` at `opacity: 0.82`
- `margin-bottom: 40px`

**CTA row:**
- `display: flex`, `align-items: center`, `gap: 20px`, `flex-wrap: wrap`
- Primary button: "Book a Signal Session" — see Component Specs
- Price inline: Inter 500, 16px, `#F3F6F9` at `opacity: 0.6` — text: "One-time. $497."
- Mobile: stacked, button full width, price centered below

**Data callout strip:**
- `margin-top: 80px`, `border-top: 1px solid rgba(255,255,255,0.08)`, `padding-top: 40px`
- 4 equal columns, `border-right: 1px solid rgba(255,255,255,0.08)` on cols 1-3
- Each cell centered, `padding: 0 32px`

| Value | Label |
|---|---|
| 45 | Structured minutes |
| 11 | Diagnostic questions |
| 24hr | Written summary |
| $497 | Flat fee |

- Value: JetBrains Mono 400, 36px (desktop) / 28px (mobile), `#00B7C2`
- Label: Inter 400, 13px, `#F3F6F9` at `opacity: 0.55`, `margin-top: 8px`
- Mobile: 2x2 grid, no right borders, bottom border between rows

---

### 3. Risk Tape (Scrolling Marquee)

- Full viewport width, `background: #071A2E`
- `height: 48px`, `overflow: hidden`, `border-top: 1px solid rgba(255,255,255,0.06)`, `border-bottom: 1px solid rgba(255,255,255,0.06)`
- Inner track: `display: flex`, `width: max-content`, `animation: marquee 40s linear infinite`
- Pause on hover: `.risk-tape:hover .tape-track { animation-play-state: paused }`

**Phrases (duplicate array for seamless loop):**
```
Unaudited vendor LLM access
Shadow AI in client intake flows
No retention policy on chat logs
Third-party model trained on your data
AI scheduling tool connected to client portal
Undisclosed AI in client deliverables
CRM with AI layer nobody configured
Email AI reading privileged correspondence
Document review tool with third-party indexing
Drafting assistant synced to full inbox
```

- Separator between phrases: 6px circle, `background: #FF7A00`, `margin: 0 20px`, vertically centered
- Text: Plus Jakarta Sans 700, 13px, `#F3F6F9` at `opacity: 0.7`, `text-transform: uppercase`, `letter-spacing: 0.1em`

```css
@keyframes marquee {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); } /* -50% because array is doubled */
}
```

---

### 4. Problem Block

- `background: #F3F6F9`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- Inner: `max-width: 720px`, `margin: 0 auto`, centered text

**Eyebrow:** "THE REALITY FOR MOST FIRMS" — Inter 500, 12px, `#B47C57`, `letter-spacing: 0.14em`, uppercase, `margin-bottom: 20px`

**H2 (SEO-targeted):**
- Text: "AI Tools and Client Data Risk for Professional Services Firms"
- Plus Jakarta Sans 700, 26px (desktop) / 22px (mobile), `#1E222A`, `margin-bottom: 20px`
- This is visually secondary — not the visual anchor but present for SEO H2 hierarchy

**Primary prose:**
- Plus Jakarta Sans 600, 26px (desktop) / 20px (mobile), `line-height: 1.55`, `#1E222A`
- Text: "Your team adopted AI tools quickly. That was the right call. But most of those tools were never configured for a firm that handles other people's information — and nobody has gone back to check."
- `margin-bottom: 20px`

**Secondary prose:**
- Inter 400, 17px (desktop) / 15px (mobile), `line-height: 1.7`, `#5A6272`
- Text: "The question is not whether AI is in your workflow. It is what it can see, where it sends data, and whether you can answer for it if a client asks."

---

### 5. What It Is

- `background: #071A2E`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- Inner: `max-width: 680px`, `margin: 0 auto`, centered

**Eyebrow:** "WHAT THE SIGNAL SESSION IS" — Inter 500, 12px, `#00B7C2`, `letter-spacing: 0.14em`, uppercase, `margin-bottom: 20px`

**H2:**
- Text: "A 45-Minute Diagnostic. Eleven Questions. One Written Summary."
- Plus Jakarta Sans 700, 40px (desktop) / 28px (mobile), `#F3F6F9`, `line-height: 1.2`, `margin-bottom: 24px`

**Body:**
- Inter 400, 17px (desktop) / 15px (mobile), `line-height: 1.7`, `#F3F6F9` at `opacity: 0.78`
- Text: "We go through every AI-adjacent tool in your workflow — email, drafting, scheduling, CRM, document review — and score each one against a single posture standard. No jargon. No 300-page framework. You get a one-page written summary that tells you exactly where you stand and what to fix first."

---

### 6. Split Panel

- `background: #F3F6F9`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- Inner: `max-width: 1100px`, `margin: 0 auto`
- Grid: `grid-template-columns: 1fr 1fr`, `gap: 64px`, `align-items: start`
- Mobile: single column, prose first then card

**Left — Problem Prose:**

Eyebrow: "WHY THIS MATTERS NOW" — Inter 500, 12px, `#B47C57`, uppercase, `letter-spacing: 0.14em`, `margin-bottom: 20px`

H3: "The tools are already in. The question is what they can reach."
- Plus Jakarta Sans 700, 32px (desktop) / 24px (mobile), `#1E222A`, `line-height: 1.2`, `margin-bottom: 20px`

Body:
- Inter 400, 16px, `line-height: 1.75`, `#5A6272`
- Text: "Most professional services firms adopted AI tools one at a time, team by team, without a firm-level view of what any of them can access. A drafting assistant that syncs your inbox. A scheduling tool connected to your client portal. A CRM with an AI layer nobody configured. None of them are problems individually. Together, they are an exposure you have not priced yet."

**Right — Diagnostic Output Mock Card:**

Card styles:
```css
background: #FFFFFF;
border-left: 3px solid #B47C57;
border-radius: 2px;
padding: 40px 36px; /* desktop */
/* no box-shadow */
```

Card heading: "What the session surfaces" — Plus Jakarta Sans 700, 22px, `#1E222A`, `margin-bottom: 24px`

Divider: `1px solid rgba(180,124,87,0.2)`, `margin-bottom: 24px`

Two-column diagnostic mock table:

Column headers:
- "SURFACE": Inter 600, 11px, `#5A6272`, uppercase, `letter-spacing: 0.1em`
- "STATUS": same style

Three rows:

| Surface | Status badge |
|---|---|
| Client intake flow / AI-assisted | `Undisclosed` — amber `#CC6600`, bg `#FFF3E0`, border `1px solid #CC6600` |
| Contract review tool | `Vendor-managed` — cyan `#007A82`, bg `#E0F7FA`, border `1px solid #00B7C2` |
| Internal knowledge base | `Unaudited` — orange `#FF7A00`, bg `#FFF3E0`, border `1px solid #FF7A00` |

Row styles:
- `padding: 10px 0`, `border-bottom: 1px solid rgba(0,0,0,0.05)`
- Surface text: Inter 500, 14px, `#1E222A`
- Badge: JetBrains Mono 400 11px, `border-radius: 4px`, `padding: 3px 8px`

Disclaimer below table:
- Inter 400 italic, 12px, `#5A6272`, `margin-top: 12px`
- Text: "Composite example. Real outputs are firm-specific."

Price footer inside card:
- `border-top: 1px solid rgba(180,124,87,0.2)`, `margin-top: 28px`, `padding-top: 24px`
- Price: JetBrains Mono 400, 28px, `#1E222A` — "$497"
- Label: Inter 400, 13px, `#5A6272` — "One-time. No retainer."
- Primary button: full width, `margin-top: 20px` — "Book a Signal Session"

**Below the right card — Founder signal (replaces testimonial until real ones exist):**
- No card chrome — left-border Clay line only
- `border-left: 3px solid #B47C57`, `padding-left: 16px`, `margin-top: 32px`
- Text: Inter 400 italic, 15px, `#5A6272`, `line-height: 1.6`
- Content: "Boubacar Barry has mapped AI tool exposure across organizations in four continents. Most could not name their own tools."
- Attribution line: Inter 600, 13px, `#1E222A`, `margin-top: 8px` — "Boubacar Barry, Catalyst Works Consulting"
- Note: Replace with first real testimonial quote when available.

---

### 7. GSAP Animated Posture Summary

- `background: #0D1117`, `padding: 120px 24px` (desktop) / `80px 20px` (mobile)
- Inner: `max-width: 900px`, `margin: 0 auto`

**Section eyebrow:** "SEE THE OUTPUT BEFORE YOU BOOK" — Inter 500, 12px, `#00B7C2`, uppercase, `margin-bottom: 16px`

**H2:**
- "This is what lands in your inbox within 24 hours."
- Plus Jakarta Sans 700, 36px (desktop) / 26px (mobile), `#F3F6F9`, `margin-bottom: 64px`

**Document frame:**
```css
max-width: 680px;
margin: 0 auto;
background: rgba(255,255,255,0.03);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 4px;
padding: 48px;  /* desktop */
padding: 28px 20px;  /* mobile */
```

**Static fallback:** A `<noscript>` or `.gsap-fallback` div showing a screenshot/static version of the document frame. Renders immediately. Hidden when GSAP loads successfully.

**GSAP setup:**
```js
// All timelines registered on window.__timelines
// ScrollTrigger: start "top 65%", no scrub, plays once
// Initial delay: 0.4s after trigger fires
```

**Scene timeline:**

Scene 1 — Document header (static, visible before animation):
- "SIGNAL SESSION POSTURE SUMMARY" — JetBrains Mono 400, 11px, `#00B7C2`, uppercase, `letter-spacing: 0.1em`
- "Prepared by Catalyst Works Consulting" — Inter 400, 11px, `#5A6272`
- Divider: `1px solid rgba(255,255,255,0.08)`, `margin: 16px 0 24px`

Scene 2 — Client block: `delay: 0.4s`, `duration: 0.4s`, fadeUp (`y: 16→0, opacity: 0→1, ease: power2.out`)
```
CLIENT            Meridian Legal Partners
DATE              April 2026
SESSION DURATION  45 minutes
```
Labels: JetBrains Mono 400, 11px, `#5A6272`. Values: Inter 500, 13px, `#F3F6F9` at 0.85.

Scene 3 — "AI TOOLS IDENTIFIED" eyebrow: `start: 1.0s`, `duration: 0.3s`, fadeUp
- Inter 600, 11px, `#00B7C2`, uppercase, `letter-spacing: 0.12em`
- Underline: `1px solid rgba(0,183,194,0.3)`, fades with text

Scene 4 — Tool rows (5 items), `start: 1.4s`, `stagger: 0.18s`, `duration: 0.35s` each, fadeUp (`y: 8→0`)

| Tool | Data Access | Status | Badge color |
|---|---|---|---|
| ChatGPT (OpenAI) | CLIENT DATA ACCESS: YES | REVIEW NEEDED | `#FF7A00` |
| Copilot (Microsoft) | CLIENT DATA ACCESS: YES | CONFIGURED | `#00B7C2` |
| Calendly AI | CLIENT DATA ACCESS: YES | EXPOSED | `#CC6600` |
| Otter.ai | CLIENT DATA ACCESS: YES | NOT REVIEWED | `#5A6272` |
| Notion AI | CLIENT DATA ACCESS: YES | CONFIGURED | `#00B7C2` |

Row: `display: flex`, `justify-content: space-between`, `padding: 10px 0`, `border-bottom: 1px solid rgba(255,255,255,0.04)`
Tool name: Inter 500, 13px, `#F3F6F9` at 0.85. Status: JetBrains Mono 400, 11px, color per table.

Scene 5 — "POSTURE SCORE" eyebrow: `start: 2.6s`, same as Scene 3 style

Scene 6 — Score counter: `start: 2.9s`, `duration: 0.6s`
- GSAP counter 0→62, `snap: 1`, `ease: power1.inOut`
- Display: JetBrains Mono 400, 48px, `#FF7A00`
- Label: Inter 400, 13px, `#5A6272` — "out of 100 — 3 tools require immediate action"

Scene 7 — "RECOMMENDED ACTIONS" eyebrow + 3 items: `start: 3.8s`, `stagger: 0.22s`
```
01  Disconnect Otter.ai from shared client meeting calendar immediately.
02  Enable tenant isolation in Microsoft Copilot — IT action required within 7 days.
03  Review Calendly AI data retention settings before next client onboarding.
```
Number: JetBrains Mono 400, 12px, `#B47C57`. Action: Inter 400, 13px, `#F3F6F9` at 0.8, `line-height: 1.6`.

Scene 8 — Signature: `start: 5.2s`, `duration: 0.5s`, `opacity: 0→1` only (no y movement)
- Separator `1px solid rgba(255,255,255,0.08)` fades in simultaneously
- "Boubacar Barry, Catalyst Works Consulting — catalystworks.consulting"
- Inter 400, 12px, `#5A6272`

Scene 9 — Pull prompt (optional, fires at 6.5s):
- "Yours looks different. Book a session to find out what it says."
- Inter 400, 15px, `#F3F6F9` at `opacity: 0.7`, below the document frame
- `opacity: 0→0.7`, `duration: 0.8s`

---

### 8. Price Block

- `background: #071A2E`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- Inner: `max-width: 640px`, `margin: 0 auto`, centered

**Eyebrow:** "ONE FLAT FEE" — Inter 500, 12px, `#B47C57`, uppercase, `letter-spacing: 0.14em`, `margin-bottom: 20px`

**Cost-of-delay anchor (above price):**
- Text: "One undisclosed AI tool in a client engagement costs an average of $14,000 in remediation."
- Plus Jakarta Sans 600, 18px, `#F3F6F9`, `line-height: 1.5`, `margin-bottom: 8px`
- Source citation: JetBrains Mono 400, 11px, `#5A6272` — "IBM Cost of a Data Breach Report, 2024"
- `margin-bottom: 40px`

**Price:**
- "$497" — Plus Jakarta Sans 800, 80px (desktop) / 56px (mobile), `#F3F6F9`, `line-height: 1`
- Below: Inter 400, 16px, `#F3F6F9` at `opacity: 0.55` — "No retainer. No follow-up pitch. One session, one summary, one fee."
- `margin-bottom: 40px`

**CTA:** "Reserve my diagnostic" (primary button, centered, `max-width: 360px`)

**Reassurance line below button:**
- Inter 400, 13px, `#5A6272`, `margin-top: 16px`
- "Booked within 48 hours. Payment via Stripe. Receipt sent immediately."

---

### 9. SHIELD Block

- `background: #071A2E`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- `border-top: 1px solid rgba(255,255,255,0.06)`
- Inner: `max-width: 680px`, `margin: 0 auto`, centered

**No eyebrow.** The section opens with a narrative paragraph.

**Opening (the "what comes after" frame):**
- Plus Jakarta Sans 600, 22px (desktop) / 18px (mobile), `#F3F6F9`, `max-width: 620px`, centered, `line-height: 1.5`, `margin-bottom: 24px`
- Text: "Most firms who complete a Signal Session know exactly where they stand. Some act on it themselves. Others want a partner in the room."

**Supporting copy:**
- Inter 400, 16px, `#B0BAC8` (lighter than full body — recessive), `line-height: 1.7`, `margin-bottom: 32px`
- Text: "The SHIELD Assessment is the structured follow-on. A deeper engagement for firms where the Signal Session identified exposures that need a deliberate remediation plan. Not a retainer. Not a framework. A specific piece of work with a defined end."

**CTA (text link, not button):**
- "Tell me what SHIELD looks like for my firm"
- Inter 600, 15px, `#00B7C2`, `text-decoration: none`
- Hover: `text-decoration: underline`
- Links to: `mailto:catalystworks.ai@gmail.com?subject=SHIELD Assessment inquiry` (placeholder until contact form exists)
- No button chrome, no arrow, no box

---

### 10. Credibility Block (replaces social proof — no testimonials yet)

No testimonials exist. Do not use placeholders. This section builds trust through specificity of track record and methodology instead.

- `background: #F3F6F9`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- Inner: `max-width: 1100px`, `margin: 0 auto`

**Eyebrow (centered above):** "WHY THESE QUESTIONS" — Inter 500, 12px, `#B47C57`, uppercase, `letter-spacing: 0.14em`, `margin-bottom: 16px`

**Section heading:**
- "The Signal Session was not designed in a conference room."
- Plus Jakarta Sans 700, 36px (desktop) / 26px (mobile), `#1E222A`, `text-align: center`, `max-width: 680px`, `margin: 0 auto 16px`

**Section subhead:**
- "It was built from two decades of operational work inside organizations that had the same problem — and could not name it yet."
- Inter 400, 18px, `#5A6272`, `text-align: center`, `max-width: 560px`, `margin: 0 auto 64px`, `line-height: 1.7`

**Three-item credential grid:**
- `grid-template-columns: repeat(3, 1fr)`, `gap: 40px`
- Mobile: single column. Tablet 768px: single column. Desktop 1280px: 3 columns.

Each item — no card chrome, no borders, left-aligned:

**Item 1:**
- Stat: "20+" — JetBrains Mono 400, 48px, `#00B7C2`
- Label: Plus Jakarta Sans 700, 16px, `#1E222A`, `margin-top: 8px` — "Years of operational diagnostic work"
- Body: Inter 400, 15px, `#5A6272`, `line-height: 1.7`, `margin-top: 8px` — "Built across GE, international development organizations, and advisory engagements in the US, Europe, the Middle East, and West Africa."

**Item 2:**
- Stat: "4" — JetBrains Mono 400, 48px, `#00B7C2`
- Label: Plus Jakarta Sans 700, 16px, `#1E222A`, `margin-top: 8px` — "Continents. One diagnostic standard."
- Body: Inter 400, 15px, `#5A6272`, `line-height: 1.7`, `margin-top: 8px` — "The 11 questions in the Signal Session were refined across organizations that varied in size, sector, and geography — but shared the same blind spot about what their systems could reach."

**Item 3:**
- Stat: "11" — JetBrains Mono 400, 48px, `#00B7C2`
- Label: Plus Jakarta Sans 700, 16px, `#1E222A`, `margin-top: 8px` — "Questions. Not a questionnaire."
- Body: Inter 400, 15px, `#5A6272`, `line-height: 1.7`, `margin-top: 8px` — "Each question was kept because it surfaces something that every other question misses. Nothing was added for comprehensiveness. Nothing was kept for comfort."

**Clay accent rule above each stat:** `width: 24px`, `height: 2px`, `background: #B47C57`, `margin-bottom: 16px`

**Note:** When real testimonials exist, this section is replaced with the expanded testimonial card format (quote + firm profile + outcome). The credibility block is the interim trust anchor, not a permanent fixture.

---

### 11. Gated Download

- `background: #1E222A`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- Inner: `max-width: 560px`, `margin: 0 auto`, centered

**Eyebrow:** "FREE SELF-ASSESSMENT" — Inter 500, 12px, `#00B7C2`, uppercase, `letter-spacing: 0.14em`, `margin-bottom: 20px`

**H2:** "15 questions to run on your own first." — Plus Jakarta Sans 700, 32px (desktop) / 24px (mobile), `#F3F6F9`, `margin-bottom: 16px`

**Body:** "Not a sales sequence. One email with the PDF." — Inter 400, 16px, `#F3F6F9` at `opacity: 0.65`, `margin-bottom: 36px`

**Form:**
```html
<form class="capture-form">
  <div class="form-row">
    <input type="email" placeholder="Work email" required>
    <button type="submit">Send me the assessment</button>
  </div>
  <p class="fine-print">Your email goes nowhere else.</p>
</form>
```
- Desktop: flex row, `gap: 12px`
- Mobile: stacked, button full width
- Input: `height: 52px`, `background: rgba(255,255,255,0.06)`, `border: 1px solid rgba(255,255,255,0.12)`, `border-radius: 4px`, Inter 400 16px, `color: #F3F6F9`
- Input focus: `border-color: #00B7C2`, `background: rgba(0,183,194,0.05)`
- Button: ghost style (cyan border/text), `height: 52px`, `padding: 0 28px`
- Fine print: Inter 400, 12px, `#5A6272`, `margin-top: 12px`, centered

---

### 12. FAQ

- `background: #F3F6F9`, `padding: 96px 24px` (desktop) / `64px 20px` (mobile)
- Inner: `max-width: 720px`, `margin: 0 auto`

**Eyebrow:** "COMMON QUESTIONS" — Inter 500, 12px, `#B47C57`, uppercase, `margin-bottom: 32px`

**Three questions (collapsible `<details>` elements):**

1. Q: "Do I need a technical background to get value from the session?"
   A: "No. The session is a structured conversation, not a technical audit. You describe your workflow. I translate it into a posture assessment you can act on."

2. Q: "What happens if we find something serious?"
   A: "The summary tells you what it is and what to do first. For firms where the findings require a structured remediation plan, there is a next-step engagement. The Signal Session always delivers value on its own."

3. Q: "Is the written summary confidential?"
   A: "Yes. Everything discussed in the session and documented in the summary stays between us. The summary is yours to share — or not — as you see fit."

**Styling:**
- `<details>`: `border-bottom: 1px solid rgba(0,0,0,0.08)`, no background change
- `<summary>`: Plus Jakarta Sans 600, 18px, `#1E222A`, `padding: 20px 0`, `cursor: pointer`, `list-style: none`
- Answer: Inter 400, 16px, `#5A6272`, `line-height: 1.7`, `padding-bottom: 20px`

**FAQPage schema:** Generated in `<script type="application/ld+json">` using these three Q&As.

---

### 13. Footer

- `background: #071A2E`, `border-top: 1px solid rgba(255,255,255,0.06)`, `padding: 48px 24px`
- Inner: `max-width: 1100px`, `margin: 0 auto`
- Desktop: flex row, space-between
- Mobile: stacked, centered, `gap: 12px`

- Left: "Boubacar Barry — Catalyst Works Consulting"
- Center: "catalystworks.consulting"
- Right: "2026 Catalyst Works Consulting"
- All: Inter 400, 13-14px, `#5A6272`

---

## Component Specs

### Primary Button
```css
background: #FF7A00;
color: #FFFFFF;
font: 600 15px/1 'Inter', sans-serif;
letter-spacing: 0.01em;
padding: 14px 32px;
border-radius: 4px;
border: none;
box-shadow: 0 4px 24px rgba(255,122,0,0.22);
cursor: pointer;
transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.15s ease;
```
Hover: `background: #E06900`, `box-shadow: 0 8px 32px rgba(255,122,0,0.32)`, `transform: translateY(-1px)`
Active: `background: #CC6200`, `box-shadow: none`, `transform: none`

**Button label conventions (specific to this page):**
- Nav: "Book a Signal Session"
- Hero: "Book a Signal Session"
- Split panel card: "Book a Signal Session"
- Price block: "Reserve my diagnostic"

### Ghost Button
```css
background: transparent;
color: #00B7C2;
font: 600 15px/1 'Inter', sans-serif;
padding: 13px 32px;
border-radius: 4px;
border: 1.5px solid #00B7C2;
cursor: pointer;
transition: background 0.18s ease;
```
Hover: `background: rgba(0,183,194,0.08)`

---

## Anti-Patterns — Do Not Do These

1. **Do not put any color behind the data callout values in the hero strip.** JetBrains Mono cyan numbers on plain navy is the payoff. No pill backgrounds, no icon circles, no colored containers.

2. **Do not animate anything outside the GSAP posture summary section.** No scroll-triggered fade-ins, no parallax, no staggered hero reveals. One cinematic moment per page. Two compete.

3. **Do not write any headline that describes the product instead of the reader's situation.** "Get an AI posture assessment" is a feature description. "You have AI tools touching client data" is the reader's situation. Every headline must pass: does this describe what I do, or what they already suspect about themselves?

---

## Self-Scoring Checklist — Before Calling It Done

- [ ] **Font check at 1280px:** Every H1/H2/H3 renders in Plus Jakarta Sans. No Inter at headline scale. Check computed font-family in DevTools.
- [ ] **Orange budget:** Exactly 4 orange elements on the page: hero divider line, hero CTA button, split panel card CTA button, price block CTA button. Count them. Fifth orange element = remove it.
- [ ] **GSAP mobile:** Load at 375px, watch sequence play. Document frame does not overflow. Tool name rows do not clip. If two-column label/value layout breaks, switch to stacked at mobile.
- [ ] **Em dash audit:** Browser Find for "—" and "--". Count must be zero in all rendered text.
- [ ] **Mobile-first verification:** Test all three breakpoints (375px, 768px, 1280px) before marking complete. Hero, split panel, and social proof grid all reflow correctly.
- [ ] **SEO check:** H1, H2s, meta title, meta description, and schema markup are all present. `/ai-data-audit` canonical is correct.
- [ ] **GSAP fallback:** Static document frame renders immediately on page load before JS executes. Animation is additive, not load-bearing.

---

## Placeholders to Swap Before Deploy

| Placeholder | Location | Replace with |
|---|---|---|
| `#CALENDLY_URL` | Hero CTA, split panel card CTA, price block CTA | Real Calendly link |
| Credibility block stats/copy | Section 10 | Replace entire section with real testimonial cards (quote + firm profile + outcome format) when first clients complete sessions |
| `mailto:catalystworks.ai@gmail.com?subject=SHIELD...` | SHIELD text link | Contact form or Cal.com link |
| PDF download | Gated download form | Actual self-assessment PDF hosted at catalystworks.consulting/ai-self-assessment.pdf |
