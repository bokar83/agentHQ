# humanatwork.ai — Site Design Spec
Date: 2026-04-19
Status: Approved for implementation

---

## Mission

Build the complete production website for humanatwork.ai. This is a destination, not a landing page. A scared worker who just got the AI transformation all-staff email lands here and finds: a clear assessment of their situation, a trusted voice who has been on both sides, a weekly intelligence update worth returning for, and a newsletter that delivers what leadership should already be saying out loud.

Single deliverable for launch: one index.html file. Complete. No placeholders except marked Beehiiv embed slots and GA4 tag slot.

---

## Who This Is For

Salaried workers aged 28 to 52. Operations, finance, marketing, HR, mid-level management. They just heard "AI transformation" or "efficiency initiative" at their company. They are quietly scared. They are not looking for inspiration. They are looking for someone who has been inside and will speak plainly.

They are also HR professionals. The site does not position itself as adversarial to HR. It positions itself as saying what leadership should already be saying out loud.

---

## Emotional Contract

Human support first. Intelligence second. The visitor lands and feels: "This person has been there. They are not selling me something. They are telling me the truth."

NOT: classified, edgy, insider cool, theatrical.
YES: warm, grounded, specific, earned authority.

The credibility comes from specificity, not credentials.

---

## The Hero Credential Sentence

Use verbatim in the hero section:

"I have been in those rooms. I have made those lists. I have also sat across the table from people and delivered the news. That experience is why I built this — not to expose anyone, but to make sure workers have what leadership should already be giving them."

Boubacar's philosophy (informs tone throughout, does not appear verbatim): restructuring is a last resort, done once and then given years to prove itself. Sitting across from someone and telling them their role is gone is one of the hardest things an HR leader does. This site exists because no one should be caught unprepared for that conversation.

---

## Page Hierarchy (Council-corrected order)

1. Nav — wordmark + single CTA
2. Hero — emotional hook, credential sentence, assessment CTA
3. Stats bar — three data points, counter animation
4. Weekly Signal — the return hook, updated every week with one intelligence update
5. Problem section — what is actually happening, Boubacar's pull quote
6. Assessment pitch — three cards, CTA
7. About — why this exists, video placeholder
8. Newsletter signup — the weekly brief
9. Article/content hub — below fold, grows over time, launch with 2 to 3 placeholder slots
10. FAQ — GEO optimized, full accordion
11. Footer

---

## Design Direction: Signal and Warmth

### Color System

```css
:root {
  --navy:        #0D1B2A;   /* hero, dark sections */
  --cream:       #FAF7F2;   /* light sections, warm not clinical */
  --amber:       #D4872A;   /* Boubacar signature, eyebrows, accents */
  --cyan:        #00B4C6;   /* interactive only: CTAs, focus, progress bar */
  --carbon:      #131920;   /* footer */
  --ink:         #1A1A1A;   /* body text on cream */
  --muted-dark:  rgba(255,255,255,0.52);
  --muted-light: rgba(26,26,26,0.55);
  --border-dark:  rgba(255,255,255,0.07);
  --border-light: rgba(26,26,26,0.09);
  --score-low:   #2ECC8A;   /* calm green for low exposure */
  --score-mid:   #E07B39;   /* orange for medium exposure */
  --score-high:  #C0392B;   /* serious red for high exposure */
}
```

### Typography

- Display/Headlines: Playfair Display, weight 700 and 900, italic for pull quotes
- UI and Body: Plus Jakarta Sans, weight 400/500/600
- Data/Score/Labels: DM Mono, weight 400/500

Google Fonts import:
```
https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Plus+Jakarta+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap
```

### Visual Signature

- Adinkra-inspired geometric grid: abstract interlocking rotated squares, SVG inline, 4% opacity, hero section only
- Grain texture: SVG noise filter pseudo-element, 3 to 5% opacity, all dark sections
- Amber left-border accent: 3px solid amber on pull quotes and key callouts, no background card
- Dot grid: radial gradient dot pattern, navy at 5% opacity, 24px spacing, cream sections
- Custom scrollbar: 4px wide, navy track, amber thumb
- Section transitions: straight cuts, alternating navy and cream, generous padding

### Animations (CSS-first, vanilla JS only)

- Hero rotating job titles: fade out/in every 2.8s, amber italic
- Staggered scroll reveals: translateY 24px to 0, opacity 0 to 1, IntersectionObserver, 80ms stagger, cubic-bezier(0.16,1,0.3,1)
- Stats counter: count up from 0 on scroll, 1.2s ease-out, DM Mono
- Assessment result reveal: 0.8s pause then card rises from below (translateY), feels like opening an envelope, then warm private-conversation result
- CTA pulse glow: box-shadow cyan, 3s loop, low amplitude
- Assessment progress bar: 3px cyan, fills left to right, 0.4s ease
- Nav links hover: amber underline slides in from left
- Answer options hover: cyan left border, 0.15s transition

---

## Weekly Signal Section (New — the return hook)

Position: between stats bar and problem section.

Design: cream background, full width. Left: date stamp in DM Mono amber. Headline in Playfair Display navy. One short paragraph (3 to 5 sentences) in Plus Jakarta Sans. Right: a "previous signals" list, 3 items, DM Mono, linked, muted. This section gets updated weekly. Same content as the LinkedIn post for that week, repurposed here.

This is what brings people back. No CMS required at launch — it is a static block in the HTML that Boubacar (or Claude) updates weekly in under five minutes.

Eyebrow: "This Week's Signal"
Date stamp format: DM Mono, amber, e.g. "APR 19 2026"
Right column label: "Previous Signals" with links to archived posts (can be LinkedIn URLs at launch)

---

## Assessment

Trigger: both CTAs open a full-screen overlay.
Background: navy, grain overlay, 100vw 100vh, z-index 1000.

### 10 Questions (verbatim from brief, no changes)

Scoring:
- Standard questions (Q1, Q2, Q3, Q5, Q7, Q8, Q9, Q10): A=0 B=1 C=2 D=3 E=4
- Q4 (restructure pattern): A=3 B=2 C=1 D=1 E=0
- Q6 (AI tool use): A=0 B=1 C=2 D=2 E=3
- Raw total: 0 to 40. Compress: Math.round(rawScore / 4). Final: 0 to 10.

### Result Reveal

0.8s weighted pause after final answer. Card rises from below (translateY 40px to 0, opacity 0 to 1, 0.6s ease). Feels like opening an envelope. No scan line. Warm, direct, private.

Result tiers:
- LOW (0 to 3): green left border, "You are better positioned than most"
- MEDIUM (4 to 6): orange left border, "You have a window. Use it now."
- HIGH (7 to 10): clay red left border, "The signals are real. Here is what to do."

Email capture below result: Beehiiv embed slot 1.

---

## Content Hub Section (New)

Position: between newsletter signup and FAQ.

Design: cream background, dot grid. Eyebrow: "From the Brief". Section header: "Recent Intelligence". Three article cards at launch — placeholder content with real titles from existing LinkedIn posts. Each card: amber top border, date in DM Mono, headline in Playfair Display, 2-sentence excerpt in Plus Jakarta Sans, "Read more" link in cyan.

This section grows as content is published. At launch it shows 3 slots. No CMS needed at launch — static HTML updated alongside the Weekly Signal.

---

## Copy Changes from Original Brief

| Original | Revised |
|----------|---------|
| "global HR director" | "global HR leader" |
| "HR won't brief" eyebrow | "What leadership should be saying out loud" |
| Hero credential (fabricated years/detail) | Version 3 verbatim (see above) |
| Classified/insider aesthetic | Human support first, intelligence second |
| Page order: stats, problem, assessment, about, newsletter | New order: hero, stats, weekly signal, problem, assessment, about, newsletter, content hub, FAQ, footer |

---

## Technical Specifications

- Single file: index.html
- No framework. Pure HTML, CSS, vanilla JavaScript.
- External resources: Google Fonts only
- All CSS inlined in style tag in head
- All JS at bottom of body, deferred
- No images except inline SVG icons
- Mobile first: 375px base, then 768px, then 1024px and above
- Assessment overlay scrollable on mobile
- Proper semantic HTML: one h1, h2 for sections, h3 for cards
- Landmarks: main, nav, footer, article
- FAQ: details and summary elements, JSON-LD FAQPage schema in head
- aria-label on all icon-only buttons
- role="dialog" and aria-modal="true" on assessment overlay
- Focus trap in assessment overlay
- prefers-reduced-motion respected for all animations
- preconnect links for Google Fonts CDN

---

## SEO and GEO

Title: "Human at Work | The AI Career Intelligence Brief by Boubacar"
Description: "Former global HR leader publishes the weekly brief your leadership should already be sending. Take the free AI Exposure Score and find out exactly where you stand and what to do about it."
Canonical: https://humanatwork.ai
JSON-LD: WebSite + FAQPage schemas
FAQ accordion uses details/summary for GEO indexing

---

## Placeholders (clearly marked in HTML comments)

1. Beehiiv embed 1: assessment result email capture
2. Beehiiv embed 2: newsletter section signup
3. GA4 tag: in head
4. Video embed: about section (Loom or YouTube, 60 to 90 seconds)
5. LinkedIn URL: footer and about section

---

## Files and Repo

Local folder: d:/Ai_Sandbox/agentsHQ/output/websites/humanatwork-site/
GitHub: https://github.com/bokar83/humanatwork-site
Deploy: Hostinger via GitHub integration (same pattern as catalystworks-site)

Required files at launch:
- index.html
- sitemap.xml
- robots.txt
- ads.txt (if AdSense later)

---

## Success Criteria

1. A scared worker lands on it and within 10 seconds understands: this person has been inside, they are not selling anything, they have something real to say.
2. The assessment draws them in because it asks questions only an insider would know to ask.
3. The result feels like a private conversation, not a quiz score.
4. They enter their email because the three moves feel worth having.
5. They come back next week because the Weekly Signal updated.
6. The site looks nothing like HRexposed.net, LinkedIn, a startup AI site, or a coaching template.
