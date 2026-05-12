---
name: design-audit
description: >
  Score any visual artifact (local HTML, PDF, slide, banner, social photo, OR live URL,
  OR multi-page live site) against the 5-dimension Impeccable rubric. Documents only,
  never fixes. Use when the user says /design-audit, "audit this design", "score this
  page", "rate this build", "audit this site", "audit this URL", or after any
  frontend-design / hyperframes / slides / banner-design build to verify quality
  before shipping. Three modes: local file, single URL, multi-page crawl.
---

# Design Audit

Adapted from Impeccable (github.com/pbakaus/impeccable, MIT). 5 dimensions, scored 0-4 each, total /20. Documents issues. Does not fix them.

**Core rule:** This skill produces a numeric score and an issue list. It never edits the artifact. If the user wants fixes, they invoke `frontend-design` or run `node scripts/design-live/design-live.mjs <path>` for live tweaking.

---

## Three modes

This skill works on three input types. Pick the mode based on what the user gave you.

### Mode 1: Local file

User gave you a path to a local HTML or PDF. Read it directly, score it.

```
/design-audit workspace/demo-sites/volta-studio/index.html
/design-audit output/websites/signal-works-demo-dental/index.html
/design-audit workspace/articles/2026-04-28-saas-audit-assets/saas-audit.html
```

### Mode 2: Single URL (live site)

User gave you a URL. Fetch the rendered HTML first, then audit it.

```
/design-audit https://signal-works-demo-dental.vercel.app
/design-audit https://catalystworks.consulting
```

**To fetch:** run `python scripts/design-audit/fetch_url.py <url>`. It writes the HTML to `workspace/design-audits/_fetched/<host>__<path>.html` and returns JSON with the file path. Then audit that local file. The fetched file has a comment header indicating the source URL, so the audit output should reference the URL (not the cached file path) when calling things out.

The fetcher uses urllib (Python stdlib, no API credits). Works for static HTML, SSR Next.js (Vercel), Hostinger, plain HTML. Does NOT execute JS — for pure SPAs that require client-side rendering, the fetched HTML may be near-empty. If that happens, note it in the audit and recommend the user test locally instead, or fall back to Firecrawl if needed.

### Mode 3: Multi-page crawl

User gave you a root URL and wants the whole site audited. Crawl, audit each page, produce per-page audits AND a site-wide summary.

```
/design-audit https://catalystworks.consulting --crawl
/design-audit https://catalystworks.consulting --crawl --limit 5
```

**To crawl:** run `python scripts/design-audit/fetch_url.py <root-url> --crawl --limit 5`. Default limit is 5 pages. The fetcher discovers internal links from the root, fetches each, returns JSON with all file paths. Then audit each one and produce a site-wide summary at `workspace/design-audits/<host>-site-audit.md`.

### Mode 4: Design CI extraction (memoire-backed)

User wants design-system drift surfaced in addition to the rubric — token inconsistency, Tailwind class drift, spacing/color anomalies across pages. Layered on top of any of Modes 1–3.

```
/design-audit https://catalystworks.consulting --tokens
/design-audit https://catalystworks.consulting --crawl --tokens
```

**To run:** invoke `memoire` ([github.com/sarveshsea/m-moire](https://github.com/sarveshsea/m-moire)) on the same target.

```
npx m-moire diagnose <url>
```

Capture the token-drift report and append to the standard output as **Section 6: Design System Drift** (Tailwind tokens, color drift, spacing inconsistencies).

**Bar to clear:** memoire must catch at least one issue the standard 5-dimension rubric does not catch on the same target. If overlap is total, drop Section 6 from the report and log "memoire redundant on this artifact" — don't pad the audit.

If memoire errors, returns empty, or its CLI verb has changed: skip Section 6, run the standard rubric, log the failure mode in the audit footer. Don't block the audit on one tool.

Posture remains: documents only, never fixes. memoire's "plan safe UI fixes" output goes into the issue list, not into the artifact.

Borrowed from awesome-shadcn-ui curation (2026-05-02 absorb).

---

## When to use

- User says `/design-audit <path-or-url>` or asks you to score/audit/rate a design
- After ANY visual artifact ships (HTML, PDF, slide, banner, social photo, video)
- Before sending a client-facing deliverable
- To establish baseline scores on existing work or competitor sites
- To audit a deployed site (vs. just the local source which may have drifted)
- During the build-log update step in `frontend-design` workflow

## When NOT to use

- User wants the design fixed (use `frontend-design` or `scripts/design-live/`)
- User wants design ideas (use `frontend-design` or `ui-ux-pro-max`)
- Artifact does not exist yet (audit is post-build only)

---

## How to run

1. **Pick mode.** Local file path → Mode 1. URL → Mode 2. URL + "site" / "crawl" / "all pages" → Mode 3.
2. **For URL modes:** run the fetcher first. Read the returned file path from JSON.
3. **Read the artifact** (the local file, or the fetched HTML).
4. **Score each of 5 dimensions 0-4.** Write the score and the specific evidence behind it. Vague scores ("looks good") are not allowed.
5. **List every issue tagged P0-P3** with location, category, impact, recommendation.
6. **Compute the total /20 and assign a band.**
7. **Write the result to** `workspace/design-audits/<artifact-name>-audit.md` (create dir if missing). For URL audits, use the host + path as the artifact name (e.g. `catalystworks-consulting-audit.md`). For multi-page, write one file per page AND a site-wide summary at `workspace/design-audits/<host>-site-audit.md`.

---

## The 5 Dimensions (each 0-4)

### Dimension 1: Accessibility

What to check:
- Color contrast ratios (text against background, UI against background) meet WCAG AA (4.5:1 for body, 3:1 for large text and UI)
- All interactive elements have visible focus states
- Keyboard navigability: tab order makes sense, no traps, all interactions reachable
- Semantic HTML: headings in order (h1 → h2 → h3, no skipping), landmarks (`<main>`, `<nav>`, `<footer>`), lists are `<ul>`/`<ol>`
- All `<img>` have meaningful `alt` (decorative = `alt=""`, content = describes what it shows)
- Forms: labels are associated with inputs, errors are announced, required fields marked
- ARIA only when semantic HTML cannot express the role

Scoring:
- **4** = WCAG AA across the board, focus states present, semantic HTML throughout
- **3** = One or two minor issues (one low-contrast element, one missing alt)
- **2** = Multiple issues but no blockers (missing focus states, some unlabeled forms)
- **1** = Blockers present (text under 4.5:1 contrast on key content, missing landmarks)
- **0** = Inaccessible (no alt anywhere, no focus states, divs as buttons)

### Dimension 2: Performance

What to check:
- Layout thrashing (animations on `top`, `left`, `width`, `height` instead of `transform`/`opacity`)
- Expensive CSS (`backdrop-filter`, large box-shadows on many elements, blur on scroll)
- Image strategy: lazy loading on below-fold, modern formats (WebP/AVIF), sized appropriately
- JS bundle: third-party scripts, render-blocking, deferred where possible
- Animation triggers: ScrollTrigger correctly configured, no infinite RAF loops
- Font loading: `font-display: swap`, preloaded, only weights actually used

Scoring:
- **4** = transform/opacity only, lazy images, fonts preloaded with swap, no layout thrash
- **3** = Mostly clean, one expensive animation or two unoptimized images
- **2** = Multiple performance smells (3+ blur effects, animating layout properties, no lazy)
- **1** = Significant problems (animating width/height, no lazy load, unoptimized hero image)
- **0** = Page jank guaranteed (multiple full-page filters, layout-thrashing animations everywhere)

### Dimension 3: Theming

What to check:
- Hard-coded colors in CSS (`#ff0000` instead of `var(--accent)`)
- Color tokens defined and consistently used
- Dark mode support if site warrants it (or explicit reason it doesn't)
- Spacing follows a scale (not arbitrary px values)
- Typography scale defined and used (not arbitrary font sizes)
- Component consistency: a button looks like a button across the page

Scoring:
- **4** = All colors via tokens, spacing scale, type scale, components reuse styles
- **3** = Mostly tokenized, one section with hard-coded values
- **2** = Tokens defined but inconsistently applied, multiple one-off values
- **1** = Few tokens, lots of arbitrary px and hex
- **0** = No tokens, every value hard-coded, components styled inline

### Dimension 4: Responsive

What to check:
- Mobile (375px): no horizontal scroll, no overflow, all content reachable
- Tablet (768px): layout adapts meaningfully, not just shrunk desktop
- Desktop (1280px+): no awkward stretching, max-width on text containers (≤75ch for body)
- Touch targets: 44×44px minimum for taps on mobile
- Images: respond to viewport (responsive images or fluid containers)
- Text: scales appropriately, doesn't become microscopic on mobile or huge on desktop

Scoring:
- **4** = Three breakpoints verified, touch targets ≥44px, fluid type, no overflow at any width
- **3** = Mostly responsive, one breakpoint has minor issues
- **2** = Desktop-first with breakpoints bolted on, some overflow or tiny touch targets
- **1** = Breaks at 375px (horizontal scroll, hidden CTAs, overlapping text)
- **0** = Desktop-only, mobile is unusable

### Dimension 5: Anti-Patterns (CRITICAL)

This is the AI-slop dimension. Score harshly. **Default for AI-generated work is 1-2.**

Banned patterns (each one drops the score):
- Side-stripe borders (`border-left` or `border-right` >1px as colored accent on cards/sections)
- Gradient text (`background-clip: text` + linear-gradient)
- Glassmorphism as default surface treatment (frosted blur on most cards)
- Hero-metric template (giant number + small label + supporting stats grid + gradient accent)
- Identical card grids (3-6 cards in a row with same structure, same icon, same heading + body)
- Modal as first interaction thought (popups for things that should be inline)
- Em-dashes anywhere in content
- Bounce easing (`cubic-bezier` with overshoot) used as default
- Purple-to-pink or blue-to-purple gradients
- Inter / DM Sans / Plus Jakarta Sans / Space Grotesk as the primary typeface (training-data reflexes)
- Generic stock-photo hero (smiling person looking at laptop, abstract gradient mesh)
- Card-grid services section (regardless of how the cards are styled)
- "Trusted by" logo strip in monochrome with arbitrary brand logos
- Newsletter signup as the only CTA
- Footer with 4 columns of identical link lists

Category-reflex check:
- Could someone guess the palette/theme from the business category alone? (dental → blue/white, law → navy/gold, healthcare → white/teal, observability → dark blue, crypto → neon-on-black, agency → dark + neon green/orange) — if yes, this is training-data slop. Drop the score.

Scoring:
- **4** = No AI tells. A human designer at a real studio could have made this.
- **3** = One or two AI tells, otherwise distinctive.
- **2** = 3-4 AI tells. Recognizable as AI-generated by a designer within 5 seconds.
- **1** = Multiple slop signatures (gradient text + card grid + Inter + category-reflex palette).
- **0** = AI slop gallery — every banned pattern present. Could be in a "ChatGPT designed my site" Twitter joke.

---

## Issue Format

For each issue found, write:

```
[P0-P3] [Dimension] [Location] — [Description]
Impact: [what breaks or who is affected]
WCAG: [if accessibility issue, cite the criterion]
Recommendation: [specific fix, not "make it better"]
```

Severity:
- **P0** = Blocker (broken accessibility, broken on mobile, page does not function)
- **P1** = High (anti-pattern signature, contrast failure on body text, missing key responsive behavior)
- **P2** = Medium (one-off styling inconsistency, missing focus state on secondary element)
- **P3** = Low (suggestion, polish opportunity, edge case)

---

## Output Format

```markdown
# Design Audit — [Artifact Name]
**Date:** [YYYY-MM-DD]
**Path:** [absolute or repo-relative path]
**Type:** [HTML site | PDF | slide deck | banner | social photo | video]

## Score: [X]/20 — [Band]

| Dimension | Score | One-line summary |
|---|---|---|
| Accessibility | X/4 | [evidence] |
| Performance | X/4 | [evidence] |
| Theming | X/4 | [evidence] |
| Responsive | X/4 | [evidence] |
| Anti-Patterns | X/4 | [evidence] |

## Bands
- 18-20 Excellent (ship as-is)
- 14-17 Good (ship with P1+ fixes)
- 10-13 Acceptable (rework before client-facing)
- 6-9 Poor (rebuild major sections)
- 0-5 Critical (do not ship)

## Issues

### P0 (blockers)
[list or "none"]

### P1 (high)
[list]

### P2 (medium)
[list]

### P3 (low)
[list]

## Anti-Pattern Tells
[list every banned pattern found, with location]

## Category-Reflex Check
- Business category: [type]
- Palette/theme: [description]
- Could a stranger guess category from palette? [yes/no — explain]

## Recommendation
[ship as-is | fix P0/P1 then ship | rework section X | rebuild]
```

---

## Multi-page site summary format (Mode 3 only)

After auditing N individual pages, write a site-wide summary at `workspace/design-audits/<host>-site-audit.md`:

```markdown
# Site Audit — <host>
**Date:** YYYY-MM-DD
**Pages audited:** N
**Crawl source:** <root URL>

## Site-wide score: X.X/20 average

| Page | URL | Total | A11y | Perf | Theme | Resp | Anti-Slop |
|---|---|---|---|---|---|---|---|
| Home | / | X/20 | X/4 | X/4 | X/4 | X/4 | X/4 |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Average:** XX/20 — Band

## Site-wide patterns (issues that appear on multiple pages)

[List patterns that recur — e.g. "Inter font on all 5 pages", "side-stripe borders on 3 of 5 pages", "modal CTA pattern on 2 pages"]

## Per-page audit files

- [<page name>](<host>__<path>-audit.md)
- ...

## Site-wide recommendation

[Top 3-5 fixes that would lift the WHOLE SITE, ranked by impact. Not page-specific fixes — patterns to address globally.]
```

The site-wide summary is the highest-leverage output of multi-page mode. Per-page audits are the evidence; the summary is the strategy.

---

## Hard rules

- **Never edit the artifact.** This skill scores. It does not fix.
- **No vague scores.** Every dimension score has at least one piece of specific evidence (file:line for HTML, page:section for PDF, frame for video).
- **Default suspicion on AI tells.** When in doubt on dimension 5, score lower not higher. The point is to surface slop, not to rationalize it.
- **Do not soften scores to be encouraging.** A 1/4 is a 1/4. The user explicitly asked for an honest scorer.
- **Write the audit file.** Every run produces a file at `workspace/design-audits/<artifact-stem>-audit.md`. No file = audit did not run.
- **One artifact per audit.** For batch runs, produce one file per artifact and one summary file at `workspace/design-audits/baseline.md` listing all scores.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| Scoring 3-4 across the board to be nice | Score harshly, especially anti-patterns. The user wants signal, not validation. |
| Suggesting fixes inline | Don't. Recommendations go in the recommendation field. Fixes happen in a separate skill run. |
| Skipping the category-reflex check | Always run it. It's the single most useful slop detector. |
| Auditing a draft in progress | Audit ships, not drafts. If the user says "I'm still building," tell them to re-run when done. |
| Scoring without reading the file | Read it. Score from evidence, not from memory or reputation. |
