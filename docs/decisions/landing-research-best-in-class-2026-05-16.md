# Landing Page Research — Best-in-Class Digital Products + Editorial Pages

Date: 2026-05-16
Source: subagent research via WebFetch on 12 verified pages
Purpose: copy + innovate on patterns for humanatwork.ai/start-ai landing rebuild

## 12 verified pages

| URL | Title | Why it converts | Aesthetic | One thing to steal |
|---|---|---|---|---|
| acquisition.com | Do You Want to Scale Your Business? | Tactical-not-motivational. Free intro -> qualified workshop. Stacked credibility numbers. | Geometric sans, navy + white, centered hero w/ single CTA | "Expect zero motivational talks. We get tactical." → use as positioning subhead |
| lennysnewsletter.com | Deeply researched product + growth advice | Specific reader profile + 1.2M subscriber count | Substack white, near-black body, single sans, centered 720px | Name the reader profile in H1, not "everyone who wants AI" |
| jamesclear.com | Atomic Habits — Easy and Proven Way... | 25M copies sold + Time/NYT/WSJ stacked badges. Multiple free entry points | Off-white paper, near-black serif body, book cover anchor | Single photographic artifact in hero — Boubacar has zero image weight |
| cursor.com | Built to make you extraordinarily productive | Live-state UI mockups + named-figure testimonials (YC, NVIDIA, Stripe, shadcn) | Dark bg, subtle blue, system sans, bento-grid | Embedded interface mockups (real, not stock) |
| claude.com/product/overview | Meet your thinking partner | Conversational microcopy. Interactive prompt cards | White paper, near-black, blue accents, generous whitespace | Conversational subhead beats feature-promise subhead |
| stripe.com | Financial infrastructure to grow revenue | Customer-logo carousel (Amazon, Shopify, Uber, OpenAI). $1.9T scale stat | Sans-dominant, white + electric blue, modular bento | Photographic founder/customer portraits beat numeric stats alone |
| refactoringui.com | Make your ideas look awesome, without designer | $99/$149 two-tier. 20+ named testimonials (Wes Bos, Taylor Otwell). 60-day no-DRM refund. Quantified deliverables (50ch / 200pp / 200 components) | Clean sans, monochrome + 1 accent, before/after pairs | "50 chapters / 200 pages / 200 components" → quantified-substance line beats value-stack |
| tailwindcss.com/plus | Build your next idea even faster | One-time pricing ($299/$979 lifetime, NO subscription). Self-demonstration | Neutral grayscale, hairline borders, system sans, modular grid | "$19 one time. Not a subscription. Not a course-drip." |
| every.to | The Only Subscription to Stay at the Edge of AI | Dark-mode premium. Product ecosystem layered onto editorial. Practitioner tone | Dark navy, white type, blue accents, bold sans 32-48px | "Trusted by 100,000 builders" line under hero pattern |
| linear.app | Product development system for teams + agents | Repeated H1 (3x emphasis). "Issue tracking is dead" — sells against the category | White/near-black bg, system sans, modular product screenshots | Anti-category positioning. "Prompt-pack PDFs are dead." |
| julian.com | I invest in deeptech startups. Are you fundraising? | Single declarative sentence. 4 illustrated handbooks as content moat. No testimonials | Dark charcoal, light gray text, bright blue links, serif-influenced sans, asymmetric blocks | The 4-handbook visual moat — show illustrated covers as catalog depth |
| commoncog.com | Do Business Like You've Seen It Before | Logo wall (Microsoft, Amazon, Berkshire, GC). Free 7-day email course as funnel entry | Premium B2B neutral, dark-mode toggle, serif body / sans hero | Free 7-day email course as lead magnet for non-buyers |

## 5 cross-cutting patterns (3+ winners share)

1. **Anti-category positioning in or below H1.** Linear "Issue tracking is dead". acquisition.com "zero motivational talks". refactoringui "without relying on a designer". The H1 names the alternative the buyer is sick of.
2. **One photographic anchor in the hero**, not a gradient or icon. James Clear (book cover), Stripe (founder portrait), Cursor (interface mockup), Linear (product screenshot).
3. **Quantified substance lines**, not value-stacked $ math. Refactoring UI ("50 chapters, 200 pages, 200 components"), Lenny ("1.2M subscribers"), James Clear ("25M copies sold").
4. **One-time-not-subscription clarity**, named explicitly. Tailwind, Refactoring UI, Acquisition.com books. Reduces "is this gonna auto-charge me" hesitation.
5. **Named testimonials w/ role + recognizable affiliation OR no testimonials at all.** Half-credible "Sarah from HR" testimonials underperform either pole.

## 3 concrete aesthetic moves for Boubacar's rebuild

1. **H1 typography swap.** Drop Inter 56px/800. Use tighter serif-display + italic accent. CSS: `font-family: "Tiempos Headline", "Charter", "Iowan Old Style", Georgia, serif; font-size: 72px; line-height: 0.98; letter-spacing: -0.03em; font-weight: 600;` w/ one italic word inline ("`<em>start</em>` using AI within 24 hours"). Charter is already loaded; promote to H1.

2. **Hero anchor image: 16:9 photographic bleed on right side, asymmetric two-column.** CSS: `.hero { display: grid; grid-template-columns: 1.2fr 1fr; gap: 48px; align-items: center; }`. Image = real photo of Boubacar's actual setup (laptop, Claude open, coffee, Conakry artifact). Not stock. Not illustrated.

3. **Drop $219 stacked-value table. Replace with quantified-substance line + 4-cover catalog strip.** 4-column grid of covers (24h Guide, Paste Pack, Workbook, Audit) at same horizontal level as buy box. Hover reveals "ships with T2/T3/T4". Steals Julian Shapiro handbook moat.

## 2 hook formulas out-performing current "Without overwhelm"

| Hook | Out-performance reasoning |
|---|---|
| A. "Stop reading about AI. Start using it before you sleep tonight." | Anti-category (Linear pattern). Time-anchor "tonight" beats abstract "24 hours". Calls out the buyer's exact stuck loop. |
| B. "You have read 40 articles about AI. You have used it for nothing. That ends today." | Specific past behavior. 3-sentence rhythm. Decision-language not benefit-language. Maps to ship-then-adjust. |

Use A for hero H1, B for final-CTA section. Not either-or.

## Color palette recommendation — DROP warm-orange + paper

Current `#c2410c` orange + `#fed7aa` peach reads 2023-Tailwind-template. Default ramp every AI-aesthetic landing uses.

**Adopt:**
| Role | Hex | Why |
|---|---|---|
| Paper (bg) | `#F4F1EA` | Warm off-white, James Clear / Every editorial paper. Reads "book," not "SaaS." |
| Ink (body) | `#161513` | Near-black w/ warm undertone. Pairs w/ paper. |
| Editorial red (accent, sparingly) | `#B23A1F` | Penguin-paperback red. Authoritative, not Hormozi-orange. |
| Sage (secondary accent) | `#5C6B5A` | Muted text + dividers. Colored neutral. |
| Sand (section bg) | `#E8E2D3` | Section dividers. Warmer than `#ecebe5`. |

## Typography stack recommendation

- **Display H1/H2:** "Tiempos Headline" (Pangram Pangram) or fallback Charter Display / PP Editorial New. High-contrast serif w/ tight tracking.
- **Body:** Charter / Iowan Old Style / Georgia (KEEP — already loaded)
- **Microcopy + buy-box price + nav:** Inter Tight (NOT Inter) at 14-16px only. Demoted.
- **Italic accent (one word per section):** PP Editorial New Italic or Charter Italic. The editorial flourish move.
- **Monospace:** None unless code element. Boubacar's page has none currently; leave off.

## Single-page offer flow (8 sections, NO T3/T4 on landing)

1. **Hero, asymmetric 2-col** — serif H1 + italic accent + photographic anchor + buy box + "Not a subscription. Not a course-drip. One file. One read."
2. **The cost of waiting** — 1 paragraph, own section
3. **The problem is not your effort** — pain cards w/ "kitchen table in Salt Lake" opener
4. **What is inside (Chapters 1-8)** — replace "Module" w/ "Chapter" (editorial register)
5. **Catalog moat strip** — 4 illustrated covers (24h Guide, Paste Pack, Workbook, Audit). Replaces stacked-value table.
6. **Who I am. Why I built this.** — moved ABOVE FAQ. Photo of Boubacar.
7. **Common questions** — 5 entries (trim from 7). Drop "refund" + "company AI policy".
8. **Final CTA** — re-anchor w/ Hook B. Same buy box. No tier comparison.

## REMOVE from current draft

- Upsell tiers section (entire 3-tier grid) — moves to /start-ai/upgrade post-purchase
- 14-day refund everywhere
- $219 stacked-value table — replace w/ catalog strip
- "Most picked" / "Where most upgrade lives" / "Best value gap" badges
- "First 100" early-bird w/o live counter — keep "Early-bird through May 23" only

## See also

- docs/decisions/council-sales-conversion-skill-2026-05-16.md (5-voice audit)
- docs/decisions/landing-copy-rewrite-2026-05-16.md (full new copy)
- C:/Users/HUAWEI/.claude/projects/D--Ai-Sandbox-agentsHQ/memory/feedback_digital_asset_voice_boubacar_fingerprint.md
