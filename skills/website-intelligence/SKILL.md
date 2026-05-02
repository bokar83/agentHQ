---
name: website-intelligence
description: |
  Research-driven competitive intelligence engine for websites. Scrapes a client's existing site,
  analyzes their top 5 competitors, produces a professional competitive analysis report (PDF-ready
  HTML), then builds a premium scroll-animated website informed by real market data. Uses Firecrawl
  MCP for scraping. Trigger when the user says "website intelligence", "build a site", "redesign",
  "website for [business]", "scrape and rebuild", "competitive analysis", "niche research", or
  "website audit".
allowed-tools: Read, Write, Grep, Glob, Bash, WebFetch
---

# Website Intelligence: Research-Driven Premium Websites

You are a senior web strategist and developer. Your job is to research a niche,
scrape a client's existing site, analyze their competitors, and build a premium
scroll-animated website grounded in competitive intelligence: not guesswork.

Work through each phase in order. Save all research outputs to the project directory
so the user has deliverables at every stage.

## ⛔ HARD RULES (read these before every run)

1. **Phase 1 includes a MANDATORY media inventory.** Download the client's hero video, project photos, logos (every variant), and Open Graph image to `site/assets/media/` BEFORE generating anything new. The generation queue is the GAP between what they have and what they need, never a blanket fresh build.

2. **Use the client's REAL logo in the build.** Do not improvise a text-based logotype. The client recognizes their own logo and does not recognize a stylized text version. Render their actual PNG via `<img class="brand-logo">`. For dark surfaces use `filter: brightness(0) invert(1)`.

3. **Redesigns must be 20-50% different, never 100%.** Familiar-but-elevated wins. The brief MUST include a KEPT vs ENHANCED vs NEW matrix (Phase 4). Default to KEPT when uncertain. Replacement requires justification.

4. **Phase 5 hand-off is mandatory.** This skill does NOT build the actual site. It hands off to `frontend-design` (default) or `3d-website-building` (when video/3D assets are available). The skill's old "static HTML + GSAP" template was a step backwards from most existing client sites and is banned.

5. **Every redesign must contain at minimum:** real logo (header + footer), real video or photo (hero), real project photos (gallery), and the client's voice fingerprint preserved verbatim in 3+ visible places. If any are missing, the redesign rule has been violated.

6. **No em-dashes in any output.** Site HTML, CSS, JS, source generators: scrub before declaring done.

These rules were learned the hard way on the Elevate Roofing pilot (2026-04-30, see `_archive/v1-boring-template/` in that project for what NOT to ship).

---

## BEFORE YOU START: Firecrawl Setup

This skill depends on **Firecrawl** for web scraping. Before beginning any work, confirm
that Firecrawl is available and authenticated.

### Check if Firecrawl MCP is connected

Look for Firecrawl tools in your available MCP tools (e.g., `mcp__firecrawl__scrape`,
`mcp__firecrawl__map`, `mcp__firecrawl__search`). If they are available, you're good to go.

### If Firecrawl is NOT connected

Ask the user:

> "This skill uses Firecrawl to scrape websites and research competitors. I need a Firecrawl
> API key to get started. You can get one at https://firecrawl.dev: they have a free tier.
> Once you have it, what's your Firecrawl API key?"

Once the user provides the key, help them configure it:

1. **If using Claude Code with MCP**: The user needs to add Firecrawl as an MCP server in their
   Claude Code settings. Guide them to add it via the settings UI or `settings.json`:
   ```json
   {
     "mcpServers": {
       "firecrawl": {
         "command": "npx",
         "args": ["-y", "firecrawl-mcp"],
         "env": {
           "FIRECRAWL_API_KEY": "fc-THEIR_KEY_HERE"
         }
       }
     }
   }
   ```
   After adding, they'll need to restart Claude Code for the MCP server to connect.

2. **If Firecrawl MCP is not an option**: Fall back to using `WebFetch` for basic page scraping.
   This is less powerful (no `/map` endpoint, no search, no bulk scraping) but still works for
   extracting content from individual URLs. Adjust the process accordingly: fetch each page URL
   manually instead of using Firecrawl's automated discovery.

### Firecrawl Tool Reference

Once connected, these are the key Firecrawl MCP tools you'll use:

| Tool | Purpose | When to use |
|------|---------|-------------|
| `mcp__firecrawl__scrape` | Scrape a single URL: returns full page content, HTML, metadata | Phase 1: scraping client site pages. Phase 2: deep-scraping competitor sites |
| `mcp__firecrawl__map` | Discover all URLs on a domain: returns the full site architecture | Phase 1: mapping client's site structure |
| `mcp__firecrawl__search` | Search the web for relevant pages/companies | Phase 2: finding competitors in the niche |

---

## PHASE 1: Client Brand Extraction + Media Inventory

Before anything else, extract everything from the client's existing website AND download every reusable media asset locally. We are building a 20-50% redesign, not a 100% replacement. Familiar-but-elevated is what gets the yes. (Lesson learned the hard way on the Elevate Roofing pilot, 2026-04-30.)

**Using Firecrawl (or WebFetch as fallback), scrape the client's current site and extract:**

1. **Logo**: Find and download EVERY variant (mark, wordmark, footer logo, favicon). Check `<img>` tags in header/nav, footer, favicon links, and Open Graph images. WordPress sites typically expose them under `/wp-content/uploads/`.
2. **Brand colors**: Extract from CSS: primary, secondary, accent colors. Check inline styles, stylesheets, and CSS custom properties. WARNING: WordPress block editor leaks default Gutenberg palette colors (`#ff6900`, `#fcb900`, `#cf2e2e`, etc.) into HTML even when the site doesn't use them visually. The REAL palette lives in the rendered Elementor/theme CSS files (e.g. `/wp-content/uploads/elementor/css/post-N.css`).
3. **Fonts**: Identify font families from CSS `font-family` declarations and any Google Fonts / Adobe Fonts links.
4. **Tone of voice**: Analyze homepage copy. Formal, casual, playful, authoritative? Note signature phrases verbatim: those ARE the brand.
5. **Key messaging**: Headline, tagline, value proposition.
6. **Existing content**: Pull all text content from main pages (home, about, services, contact).
7. **Site structure**: Use Firecrawl's `/map` to discover their full URL architecture.

### MANDATORY: Media Inventory (download to `site/assets/media/` BEFORE building anything)

Most clients already have hero video, project photos, and logos that are good enough to keep. Find them and download them. **Replacement is the exception, not the default.**

- **Hero / background videos**: WordPress + Elementor stash these in `data-settings` JSON on section elements, NOT visible in the rendered video tag (Elementor injects the source via JS at runtime). Pattern to extract:
  ```python
  import re, json
  html = open('home.html', encoding='utf-8').read()
  for m in re.findall(r'data-settings="([^"]+)"', html):
      decoded = m.replace('&quot;', '"').replace('&amp;', '&')
      if 'video' in decoded.lower() or '.mp4' in decoded.lower():
          j = json.loads(decoded)
          print(j.get('background_video_link'))
  ```
  Same trick works for Webflow (data attributes) and Squarespace (CDN URLs in JSON).

- **All `/wp-content/uploads/` images**: sequential filenames like `20251009_130253.jpg` are real phone-camera shots from real jobs: gold for portfolio. Don't dismiss them as "DIY phone shots." Use them.

- **Logos in every variant**: favicon, header mark, footer wordmark, dark/light variants. **USE THE REAL LOGO IN THE BUILD.** Do NOT improvise a text-based logotype as a stand-in. The client immediately recognizes their own logo and immediately doesn't recognize a stylized text version. Render their actual PNG via `<img class="brand-logo">` with `filter: brightness(0) invert(1)` for dark surfaces.

- **Curl invocation** for Windows with cert-revocation issues:
  ```bash
  curl -sSL -k --ssl-no-revoke -A "Mozilla/5.0" -o assets/media/hero.mp4 <URL>
  ```

After downloading, list every reusable asset in the brand snapshot under a "Media inventory: kept" section. Anything you generate later (Phase 5) is a GAP fill against this inventory, not a blanket "generate everything fresh."

**Save output as:** `research/01-client-brand.md`

Include a summary section at the top:
```
## Brand Snapshot
- **Company:** [name]
- **Primary Color:** [hex]
- **Secondary Color:** [hex]
- **Accent Color:** [hex]
- **Fonts:** [heading font] / [body font]
- **Tone:** [one-word descriptor]
- **Core Message:** [their value prop in one sentence]
```

For a full example of what this output should look like, see `examples/sample-brand-snapshot.md`.

---

## PHASE 1.5: Run web-design-guidelines on the existing client site

After Phase 1 brand extraction but before Phase 2 competitor research, also run the `web-design-guidelines` skill on the client's existing site (URL or saved HTML). This produces a UX/accessibility/best-practices scorecard that is the COMPLEMENT to the competitive-analysis lens.

**Why both:** website-intelligence answers *"what does the market do?"* (outside-in). web-design-guidelines answers *"how does this specific design hold up against best practices?"* (inside-out). Boubacar wants BOTH lenses in every Signal Works report: competitor scrape gives you the market gap, design audit gives you the craft gap. Without both, the report only tells half the story.

**Output:** save the design-guidelines scorecard to `research/01b-design-audit.md` (between brand extraction and competitor analysis). Reference key findings from it in the audit-one-pager (Phase 3) so the prospect sees BOTH:

- "Here's what your competitors are doing that you aren't" (competitive)
- "Here's where your current site fails accessibility / UX best practices regardless of competitors" (design audit)

**Then weave both into the SEO/GEO scorecard block of the audit-one-pager.** The one-pager template now has 8 SEO/GEO scorecard cards: extend with 4-6 more cards from the design-guidelines audit (color contrast, mobile usability, focus indicators, alt-text coverage, etc.) so the prospect sees the full picture in a single page.

---

## PHASE 2: Competitive Niche Analysis

Research the client's niche to understand what "top 10%" looks like.

**Step 1: Find the top 10 competitors:**
Use Firecrawl's search to find leading companies in the same niche/industry.
Evaluate each against these criteria (score 1-10):

| Criterion | What to look for |
|-----------|-----------------|
| Search visibility | Do they rank on page 1 for key industry terms? |
| Review quality | Google reviews, Trustpilot, G2: 4.5+ stars? |
| Visual design | Modern, professional, not template-looking? |
| Mobile responsive | Clean on mobile, not just "it works"? |
| Content depth | Real copy or placeholder garbage? |
| Social proof | Testimonials, logos, case studies visible? |
| CTA strategy | Clear next step for the visitor? |
| Page speed | Fast load, no layout shift? |

**Step 2: Deep scrape the top 5:**
For each of the top 5 scoring sites, use Firecrawl to scrape and extract:

- **Visual identity**: colors (hex), typography, photography style, design aesthetic
- **Content strategy**: headline formula, CTA copy, value prop structure, word count
- **Site architecture**: number of pages, nav structure, depth
- **Conversion strategy**: primary CTA, lead capture method, social proof placement

**Step 3: Identify patterns:**
What do ALL top sites do that the bottom ones don't? Find the 3-5 patterns
that separate elite from average.

**Save output as:** `research/02-competitor-analysis.md`

Include a comparison table and a clear "Patterns of the Top 10%" section.

---

## PHASE 3: Competitive Analysis Report (PDF-Ready HTML)

This is a **client-facing deliverable**: a polished, print-ready HTML report.

**Build it as a beautiful HTML page** (not markdown) styled for printing to PDF.

For the exact HTML/CSS reference, see `references/process-overview.html`: this is the design
language to follow: warm paper tones, Instrument Serif + DM Sans, subtle grain texture, elegant
cards with accent-colored left borders, flow connectors between phases, print-ready with
`@media print` rules.

**The report must include:**

1. **Cover section**: Report title, client name, date, "Competitive Analysis" badge
2. **Executive summary**: 3-4 sentence overview of findings
3. **Competitor profiles**: For each of the top 5:
   - Company name and logo (downloaded and embedded or linked)
   - Brand colors shown as visual swatches
   - Key strengths and weaknesses
   - Score breakdown across the 8 criteria
4. **Comparison table**: All 5 competitors scored side-by-side
5. **SEO landscape**: Keyword opportunities, gaps, and recommendations
6. **Patterns of the top 10%**: The 3-5 things all winning sites do
7. **Recommended design direction**: Colors, typography, structure, and animation recommendations
   backed by competitor data

**Save as:** `competitive-analysis.html` in the project root

**Design specs (matching the reference):**
- A4-formatted for clean PDF export (`@media print` rules)
- `Instrument Serif` for headings, `DM Sans` for body
- Warm paper background (`#f6f4f0`), terracotta accent (`#c45d3e`)
- Grain overlay via SVG filter
- Cards with 4px accent left border, `#fffefa` background, subtle shadow on hover
- Phase numbers large and faded, titles in serif
- Tags in pill-shaped badges below each section
- Flow connectors (dashed SVG lines) between sections
- Responsive with mobile breakpoint at 640px
- No JavaScript: pure HTML + CSS

---

## PHASE 4: Build Brief & Approval

Combine brand extraction + competitor analysis into a Website Build Brief.

**The brief must include:**

### Design Direction
- Recommended color palette: keep client's brand colors but refine based on competitor analysis
- Typography pairing: heading + body font recommendation
- Photography/asset style guide
- Animation recommendations (scroll-triggered effects, hover states, parallax)
- What to AVOID (things competitors do badly)

### Site Architecture
- Exact pages to build with the purpose of each
- Navigation structure
- Content hierarchy per page
- CTA strategy (primary + secondary per page)

### Content Framework
- Homepage headline: provide 3 options using proven formulas from top competitors
- Value proposition structure
- Section-by-section copy direction
- SEO keyword targets (based on what top competitors rank for)

### Conversion Playbook
- Primary conversion goal
- Lead capture strategy
- Social proof plan (what to include and where)
- Trust signal checklist

### MANDATORY: KEPT vs ENHANCED vs NEW matrix

The brief must explicitly mark which elements from the existing site are being KEPT, which are ENHANCED, and which are NEW. This is the artifact that proves the redesign is 20-50% different (not 100%) and is the lens you use during the build.

```markdown
### KEPT (their existing brand, untouched)
| Asset | Source | Used where |
|---|---|---|
| hero-video.mp4 | Their Elementor data-settings | Full-bleed hero |
| project-photos (4) | wp-content/uploads | Portfolio gallery |
| Voice phrase: "..." | Their homepage | Verbatim, kept where they had it |
| Logo (real PNG) | wp-content/uploads | Header + footer |
| Their primary color (hex) | Their CSS | Anchor in token system |

### ENHANCED (their elements, sharper wrapper)
| Element | Before | After |
|---|---|---|
| Color | 5 competing accents | Their primary + ONE sharp accent + neutrals |
| Typography | Default WP Montserrat | Distinctive serif + humanist sans (named) |
| Hero | Static photo banner | Their video, scroll-driven |

### NEW (additions that didn't exist on their site)
| Addition | Why |
|---|---|
| City service-area pages | Local SEO lever every winning competitor pulls |
| Cost-band tool | No competitor publishes prices |
| Schema.org JSON-LD | None of their pages had structured data |
```

**Default to KEPT when uncertain.** Replacement requires justification. Retention is the safe default. The pitch to the client becomes "Here's what we kept of yours, here's what we sharpened, here's what we added": not "Here's the new site."

**Save output as:** `research/03-build-brief.md`

### HARD STOP: APPROVAL CHECKPOINT

**Do not proceed to the build until the user explicitly approves the brief.**
Present the brief, highlight the key decisions, and ask: "Ready to build?"

This checkpoint exists because once the build starts, major direction changes are expensive.
The user should review and reshape the plan here: not during the build.

---

## PHASE 5: Build the Website

### ⛔ HARD RULE: Hand off to frontend-design. Do NOT build with this skill's default template.

This skill's earlier guidance suggested building the site with the same warm-paper / Instrument Serif design language used in the Phase 3 PDF report. **That design language is for the print-friendly PDF only.** It produces a generic site that's a step BACKWARDS from most existing client sites: even a placeholder Elementor site with a drone background video is more dynamic than a static-template rebuild.

Lesson learned hard on the Elevate Roofing pilot (2026-04-30): the user's exact reaction to the v1 static template was *"You're using the exact same template I told you not to use for websites. This is too boring. His website has a video on it already. This is a step back. This is a $50,000 to $100,000-valued website."* The v1 was archived as a warning artifact at `_archive/v1-boring-template/`.

**For the actual site build, hand off to one of these skills:**

1. **`frontend-design`** (DEFAULT for most SW client sites): Volta-grade, cinematic, distinctive. Avoids the banned default skeleton.
2. **`3d-website-building`** (use when the client has video/3D assets to lean on, or a product/object that benefits from scroll-driven animation): Next.js + Framer Motion, scroll-driven, cinematic. Chains website-intelligence → image-generator → 3d-animation-creator → seo-strategy.
3. **`hyperframes`** (use only for video/scene compositions inside the site, not the whole site).

**Do NOT generate the site as static HTML inside this skill.** Pass the brand snapshot, the build brief, the local media inventory, and the competitor analysis to the chosen build skill and let it execute.

### ⛔ HERO IS THE CLOSE (locked 2026-05-01, after the Elevate hero substitution incident)

The hero closes the client AND the client's clients. It gets the most attention.
Cross-reference: `memory/feedback_hero_is_the_close.md` and the `frontend-design`
skill's hard rule. Five non-negotiables enforced during build:

1. **Video over still imagery whenever possible** (drone, time-lapse,
   walk-through, founder-to-camera, before/after).
2. **If video isn't available, use the single most representative still** : 
   never substitute a smaller-but-different image to game LCP. Compress the
   approved asset (WebP + JPG fallback via `image-set()`).
3. **Asset-level hero changes need explicit operator sign-off** post-approval.
   Code-level fixes are silent; asset changes are not.
4. **Lead with hero changes in any user-facing report**: not buried in a list.
5. **Default hero pattern by business type**: see the `frontend-design`
   skill for the canonical roofer / dentist / HVAC / lawyer / SaaS / restaurant
   table.

Trends source: `memory/reference_web_design_trends.md`. Ship at least one
trend-leading element per build that the next 50 contractors in the niche
won't have for 12-18 months.

### Build expectations the chosen skill must hit (every SW redesign)

- **Reuse the client's existing media first.** Hero video they already have → keep it. Real project photos → use them. Real logo → render their actual PNG via `<img class="brand-logo">`. Generation is for gaps only.
- **Real video hero** (theirs or generated), not a static photo
- **Scroll-driven animation throughout** (GSAP ScrollTrigger or Framer Motion): section reveals, parallax, count-ups, hover micro-interactions, smooth scene transitions
- **Distinctive type pairing**: not "Inter + Instrument Serif default," not Montserrat. Pick fonts that read premium and that NO competitor in the analysis uses (e.g. Fraunces + Geist worked well for Elevate)
- **Dark/light section rhythm** for cinematic pacing: not all dark (reads agency/edgy, kills trust for residential trades), not all light (boring). Aim for ~50/50.
- **The bar is Apple / Stripe / Linear**: not "competent WordPress refresh"
- **20-50% different from their current site, not 100%**: the client must see their brand in the new site, just elevated. Honor the KEPT/ENHANCED/NEW matrix from the brief.

### Minimum content every redesign deliverable must contain

If ANY of these are missing from the build, the redesign rule has been violated:

1. Their **real logo** in the header + footer (not a text-based improvisation)
2. Their **existing hero video or photo** if it exists and isn't terrible
3. Their **real project photos** in the gallery
4. Their **voice fingerprint** preserved verbatim in at least 3 visible places (signature phrases, taglines, turns of phrase)

### Structure (still required regardless of which skill builds)

- Proper `<title>` + meta description per page (unique)
- Single H1, logical H2/H3 hierarchy
- Alt text on every image (use the client's existing photo context: the timestamps in their filenames tell you which job they're from)
- Schema.org markup for the business type (LocalBusiness, RoofingContractor, Restaurant, etc.)
- Open Graph + Twitter cards
- Sitemap.xml + robots.txt
- 404 page
- Cache-bust pattern on `<link>` and `<script>` tags during iteration: `?v=<unix_timestamp>`. Bump via Python regex sweep across all pages on every change so browser refresh picks it up immediately. Without this, every "fix" reads as "no change" to the user staring at a cached browser.

### Performance Targets

- Lighthouse 90+ on all metrics
- Lazy load all images and videos (`loading="lazy"` + `preload="metadata"` on video)
- `prefers-reduced-motion` support
- `will-change` hints on animated elements
- No render-blocking resources
- Hero video: poster image set, `playsinline muted autoplay loop`, compressed to < 8 MB if possible (`ffmpeg -c:v libx264 -crf 28 -preset slow -an -movflags +faststart`)

### Known pitfalls (learned the hard way)

- **NEVER hide H2 text by default with `transform: translateY(110%)` waiting for a GSAP/IntersectionObserver reveal.** If JS misfires (slow connection, ScrollTrigger trigger missed on fast scroll, GSAP CDN timeout), the headline stays invisible forever and the page reads as a giant empty column. If you want a reveal animation, gate the hide behind a `.js-ready` class added by your IIFE entry point, so without JS the text is always visible. Better: use `gsap.from()` (animates FROM a state) instead of CSS-default-hidden, so the rendered DOM is always the final state.
- **Em-dash scrub before declaring done.** Boubacar's hard rule: no `: ` or `: ` site-wide. Run a Python sweep replacing `: ` → ` - `, bare `: ` → `, `, `: ` → ` - `, bare `: ` → `-`. Caught 12-166 instances per scrub on the Elevate build. Apply to HTML, CSS, JS strings (watch out for cost-range fallback strings), and any source generators.
- **Don't write meta-commentary in visitor-facing copy.** Lines like "Three real reviews from real clients" or "01 / Stack" or "Don't just take our word for it" read as designer notes that escaped into production. Write copy FOR the visitor, not ABOUT the page.

### Code Quality

- Clean, commented code
- Logical file structure
- README.md with deployment instructions (Vercel)

---

## PHASE 6: Quality Audit

Run a final check before handoff.

### SEO Audit
- [ ] All meta tags present and unique per page
- [ ] Heading hierarchy correct (one H1 per page)
- [ ] Alt text on all images
- [ ] Schema markup validates
- [ ] XML sitemap generated
- [ ] Robots.txt present
- [ ] Open Graph tags set

### Accessibility Audit
- [ ] Color contrast ratios pass WCAG AA
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] `prefers-reduced-motion` respected
- [ ] Semantic HTML used throughout

### Performance Audit
- [ ] Images optimized and lazy loaded
- [ ] No render-blocking CSS/JS
- [ ] GSAP loaded efficiently
- [ ] Animations don't cause layout shift

### Client-Ready Checklist
- [ ] All placeholder content clearly marked
- [ ] 3D asset placeholder clearly marked
- [ ] Forms have action endpoints noted
- [ ] Favicon set
- [ ] OG images set
- [ ] 404 page exists
- [ ] README includes deployment steps
- [ ] Project deployed to preview

**Save audit as:** `research/04-quality-audit.md`

Fix anything that fails before declaring the build complete.

---

## OUTPUT SUMMARY

When complete, the project directory should contain:

```
project/
├── research/
│   ├── 01-client-brand.md         # Brand extraction
│   ├── 02-competitor-analysis.md  # Niche research
│   ├── 03-build-brief.md          # Master build document
│   └── 04-quality-audit.md        # Final audit results
├── competitive-analysis.html      # PDF-ready client deliverable
├── site/
│   ├── index.html
│   ├── css/
│   ├── js/
│   ├── assets/
│   └── ...
└── README.md
```

---

## IMPORTANT RULES

1. **Always scrape the client's existing site first.** Never start from scratch when they already have brand assets online.
2. **Save research at every phase.** Each file is a deliverable the user can share with the client.
3. **The competitive analysis report is a sales tool.** Format it as something impressive enough to email to a cold prospect or hand to a client in a meeting. Use the design reference in `references/process-overview.html` as your style guide.
4. **Leave clear 3D asset placeholders.** The user will generate scroll-stop video content separately (using the Image Generator skill) and drop it in.
5. **Be opinionated about design.** Pick specific colors, specific fonts, specific animations. Justify each choice with competitor data.
6. **The approval checkpoint is real.** Do not skip Phase 4's hard stop. The user must approve before you build.
7. **Speed matters.** The whole process should feel fast and automated, not like a consulting engagement.
