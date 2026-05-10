---
name: clone-builder
description: |. Triggers on "clone-builder", "build this clone", "start building", "clone targets", "build the target".
  Takes a Clone Targets Notion record by name and executes the full build pipeline:
  fetch Launch Brief → profile the target site → generate copy in target language →
  scaffold the build → deploy via vercel-launch → update Notion status to Building.
  Uses website-intelligence for competitive research, boub_voice_mastery for language
  copy, seo-strategy for keyword targeting, and vercel-launch for deployment.
  Trigger with: "clone-builder", "/clone-builder [name]", "build [target name]",
  "start building [target]", "go on [target name]".
allowed-tools: Read, Write, Grep, Glob, Bash, WebSearch, WebFetch, mcp__claude_ai_Notion__notion-search, mcp__claude_ai_Notion__notion-fetch, mcp__claude_ai_Notion__notion-update-page
---

# clone-builder — Clone-to-Launch Pipeline

You take a scouted target from Notion and build it. Your job is to produce a
working, deployed website or tool that ships **bilingual by default** — English always
plus the Language Target from the Notion record (FR, AR, PT, etc.).

**Bilingual is non-negotiable.** Every build has an English version AND a target-language
version. Not a toggle, not a language switcher — separate SEO-optimized routes:

```
/          → English (global audience, highest AdSense CPC)
/fr        → French (FR/Belgium/Quebec + West Africa)
/ar        → Arabic (MENA — only if Language Target = AR)
/pt        → Portuguese (Brazil/Portugal — only if Language Target = PT)
```

Why both:
- Double SEO surface from one codebase
- English pages earn 3-5x more AdSense CPC, subsidizing language-target traffic while it builds
- Existing English competitors have no FR/AR/PT routes — you have all of theirs plus yours

You do NOT redesign. You do NOT add features beyond the brief. Clone first, improve second.
The 1-5% improvement is always: language localization + market-specific data (rates, currency, law).

**Clone Targets Notion DB ID:** `1e54c4a6-d7dc-4031-b730-89f504257493`
**Data Source ID:** `collection://f19ceb0d-055a-4ee7-bf58-91d9e3c090e1`

---

## BEFORE YOU START

1. Read the target name from the user's argument: `/clone-builder [name]`
2. Fetch the record from the Clone Targets Notion DB by searching for the name
3. Read the full Launch Brief, Clone Play, Tech Stack, Language Target, Enhancement Idea
4. Confirm Clone Difficulty and route to the correct Build Mode below
5. Announce the plan before touching any code — one sentence: "Building [name] via Mode [A/B/C] in [language]. Estimated time: [X days]."

---

## PHASE 0 — FETCH TARGET FROM NOTION

Search for the target record:

```
Search Clone Targets DB for: [user-provided name]
Extract: Name, URL, Launch Brief, Clone Play, Tech Stack, Clone Difficulty,
         Language Target, Enhancement Idea, Distribution Channel, Viability Score
```

If not found: ask user to confirm the exact name as it appears in Notion.

---

## PHASE 1 — PROFILE THE TARGET

Use WebFetch to scrape the reference URL from the Launch Brief.

Extract:
- Visual structure: hero, value prop, primary CTA, nav items, footer
- Copy: headline, subheadline, feature bullets, pricing copy
- Color palette: dominant colors from CSS or inline styles
- Font families: check Google Fonts links or font-face declarations
- Tech stack confirmation: Next.js (`_next/static`), WP (`wp-content`), Webflow, Framer, Carrd
- Monetization: pricing page structure, checkout type, AdSense scripts
- Form fields: what inputs does the tool take, what does it output

**For calculator/utility sites specifically:**
- Document every input field name and type
- Document the calculation logic if visible in page source or JS
- Document the output display format
- Note any PDF export or email capture mechanics

This profile becomes your build spec. Do not proceed to Phase 2 until it is complete.

---

## PHASE 2 — GENERATE COPY IN BOTH LANGUAGES

Every build requires two full copy sets: English AND the Language Target from Notion.
Generate both before writing any code. Store them in `content.ts` as separate objects.

### English copy (always required)

Write for a global English audience. US terminology for financial tools.

```typescript
// content.ts
export const en = {
  meta: {
    title: "...",           // SEO title, include primary keyword
    description: "...",     // 155 chars max, include keyword
  },
  hero: {
    headline: "...",        // benefit-led, max 8 words
    subheadline: "...",     // max 20 words, addresses the pain
    cta: "...",             // primary button text
  },
  features: ["...", "...", "..."],  // 3 bullets, what it does not what it is
  footer: { tagline: "..." },
  // calculator-specific:
  inputs: { fieldName: "label", ... },
  outputs: { resultName: "label", ... },
  errors: { required: "...", invalid: "..." },
}
```

### Target language copy (always required)

Based on Language Target from the Notion record:

- **FR**: French. Formal "vous" for B2B, informal "tu" for consumer. Adapt to market
  context — France uses Euro and French tax law; CI/Senegal use FCFA, CNPS, IRPP.
  Do not just translate — localize the pain point and the cultural reference.
- **AR**: Modern Standard Arabic (MSA). RTL layout required. Add `dir="rtl"` to html tag.
  Reference Hijri calendar and Islamic finance modes where relevant.
- **PT**: Brazilian Portuguese unless market is Portugal/Mozambique.
  BR uses Pix, PT uses MB Way — payment references must match.

```typescript
export const fr = {
  meta: {
    title: "...",           // French keyword — different keyword than EN, not a translation
    description: "...",
  },
  hero: {
    headline: "...",
    subheadline: "...",
    cta: "...",
  },
  features: ["...", "...", "..."],
  footer: { tagline: "..." },
  inputs: { fieldName: "libellé", ... },
  outputs: { resultName: "libellé", ... },
  errors: { required: "...", invalid: "..." },
}
```

**Key rule:** The FR/AR/PT keyword in the meta title must be the actual search term people
use in that language — not a word-for-word translation of the English keyword.
"Paycheck calculator" → "calculateur salaire net" (not "calculateur de chèque de paie").
Research the actual term with one WebSearch if unsure.

---

## PHASE 3 — BUILD

Route to the correct mode based on Clone Difficulty from Notion.

### MODE A — Easy (Calculator / Static Utility Tool)
*Clone Difficulty: Easy | Tech Stack: HTML/JS or pure utility*

This is the most common mode. Build a single-page Next.js app.

**Structure:**

```
output/apps/[site-name]-app/
├── pages/
│   ├── index.tsx          # English version — /
│   └── fr/
│       └── index.tsx      # French version — /fr (or /ar, /pt)
├── lib/
│   ├── calculator.ts      # Shared calculation logic (language-agnostic)
│   └── content.ts         # All copy: export const en = {...}; export const fr = {...}
├── components/
│   └── Calculator.tsx     # Shared UI component, accepts content prop
├── public/
│   └── favicon.ico
├── styles/
│   └── globals.css        # Match target site colors/fonts (generate via tweakcn, see `skills/ui-styling/references/shadcn-theming.md`)
├── package.json
└── next.config.js
```

**Routing pattern — both pages import the same Calculator component, different content:**

```tsx
// pages/index.tsx (English)
import { en } from '../lib/content'
import Calculator from '../components/Calculator'
export default function Home() {
  return <Calculator content={en} lang="en" />
}

// pages/fr/index.tsx (French)
import { fr } from '../lib/content'
import Calculator from '../components/Calculator'
export default function HomeFR() {
  return <Calculator content={fr} lang="fr" />
}
```

**Language switcher in nav:** Add a simple EN | FR toggle that links between `/` and `/fr`.
No i18n library needed — two static pages, one shared component.

**Build steps:**
1. Create the folder structure above in `output/apps/[site-name]-app/`
2. Write all calculation logic in `lib/calculator.ts` — pure functions, no UI, no strings
3. Write both copy sets in `lib/content.ts` (EN + target language from Phase 2)
4. Build `components/Calculator.tsx` accepting a `content` prop — renders both languages
5. Style to match the reference site's visual structure (colors, layout, typography)
6. Create both page routes: `pages/index.tsx` (EN) and `pages/fr/index.tsx` (or `/ar`, `/pt`)
7. Wire AdSense placeholder in Calculator component (one slot, appears on both language pages)
8. Add email capture form if Launch Brief specifies it (Formspree, same form ID both languages)
9. Mobile-first: 375px base, 1280px desktop

**Calculator logic rule:** Do not approximate. If the reference site calculates CNPS at
6.3% employee contribution, your code must calculate exactly 6.3%. Look up the real
rate if the reference site doesn't show it. Accuracy is the product.

**Enhancement (1-5% only):** Apply the Enhancement Idea from the Notion record.
Examples: add FCFA currency formatting, add PDF export button, add a "What does this mean?"
tooltip explaining the result in plain language. One enhancement, no more.

### MODE B — Medium (WordPress / CMS / Digital Product)
*Clone Difficulty: Medium | Revenue Source: Digital Product or Affiliate*

**Build steps:**
1. Generate product listing copy in full (title, description, bullet points, FAQ)
2. Create a Gumroad-ready product page structure (use WebFetch to scrape gumroad.com/l/any-product for reference format)
3. Build a landing page in Next.js: hero → product preview → buy CTA → FAQ
4. The actual digital product (PDF template, spreadsheet) must be described in detail — Boubacar creates it, you spec it out completely
5. Wire Gumroad buy link placeholder: `<!-- GUMROAD_PRODUCT_LINK -->`
6. Apply all copy in target language from Phase 2

**Product spec format:**
```
PRODUCT: [name]
FORMAT: [PDF / Google Sheets / Canva template / etc.]
PAGES/TABS: [list]
CONTENT OUTLINE: [section by section]
WHAT MAKES IT BETTER THAN THE REFERENCE: [specific improvement]
PRICE POINT: $[X] (reference site charges $[Y])
```

### MODE C — Hard (SaaS / Full App)
*Clone Difficulty: Hard | Revenue Source: SaaS*

Hard clones require a planning phase before any code.

**Steps:**
1. Produce a one-page MVP spec:
   - Core feature (the one thing the app does on day 1)
   - What is NOT in v1 (scope cut explicitly)
   - Database schema (3-5 tables max for MVP)
   - Auth needed? (yes/no — if yes, use Clerk or NextAuth)
   - Payment needed day-1? (yes/no — if yes, use Stripe)
2. Present the spec to Boubacar and get approval before writing code
3. After approval: scaffold with Next.js + vercel-launch, implement core feature only
4. Apply copy in target language

**Hard clone rule:** If the reference site has 20 features, your v1 has 1. The one feature
that validates the core value proposition. Everything else is roadmap.

---

## PHASE 4 — DEPLOY

After the build is complete and code is written:

**Step 1 — Preview (Vercel, for testing + client review):**

1. Run the vercel-launch skill:
   ```
   /vercel-launch [site-name]
   ```
   This handles: GitHub repo creation, git init/commit/push, Vercel linking, **preview deploy only**.

2. Report the preview URL. This is for mobile testing and sharing with Boubacar.
   **This is NOT the live site.** Vercel = preview only.

3. Do NOT deploy to production yet. Boubacar reviews first.

**Step 2 — Production (Hostinger, after Boubacar approves):**

When Boubacar says "go live", "push it live", or "to production":

- Use the `hostinger-deploy` skill
- All live/production sites go to Hostinger, not Vercel
- Vercel preview URL stays active for reference but is never the production URL

---

## PHASE 5 — SEO TARGETING

After deploy, run the seo-strategy skill on the live preview URL:

```
/seo-strategy [preview URL]
```

This generates:
- Target keyword cluster (3-5 keywords, with estimated monthly search volume)
- Meta tags to add
- H1/H2 structure recommendation
- One quick-win content addition (e.g., "add a 200-word FAQ section below the calculator")

Apply the meta tags directly to the build. Report the keyword cluster.

---

## PHASE 6 — UPDATE NOTION

Update the Clone Targets record:
- Status: Scout → Building
- Notes: "Preview live at [URL]. Built [date]. Stack: Next.js + Vercel."

---

## PHASE 7 — HANDOFF REPORT

Print a concise handoff to terminal:

```
╔══ BUILD COMPLETE ══════════════════════════════════════════════════╗
║ Target: [Name]                                                      ║
║ Score: [X/40] | Difficulty: [Easy/Medium/Hard]                     ║
║ Language: [FR/AR/PT/EN] | Market: [specific market]                ║
╠════════════════════════════════════════════════════════════════════╣
║ PREVIEW: [Vercel URL]                                               ║
║ REPO: [GitHub URL]                                                  ║
╠════════════════════════════════════════════════════════════════════╣
║ MONETIZATION READY?                                                 ║
║ AdSense slots: [Yes / No — add account ID to go live]              ║
║ Stripe: [Yes / No — add keys to .env to go live]                   ║
║ Gumroad: [Yes / No — add product link to go live]                  ║
╠════════════════════════════════════════════════════════════════════╣
║ NEXT STEP:                                                          ║
║ [Single action to take in the next 30 minutes]                     ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## BUILD STANDARDS (apply to every Mode)

### Visual cloning rules
- Match the reference site's color palette within 2 shades
- Match the primary font family (use Google Fonts if available)
- Match the layout structure: hero → value proof → tool/CTA → footer
- Mobile-first: 375px base, 1280px desktop breakpoint
- No emojis in UI unless the reference site uses them

### Code standards
- TypeScript always (not plain JS)
- Tailwind CSS for styling (install in every project)
- No unnecessary dependencies — if vanilla JS can do it, use vanilla JS
- All strings in a `content.ts` file — never hardcode copy in JSX
- No console.log in production code

### Performance standards
- No images over 200KB (use Next.js Image component)
- Lighthouse score target: 90+ on mobile
- No third-party scripts except AdSense and analytics

### Accuracy standards
- Calculator logic must be verified against the reference site with 3 test inputs
- Currency formatting must match the target market (FCFA not USD for West Africa)
- Date formatting must match target locale

---

## MONETIZATION WIRING

### AdSense (for calculator/utility sites)
Add this placeholder in the JSX where ads should appear:
```jsx
{/* ADSENSE: Replace with your publisher ID */}
{/* <ins className="adsbygoogle" data-ad-client="ca-pub-XXXXXXXX" data-ad-slot="XXXXXXXX" /> */}
```
Tell Boubacar: "Apply for AdSense at google.com/adsense. Once approved, add your publisher
ID and slot ID to replace these placeholders."

### Stripe (for SaaS/subscription tools)
If the Launch Brief specifies SaaS revenue:
- Add Stripe to package.json: `npm install stripe @stripe/stripe-js`
- Create `/api/checkout.ts` with a Stripe Checkout session
- Add `STRIPE_SECRET_KEY` and `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` to `.env.example`
- Tell Boubacar: "Add your Stripe keys to .env to activate payments."

### Gumroad (for digital products)
- Wire the CTA button to: `https://[username].gumroad.com/l/[product-slug]`
- Leave as `<!-- GUMROAD_PRODUCT_LINK -->` placeholder until Boubacar creates the listing

### Email capture (lead gen + newsletter)
- Post directly to Supabase REST API — no extra accounts, no per-site IDs
- All sites feed into one `clone_leads` table, filtered by `source` field
- API endpoint: `POST https://jscucboftaoaphticqci.supabase.co/rest/v1/clone_leads`
- Required headers: `apikey` and `Authorization` from `NEXT_PUBLIC_SUPABASE_KEY`
- Payload: `{ email, source: "[site-name]", source_language: "en"|"fr", created_at }`
- Table must exist in Supabase before first build (create once, reuse forever):
  ```sql
  create table clone_leads (
    id uuid default gen_random_uuid() primary key,
    email text not null,
    source text not null,
    source_language text default 'en',
    source_url text,
    created_at timestamptz default now()
  );
  ```
- Add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_KEY` to each site's `.env.local`
  (use the publishable key — safe to expose in frontend)

---

## IMPORTANT RULES

1. **Clone first.** Do not redesign. If the reference site has a blue button, yours is blue.
   The 1-5% improvement is language localization + one Enhancement Idea from Notion. That's it.

2. **Language is the moat.** Every string must be in the target language. No bilingual MVP.
   A French calculator that shows English error messages is a broken product.

3. **Accuracy over speed.** A calculator that computes the wrong tax rate is worse than no calculator.
   Verify every formula. Look up real rates if needed.

4. **Preview before production.** Never push to production in this skill. Boubacar reviews, then deploys.

5. **Monetization placeholders always.** Every build ships with AdSense/Stripe/Gumroad
   placeholders pre-wired. Activation is a one-line change, not a build task.

6. **Update Notion every time.** Status = Building the moment the preview is live. Never leave
   a record stuck at Scout when the build has started.

7. **This skill runs in Claude Code.** All Notion updates use the Notion MCP.
   All deploys use the vercel-launch skill. Do not deviate.

---

## REFERENCE: PRIORITY MARKET RATES (verify before use)

### Ivory Coast (CI) — CNPS rates
- Employee: 6.3% (capped at 1,647,315 FCFA/yr)
- Employer: 18.3% total (12.% workplace accidents + 5.75% family allowance + 0.55% training)
- IRPP brackets: 0-600K FCFA/yr = 0%, 600K-1.2M = 10%, 1.2M-2M = 15%, 2M+ = 25%
- Source: verify at impots.gouv.ci before building

### Senegal — IPRES + IR rates  
- Employee IPRES: 5.6% (general) + 2.4% (cadre)
- Employer IPRES: 8.4% (general) + 3.6% (cadre)
- IR brackets: similar progressive structure — verify at impots.gouv.sn

### UEMOA — BCEAO base rate
- Check current rate at bceao.int before hardcoding any loan interest rate

### Morocco — CNSS + IR
- Employee CNSS: 4.48% (illness) + 1.98% (retirement)
- Employer CNSS: 1.57% (illness) + 7.93% (retirement) + AMO contributions
- IR: progressive 0-38% — verify at tax.gov.ma
