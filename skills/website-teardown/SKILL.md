---
name: website-teardown
description: 6-phase pipeline that audits a prospect website and produces an internal viability report (PURSUE/DROP verdict, price band) plus a client-facing teardown report with before/after mockup. Triggers on "website-teardown", "teardown this site", "audit this prospect site", "run a teardown", "should we pursue this lead", "is this site worth pursuing", or /website-teardown URL.
---

# website-teardown

**Trigger:** `/website-teardown URL` or "teardown DOMAIN"

**What it is:** Thin orchestrator. Chains 5 existing skills in a 6-phase pipeline. No analytical logic lives here: every audit step delegates to the source skill. Produces two reports from one research pass.

**Accept criterion (before claiming task complete):**

- Both HTML report files exist in `deliverables/teardowns/<slug>/`
- Internal report contains verdict (PURSUE / DROP), score, price band
- Client report contains zero internal framing, verdict, or price data
- Em-dash sweep on both files passes
- Before/after mockup renders in browser

---

## Inputs

| Form             | Example                        |
| ---------------- | ------------------------------ |
| URL (default)    | `https://example.com`          |
| Local repo path  | `output/websites/client-site/` |
| Single HTML file | `output/pages/homepage.html`   |

## Outputs

Both written to `deliverables/teardowns/<slug>/`:

| File                             | Audience      | Contains                                                                    |
| -------------------------------- | ------------- | --------------------------------------------------------------------------- |
| `internal-viability-report.html` | Boubacar only | Verdict, fit signals, scope estimate, price band, weighted score, red flags |
| `client-teardown-report.html`    | Prospect      | Brand snapshot, craft gap, market gap, SEO audit, before/after mockup, CTA |

**Hard rule:** Internal framing (PURSUE/DROP verdict, price estimate, red flags) must NEVER appear in the client report. Same research, different lens.

---

## 6-Phase Pipeline

### Phase 1: Brand and Competitor Intelligence

**Delegates to:** `website-intelligence` (invoke skill)

Run `website-intelligence` against the target URL. Extract:

- Brand snapshot: name, tagline, offer, CTA, voice
- Top 3 competitors (by SerpApi / Serper search on primary keyword)
- Craft gap relative to competitors
- Market gap (what competitors claim that the target does not)

Capture output as `research/brand-intel.md` in the deliverable folder.

### Phase 2: UX and Accessibility Audit

**Delegates to:** `web-design-guidelines` (invoke skill)

Run `web-design-guidelines` audit against the target. Score across:

- Layout and visual hierarchy
- Typography legibility
- Color contrast (WCAG AA minimum)
- Mobile responsiveness
- CTA clarity and placement
- Accessibility (alt text, label/input pairing, focus states)

Capture findings as `research/ux-audit.md`. Note PASS / FAIL per dimension.

### Phase 3: SEO and GEO Audit

**Delegates to:** `seo-strategy` Mode 2 (full site SEO audit)

Run `seo-strategy` in full-audit mode. Check:

- Title tag, meta description, canonical
- JSON-LD schema (type, completeness, em-dash contamination)
- Local SEO signals (NAP, areaServed, city entities)
- Core Web Vitals proxy (Lighthouse mobile Performance, LCP, CLS)
- AI search visibility (citation-ready headings, FAQ schema, structured prose)
- Internal linking and orphan pages

Capture as `research/seo-audit.md`.

### Phase 4: Before/After Hero Mockup

**Delegates to:** `kie_media` (invoke skill, Studio Art Direction mode off)

Generate two hero images:

1. `mockups/before-hero.png`: reconstruct the current site visual aesthetic (flat, generic, dated; match the actual site energy, not a cartoon of it)
2. `mockups/after-hero.png`: reimagined hero using Catalyst Works design language (dark theme, strong typography, focused CTA)

Use the structured 6-field Kie prompt template from `skills/frontend-design/SKILL.md`:

- Composition Anchor
- Subject
- Lighting/Mood
- Palette
- Background Mode
- Anti-Slop Prohibition

Then build `mockups/before-after.html` (drag slider comparing before/after). Use the slider component from `skills/signal-works-conversion/` if present, otherwise inline a CSS-only version.

### Phase 5: Internal Viability Report

**Write** `deliverables/teardowns/<slug>/internal-viability-report.html`

Use the template at `skills/website-teardown/templates/internal-viability-report.html`. Fill in from phases 1-4 research.

**Verdict block (top of page):**

- PURSUE / DROP (bold, colored)
- One-sentence rationale

**Weighted Score (0-100):**

| Dimension                | Weight | Score | Notes |
| ------------------------ | ------ | ----- | ----- |
| Brand clarity            | 20%    | /20   |       |
| UX craft                 | 20%    | /20   |       |
| SEO foundation           | 20%    | /20   |       |
| Market gap (opportunity) | 20%    | /20   |       |
| AI search readiness      | 20%    | /20   |       |

Total: /100. PURSUE if >= 40 AND no hard stops. DROP if < 40 OR any hard stop triggers.

**Hard stops (auto-DROP regardless of score):**

- Site is a competitor agency client
- Owner copy signals zero interest in digital or AI
- Business is clearly closing (no products, no CTA, domain expired-style neglect)

**Fit signals:**

- Local service business (yes/no)
- Phone number prominent (yes/no)
- Last updated recently (yes/no; infer from copyright year or blog dates)
- Budget signals (pricing page, staff size, location prestige)

**Scope estimate:**

- Tier: Signal Works baseline / Signal Works Pro / Catalyst Works custom
- Estimated hours: X
- Price band: $X - $Y

**Red flags (internal only):** List anything that makes this prospect a harder sell or higher-risk engagement.

### Phase 6: Client Teardown Report

**Write** `deliverables/teardowns/<slug>/client-teardown-report.html`

Use the template at `skills/website-teardown/templates/client-teardown-report.html`.

**Framing rule:** This is a gift, not an audit. Voice = "I looked at your site and here is what I found." Not "Your site scored a 47." The prospect should feel seen, not graded.

**Sections:**

1. **What you have built** (1 short paragraph, honest acknowledgment of the real business)
2. **What is costing you leads** (3-5 specific craft/SEO/UX findings, each with a "how to verify" instruction taking under 60 seconds)
3. **What your competitors are doing that you are not** (2-3 specific gaps from Phase 1)
4. **Before/After** (embed the drag slider from `mockups/before-after.html`)
5. **What changes in 2 weeks** (bullet list of Phase 2+3 fixes framed as outcomes, not tasks)
6. **CTA** (single ask: "Text 'site' to PHONE" or Calendly link)

**Em-dash rule:** No em-dashes in the client report. Use a colon or comma instead.

---

## Deliverable Folder Structure

```text
deliverables/teardowns/<slug>/
  internal-viability-report.html
  client-teardown-report.html
  research/
    brand-intel.md
    ux-audit.md
    seo-audit.md
  mockups/
    before-hero.png
    after-hero.png
    before-after.html
```

Slug = domain without TLD and protocol, hyphened. Example: `elevatebuiltoregon.com` becomes `elevate-built-oregon`.

---

## Source Skills (do not duplicate their logic)

| Phase | Skill                 | Location                             |
| ----- | --------------------- | ------------------------------------ |
| 1     | website-intelligence  | `skills/website-intelligence/`       |
| 2     | web-design-guidelines | `skills/web-design-guidelines/`      |
| 3     | seo-strategy          | `skills/seo-strategy/`               |
| 4     | kie_media             | `~/.claude/skills/kie_media/`        |
| 5-6   | Templates             | `skills/website-teardown/templates/` |

---

## Pricing Reference (internal report only)

| Tier                  | SEO floor | AI search floor | UX floor | Price                  |
| --------------------- | --------- | --------------- | -------- | ---------------------- |
| Signal Works baseline | >=80      | >=75            | >=80     | $500 setup + $497/mo   |
| Signal Works Pro      | >=90      | >=85            | >=90     | $1,500 setup + $997/mo |
| Catalyst Works custom | >=95      | >=90            | >=95     | Custom scoped          |

Use Lighthouse mobile Performance as the SEO floor proxy when PageSpeed data is not available.

---

## Verification Checklist (run before marking skill invocation complete)

- [ ] `deliverables/teardowns/<slug>/internal-viability-report.html` exists
- [ ] `deliverables/teardowns/<slug>/client-teardown-report.html` exists
- [ ] Verdict (PURSUE/DROP) present in internal report
- [ ] Verdict absent from client report
- [ ] Price band present in internal report
- [ ] Price band absent from client report
- [ ] Before/after slider renders in browser
- [ ] Em-dash grep returns zero results on client report
- [ ] All 5 weighted-score dimensions filled in internal report
- [ ] CTA present in client report
