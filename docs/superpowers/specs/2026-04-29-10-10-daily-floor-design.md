# 10+10 Daily Email Floor for CW + SW Outreach

**Date:** 2026-04-29
**Goal:** Every morning runner produces a minimum of 10 strong CW drafts and 10 strong SW drafts in `boubacar@catalystworks.consulting` Drafts. No "0 leads today" days.

**Future expansion:** When the runner goes outside Utah (Tier 3+), bump the daily floor from 10 to 20 per pipeline.

## Constraints

- Apollo budget: 2,500 credits/month (paid plan)
- Hunter.io: tier TBC at runtime; degrade gracefully on rate limit
- Firecrawl: existing usage, no incremental cost concern
- Email is non-negotiable. Every drafted lead must have a real address that the existing sequence engine can send to.

## Architecture

### CW Pipeline (Hybrid: Apollo Fresh + Resend Queue)

Goal: 10 CW emails/day. 5 fresh from Apollo + 5 resends from the existing 70-80 historical contacts in `apollo_revealed`.

```
Step 4 (CW topup), target 10 leads
  │
  ├── Slot 1-5: Apollo fresh leads
  │     └── search_leads(CW_ICP_WIDENED, page=N) for N=1..6
  │     └── Score-filter (existing ICP scorer, MIN_SCORE=2)
  │     └── Skip already-revealed IDs
  │     └── bulk_match -> emails for top 5 unrevealed
  │     └── Save to leads table with email_source='apollo_fresh'
  │
  └── Slot 6-10: Resend queue
        └── SELECT name, email, company FROM apollo_revealed
            WHERE email IS NOT NULL
              AND apollo_id NOT IN (SELECT apollo_id FROM leads
                                    WHERE last_drafted_at > NOW() - INTERVAL '60 days')
            ORDER BY revealed_at ASC
            LIMIT 5
        └── If <5 returned, top up the gap from Apollo (Slot 1-5 logic, more pages)
        └── Insert into leads with email_source='cw_resend', last_drafted_at=NULL
```

The dedup table protects against re-emailing within 60 days. Past-60-day contacts cycle back to the queue, which is fine. Different season, different message.

CW_ICP widening:
- `seniority`: add `vp` to existing `[owner, founder, c_suite]` → `[owner, founder, c_suite, vp]`
- `employees`: 1-80 → 1-200
- `cities`: add Park City, Heber, Bountiful, Logan, Cedar City (9 → 14)
- `titles`: add "Managing Member", "Director of Operations", "VP of Sales"

### SW Pipeline (Geo-Expansion Ladder + 4-Layer Email Resolution)

Goal: 10 SW emails/day at Tier 1-2 (Utah). 20/day at Tier 3+ (out of Utah).

```
Step 2 (SW topup), target N (10 in Utah, 20 outside)
  │
  └── For each (niche, city, tier) in expansion_ladder.PAIRS, in order:
        │
        ├── Skip if (niche, city) already covered today (in-memory dedup)
        │
        ├── Serper Google Maps -> N businesses for niche+city
        │
        ├── For each business:
        │     │
        │     ├── Set lead.no_website = (business.website is None or empty)
        │     │
        │     ├── Has website AND no_website == False?
        │     │     └── Firecrawl scrape -> regex email
        │     │           └── Found? lead.email_source='firecrawl', save, continue.
        │     │
        │     ├── Apollo strict match (organizations/enrich + people/match)
        │     │     ├── enrich(name, city) -> domain (free, no credits)
        │     │     │     └── No domain match? Skip Apollo + Hunter, fall to "no email" branch.
        │     │     ├── match(domain, person_titles=OWNER_TITLES) -> email (~1 credit)
        │     │     ├── Owner found? lead.email_source='apollo_strict', save, continue.
        │     │     └── Owner not found? Carry domain forward to Hunter.
        │     │
        │     ├── Hunter Domain Search (only invoked if Apollo enrich resolved a domain
        │     │                          but people/match returned no owner)
        │     │     └── Top result with seniority in [owner, founder, ceo, executive]?
        │     │           └── Found? lead.email_source='hunter_domain', save, continue.
        │     │           └── Not found? Fall to "no email" branch.
        │     │
        │     └── No email branch: log + skip (do NOT save lead)
        │
        ├── Running total >= target? STOP.
        │
        └── Else: continue to next (niche, city) pair on ladder.
```

### Geo-Expansion Ladder (signal_works/expansion_ladder.py)

Walked top-to-bottom. Daily target adjusts per tier:

| Tier | Geography                    | Niches                        | Daily target |
|------|------------------------------|-------------------------------|--------------|
| 1    | Utah core (9 cities)         | 6 niches (existing list)      | 10           |
| 2    | Utah expanded (5 more cities)| 6 niches                      | 10           |
| 3    | Mountain states (Denver, Phoenix, Las Vegas, Boise, Albuquerque) | 6 niches | 20    |
| 4    | Western US (Seattle, Portland, San Diego, Reno, Tucson) | 8 niches | 20  |
| 5    | All-US Top 50 metros         | 10 niches                     | 20           |
| 6    | North America (TO, VAN, CGY, MTL) | 10 niches                  | 20           |

When a day's run finishes, lead's `niche_city_tier` is recorded. Next day starts at Tier 1 (cycles forward). The `apollo_revealed` and `leads` dedup logic prevents re-targeting same business twice within 60 days.

## Components changing

| File | Change | Type |
|---|---|---|
| `signal_works/expansion_ladder.py` | NEW: PAIRS list of `(niche, city, tier, target_for_tier)` tuples | NEW |
| `signal_works/topup_leads.py` | Replace inner loop with ladder walk + 4-layer email resolution | REWRITE |
| `signal_works/topup_cw_leads.py` | Hybrid 5+5 logic with resend queue | UPDATE |
| `signal_works/lead_scraper.py` | Add `no_website` field to scrape output | UPDATE |
| `skills/apollo_skill/apollo_client.py` | Add `find_owner_by_company(name, city)` and `CW_ICP_WIDENED` | UPDATE |
| `signal_works/hunter_client.py` | NEW: domain-search wrapper, picks highest-confidence owner email | NEW |
| `orchestrator/db.py` | Schema: add `no_website BOOL`, `email_source TEXT`, `last_drafted_at TIMESTAMPTZ`; add `get_resend_queue(limit, days_back)` | UPDATE |
| `templates/email/sw_t1.py` | Conditional opener: if `no_website=true`, lead with web-invisibility hook | UPDATE |
| `signal_works/morning_runner.py` | Fix cosmetic `sent` vs `drafted` reporting bug | UPDATE |

## Cost projections

**Apollo (steady state, Tier 1-2 Utah):**
- CW fresh: 5 credits/day = 150/month
- SW Apollo strict-match (residual after Firecrawl): ~3 credits/day = 90/month
- **Total: ~240 credits/month** = 9.6% of 2,500 budget

**Apollo at full Tier 3+ (20/20):**
- CW fresh: 5 credits/day = 150/month (unchanged, CW stays at 10)
- SW Apollo strict-match: ~6 credits/day = 180/month
- **Total: ~330 credits/month** = 13.2% of budget

Plenty of headroom for Studio expansion or future channels.

**Hunter (residual fallback):**
- Estimated ~1 search/day on Tier 1-2, 2-3/day on Tier 3+
- 25/month at free tier covers ~Tier 1-2; **upgrade to Starter $34/mo (500 searches) needed before Tier 3**.
- **Action item:** verify Hunter tier before geo-expansion is enabled (separate decision).

**Firecrawl:** unchanged from today.

## Failure handling

- After full ladder walked: if total < target, send Telegram alert "SW pipeline finished tier-walk with N/target leads. Ladder exhausted." This is an edge case that would mean Tier 6 ran out of fresh leads, which is extremely unlikely.
- Apollo 401/403: Telegram alert "Apollo creds expired" + skip Apollo path for the day.
- Hunter 429 (rate limit): log, degrade to "skip lead", do NOT crash run.
- Per-business errors logged with business name, never halt the run.

## Hunter cost protection (revised after virtual tests)

Virtual Test 3 revealed that if Apollo+Firecrawl both fail simultaneously, Hunter becomes the only resolution path and cost explodes (~400 credits/day = 1.25 days of Starter budget gone). Even Test 2 (Firecrawl-only failure) produced 50 credits/day, exhausting free tier in half a day.

Two protections required:

1. **Daily Hunter cap:** `HUNTER_MAX_SEARCHES_PER_DAY=5` (configurable). Once hit, Hunter is skipped for remainder of run, lead resolution falls through to "no email branch" and ladder advances. Telegram alert fires once per day when cap is hit.

2. **Circuit breaker on simultaneous Apollo+Firecrawl failure:** If 5 consecutive businesses fail BOTH Firecrawl AND Apollo (suggesting infra-wide failure, not per-business), trigger Telegram alert "outreach pipeline degraded" and short-circuit Hunter for the rest of the run. Wait for Boubacar to investigate root cause. Better to ship 0 SW emails today than to burn 400 Hunter credits papering over an upstream outage.

These bound the worst-case Hunter usage to 5 searches/day = 150/month, which fits within Starter (500/mo) with margin OR within free tier ceiling of 25/month if usage is light most days.

## Email send semantics

The existing `sequence_engine.py` already handles the draft-only pipeline. No change to send logic. Drafts land in `boubacar@catalystworks.consulting` Drafts. AUTO_SEND_CW / AUTO_SEND_SW flags work unchanged.

The `email_source` column is informational. It exists for inspection and later A/B analysis ("did Hunter-sourced emails convert worse than Apollo-sourced?"). It does not change which template fires.

## What "strong" means

Boubacar's bar: every drafted email must have a deliverable address AND match the ICP. The pipeline already enforces:
- Apollo: `contact_email_status=verified` filter at search time
- Firecrawl: regex + `_is_valid_email()` (rejects role accounts, placeholders, platform emails)
- Hunter: only top-confidence + seniority filter

We add: **no email_source = NULL leads ever get drafted.** If all four resolution layers fail for a business, the lead is skipped, not saved with NULL email.

## Out of scope (followups)

- Resend cadence rules (which historical contacts go back into the queue, in what order, with what new copy). For now using simple "oldest first, NOT touched in 60 days." Worth refining once we have data.
- A/B comparison of email_source quality. Possible 2-week post-launch.
- Studio pipeline (Step 6 wiring, separate engagement).
- The cosmetic `sent` vs `drafted` reporting bug in `main()`. Bundling it as a one-line fix because we're already touching the file.

## Risks flagged

1. **Hunter free-tier exhaustion** in mid-month if Tier 3+ engaged. Mitigation: feature-flag the Hunter call; if `HUNTER_ENABLED=false`, skip that resolution layer. Boubacar can decide Starter upgrade before flipping.
2. **Apollo `organizations/enrich` may not have small Utah businesses indexed.** Mitigation: degrade gracefully. Strict match returns "no match", flow falls through to Hunter or skip. Still better than today's 0/day.
3. **Firecrawl rendering JS-heavy small biz sites poorly.** Already a problem today (yesterday returned 0). Won't fix in this design. Apollo and Hunter become the rescue paths. Worth investigating the Firecrawl render config separately.
4. **Geo-expansion never being triggered if Tier 1 keeps producing 10/day.** This is desired behavior, but means lower tiers' niche/city pairs sit unused. That's fine. They're a safety net.
