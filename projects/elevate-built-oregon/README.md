# Elevate Roofing & Construction - Static Site

A premium static site for Elevate Roofing & Construction LLC (Medford, OR · CCB# 257092).

## What's here

```
projects/elevate-built-oregon/
├── research/                      # Phase 1-4 research outputs
│   ├── 01-client-brand.md
│   ├── 02-competitor-analysis.md
│   ├── 03-build-brief.md
│   └── 04-quality-audit.md
├── competitive-analysis.html      # Client-ready PDF report
├── _build/
│   └── generate_pages.py          # One-shot generator for sub-pages
└── site/                          # The deployable static site
    ├── index.html                 # Homepage
    ├── about/
    ├── portfolio/
    ├── services/                  # Hub + 4 service pages
    ├── service-areas/             # Hub + 6 city pages
    ├── get-a-quote/
    ├── contact/
    ├── 404/
    ├── css/styles.css
    ├── js/main.js
    ├── assets/                    # favicon.svg, og-image.svg
    ├── sitemap.xml
    ├── robots.txt
    └── vercel.json
```

## Tech stack

- **Static HTML + CSS + vanilla JS** (no framework, no build step required)
- **GSAP + ScrollTrigger** loaded from CDN for scroll animations
- **Google Fonts:** Instrument Serif (display), Inter (body), JetBrains Mono (accent)
- **Hosting:** Vercel (static)
- **Forms:** placeholder Formspree action - replace `REPLACE_ME` in `/get-a-quote/index.html` with your real form ID before launch

## Local preview

```bash
cd site
python -m http.server 8000
# open http://localhost:8000
```

## Deploy to Vercel

```bash
# Install Vercel CLI once
npm i -g vercel

# From the site directory
cd site
vercel --prod
```

Or connect this repo to Vercel via the dashboard and point the root to `/site`.

## Regenerating sub-pages

The 4 service pages, 6 city pages, hub pages, portfolio, get-a-quote, contact, and 404 are generated from one Python script to keep the shared header/footer in sync. The homepage and about page are hand-written.

```bash
python _build/generate_pages.py
```

## Pre-launch checklist

- [ ] Replace Formspree placeholder `REPLACE_ME` in `/get-a-quote/index.html`
- [ ] Real founder portrait → swap `.founder-portrait.placeholder` element on home + about
- [ ] Real drone hero photo → set `.hero-bg` background-image
- [ ] Real portfolio photos → swap `.portfolio-card.placeholder` elements
- [ ] Confirm Rod's email - currently `rod@elevatebuiltoregon.com` placeholder in footer
- [ ] Verify CCB# 257092 across all pages
- [ ] Add Google Analytics / Site Kit tag to `<head>` of every page (or use Vercel Analytics)
- [ ] Add real OG image at `/assets/og-image.jpg` (currently SVG placeholder)
- [ ] Wire calendar embed (Cal.com or Calendly) into `/get-a-quote/`
- [ ] Run Lighthouse against the deployed preview, fix anything < 90

## Brand tokens

- **Ink:** `#0E2238` (deep navy)
- **Paper:** `#F5F1EA` (warm off-white)
- **Copper:** `#B8632B` (accent, CTAs, brand color)
- **Stone:** `#7A7570` (muted text)
- **Display font:** Instrument Serif
- **Body font:** Inter

See `site/css/styles.css` `:root` for the full token list.
