# Unit Converter Sites — Design Spec

**Date:** 2026-04-16
**Status:** Approved for implementation

---

## What We Are Building

Two standalone static websites monetized via Google AdSense:

- **English site:** `unit-converter-site` — targeting global English-speaking search traffic
- **French site:** `convertisseur-en-ligne-site` — targeting French-speaking search traffic (France, Belgium, Canada, West Africa)

These are not part of CalcFlow (calculatorz.tools). They are separate products with separate repos, separate Hostinger deployments, and separate AdSense publisher wiring.

Reference site scraped and confirmed: https://www.unitconverters.net

---

## Revenue Strategy

Max AdSense coverage on every converter page. When in doubt, place the ad. No Pro tier, no affiliate — pure display ad revenue.

---

## Tech Stack

- **Framework:** Next.js 14, App Router, TypeScript
- **Styling:** Tailwind CSS
- **Export:** `output: 'export'` in next.config.js — fully static HTML/CSS/JS into `out/`
- **No server components, no API routes, no ISR, no database, no auth**
- **All conversion logic:** pure client-side JS
- **Locale system:** `NEXT_PUBLIC_LOCALE` env var (`en` or `fr`). Strings in `src/locales/en.json` and `src/locales/fr.json`. Math logic shared, never duplicated.
- **Deployment:** Hostinger via GitHub auto-deploy (not Vercel)

---

## Repos and Folders

| Site | Local folder | GitHub repo |
|------|-------------|-------------|
| English | `d:/Ai_Sandbox/agentsHQ/output/websites/unit-converter-site/` | `bokar83/unit-converter-site` |
| French | `d:/Ai_Sandbox/agentsHQ/output/websites/convertisseur-en-ligne-site/` | `bokar83/convertisseur-en-ligne-site` |

Build EN first, copy the folder, set `NEXT_PUBLIC_LOCALE=fr`, rebuild for FR.

---

## 10 Converter Categories

Built in this order:

| # | Category | EN slug | FR slug | Key units |
|---|---------|---------|---------|-----------|
| 1 | Length | `/length-converter` | `/convertisseur-de-longueur` | m, cm, mm, km, in, ft, yd, mi |
| 2 | Weight/Mass | `/weight-converter` | `/convertisseur-de-poids` | kg, g, mg, lb, oz, t |
| 3 | Temperature | `/temperature-converter` | `/convertisseur-de-temperature` | C, F, K |
| 4 | Volume | `/volume-converter` | `/convertisseur-de-volume` | L, mL, gal (US), fl oz, cup, m³ |
| 5 | Speed | `/speed-converter` | `/convertisseur-de-vitesse` | km/h, mph, m/s, knot |
| 6 | Area | `/area-converter` | `/convertisseur-de-surface` | m², km², cm², ft², acre, ha |
| 7 | Time | `/time-converter` | `/convertisseur-de-temps` | s, min, h, day, week, month, year |
| 8 | Pressure | `/pressure-converter` | `/convertisseur-de-pression` | Pa, kPa, bar, psi, atm, mmHg |
| 9 | Energy | `/energy-converter` | `/convertisseur-d-energie` | J, kJ, cal, kcal, kWh, BTU |
| 10 | Fuel Consumption | `/fuel-consumption-converter` | `/convertisseur-de-consommation` | L/100km, mpg (US), km/L |

---

## Converter Widget — 1:1 Design

The converter is a single From/To interaction. No one-to-all matrix.

```
[ Input value field ]   [ From unit dropdown ▼ ]
         ⇅  (swap button)
[ Result field (readonly) ]   [ To unit dropdown ▼ ]
```

- Converts in real time on input change or dropdown change
- Swap button reverses From and To units
- Result field is read-only
- All math is pure client-side JS, no external calls
- Popular conversions for the category shown as inline links below the widget (cloned from reference)

---

## Homepage Layout

**Mobile (375px) — priority:**
- Dark nav: logo left, search input right
- Short hero: site name + tagline ("Free online unit converters")
- 2-column category card grid (icon + name)
- Popular conversions list (20 links, two columns)
- Footer

**Desktop (1280px):**
- Same dark nav, expanded with category links
- Hero section
- 3-column category card grid
- Popular conversions list
- Footer

**Tablet (768px):**
- 2-column grid

---

## Converter Page Layout

### Mobile (375px)

```
Dark nav (logo + search)
Ad — 320×50 banner (top, above widget)
Breadcrumb: Home > Category > Converter
H1: [Category] Converter
Converter widget (1:1, full width)
Popular conversions for this category (inline links)
Ad — 300×250 (below widget)
Content: How it works, formula, reference table, FAQ
Ad — 300×250 (mid-content)
Footer
Ad — 320×50 sticky bottom (fixed, always visible)
```

### Desktop (1280px)

```
Dark nav
Ad — 728×90 leaderboard (below nav)
[Main 70%]                    [Sidebar 30%]
Breadcrumb                    Ad 300×250
H1                            Popular conversions widget
Converter widget              Ad 300×600
Popular conversions
Ad 300×250
Content sections
Ad 300×250 mid-content
Footer
```

Sidebar is hidden on mobile. Sticky 320×50 is mobile-only.

---

## AdSense Zone Map

| Zone | Placement | Size | Device |
|------|-----------|------|--------|
| 0 | Sticky bottom | 320×50 | Mobile only |
| 1 | Below nav leaderboard | 728×90 | Desktop only |
| 2 | Above converter widget | 320×50 | Mobile only |
| 3 | Below converter widget | 300×250 | All |
| 4 | Mid-content | 300×250 | All |
| 5 | Sidebar top | 300×250 | Desktop only |
| 6 | Sidebar bottom | 300×600 | Desktop only |

Placeholder pub ID: `ca-pub-XXXXXXXXXX` — swapped before AdSense review submission.
No ads on `/about` or `/privacy-policy`.

---

## Pages Per Site

| Page | EN URL | FR URL |
|------|--------|--------|
| Homepage | `/` | `/` |
| Length | `/length-converter` | `/convertisseur-de-longueur` |
| Weight | `/weight-converter` | `/convertisseur-de-poids` |
| Temperature | `/temperature-converter` | `/convertisseur-de-temperature` |
| Volume | `/volume-converter` | `/convertisseur-de-volume` |
| Speed | `/speed-converter` | `/convertisseur-de-vitesse` |
| Area | `/area-converter` | `/convertisseur-de-surface` |
| Time | `/time-converter` | `/convertisseur-de-temps` |
| Pressure | `/pressure-converter` | `/convertisseur-de-pression` |
| Energy | `/energy-converter` | `/convertisseur-d-energie` |
| Fuel | `/fuel-consumption-converter` | `/convertisseur-de-consommation` |
| About | `/about` | `/a-propos` |
| Privacy | `/privacy-policy` | `/politique-de-confidentialite` |

Total: 13 pages per site.

---

## Required Public Files (both sites)

- `public/sitemap.xml` — all 13 pages listed with canonical URLs
- `public/robots.txt` — allow all crawlers
- `public/ads.txt` — single line: `google.com, pub-XXXXXXXXXX, DIRECT, f08c47fec0942fa0`

---

## SEO

**EN title pattern:** `[Category] Converter — Free Online Tool | UnitConverter`
**FR title pattern:** `Convertisseur [Catégorie] — Outil Gratuit en Ligne | Convertisseur`

Each page has:
- `<title>` — per pattern above
- `<meta name="description">` — under 160 chars, keyword-targeted, unique per page
- `<h1>` — matches title intent
- Canonical URL — correct per locale and slug
- Open Graph tags (title, description, url)

---

## File Structure

```
unit-converter-site/           (or convertisseur-en-ligne-site/)
├── src/
│   ├── app/
│   │   ├── layout.tsx         Root layout, nav, footer, AdSense script tag
│   │   ├── page.tsx           Homepage
│   │   ├── globals.css        Tailwind base + design tokens
│   │   ├── about/page.tsx
│   │   ├── privacy-policy/page.tsx
│   │   └── [slug]/page.tsx    Dynamic converter page (all 10 categories)
│   ├── components/
│   │   ├── Nav.tsx            Dark nav with search
│   │   ├── Footer.tsx
│   │   ├── AdZone.tsx         AdSense zone wrapper (client component)
│   │   ├── ConverterWidget.tsx  1:1 From/To widget (client component)
│   │   └── PopularLinks.tsx   Inline popular conversion links
│   ├── lib/
│   │   ├── converters/        One file per category — units + conversion logic
│   │   │   ├── length.ts
│   │   │   ├── weight.ts
│   │   │   ├── temperature.ts
│   │   │   ├── volume.ts
│   │   │   ├── speed.ts
│   │   │   ├── area.ts
│   │   │   ├── time.ts
│   │   │   ├── pressure.ts
│   │   │   ├── energy.ts
│   │   │   └── fuel.ts
│   │   ├── registry.ts        Map slug → converter config
│   │   └── popular.ts         Hardcoded popular conversion links (20 per category)
│   └── locales/
│       ├── en.json            All UI strings in English
│       └── fr.json            All UI strings in French
├── public/
│   ├── sitemap.xml
│   ├── robots.txt
│   └── ads.txt
├── next.config.js             output: 'export'
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## Converter Config Shape

```typescript
export interface ConverterConfig {
  slug: string                  // e.g. 'length-converter'
  category: string              // e.g. 'length'
  units: Unit[]                 // all units for this category
  defaultFrom: string           // unit code, e.g. 'm'
  defaultTo: string             // unit code, e.g. 'ft'
  convert: (value: number, from: string, to: string) => number
  popularLinks: PopularLink[]   // 20 hardcoded pairs per category
}

export interface Unit {
  code: string      // e.g. 'm'
  labelEn: string   // e.g. 'Meter'
  labelFr: string   // e.g. 'Mètre'
}

export interface PopularLink {
  fromCode: string
  toCode: string
  labelEn: string   // e.g. 'meters to feet'
  labelFr: string   // e.g. 'mètres en pieds'
}
```

---

## Design Tokens

Matching the dark nav + clean card aesthetic chosen in brainstorming:

- Nav background: `#111827` (dark)
- Nav text: `#ffffff`
- Page background: `#f9fafb`
- Card background: `#ffffff`
- Card border: `#e5e7eb`
- Primary accent: `#2563eb` (blue — links, active states)
- Text primary: `#111827`
- Text secondary: `#6b7280`
- Ad zone background: `#fef9c3` (placeholder only, removed in production)

---

## Build and Deploy Flow

1. Build EN: `npm run build` in `unit-converter-site/` — generates `out/`
2. Test locally: `npx serve out/` — verify all pages, all conversions, all ad zones, all three breakpoints
3. Push EN to `bokar83/unit-converter-site`
4. Build FR: copy source folder to `convertisseur-en-ligne-site/`, set `NEXT_PUBLIC_LOCALE=fr`, run `npm run build`
5. Test FR locally
6. Push FR to `bokar83/convertisseur-en-ligne-site`
7. Connect both repos to Hostinger via `/hostinger-deploy` skill

---

## Done When

- `npm run build` passes with zero errors for both EN and FR
- All 10 converter pages work in browser (1:1 real-time conversion confirmed)
- Homepage shows all 10 categories + 20 popular conversion links
- `sitemap.xml`, `robots.txt`, `ads.txt` present in `out/` for both sites
- AdSense placeholder tags in place on all converter pages
- Mobile (375px), desktop (1280px), tablet (768px) verified in browser
- Both repos pushed to GitHub under `bokar83`
- Hostinger Git connection live for both sites
