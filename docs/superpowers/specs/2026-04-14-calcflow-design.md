# CalcFlow — Design Spec

**Date:** 2026-04-14  
**Status:** Approved for implementation

---

## What We Are Building

CalcFlow is a standalone calculator website and PWA targeting a global audience. It is monetized via Google AdSense display ads, a freemium Pro subscription ($7/mo, $49/yr, $79 lifetime), and affiliate revenue on finance pages. It is not tied to Catalyst Works branding except for a small footer credit.

The site competes directly with TheCalculatorSite.com. Strategy: clone what works, enhance execution only where it genuinely improves the product.

**Wave 1 (this build):** 30 finance calculators + 10 health calculators. Finance-first because finance pages earn $15-40 RPM vs $3-8 for general math, and are the only pages with affiliate revenue potential. This gets to $1K/month at ~20K visitors instead of ~50K.

**Wave 2 (future):** Math, Date/Time, Conversions, Home/Garden categories.

---

## Brand

- **Name:** CalcFlow
- **Domain:** TBD (calcflow.io preferred, or calcflow.app)
- **Tagline:** "Every number, answered."
- **Footer credit only:** "Created by Catalyst Works" — no other brand tie-in
- **Color system:**
  - Teal: `#0F766E` (primary)
  - Teal dark: `#0D5C57`
  - Teal pale: `#F0FDFA`
  - Deep Slate: `#0C3547` (nav, footer, gradients)
  - Orange: `#FF6B35` (CTA, Pro badge, affiliate)
  - Off-white: `#F8FAFB` (page background)
  - Border: `#E5E7EB`
  - Text-1: `#1A1F36`, Text-2: `#6B7280`, Text-3: `#9CA3AF`
- **Typography:** Inter (Google Fonts), weights 400/500/600/700/800
- **Design reference mockups:** `.superpowers/brainstorm/1981-1776199291/content/`
  - `homepage-mockup-v3-final.html` — homepage
  - `calculator-page-v2.html` — calculator page template

---

## Tech Stack

- **Framework:** Next.js 14 App Router (TypeScript)
- **Styling:** Tailwind CSS with custom design tokens matching the color system above
- **Deployment:** Vercel
- **Repo:** `bokar83/calcflow` (GitHub)
- **Local folder:** `d:/Ai_Sandbox/calcflow`
- **PWA:** next-pwa (service worker, offline support, installable)
- **Analytics:** Vercel Analytics + Google Analytics 4
- **Ads:** Google AdSense (client-side, async)
- **Database:** None for wave 1 (static calculator data in JSON/TS)
- **Pro auth:** Supabase Auth + Stripe (wave 2 — not in this plan)

---

## Site Architecture

```
/                           Homepage — category grid + featured calculators
/finance/                   Finance hub — all 30 finance calculators listed
/health/                    Health hub — all 10 health calculators listed
/finance/[slug]/            Individual finance calculator page
/health/[slug]/             Individual health calculator page
/pro/                       Pro upgrade page
/about/                     About page
/sitemap.xml                Auto-generated sitemap
/robots.txt                 Auto-generated
```

---

## Page Structure — Calculator Page

Each calculator page follows this layout (see `calculator-page-v2.html` for pixel-accurate reference):

1. **Sticky anchor ad** — 320x50, mobile only, fixed bottom (Zone 0)
2. **Leaderboard ad** — 728x90, desktop only, top of page (Zone 1)
3. **Nav** — logo + category links + search + Pro CTA. Mobile: compact with search + Pro button
4. **Breadcrumb** — Home > Category > Calculator Name
5. **Main content** (left, ~70% width on desktop, full width mobile):
   - Page title card — h1, subtitle, "Updated [date]" line (no individual author attribution — content is from CalcFlow Editorial)
   - Calculator tabs (e.g. Basic / Advanced / Reverse / Chart)
   - Calculator widget — currency selector, inputs, Calculate button, results gradient block, affiliate strip
   - In-feed ad — 300x250 after calculator widget (Zone 2)
   - Content sections — How to use, Formula, Reference table, Country median table, FAQ, Disclaimer, Related calculators grid
   - In-content ad — 300x250 mid-content (Zone 3)
6. **Sidebar** (right, ~268px on desktop, hidden on mobile):
   - Ad 300x250 (Zone 4)
   - Popular in Finance widget
   - Pro upgrade widget (gradient)
   - Ad 300x600 (Zone 5)
   - Data sources widget
7. **Footer** — 4-col on desktop, 2-col on tablet, stacked on mobile. "Created by Catalyst Works" credit line

---

## Currency Selector

**6 pinned buttons:** USD, EUR, GBP, AED, INR, CAD (quick-access; also present in dropdown for search)

**"More currencies" dropdown** — searchable, grouped by region. Pinned 6 appear at the top of their respective regional groups so they are findable by search:

- Americas: **USD**, **CAD**, MXN, BRL, ARS, COP, CLP, PEN
- Europe: **EUR**, **GBP**, CHF, SEK, NOK, DKK, PLN, TRY, CZK, HUF, RON, RUB
- Middle East: **AED**, SAR, QAR, KWD, BHD, OMR, JOD, IQD, ILS
- Africa: ZAR, EGP, NGN, ETB, KES, TZS, GHS, MAD, DZD, TND, XOF, XAF, GNF, UGX, AOA, MZN
- Asia Pacific: **INR**, JPY, CNY, KRW, SGD, HKD, AUD, NZD, THB, MYR, PHP, IDR, VND, PKR, BDT, LKR, NPR, MMK, TWD, KHR

All DOM manipulation via `textContent` only — no innerHTML. Data stored in `data-code`, `data-sym`, `data-label` attributes.

---

## Mobile-First Responsive

Priority: **375px mobile** > **1280px desktop** > **768px tablet**

Mobile rules:
- Nav collapses to logo + search input + Pro button
- Leaderboard ad hidden; sticky anchor ad shown (fixed bottom)
- Single-column layout (sidebar drops below main)
- Results grid: 2x2 instead of 4x1
- Tabs: horizontally scrollable, no wrapping
- Input grid: single column
- Affiliate strip: stacks vertically
- Related grid: 2 columns
- Footer: 2-col then stacked

---

## Monetization Architecture

### AdSense Zones (per page)
| Zone | Placement | Size | Device |
|------|-----------|------|--------|
| 0 | Sticky anchor bottom | 320x50 | Mobile only |
| 1 | Below nav leaderboard | 728x90 | Desktop only |
| 2 | Below calculator widget | 300x250 | All |
| 3 | Mid content | 300x250 | All |
| 4 | Sidebar top | 300x250 | Desktop only |
| 5 | Sidebar bottom | 300x600 | Desktop only |

### Affiliate (Finance pages only)
Wire affiliate CTA inside the results block, not in sidebar. Partners: LendingTree, SoFi, Betterment (context-sensitive per calculator type).

**Rule:** Affiliate link appears only after user has interacted with the calculator (result is shown).

### Pro Tier (UI only in wave 1 — no auth yet)
- $7/month, $49/year, $79 lifetime
- Shown in: sidebar widget, Pro banner strip, nav button, upgrade page
- Features teased: no ads, PDF export, history, API access, batch calculations

---

## Wave 1 Calculator Inventory

### Finance (30)

**Salary & Income**
1. Hourly to Annual Salary (`hourly-to-salary`)
2. Salary to Hourly (`salary-to-hourly`)
3. Take-Home Pay / Net Salary (`take-home-pay`)
4. Overtime Pay (`overtime-pay`)
5. Raise Calculator (`raise-calculator`)
6. Salary Comparison (`salary-comparison`)

**Loans & Debt**
7. Loan Payment (`loan-payment`)
8. Mortgage Payment (`mortgage-payment`)
9. Auto Loan (`auto-loan`)
10. Personal Loan (`personal-loan`)
11. Student Loan (`student-loan`)
12. Debt Payoff (`debt-payoff`)
13. Debt-to-Income Ratio (`debt-to-income`)

**Savings & Investment**
14. Compound Interest (`compound-interest`)
15. Simple Interest (`simple-interest`)
16. Savings Goal (`savings-goal`)
17. Investment Return (`investment-return`)
18. 401k / Retirement (`retirement-savings`)
19. Emergency Fund (`emergency-fund`)

**Tax**
20. Income Tax Estimator (`income-tax`)
21. Capital Gains Tax (`capital-gains-tax`)
22. Sales Tax (`sales-tax`)
23. VAT Calculator (`vat-calculator`)

**Business & Misc Finance**
24. Profit Margin (`profit-margin`)
25. Break-Even Point (`break-even`)
26. ROI Calculator (`roi-calculator`)
27. Inflation Calculator (`inflation`)
28. Currency Converter (`currency-converter`)
29. Tip Calculator (`tip-calculator`)
30. Percentage Calculator (`percentage`)

### Health (10)

1. BMI Calculator (`bmi`)
2. BMR / Daily Calorie Needs (`bmr-calories`)
3. Body Fat Percentage (`body-fat`)
4. Ideal Body Weight (`ideal-body-weight`)
5. Calorie Deficit (`calorie-deficit`)
6. Water Intake (`water-intake`)
7. Heart Rate Zones (`heart-rate-zones`)
8. Pregnancy Due Date (`due-date`)
9. Ovulation / Fertile Window (`ovulation`)
10. Sleep Calculator (`sleep-calculator`)

---

## SEO Architecture

Every calculator page includes:
- `<title>` — "[Calculator Name] — Free Online Calculator | CalcFlow"
- `<meta description>` — 155 chars, includes primary keyword
- `<h1>` — calculator name
- JSON-LD: `FAQPage` schema (4+ Q&As per page)
- JSON-LD: `HowTo` schema (steps derived from calculator usage)
- JSON-LD: `Article` schema (author, datePublished, dateModified)
- Content length: 1,400-1,800 words per page
- Internal linking: related calculators section (6 cards minimum)
- Canonical URL on every page
- Open Graph + Twitter Card meta tags
- Auto-generated sitemap.xml with lastmod dates

---

## File Structure

```
d:/Ai_Sandbox/calcflow/
├── app/
│   ├── layout.tsx                    Root layout, nav, footer, AdSense script
│   ├── page.tsx                      Homepage
│   ├── globals.css                   Design tokens, global styles
│   ├── finance/
│   │   ├── page.tsx                  Finance hub
│   │   └── [slug]/
│   │       └── page.tsx              Finance calculator page (dynamic)
│   ├── health/
│   │   ├── page.tsx                  Health hub
│   │   └── [slug]/
│   │       └── page.tsx              Health calculator page (dynamic)
│   └── pro/
│       └── page.tsx                  Pro upgrade page
├── components/
│   ├── Nav.tsx                       Top navigation
│   ├── Footer.tsx                    Footer
│   ├── AdZone.tsx                    AdSense zone wrapper (client component)
│   ├── calculator/
│   │   ├── CalculatorShell.tsx       Tabs + widget wrapper
│   │   ├── CurrencySelector.tsx      Pinned buttons + dropdown
│   │   ├── ResultsBlock.tsx          Gradient results display
│   │   ├── AffiliateStrip.tsx        Affiliate CTA (finance only)
│   │   └── ProWidget.tsx             Sidebar Pro upgrade widget
│   └── content/
│       ├── FormulaBox.tsx            Monospace formula display
│       ├── RefTable.tsx              Reference data table
│       ├── FaqSection.tsx            FAQ accordion
│       ├── RelatedGrid.tsx           Related calculators 6-card grid
│       └── JsonLd.tsx                JSON-LD schema injector
├── lib/
│   ├── calculators/
│   │   ├── types.ts                  Calculator config type definitions
│   │   ├── finance/
│   │   │   ├── hourly-to-salary.ts   Calculator logic + page config
│   │   │   ├── compound-interest.ts
│   │   │   └── ... (one file per calculator)
│   │   └── health/
│   │       ├── bmi.ts
│   │       └── ... (one file per calculator)
│   ├── currencies.ts                 Full currency list with codes/symbols/flags
│   └── registry.ts                  Map slug → calculator config
├── public/
│   ├── manifest.json                 PWA manifest
│   └── icons/                        PWA icons (192, 512)
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Calculator Config Type

Each calculator is defined by a config object with this shape:

```typescript
export interface CalculatorConfig {
  slug: string
  title: string
  category: 'finance' | 'health'
  description: string
  author: string
  reviewer: string
  updatedDate: string
  tabs: Tab[]
  inputs: InputField[]
  calculate: (inputs: Record<string, number>, currency: Currency) => CalculatorResult
  resultLabels: string[]
  formula: string
  content: {
    howTo: string[]
    refTable?: { headers: string[]; rows: string[][] }
    faqs: { q: string; a: string }[]
    related: string[]  // slugs of related calculators
  }
  affiliate?: AffiliateConfig
  jsonLd: {
    faqs: { q: string; a: string }[]
    howToSteps: string[]
  }
}
```

---

## Constraints

- No server-side data fetching for calculator logic — all math runs client-side
- No innerHTML anywhere — all DOM via React (textContent equivalent through JSX)
- AdSense loads async and never blocks render
- Affiliate links appear only after calculator has been used (result is shown)
- "Created by Catalyst Works" footer text only — no Catalyst Works colors, logo, or style guide
- Mobile view at 375px must pass visual check before any page is marked complete
