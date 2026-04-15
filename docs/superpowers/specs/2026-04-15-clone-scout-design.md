# clone-scout — Design Spec
**Date:** 2026-04-15
**Status:** Approved — ready for implementation
**Type:** Claude Code Skill + Notion Database

---

## What It Is

A Claude Code skill invoked as `/clone-scout [optional: niche or keyword]`. It runs a 4-phase
research pipeline, scores targets on clone viability and revenue potential, and writes qualifying
targets to a "Clone Targets" Notion database in the same space as the Content Board.

**Goal:** Surface 2-5 high-quality clone targets per run that the operator can realistically
launch and monetize at $500-$1,000/month within 90 days.

**This skill scouts and scores only.** It does not build, deploy, or push code. Output is a
ranked shortlist for operator review and decision.

---

## Operating Principle

> Validate manually. Automate after. Nothing gets scheduled until the premise is confirmed.

The skill runs on-demand. A weekly cron (Phase 2) will be added only after the scouting
criteria are proven through 10+ manual runs.

---

## The 4 Phases

### Phase 1 — DISCOVER
Find candidates via:
- Serper search across IndieHackers, Starter Story, Reddit (r/SideProject, r/EntrepreneurRideAlong)
- Empire Flippers API (free, unauthenticated, 1 req/sec — verified revenue data)
- Gumroad + Lemonsqueezy browse pages (Firecrawl scrape of trending/popular sections)
- Chrome Web Store top earners (by category, filtered for paid tiers)
- App Store "Top Grossing" by category — US/UK storefront, then cross-referenced against
  FR/AR/PT storefronts (Senegal, Morocco, Brazil) to detect language gap directly at source
- GitHub Sponsors pages (open source with paying sponsors = proven demand)
- Serper fallback for any niche-specific keyword the operator provides

**Serper budget discipline:** Max 8 queries per run to stay within free tier (2,500/month).
One query per source group, not per candidate.

### Phase 2 — PROFILE
Firecrawl-scrape each candidate (max 10 candidates per run). Extract:

| Signal | Method |
|---|---|
| Pricing page present | URL pattern match (/pricing, /plans, /subscribe) |
| Checkout type | Footprint detection (Stripe, Gumroad, Lemonsqueezy, PayPal scripts) |
| Tech stack | Script/meta tag analysis (Webflow, Framer, Carrd, WP, Next.js, etc.) |
| hreflang / /fr /ar subdirs | Header + link tag scan (absence = language gap signal) |
| App Store review language distribution | Serper search for app name + reviews in target language |
| Site index size | `site:domain.com` Serper query (proxy for content investment) |
| Competitor density | Serper: "[product name] alternative" — count of comparison pages |
| Ad network footprints | AdSense, Mediavine, Ezoic script detection |
| Founding date | WHOIS-style meta or footer copyright year |

**What we do NOT try to get (no paid API = no reliable data):**
- Backlink count (requires SEMrush/Ahrefs)
- Social following size (Twitter API $100/month, LinkedIn blocks scraping)

These were in earlier drafts and removed. The scoring matrix is built only on data
we can reliably retrieve for free.

### Phase 3 — SCORE
Run each candidate through the Clone Viability Matrix (max 40 points).
Threshold: **30+ goes to Notion. Below 30 is printed to terminal and dropped.**
No "maybe" pile. Hard gate prevents graveyard accumulation.

### Phase 4 — LOG
Write qualifying targets to Notion "Clone Targets" database via Notion MCP.
Print a ranked terminal summary of all candidates (scored + dropped).
Auto-generate Launch Brief for each qualifying target.

---

## Clone Viability Matrix (max 40, threshold 30+)

| # | Dimension | What's measured | Max |
|---|---|---|---|
| 1 | Revenue signal | MRR estimate + source credibility. Verified (Empire Flippers P&L) = 5. Self-reported forum post = 2-3. | 5 |
| 2 | Clone simplicity | Tech stack complexity. Static/Webflow/Carrd = 5. Custom infra/mobile app = 1. | 5 |
| 3 | Monetization clarity | Pricing page visible + checkout type detectable = 5. No visible monetization = 0. | 5 |
| 4 | Language gap | Target-language version absent AND Google Trends confirms search demand in that market = 5. No gap or no demand = 0. | 5 |
| 5 | Time to launch | 1 day = 5. 3 days = 4. 1 week = 3. 2 weeks = 2. 1 month = 1. | 5 |
| 6 | Competition density | 0-2 "alternatives" pages = 5. 3-10 = 3. 10+ = 1. | 5 |
| 7 | Distribution readiness | Specific day-1 acquisition channel exists and is replicable (App Store category, SEO keyword gap, active subreddit, niche newsletter). Vague = 0. | 5 |
| 8 | Willingness to pay | Target market already pays for this category. Evidence: Capterra/G2 reviews in target language, paid competitors exist in market. Unproven = 0. | 5 |

**Scoring is done by the skill (Claude reasoning), not computed from scraped numbers.**
Each dimension gets a 1-5 score with one-line justification written to the terminal.

---

## Launch Brief (auto-generated for each 30+ target)

```
TARGET: [Name] — [URL]
VIABILITY SCORE: [X/40]

WHY NOW: [One sentence — what makes this the right moment to clone this]

CLONE PLAY: [Exact build approach — "Webflow template copy", "Next.js scaffold via vercel-launch",
             "WordPress theme on Hostinger", etc.]

LANGUAGE PLAY: [Specific market (not just "FR" but "Senegal/Ivory Coast") + payment rail that
               works there (Wave, Orange Money, Stripe) + one distribution channel with that
               audience (specific Facebook group, WhatsApp community, local directory)]
               Write N/A if English-market clone.

REVENUE PATH: [Day-1 acquisition channel] | [Target keyword cluster + monthly volume estimate]
              | [Break-even customer count] | [First revenue milestone trigger — specific, not vague]

COST TO LAUNCH: $[estimate] | [time estimate in days]

FIRST 100 USERS: [Single sentence — exactly how the first 100 users arrive. Required.
                 If you cannot answer this, score is invalid.]

FIRST ACTION: [Single next step the operator takes in the next 30 minutes]
```

**The Launch Brief is the skill's primary deliverable.** A well-scored target without a
complete Launch Brief is not ready for Notion.

---

## Hard Gates

Nothing moves from Scout to Building without:
1. First 100 Users field filled (specific, not "SEO" or "social media")
2. Cost to Launch filled (dollar amount)
3. Language Play complete with all 3 specifics (market + payment rail + channel) or explicit N/A

These are enforced as required Notion fields. Operator cannot skip them when updating status.

---

## Notion Database Schema

**Database name:** Clone Targets
**Location:** Same Notion space as Content Board

| Field | Type | Notes |
|---|---|---|
| Name | Title | Product/site name |
| URL | URL | Target URL |
| Niche | Select | Category/industry |
| Est. Monthly Revenue | Number | In USD |
| Revenue Source | Select | Ads / SaaS / Affiliate / Digital Product / Marketplace |
| Tech Stack | Text | Detected stack |
| Clone Difficulty | Select | Easy / Medium / Hard |
| Language Target | Select | EN / FR / AR / PT / ES / Other |
| Google Trends Confirmed | Checkbox | Demand verified in target market |
| Competition Density | Select | Low / Medium / High |
| Viability Score | Number | Out of 40 |
| Distribution Channel | Text | Day-1 acquisition path (required before Building) |
| First 100 Users | Text | Required before Building |
| Cost to Launch | Number | In USD, required before Building |
| Enhancement Idea | Text | What you'd add or change |
| Launch Brief | Text | Auto-generated by skill |
| Notes | Text | Reminders, lessons learned, anything |
| Source | Select | IndieHackers / EmpireFlippers / Reddit / Gumroad / AppStore / Chrome / GitHub / Other |
| What Worked | Text | Filled when Status = Revenue. Feeds future scoring. |
| Status | Select | Scout / Evaluating / Building / Live / Revenue |
| Scouted Date | Date | Auto-filled by skill |
| Revenue Confirmed Date | Date | Filled when first dollar earned |

---

## Feedback Loop

After 20+ entries with Status = Revenue, run a simple analysis:
- Which Source field appears most in revenue-confirmed targets?
- Which scoring dimensions correlated with actual revenue?
- Which Language Target markets delivered fastest?

Output becomes a config note in the skill's SKILL.md that re-weights discovery priority.
This is how the skill gets smarter over time without rebuilding it.

---

## Trigger Examples

- `/clone-scout` — general scan, all sources
- `/clone-scout saas tools` — scoped to a niche
- `/clone-scout french market` — language arbitrage angle, prioritizes FR gap detection
- `/clone-scout empire flippers` — pulls directly from Empire Flippers API only
- `/clone-scout gumroad` — Gumroad trending only, fastest run

---

## Skill File Location

- Primary: `d:/Ai_Sandbox/agentsHQ/skills/clone-scout/SKILL.md`
- Global copy: `C:/Users/HUAWEI/.claude/skills/clone-scout/SKILL.md`

---

## What This Is NOT

- Not a builder — does not scaffold, deploy, or push code
- Not a scheduler — manual trigger only until criteria are proven
- Not a CRM — does not track customers, revenue, or post-launch metrics
- Not a content tool — no social posts, no SEO writing

---

## Phase 2 (Future — after 10+ validated runs)

Add weekly cron via agentsHQ orchestrator:
- Runs every Monday, scouts 10 targets
- Pings Telegram with top 3 picks
- Only after manual scouting has validated the scoring criteria

---

## Key Design Decisions and Why

| Decision | Reason |
|---|---|
| Threshold 30/40, not 22/30 | Higher bar forces quality over quantity. A graveyard of 40 mediocre targets is worse than 5 great ones. |
| Max 10 candidates per run | Prevents Serper budget drain and keeps each run to under 20 minutes |
| Drop backlinks + social following | Both require paid APIs and return null silently. Removed to keep scoring honest. |
| Language Play requires 3 specifics | "FR" is not a market. Forces real launch thinking before logging. |
| Source field in Notion | Enables feedback loop without extra tooling |
| Hard gates before Building | Prevents graveyard accumulation — the most common failure mode |
| Notes field kept | Operator uses this for reminders and lessons learned |
