---
name: website-teardown
description: Two-mode pipeline that audits a prospect website. COLD mode = lean outbound-email teardown (Phase 0 auto-filter + 3-leak markdown + paste-ready cold email). WARM mode = full 6-phase pipeline with HTML internal-viability + client-facing report + before/after mockup. Triggers on "website-teardown", "teardown this site", "cold teardown", "warm teardown", "run a teardown", "should we pursue this lead", or /website-teardown URL.
---

# website-teardown

**Trigger:** `/website-teardown URL` or "teardown DOMAIN"

**Two modes, pick by intent:**

| Mode | Use when | Audience | Output | Cost |
|---|---|---|---|---|
| `cold` (default) | Outbound to a prospect who has never heard of us. Goal: provoke reply. | Stranger | Paste-ready cold email + 3-leak markdown + HTML review board on localhost. NO sample link, NO HTML report in the email. | ~$0.005/site |
| `warm` | Booked-call prospect, referral, or paid teardown. Goal: justify scope + close. | Already curious | Full HTML internal-viability + client-facing teardown + before/after Kie mockup. | ~$0.50/site |

Routing rule: if Boubacar says "cold teardown" / "teardown this lead" / "prospect outbound" → cold. If "full teardown" / "warm teardown" / "send them a teardown report" / "post-call deliverable" → warm. If ambiguous, ask.

---

## COLD MODE (lean, outbound-driven)

### Phase 0: Auto-filter pre-gate (REQUIRED, runs BEFORE full audit)

**Decision:** PURSUE / DEFER / DROP based on website-datedness. Avoid spending money + time on leads that aren't worth pursuing.

**Cost:** ~$0.005/site (1 HTTP fetch + 1 Haiku-4.5 classification via OpenRouter)

**Hard stops (auto-DROP):**
- `site_dead`: fetch failed / 404 / expired domain
- `agency_owned`: footer says "Built by X" / "Designed by X" marketing agency
- `closed_business`: "permanently closed", no products, no CTA
- `already_modern`: clearly Apple-tier site, custom animations, dark-mode toggle — nothing to fix
- `out_of_scope`: national chain or corporate giant (Mr. Rooter, QXO, etc.) — not owner-operated

**Scoring rubric (datedness 0-100):**
- 70-100 = PURSUE. Dated (pre-2022 design), broken forms, no mobile CTA, big leak surface
- 40-69 = DEFER. Mid-tier. Modernish but craft-gap exists. Revisit Q3.
- 0-39 = DROP. Already polished. No pitch to make.

**Signals captured (HTTP fetch, no LLM needed):**
- copyright year, mobile viewport meta, framework (Wix/Squarespace/WordPress/Tailwind/Bootstrap-3), slideshow/carousel presence, form input count, JSON-LD schema, "Built by" agency credit, title + H1, HTML size, 404/closed-business strings.

**LLM call:** Haiku-4.5 via OpenRouter. Strict JSON output: `{datedness_score, verdict, verdict_reason, hard_stop, leaks_visible[], tier_estimate, owner_eyetest_one_liner}`.

**Reference implementation:** `agent_outputs/teardowns/phase0_filter.py` (gitignored but reusable — copy into the run dir).

**Output:** `phase0-board.html` rendered with TL;DR card (PURSUE/DEFER/DROP counts + avg datedness), then 3 grouped sections, each lead as a card with score-pill, verdict badge, chips (Wix/WordPress/©2020/carousel/N form fields), owner-eye-test one-liner, expandable leaks list.

### Phase 1: Full teardown (only PURSUE leads from Phase 0)

For each PURSUE lead, run a focused WebFetch pass + ≤1 competitor scan. Identify 3 concrete conversion leaks with cited site copy. Write to `agent_outputs/teardowns/<id>_<slug>_teardown.md`.

**Required sections in the .md (for `render.py` to parse):**

```markdown
# <Business Name> — Cold Teardown
**Lead ID:** <id> | **Niche:** <niche> | **City:** <city> | **Owner:** <email>
**Site:** <url>
**Date:** <YYYY-MM-DD>

## The Hook (for cold email)
**Subject line option A:** <50 char max>
**Subject line option B:** <50 char max>
**Opening hook (1-2 sentences):** <references a specific element on their site>

## The Reality — 3 Biggest Conversion Leaks

### Leak 1: <specific name>
**What's happening:** <quote actual copy/element>
**Why it costs them money:** <1 sentence, no unverified %>
**How they can verify in 60 sec:** <imperative instruction>

### Leak 2: ...
### Leak 3: ...

## The Redesign Blueprint (3 high-impact changes Catalyst would make)
1. **<change name>:** <what + outcome framing>
2. ...
3. ...

## Cold-Email Body (draft, ready to send)
Subject: <subject>

<email body following the Council Mandates below>

## Analysis Notes (internal)
- **Above-the-fold check:** ...
- **Mobile sticky CTA:** ...
- **Form friction:** <# fields>
- **Trust markers above fold:** ...
- **Page-load gut check:** ...
- **Copyright year:** ...
- **Internal fit score (1-10):** <N>
- **Recommended next move:** SEND / SKIP / NEEDS WARM-UP first
```

### Phase 2: Render HTML for Boubacar review

Use `render.py` (in `agent_outputs/teardowns/`) to convert each `.md` → standalone HTML with:
- TL;DR card with /100 score (score = `fit_1_10 * 10`), color-coded (green ≥80, amber 60-79, red <60)
- Paste-ready email card at top (gold border, monospace, subject highlighted, sig dimmed)
- Subject options A/B as hook cards
- 3 leak cards (red border, structured What/Why/Verify)
- 3 fix cards (green border)
- Collapsible internal analysis notes

Plus an `index.html` card-grid landing page with batch TL;DR (avg score, PURSUE count). Serve at `localhost:8765`.

### Phase 3: Send (REQUIRES EXPLICIT BOUBACAR AUTHORIZATION)

**HARD RULE 0 (see `CLAUDE.md` / `AGENTS.md` / `docs/AGENT_SOP.md`):** No email send without Boubacar saying "send this email" / "send batch N" in the current session, for this specific batch. Past authorizations do NOT carry. NEVER re-send to "verify".

**Send path** (from `feedback_cw_send_canonical_path.md`):
- From: `boubacar@catalystworks.consulting`
- Credentials: `/app/secrets/gws-oauth-credentials-cw.json` (cw OAuth, identity = boubacar@catalystworks.consulting)
- API: `POST gmail.googleapis.com/gmail/v1/users/me/messages/send`
- Mandatory: verify-after-send via `GET /messages/<id>?format=metadata`, assert From-header matches intended
- DO NOT use `gws gmail messages send` CLI (authed as bokar83, silently rewrites From)

### Council Mandates (encoded from Sankofa Council review 2026-05-11)

These rules govern the cold-email body. Sankofa Council review confirmed 72% convergence on these, unanimous on the trust-anchor blocker.

**1. Lead with a witnessed loss, not a finding.**
- ❌ "Hey, looked at sandsroofingutah.com this morning. Your form asks for 8 required fields..."
- ✅ "Pulled up sandsroofingutah.com on my phone. Picture a homeowner with a leaking roof. They land, hit field 3 of 8, and call the next roofer."
- The opener must declare a job walked away. Mechanics are abstract. Loss is visceral.

**2. Replace stats with consequences.**
- ❌ "Usually moves form completion 20 to 40 percent for trade sites."
- ✅ "They call the next roofer."
- Trade owners discount % from strangers. Lost-call image is undeniable. Matches `feedback_verified_stats_only.md`.

**3. Honest hypothetical opener (Boubacar's rule, overrides council's first-person simulation).**
- The opener template = `Pulled up {URL} on my phone {time_modifier}. {literal_finding}.` (literal action lane) + `Picture a {customer_archetype} {context}. They {action}, hit {friction_point}, and {consequence}.` (clearly hypothetical lane). Never blur. Never fabricate.

**4. Referral anchor (P.S. line). Optional but high-leverage.**
- When populated: `P.S. {Name} at {Business} in {City} said I should take a look at yours.` → reply rate target 5-10%.
- When empty: no P.S., ship email. Ceiling ~1% reply rate.
- NEVER fabricate. Skill schema field: `referral_anchor` = optional. If empty, P.S. simply does not fire.

**5. Banned phrases (skill linter rule):**
- "looked at", "Quick note", "I noticed", "no pitch", "Happy to send", "Worth a 15-minute call", "moves form completion", "{N}% lift"

**6. Subject line in body.**
- Always include `Subject: <line>` as the literal first line of the email body so paste-and-send doesn't drop it.

**7. Signature:**
- First-name only. `Boubacar / Signal Works / 801-888-1963`
- DROP "(a Catalyst Works brand)" tag in cold email body. Internal context.
- NO unverified credibility claims ("Fixed 114 Utah trade sites" stays out until earned).

**8. CTA:**
- Single: `https://calendly.com/boubacarbarry/signal-works-discovery-call`
- NO sample-report link, NO HTML teardown link in the cold email (would trigger spam classifier + reads as templated). Save the full teardown HTML for the reply-2 warm follow-up.

### Cold-mode accept criteria (before claiming task complete)

- [ ] Phase 0 board HTML exists with TL;DR + PURSUE/DEFER/DROP grouping
- [ ] Per-lead `.md` written for each PURSUE
- [ ] Per-lead `.html` rendered with TL;DR + paste-ready email card + score + collapsible notes
- [ ] `index.html` card-grid page exists
- [ ] localhost server live on :8765
- [ ] No em-dashes in any email body
- [ ] No banned phrases in any email body
- [ ] No referral-anchor P.S. unless `referral_anchor` field is explicitly populated
- [ ] **NO email sent without explicit Boubacar "send batch N" authorization (HARD RULE 0)**

---

## WARM MODE (full 6-phase pipeline)

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
