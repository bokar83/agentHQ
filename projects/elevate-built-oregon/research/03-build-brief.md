# 03 - Website Build Brief

**Client:** Elevate Roofing & Construction LLC
**Date:** 2026-04-30
**Owner:** Rod (founder) - to approve before build
**Status:** ⛔ AWAITING APPROVAL - do not proceed to Phase 5 until Rod signs off

---

## Strategic Frame (one paragraph)

Elevate is a 20+ year owner-operator roofing/construction shop in Medford with strong reviews, an unusually broad service stack (roof + remodel + ADU + custom home), and a placeholder website that hides all of it. The Southern Oregon market is faceless - every top competitor is a navy-blue WordPress site with no founder, no drone, no video, no published prices. The strategic move is to be the only **owner-operator-led, full-stack, premium-feel** site in the market. Not the biggest. The most distinctive.

---

## 1. Design Direction

### Color palette

Drop the current 5-accent palette (royal blue + bright yellow + terracotta + tan + sky blue). Tighten to:

| Role | Color | Hex | Usage |
|---|---|---|---|
| **Ink** | Deep navy | `#0E2238` | Headlines, body text on light bg, dark sections |
| **Paper** | Warm off-white | `#F5F1EA` | Primary background, light sections |
| **Accent** | Warm copper | `#B8632B` | CTAs, eyebrows, accent borders, link underlines |
| **Accent light** | Soft copper | `#E2A57F` | Hover states, secondary accents |
| **Stone** | Warm gray | `#7A7570` | Muted text, subtitles |
| **Divider** | Sand | `#D9D2C5` | Dividers, card borders |
| **Card** | Pure paper | `#FFFDF7` | Card backgrounds, contrast cards |

**Rationale:** Every competitor leans cool corporate blue. Copper signals craft and warmth - directly differentiating from JAM (gray-navy), Pressure Point (bright blue), Rogue Valley (red-blue), Eric Preston (slate-blue). Navy retains industry expectation; copper carries the brand.

### Typography

| Role | Font | Weight | Notes |
|---|---|---|---|
| **Display** | Instrument Serif | 400 (regular + italic) | Hero, section H1/H2 |
| **Body** | Inter | 400, 500, 600 | All body, nav, UI |
| **Mono accent** | JetBrains Mono | 400 | License number, CCB#, project specs |

**Rationale:** All five competitors use sans-serif headings (Montserrat, Open Sans, Roboto). A serif display face is the single biggest visual differentiator and immediately reads premium. Inter for body is readable, modern, and load-efficient (one font family vs. the four currently loaded).

### Photography & asset direction

- **Hero:** Drone shot of a finished Elevate residential roof in Southern Oregon (Mount McLoughlin or Roxy Ann Peak in the distance). Shot at golden hour, warm light, real local landmark.
- **Founder portrait:** Rod, 3/4 turn, on a job site or in front of a finished home. Natural light. No corporate headshot lighting.
- **Project gallery:** Wide drone shots + tight detail shots (ridge cap, valley, finished gable). Before/after pairs where available.
- **Avoid:** stock construction imagery, hard hats over blueprints, smiling-people-with-arms-crossed corporate photos.

> ⚠️ Until real assets are shot, use clearly-marked placeholders with comments: `<!-- PLACEHOLDER: drone shot of finished Medford roof, golden hour, 16:9 -->`

### Animation direction

- GSAP + ScrollTrigger
- Hero: subtle parallax on drone shot, fade-up text reveal, CTA pulse on first scroll
- Section transitions: fade-up + slight Y translate on scroll into view
- Service cards: hover lift + accent border slide-in
- Numbers (years, projects, reviews): scroll-triggered count-up
- Reduced motion: respect `prefers-reduced-motion: reduce` and fall back to opacity-only fades

### What to AVOID (anti-patterns from the competitive set)

- ❌ Auto-rotating photo carousels in the hero (JAM, Rogue Valley)
- ❌ Banner-style headers with phone-number-top-right (every WordPress competitor)
- ❌ "We've got you covered" / "trusted partner" / "your vision is our mission" copy
- ❌ Generic stock photography
- ❌ Five-accent rainbow palettes
- ❌ Cookie-cutter "Free Estimate" CTA repeated 5x without variation
- ❌ Stock testimonial cards with no photos and no project context

---

## 2. Site Architecture

8 pages, indexed for local SEO. Service-area pages are the local-SEO lever every winning competitor pulls.

```
/                           Home (one-pager hub, not a brochure)
/services/                  Services overview (4 cards → 4 deep pages)
  ├── /services/roofing/        Residential + commercial, materials, warranty
  ├── /services/remodels-adus/  Remodels + ADU specifics
  ├── /services/new-homes/      Custom homes, design-build process
  └── /services/custom/         "Other Cool Stuff" - the unusual jobs
/portfolio/                 Project gallery (drone + detail shots)
/about/                     Rod's story, team, CCB#, certifications
/service-areas/             Hub
  ├── /service-areas/medford/
  ├── /service-areas/ashland/
  ├── /service-areas/grants-pass/
  ├── /service-areas/central-point/
  ├── /service-areas/jacksonville/
  └── /service-areas/klamath-falls/    ← whitespace, nobody owns this
/get-a-quote/               Cost-band tool + form + calendar
/contact/                   Phone, form, hours, address, map
```

**Nav:** Services · Portfolio · Service Areas · About · Get a Quote (CTA-styled)
**Footer nav:** all of the above + License #, social, legal

### Page hierarchy per page

Every page must include:
- One H1 (Elementor was likely emitting multiple - fix)
- Logical H2/H3 nesting
- Meta title + meta description (unique per page)
- Open Graph image + title + description
- Schema.org markup: `LocalBusiness` + `RoofingContractor` on home, `Service` on service pages, `Article` on any future blog posts
- Alt text on every image
- Canonical URL

---

## 3. Content Framework

### Homepage hero - three headline options

**Option A (whitespace play, recommended):**
> One builder. Roof to ADU to custom home.
> 20+ years across Southern Oregon - and the same hands on every job.

**Option B (founder-led):**
> If your roof or remodel isn't right, I personally make it right.
> - Rod, founder · Elevate Roofing & Construction · Medford, OR · CCB# 257092

**Option C (anchor + warmth, closest to current voice):**
> Built for what matters most.
> Premium roofing, remodels, and custom homes across Southern Oregon - done by the same crew, signed by the founder.

> **Recommendation:** Option A as primary headline + Option B as the founder-pledge sub-block lower in the hero. This stacks the unique full-stack positioning *and* the unique founder face.

### Sub-headline / hero supporting line

> Same crew on your roof, your remodel, and your new build. CCB# 257092 · Licensed, bonded & insured · Serving Medford, Ashland, Grants Pass & Klamath Falls.

### Primary CTA copy

- Primary: **"See if we're a fit →"** (links to /get-a-quote/)
- Secondary: **"Call Rod direct: 458-488-3710"** (tel: link)

> Avoid the generic "Get a Free Quote" - every competitor uses it. "See if we're a fit" reads as confidence + selectivity (the Hormozi qualifier move).

### Section-by-section copy outline

1. **Hero** - headline, sub, CTAs, founder pledge, drone background
2. **Trust strip** - CCB# 257092 · 20+ years · 5★ reviews · Licensed, bonded, insured · [GAF/OC cert when achieved]
3. **What we build** - 4 service cards (Roofing, Remodels & ADUs, New Homes, Custom Projects) with one-line voice-matched descriptions kept from current site
4. **The full-stack pitch** - One paragraph explaining why one builder for roof + remodel + ADU + new home means fewer subs, fewer handoffs, one warranty, one phone number
5. **Recent work** - 3-card portfolio teaser → /portfolio/
6. **Founder block** - Rod portrait + short story + signed pledge + link to /about/
7. **Service areas** - Visual map of Southern Oregon with city pills → /service-areas/[city]/
8. **Reviews** - 3 testimonials (existing Elana, Michael, Susan) + Google reviews link + (when wired) live count
9. **Cost-band tool teaser** - "What does this cost in Medford in 2026?" → /get-a-quote/
10. **CTA band** - Final close, dual CTA, phone number large
11. **Footer** - license, contact, nav, social

### SEO keyword targets per page

| Page | Primary KW | Secondary KW |
|---|---|---|
| Home | roofing contractor Medford OR | Southern Oregon roofing |
| /services/roofing/ | roof replacement Medford | metal roofing Southern Oregon |
| /services/remodels-adus/ | ADU builder Medford | home remodel Medford OR |
| /services/new-homes/ | custom home builder Jackson County | design-build home Southern Oregon |
| /services/custom/ | construction contractor Medford | custom build Southern Oregon |
| /service-areas/medford/ | Medford roofer | roofing contractor Medford |
| /service-areas/ashland/ | roofer Ashland OR | Ashland roof repair |
| /service-areas/grants-pass/ | roofing Grants Pass | Grants Pass contractor |
| /service-areas/klamath-falls/ | Klamath Falls roofer | roof repair Klamath Falls |
| /about/ | Rod Elevate Roofing | CCB 257092 |
| /portfolio/ | roofing projects Medford | custom homes Southern Oregon portfolio |

---

## 4. Conversion Playbook

### Primary conversion goal
Booked 15-min consultation (calendar appointment) - not a lead form. Calendar-first reduces back-and-forth and qualifies seriousness.

### Secondary goal
Phone call to 458-488-3710 (tracked).

### Lead capture strategy

1. **Cost-band tool** (the lead magnet): two-step - "What's the project?" → "What's the typical Medford 2026 range, and want to book 15 min with Rod?"
2. **Calendar widget** at /get-a-quote/ (Calendly or Cal.com, embedded)
3. **Tap-to-call** phone number persistent on mobile (sticky bottom bar on scroll)
4. **Contact form** as fallback - short: name, phone, project type, "anything we should know"

### Social proof plan

| Element | Where | Source |
|---|---|---|
| 3 named 5★ testimonials | Hero scroll-into-view | Existing site copy |
| Google Reviews live count + average | Trust strip + footer | Wire to Google Place API (post-launch) |
| CCB# 257092 | Trust strip + every footer | Always visible |
| Years claim | Hero subhead | "20+ years" |
| GAF Master Elite / OC Preferred badge | Trust strip | When achieved (note for Rod) |
| Project count | Trust strip | When portfolio is populated |

### Trust signals checklist (above the fold or one scroll down)

- [x] CCB# 257092 (license number)
- [x] "Licensed, Bonded & Insured"
- [x] 20+ years in business
- [x] 5★ rating
- [x] Founder face + name + signed pledge
- [ ] GAF Master Elite or Owens Corning Preferred badge (TODO for Rod - single biggest credibility win)
- [ ] BBB rating (apply if not already; A+ is the standard)
- [ ] Specific project count once portfolio loads

---

## 5. Technical Spec

- **Stack:** Static HTML + CSS + vanilla JS + GSAP + ScrollTrigger. No framework.
- **Hosting:** Vercel (preview-first, then production).
- **Analytics:** GA4 + Vercel Analytics
- **Forms:** Formspree or Netlify Forms (static-friendly), email to Rod's inbox + Notion/Airtable mirror
- **Calendar:** Cal.com or Calendly embed at /get-a-quote/
- **Schema:** RoofingContractor + LocalBusiness JSON-LD on home and contact
- **Sitemap:** sitemap.xml + robots.txt
- **Performance targets:** Lighthouse 90+ Performance, 100 Accessibility, 100 Best Practices, 95+ SEO
- **Browser support:** evergreen Chrome/Safari/Firefox/Edge, iOS 15+, Android Chrome 110+

---

## 6. What's NOT in v1 (deferred)

To keep scope tight and ship fast:

- Live Google Reviews API integration (use static testimonials at launch, wire later)
- Real cost-band tool with backend logic (use static published ranges + form, build interactive in v2)
- Blog (no posts yet - leave the IA hook so v2 can add it without rework)
- Spanish translation
- Portfolio CMS (start with hand-coded gallery, add Sanity/Contentful in v2)
- Live chat / chatbot

---

## 7. Open Questions for Rod (please confirm before build)

1. **Founder photo + drone shots** - do you have any to use, or should v1 ship with placeholder boxes that you swap in later?
2. **Manufacturer certifications** - do you currently hold GAF Master Elite, Owens Corning Preferred, or any other badge? If not, is that something we should plan to pursue?
3. **Service-area extent** - confirm the six cities listed (Medford, Ashland, Grants Pass, Central Point, Jacksonville, Klamath Falls). Missing anywhere? Drop anywhere?
4. **Phone number routing** - is 458-488-3710 your direct cell or a routed line? (Affects tap-to-call CTA copy.)
5. **Email** - the site currently shows a Cloudflare-protected email; what's the real address for form submissions?
6. **Calendar tool** - Cal.com or Calendly preference? Do you have an account already?
7. **License + insurance docs** - anything we should link to (PDF) for buyers who ask?
8. **Existing project photos** - any photos from past jobs we can use in the portfolio at launch?

---

## ⛔ APPROVAL CHECKPOINT

This brief locks the direction. Once approved, the build proceeds as specified - material direction changes after this point are expensive.

**Key decisions to confirm:**

1. **Palette:** Deep navy + warm copper + warm paper (replacing the current 5-color set) - ✅ / ❌
2. **Typography:** Instrument Serif (display) + Inter (body) - ✅ / ❌
3. **Hero positioning:** "One builder. Roof to ADU to custom home." + Rod's pledge - ✅ / ❌
4. **Architecture:** 8-page structure with city pages + cost-band tool - ✅ / ❌
5. **Tech stack:** Static HTML/CSS/JS + GSAP, Vercel hosting - ✅ / ❌

**Approve all five → I build. Push back on any → we adjust before building.**
