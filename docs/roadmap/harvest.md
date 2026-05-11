# Harvest: Catalyst Works Revenue Pipeline

**Codename:** harvest
**Status:** active
**Lifespan:** open-ended
**Started:** 2026-04-25 (stub; populate in a revenue session)
**Owner:** Boubacar Barry
**One-line:** move Catalyst Works from zero paid engagements to a stable revenue pipeline

> **Note:** Partially populated 2026-04-28 from YC RFS S26 strategy session. Lock Done Definition in first revenue-focused session once Signal Works contract #1 signs.

---

## Why This Is Separate

The autonomy roadmap (`atlas.md`) is about building the system that supports Boubacar's work. This roadmap is about the work itself: pipeline, discovery calls, content, SEO, conversions.

**They share zero milestones.** Mixing them in one document conflates "system that runs while my laptop is off" with "income that pays rent."

---

## Done Definition (placeholder; lock in revenue-session)

Target: $5K MRR by June 2026. Possible framings to choose from:
- N paid engagements per quarter
- $X MRR / quarterly revenue floor
- Pipeline coverage ratio (qualified leads / revenue target)
- First-engagement-shipped milestone (then revisit done definition)

---

## Status Snapshot (updated 2026-04-28)

**Signal Works (closest to cash):**

- Daily email pipeline LIVE: 20 drafts/day (10 SW + 10 CW) in CW drafts folder
- 3 demo sites live on Vercel: roofing, dental, HVAC
- 3 pitch reels built
- First contract target: 2026-05-02
- Week 1 (manual review), Week 2 (auto-send flip)

**Catalyst Works:**

- Zero paid engagements as of 2026-04-28
- Phase 0 playbook: LinkedIn + BNI + South Valley Chamber
- 4-7 discovery calls in 30 days target
- Signal Session = $497, 90 min
- Discovery Call OS v2.0 documented

**Active offer stack:**

- Signal Works Tier 1: $500 setup + $497/month (AI presence infrastructure)
- CW Signal Session: $497, 90 min (diagnostic)
- SaaS Audit: $500 flat (TBD: not yet built, see R2 below)
- "We are your AI department" unified SKU: $997/month (TBD: design phase)

**Revenue as of 2026-04-28:** $0

---

## Milestones

### H1: First Signal Works contract (trigger: email reply converts)

**Status:** In progress. **First-touch SENT 2026-05-07 to Rod (Elevate Roofing & Construction, Medford OR)** with two URLs (demo site + mobile-first audit brief). Awaiting reply.

**Send event log (2026-05-07):**

- **Demo site:** https://site-phi-silk-71.vercel.app/
- **Audit brief (mobile-first card stack):** https://auditdeploy.vercel.app/ (18/20 design-audit @ 375px)
- **Full desktop memo:** https://auditdeploy.vercel.app/full/ (19/20 design-audit @ 1280px, linked from mobile accordion)
- **Email subject:** "Long time, Rod. Built you a thing."
- **Recipient:** rod@elevatebuiltoregon.com (scraped from Elevate site footer; status unconfirmed but only available channel)
- **Channels touched:** LinkedIn DM (sent 2026-04-30 as part of 3-warm-DM batch with Brody Horton + Rich Hoopes, no reply at 7-day mark), email (2026-05-07 with full deliverable)
- **Voice:** peer-to-peer warm reconnect, BYU friend dynamic, zero price talk, mailto reply CTA only
- **Hold rule:** 7 days minimum before any follow-up. One light bump max if no reply by 2026-05-14. Then drop.

**Warm DM trio context (2026-04-30 → 2026-05-07):** Rod is one of 3 dormant-warm LinkedIn reach-outs sent 2026-04-30 evening. As of 2026-05-07, all 3 are at zero replies. Per Hormozi 4-row diagnostic "3 sent / 0 replies" = audit personalization + list quality. Operator interpretation: dormant-warm DM without a deliverable is throwing a coin in a fountain. Rod escalated today by adding the deliverable; Brody Horton and Rich Hoopes remain pending decision (default: light bump 2026-05-10 if no other action). Full state in `project_warm_dm_trio_2026-04-30.md`.

**Actions before this milestone closes:**

- Watch inbox + LinkedIn for Rod reply (24-hr response SLA on any reply)
- **A/B TEST PAUSED (2026-04-28):** All leads get Variant A (original score framing). Variant B code preserved in `email_builder.py` with `AB_TEST_ACTIVE = False`. Re-enable after 2026-05-12 once SW sequence performance data exists.
- If Rod replies yes → 15-min walkthrough → close at Signal Works Tier 1 ($500 setup + $497/month) OR friend pricing per `MESSAGE_TO_ROD.md`
- If no reply by 2026-05-14: send single light bump (max 1 follow-up). Drop after.
- If Rod converts: lock canonical SW audit template (already saved to `reference_sw_audit_template_canonical.md`) as the v1 reusable for SW prospect #2.

**Success criterion:** Signed contract + first payment received.

#### H1a: Score-report conversion methodology (NEW . added 2026-05-01 mid-session)

**Why this exists:** First conversion attempt (Rod / Elevate) surfaced a gap in the SW pitch . the v1 "Before/After scorecard" report was internally proof-strong but cold-read weak. Sankofa Council 2026-05-01 verdict: judgment-call scores torch trust, "GEO" jargon gates comprehension, no money line, no real CTA, project-plan masquerading as a call-to-action. The fix is a repeatable 8-step playbook every SW prospect now goes through.

**Operator framing (locked 2026-05-01):** "Removing pain that's worth paying me to remove." Every Rod-facing artifact must read as *I see a problem costing you money, I already started fixing it, here's the easiest way to look at it.* Not *here's an audit of what you got wrong.*

**Status:** In flight. Live artifacts at `projects/elevate-built-oregon/_build/` + localhost:8771.

**The 8-step playbook (becomes the SW conversion standard):**

1. **Soften the verdict . acknowledge the business the prospect actually built before naming what's missing.** *(Done for Rod 2026-05-01.)*
2. **Drop industry jargon . "GEO" → "AI search visibility (ChatGPT, Perplexity, Gemini)" . speak the prospect's vocabulary.** *(Done for Rod 2026-05-01.)*
3. **Replace the project-plan CTA with a single ask . "Text 'site' to [number]" . phone + name + verb.** *(SUPERSEDED 2026-05-02. Current Rod outreach in `projects/elevate-built-oregon/MESSAGE_TO_ROD.md` uses a demo-link CTA, not a phone CTA. The "text site to phone" approach was replaced when the demo became the lure. No phone placeholder remains in active files.)*
4. **Reframe the lead-loss section around pain-removal + revenue compounding, not score gaps.** *(Done for Rod 2026-05-01.)*
5. **Replace judgment-call scorecard numbers with third-party validator screenshots . PageSpeed Insights, Schema validator, Lighthouse SEO, WAVE, Rich Results Test.** *(Pending . runs against live + rebuild URL.)*
6. **Add the money line . "~$X-$Y/month in missed jobs" . derived from public keyword volumes × industry CTR × close rate × avg job value.** Methodology in collapsed section so skeptics can audit.
7. **Draft cover note in 3 variants . email, SMS, DM . each leads with one undeniable observation Rod can verify in 30 seconds, links to the report only if he asks for it.** Report becomes proof, not lead.
8. **Add competitor scoring . third column on every scorecard showing top-3 Medford competitors' scores. Reframes pitch from "fix your site" to "claim Medford before someone else does."** *(Pending; ~2 hours; pull via Firecrawl.)*

**Tier floors locked 2026-05-01:**

| Tier | SEO | AI search | UX | Frame |
| --- | --- | --- | --- | --- |
| Signal Works baseline ($500 setup + $497/mo) | ≥80 | ≥75 | ≥80 | "Indexable, citable, converting." |
| Signal Works Pro | ≥90 | ≥85 | ≥90 | "Above your competition." |
| Catalyst Works custom | ≥95 | ≥90 | ≥95 | "Category leader." |

**Build target rule:** every SW deploy must clear baseline floors on third-party validators before cut-over. Floors are the QA gate, not the goal.

**Success criterion for R1a (separate from R1):** the 8-step playbook is captured in `skills/signal-works-conversion/SKILL.md` (sibling to `signal-works-pitch-reel`), runs end-to-end on Rod, and either (a) Rod converts using it OR (b) we surface why he didn't and the playbook is updated for SW prospect #2.

#### H1a-v3: Hook-and-deliverable architecture (locked 2026-05-01 mid-session, post-v2 Sankofa)

**Why this is here:** v2 stress-test verdict on 2026-05-01: "v2 is shaped like a deliverable. It needs to be shaped like a fishing lure." Council disagreement resolved by operator: skill scales to thousands of contractors, conversion math favors the lure-and-deliverable split.

**The locked architecture:**

| Layer | File | Job | Length |
| --- | --- | --- | --- |
| Cover note | `rod-cover-note.md` (3 variants) | Open the hook page | 3-4 lines, leads with empty `<title>` finding |
| **Hook page (LEAD)** | `rod-hook.html` | Convert opener to "text site" | 1 page, ~3 phone scrolls |
| Deep-dive (deliverable) | `rod-validators-before-after.html` | Close prospect after they ask for more | 5 sections, real Lighthouse data |
| Rebuild preview | `site/` served on Vercel | Final close | The actual product |

**Hook page formula (locked, do not deviate without re-running Sankofa):**

1. H1 = the most damning verifiable observation (one sentence, two clauses)
2. Lede = how to verify it in under 30 seconds (right-click view-source instructions, validator URL, etc.)
3. Side-by-side phone screenshots (393×852 viewport, iPhone-shaped frames)
4. One-line caption under screenshots: "Same business. Same domain. Two weeks of work between them."
5. Verify-yourself proof block: 3 rows, each with explicit timing (10s / 2min / 90s)
6. Cost line: "$500 setup + $497/month ... pays for itself within 90 days at the conservative case"
7. Single-ask CTA: "Text 'site' to [PHONE]" (NOT a project plan, NOT a calendar link)
8. Tap-to-call link below the CTA for mobile readers
9. Deep-dive link at the bottom for prospects who need more proof
10. Footer with reproducibility instructions ("anyone with Chrome in three clicks")

**Three pre-baked observation hooks (productized):**

- `empty_title` . fires when view-source shows `<title></title>`. Most visceral. Used for Rod.
- `missing_schema` . fires when zero JSON-LD blocks on homepage. Best AI-search wedge.
- `broken_mobile_speed` . fires when Lighthouse mobile Performance < 50 or LCP > 5s. Most measurable.

Selection priority when multiple apply: `empty_title` > `missing_schema` > `broken_mobile_speed`. Most visceral wins.

**Skill location (live as of 2026-05-01):**

```text
skills/signal-works-conversion/
├── SKILL.md                              ← invocation contract
├── templates/
│   ├── hook.html.template                ← master HTML with {{VAR}} placeholders
│   └── hooks.json                        ← 3 pre-baked hooks + selection rule
├── prospects/
│   └── rod-elevate.json                  ← worked example (Rod, hook=empty_title)
└── builder/
    └── build_hook.py                     ← dependency-free renderer (~140 lines)
```

**Workflow per prospect (~30 min once audit is done):**

1. Audit live site (Lighthouse + view-source + schema validator) → pick which hook fires
2. Take phone screenshots via Playwright (393×852 mobile emulation, before-phone.png + after-phone.png)
3. Copy `prospects/rod-elevate.json` → fill in variables for new prospect
4. Run `python builder/build_hook.py --prospect prospects/[name].json --out [project]/_build/[name]-hook.html`
5. Verify on localhost in phone viewport via Playwright
6. Deploy hook + screenshots + deep-dive to Vercel preview URL
7. Update cover note URLs to match Vercel URLs
8. Send cover note → wait for reply → text rebuild preview link

**Open work that did NOT make it into v3 (deferred, not dropped):**

- **Competitor scoring** (Sankofa Expansionist's biggest insight) . adds a third column to the deep-dive showing top-3 Medford competitors' Lighthouse scores. Reframes pitch from "fix your site" to "claim Medford before someone else does." Pull next week if Rod converts or as v3.1 enhancement.
- ~~**Vercel preview deploy** . currently on localhost.~~ ✅ **DONE 2026-05-01:** rebuild at <https://elevate-rebuild-app.vercel.app/>, hook + deep-dive at <https://signal-works-rod-app.vercel.app/>. Both noindex. Cover note URLs updated.
- **The skill self-extracting after 5 prospects** . review which hook converted highest, lock as default. SKILL.md has the audit checklist.

**Updated cross-references:**

- Cover note (3 variants): `projects/elevate-built-oregon/_build/rod-cover-note.md`
- Hook page (Rod, hand-built): `projects/elevate-built-oregon/_build/rod-hook.html`
- Hook page (Rod, from template): `projects/elevate-built-oregon/_build/rod-hook-from-template.html`
- Deep-dive (now second-touch role): `projects/elevate-built-oregon/_build/rod-validators-before-after.html`
- Phone screenshots: `projects/elevate-built-oregon/_build/validator-screenshots/{before,after}-phone.png`
- Lighthouse raw data: `projects/elevate-built-oregon/_build/validator-data/`
- Skill (live): `skills/signal-works-conversion/`
- Sankofa Council v1 verdict: 2026-05-01 chat (re v1 report)
- Sankofa Council v2 verdict: 2026-05-01 chat (re v2 report → produced v3 architecture)

---

### H1c: website-teardown skill (one-trigger master diagnostic)

**Status:** SHIPPED 2026-05-04. SKILL.md + both HTML report templates built and pushed on `feature/website-teardown`. Ready to test on next prospect.
**Trigger:** Any teardown request now uses `/website-teardown` instead of manually invoking 4-5 separate skills.

**What it is:** A thin orchestrator skill at `skills/website-teardown/SKILL.md` that chains `website-intelligence` (Phase 1 brand + Phase 2 competitors), `web-design-guidelines` (UX/accessibility audit), `seo-strategy` Mode 2 (full SEO/GEO audit), `kie_media` (before/after hero mockups), and `signal-works-conversion` (slider component) in a single 6-phase pipeline. No logic duplication. Every analytical step calls an existing skill.

**Inputs accepted:** URL (default), local repo path (for internal builds not yet shipped), single .html file path (for auth-blocked or one-off pages).

**Outputs (TWO reports, same research):**
1. `internal-viability-report.html` . internal-only. Verdict (PURSUE / DROP), fit signals, scope estimate, price band, red flags, weighted score. Answers: do we pursue this lead?
2. `client-teardown-report.html` . client-facing. Brand snapshot, craft gap, market gap, SEO audit, before/after mockup, single CTA. The sales/diagnostic asset.

**Why two reports:** internal viability framing must never leak into client output. Same data, different audiences, different framing.

**Why this skill exists:** Boubacar's manual workflow was "run website-intelligence, then web-design-guidelines, then seo-strategy, then kie_media, then signal-works-conversion." Five skills, four trigger words to remember. One trigger now (`/website-teardown` or "teardown <domain>"). Built on Sankofa Council + Karpathy audit on 2026-05-01 that rejected the original "build a new monolith skill" plan in favor of a thin orchestrator.

**Verification next move:** run the skill end-to-end against the next SW prospect (after Elevate). Confirm both report files generate, no internal leakage into client report, em-dash sweep passes, before/after mockup renders.

**Files:**
- Skill: `skills/website-teardown/SKILL.md`
- Source skills it orchestrates: `skills/website-intelligence/`, `skills/web-design-guidelines/`, `skills/seo-strategy/`, `~/.claude/skills/kie_media/`, `skills/signal-works-conversion/`

---

### H1d: catalystworks.consulting v1 self-teardown (eat our own food)

**Status:** Teardown completed 2026-05-01 against the live CW site. Verdict: ITERATE. Patches applying on `dev` branch as of 2026-05-01.
**Trigger:** First end-to-end run of the website-teardown skill (R1c). Self-applied to validate the pipeline before pointing it at prospects.

**What it surfaced:** voice, offer architecture, and structured data are already at v2 quality. The site bleeds on visual craft (real logo not used, em-dashes in body + JSON-LD, broken nav anchor, contrast fail), two orphan interior pages (governance.html and ai-data-audit.html with no homepage links and bare meta/schema), and zero local-SEO signal despite footer naming five cities.

**Closest competitor:** smbstrategyconsultants.com. Same diagnosis-before-prescription frame, same constraint vocabulary, lighter theme + premium photography. Catalyst Works wins on offer specificity ($497 productized first-touch with 24-hour written deliverable), loses on first-impression craft.

**Patch list (dev branch, ~3 hours focused):**

1. Real CW logo in header + footer (replace text logotype). Inherits website-intelligence HARD RULE #2.
2. Fix broken `#offers` nav anchor. Either rename or add the id.
3. Em-dash scrub site-wide + JSON-LD FAQ answers (em-dashes leak into Google rich snippets).
4. Wrap booking modal in `<form>`, add `required` + `name` attrs to all inputs, add label for newsletter email.
5. `color-scheme: dark` on `<html>` + raise `--text-dim` to 50%+ opacity + `<meta name="theme-color">`.
6. Link homepage to governance.html and ai-data-audit.html (un-orphan).
7. Add meta description + canonical + JSON-LD to governance.html.
8. Add meta description + canonical + JSON-LD to ai-data-audit.html (+ scrub em-dash in H1).
9. Upgrade Organization schema `areaServed` from country names to City entities. Add Service Areas section to homepage.

**Deferred (v2.1):** hero photograph swap. The kie_media render is good directionally but a real founder portrait shot in similar lighting is the right v2.1 task. v2.0 ships with the existing dark-grid hero retained.

**Workflow rule for this run:** all changes happen on `dev` branch in `output/websites/catalystworks-site/`. Localhost preview and sign-off BEFORE any push to GitHub. `main` stays untouched until Boubacar approves.

**Success criterion:**
- All 9 patches land on `dev`
- Local preview at `http://127.0.0.1:<port>/` shows the v2 site rendering correctly across desktop and mobile
- Em-dash sweep clean (`grep` for em-dash returns nothing)
- After sign-off: dev pushed to GitHub, then optionally PR to main

**Deliverable artifacts (already produced 2026-05-01):**
- `deliverables/teardowns/catalystworks-consulting/internal-viability-report.html` (verdict + score + patch list)
- `deliverables/teardowns/catalystworks-consulting/client-teardown-report.html` (sanitized for prospect viewing)
- 4 research files (brand / design audit / competitors / SEO audit)
- Before/after hero mockup with drag slider (`mockups/before-after.html`)

---

### H1f: frontend-design skill - art direction + design audit lift (taste-skill absorb)

**Status:** PROCEED. Integration target 2026-05-07.
**Source:** `leonxlnx/taste-skill` (MIT). Security scan: STATIC-CLEAN.
**Absorb verdict:** continuous-improvement. Logged in `docs/reviews/absorb-log.md`.

**What this is:** Two surgical changes to `skills/frontend-design/SKILL.md` that directly lift image and design quality on every SW and CW site build:

1. **Kie prompt template rewrite** (~line 1002-1070): replace the current one-sentence example prompt format with a structured 4-6 line template using compositional vocabulary from `imagegen-frontend-web`: composition anchor + background mode + hero scale + typography character + one anti-slop prohibition per site type. Today's Kie prompts are single sentences; every site's images are generic as a result.

2. **Design audit reference file**: add `skills/frontend-design/references/design-audit.md` - flat checklist ported from taste-skill's `redesign-skill` Design Audit section (80+ specific anti-generic checks across typography, color, layout, interactivity, content, components, icons). Wire one line into Step 5 pre-launch checklist: "Run design-audit.md against all visible sections."

**Why now:** Design quality is Boubacar's stated key area of focus. Every SW build (Rod/Elevate, future prospects) and CW site ships via frontend-design. The current Kie prompt generates single-sentence briefs; imagegen-frontend-web's combinatorial vocabulary (composition anchors, background modes, hero scale, anti-slop rules) is exactly what's missing. Sankofa chairman verdict: "the gap is in the Kie prompt construction, not in the art direction vocabulary." Karpathy verdict: SHIP.

**What was NOT absorbed:** The full 20-section imagegen-frontend-web art direction system was not imported wholesale - it is designed for models that generate images directly. Claude Code's role is prompt writer for Kie API. Vocabulary extraction only, not system import. Studio thumbnail art direction (kie_media) and brandkit content (design skill) deferred to separate sessions.

**Tasks:**
- [ ] Rewrite Kie prompt block in `skills/frontend-design/SKILL.md` ~line 1002-1070
- [ ] Add `skills/frontend-design/references/design-audit.md` (80+ checklist from redesign-skill)
- [ ] Wire one-line reference into Step 5 pre-launch checklist
- [ ] Verify: run one site build, confirm Kie prompt contains 2+ compositional vocabulary terms

**Success criterion:** Next SW or CW site build generates a Kie prompt with 2+ compositional vocabulary terms (composition anchor / background mode / hero scale / typography character / anti-slop prohibition). Design-audit.md exists and is referenced in Step 5.

**Target:** 2026-05-07

---

### H1e: catalystworks.consulting v3-WOW (cinematic + Constraints AI live demo)

**Status:** Tier 1 shipped 2026-05-01. **Tier 2 partial-ship 2026-05-11** to `dev-v3-WOW` (commits `f63e5f2`, `aba107d`): T2.1 outcomes strip, T2.5 SEO polish, T2.6 mobile a11y, T2.8 worker fallback hardening (deploy still pending). Tier 3 not yet built.

**What shipped (Tier 1, 2026-05-01):**
- Single-page cinematic dark theme (deep navy + amber + cyan accents)
- Three.js constellation hero with glow-circle particles
- Custom amber cursor (dot + lerp ring)
- Live Constraints AI demo (sandboxed system prompt with 3 modes: diagnostic / redirect / refuse-with-wit, locked banned-phrase regex, OpenRouter via Cloudflare Worker, simulated keyword-rule fallback)
- Email capture below diagnosis output (cyan "Want this as PDF?" form, posts to Worker `/capture` route + Supabase `diagnostic_captures` table)
- Risk-reversal "Protocol Guarantee" on offer card ("If I cannot name a constraint specific enough to act on Friday, you do not pay")
- Calendly popup CTA replacing `mailto:` (free 45-min discovery call → invoice $497 if proceeds)
- Person + FAQPage + ProfessionalService JSON-LD schemas
- A11y trio: WCAG-passing lens-tag contrast, brand-coherent `:focus-visible`, explicit img dimensions, logo alt text
- Real Boubacar.JPG portrait (magazine-cover AI portrait archived for later)

**Tier 2 (target: within 2 weeks of 2026-05-01, due 2026-05-15):**

| # | Task | Time | Why |
|---|---|---|---|
| T2.1 ✅ | Anonymized 30-day-outcome strip below offer (3 rows: industry / what was stuck / what changed). Use real informal Signal Sessions Boubacar has run; composite if needed (clearly labeled). | 90 min | Closes the "no social proof" cold-read gap (Sankofa Outsider). **Shipped 2026-05-11 (f63e5f2):** `.offer-outcomes` block, 3-col desktop / 1-col <880px, cinematic tokens, composite disclaimer. |
| T2.2 | Programmatic SEO: 5 lens-explainer pages (`/lens/throughput`, `/lens/friction`, `/lens/decision`, `/lens/information`, `/lens/inference`) | 3 hr | Site has 3 ranking pages today. 8 pages rank for ~8x more long-tail. |
| T2.3 | Programmatic SEO: 3 industry-specific pages (`/for/professional-services`, `/for/hvac`, `/for/healthcare-smb`) | 2 hr | Adds vertical entry points |
| T2.4 | Migrate Three.js off deprecated UMD build (`build/three.min.js` → ES module or pin `three@0.149`) | 10 min | Prevents silent breakage on next CDN update (audit #11) |
| T2.5 ✅ | Title + meta rewrite with "Salt Lake City", "Utah", "fractional advisor" keywords | 4 min | Closes local-SEO gap (audit #8). **Shipped 2026-05-11 (f63e5f2):** title + description + `og:*` + `twitter:*` all weave SLC + Utah + fractional advisor + diagnostic business consulting. |
| T2.6 ✅ | Footer link tap targets to 44x44 min height on mobile | 4 min | Mobile a11y standard (audit #12). **Shipped 2026-05-11 (f63e5f2):** `@media (max-width: 480px)` rule on `.foot-links a` + `footer .brand`, verified via Playwright DOM measure (all 44px). |
| T2.7 | Create paid `Executive Signal Session` Calendly event type (90-min, $497, Stripe-wired) and switch CTA from discovery-call URL to direct booking | 30 min on Calendly side | Removes one funnel step. Currently using free discovery as stepping stone. |
| T2.8 🟡 | Deploy `_worker.js` to Cloudflare Workers; set OPENROUTER_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, HASH_SALT secrets; paste deployed URL into `WORKER_URL` constant in `index.html` | 20 min | Activates real Claude/GPT diagnoses + Supabase capture (currently simulated mode). **2026-05-11 (f63e5f2):** front-end hook hardened with `AbortController` + 12s timeout + try/catch/finally; seamless fallback to `simulate()` when `WORKER_URL=''`. **Still pending:** `wrangler deploy` + secrets + paste URL into `index.html`. |
| T2.9 ✅ | Production case-sensitivity hardening + image perf hints | 10 min | Prevents Linux/Hostinger 404 on `Boubacar.JPG`. **Shipped 2026-05-11 (aba107d):** `git mv` rename to `Boubacar.jpg`, `loading="lazy" decoding="async"` on below-fold images, `decoding="async" fetchpriority="high"` on header logo. |

**Tier 3 (target: within 30 days of 2026-05-01, due 2026-05-31):**

| # | Task | Why |
|---|---|---|
| T3.1 | First "Diagnostic Patterns Q2 2026" post mining Supabase `diagnostic_submissions` for the 5-7 most-common constraints visitors are typing in. Becomes a McKinsey-quality insights piece you publish from your own funnel. | Sankofa Expansionist: aggregate the diagnoses |
| T3.2 | Internal anchor-text variation on secondary cards ("AI consulting" / "constraint coaching" instead of bare titles) | SEO ranking (audit #9) |
| T3.3 | Mobile H1 size drop to 34px on `<480px` viewports + tighter line-height | Polish (audit #14) |
| T3.4 | Email follow-up sequence wired (3 emails over 14 days after capture: PDF → 30-day framework → "ready for Signal Session?") | Converts the email list into bookings |
| T3.5 | Add Stripe direct-payment to Signal Session offer card (skip Calendly discovery, sell straight to $497) once first 3 paid sessions happen via T2.7 path | Tightens funnel |

**Live URLs:**
- Branch: https://github.com/bokar83/catalystworks-site/tree/dev-v3-WOW
- Live (after deploy): https://catalystworks.consulting/
- Localhost preview: `cd output/websites/catalystworks-site && python -m http.server 8745`

**Sankofa Council verdict (2026-05-01):** the site is a $100k positioning piece. Tier 1 added the conversion mechanics (capture, risk reversal, Calendly). Tier 2 + 3 turn it into a $100k revenue piece.

---

### H-automation: CW AI automation delivery service line

**Status:** Queued. n8n-mcp MCP installed 2026-05-04. Skill build target 2026-05-18.
**Trigger:** After R1 closes (need first social proof) OR first inbound automation inquiry.

**What it is:** One-man AI automation agency offering alongside Catalyst Works. Build client n8n workflows that save 5-20 hours/week. Pricing: $3K-$5K per build engagement, $500-$1K/month maintenance. Model validated by X-thread 6-phase playbook (@eng_khairallah1).

**Stack wired 2026-05-04:**
- n8n-mcp MCP server installed (`npx n8n-mcp`) - gives Claude expert knowledge of 1,650 n8n nodes + 2,352 templates
- `cw-automation-engagement` skill planned (v1 = Phase 3 only: case study acquisition workflow)

**Karpathy WARN (logged):** v1 skill scoped to Phase 3 only. Do not build full 6-phase skill speculatively. Acceptance criterion: first CW automation engagement scoped and priced by 2026-07-04.

**Sankofa verdict:** n8n-mcp install-only (not skill absorb). Real asset is the engagement methodology (6-phase X-thread). Skill worth building is `cw-automation-engagement`, not a wrapper around the MCP docs.

**Why this is adjacent to CW (not separate):** Same buyer (SMB professional services). Same discovery motion (Signal Session). Same constraint: Boubacar's time. Automation delivery = the natural upsell after AI presence (Signal Works) and AI diagnostic (CW Signal Session).

**Success criterion:** First paying automation engagement closed and delivered using this stack.

---

### H2: SaaS Audit offer live ($500 flat)

**Status:** SHIPPED 2026-05-04.

**What shipped:**

- PDF: `workspace/articles/2026-04-28-saas-audit-assets/saas-audit.pdf` (built 2026-04-28, manually rendered via Chrome)
- Drive link (public, anyone with link): `https://drive.google.com/file/d/1ctmqUjhxa5hBkIj47AMDPvgbJzXwkETd/view`
- `templates/email/sw_t5.py`: SW Touch 5, Day 17 upsell. Subject: "Different angle: the software question". Niche-personalized. Links to Drive PDF. $500 audit CTA.
- `skills/outreach/sequence_engine.py`: TOUCH_DAYS_SW extended to {1:0, 2:3, 3:7, 4:12, 5:17}. TEMPLATES['sw'] wired to sw_t5.

**Why:** Buyer calculates ROI in 30 seconds. Fastest path to a cash transaction from cold email. No new infrastructure required.

**Success criterion:** One paying audit client within 30 days of offer going live.

---

### H3: First CW Signal Session sold ($497)

**Status:** Waiting on R1 social proof or direct LinkedIn outreach conversion.
**Trigger:** After R1 closes OR first LinkedIn discovery call books.

**Actions:**

- Run Discovery Call OS v2.0 on first call
- Diagnostic output: one named problem, written, specific, with implications and clear next action
- Close at $497 Signal Session

---

### H4: "We are your AI department" unified SKU designed

**Status:** Concept only. Design phase.
**Trigger:** After R1 + R3 both close (need proof that both brands convert independently before bundling).

**What it is:** Combined offer: CW diagnostic + Signal Works AI presence + monthly operations report = $997/month. One SKU. One pitch. Removes decision complexity for buyers who want the full picture.

**Build required:** One offer page on Signal Works or CW site. Pricing decision. Zero infrastructure work.

---

### H5: Client portal pilot (Atlas dashboard white-labeled)

**Status:** Parked until R1 closes.
**Trigger:** First Signal Works client asks for more visibility into their data.

**What it is:** Permission gate on existing Atlas dashboard showing that client's AI presence data. One afternoon of work per client. Adds $97/month to existing plan.

**WARN (Karpathy):** Do not build until one client explicitly requests it. Test with weekly automated email report first. If that creates enough perceived value, build the portal. If not, skip it.

---

### H6: Repeatable lead source identified

**Status:** Not yet measurable. Needs 30 days of outreach data.
**Trigger:** After 100+ contacts reached and reply/close rates logged.

**Measure:** Which source (cold email, LinkedIn, BNI, referral) produces the lowest cost-per-conversation.

---

### Quality follow-ups (small, opportunistic)

These are paper cuts surfaced during 2026-04-29 work. None block the cash path. Pull when a session has a 15-30 min gap.

- **email_builder.py pre-existing em-dashes (~15-20 instances).** Diff-aware em-dash hook (`scripts/check_no_em_dashes.py`) now ignores them, but they will fire if anyone passes `--full`. Run `python scripts/check_no_em_dashes.py --full signal_works/email_builder.py`, scrub each prose `--` to `:` or `,`, commit as one cleanup.
- **scan_line `{name}` injection bug for CW leads.** In `_opening()` template branches (lines ~285, 296, 318+ on `feature/style-dna-wirein`), scan_line uses `{name}` which for CW leads is a person's name, producing "a quick demo showing what Adam Ingersoll could look like with a site built for AI visibility." The voice-line short-circuit at line 255 already de-personalized; the template branches still have the bug. SW leads are unaffected because `name` is the business there. Fix: detect when lead is CW (source contains "apollo") and use generic phrasing, OR add `business_name` field that maps to lead.company for CW and lead.name for SW.

---

### H7: transcript-style-dna lift-test verdict (KEEP or DELETE)

**Status:** ⏰ Active, eval date 2026-06-01.
**Trigger date:** 2026-06-01. Surface in any session that starts on or after that date. **If the trigger date has passed, this is the FIRST item to action this session.**

**What this is:** Wired into Signal Works CW outreach 2026-04-29. Per-lead voice opener via transcript-style-dna + find_company_website + BeautifulSoup. Smoke-tested on 3 real CW leads (Adam @ Shasta Dental, Ben @ MMI, Galen @ ShareMy.Health), all produced personalized openers. 30-day clock started 2026-04-29.

**Eval procedure (run on 2026-06-01):**

1. Query local CRM Postgres:
   ```sql
   SELECT
     COUNT(*) FILTER (WHERE voice_personalization_line IS NOT NULL) AS personalized,
     COUNT(*) FILTER (WHERE voice_personalization_line IS NULL) AS baseline,
     COUNT(*) FILTER (WHERE voice_personalization_line IS NOT NULL AND replied_at IS NOT NULL) AS personalized_replied,
     COUNT(*) FILTER (WHERE voice_personalization_line IS NULL AND replied_at IS NOT NULL) AS baseline_replied
   FROM leads
   WHERE source = 'apollo_catalyst_works'
     AND created_at >= '2026-04-29';
   ```
2. Compute reply rate per cohort: `replied / total`. Then relative lift: `(p_rate - b_rate) / b_rate`.
3. **KEEP** if relative lift ≥ +20%. **DELETE** if not. No EXTEND, no qualitative override.
4. Also pull diagnostic instrumentation from `logs/signal_works_morning.log`: count "voice_personalizer: skip ... reason=..." vs "voice_personalizer: ok ..." entries since 2026-04-29. Skip-reason distribution distinguishes bad-skill from bad-input.

**If DELETE, the cleanup PR:**
- Drop column: `ALTER TABLE leads DROP COLUMN voice_personalization_line;`
- Remove file: `signal_works/voice_personalizer.py`
- Revert `email_builder._opening()` short-circuit (the voice_line block, currently lines 255-272 on `feature/style-dna-wirein`)
- Remove `morning_runner.py` Step 4.5 (currently lines 133-144 on `feature/style-dna-wirein`)
- Remove `find_company_website` from `lead_scraper.py` if no other consumer (it was added solely for this wire-in)

**If KEEP:** wire transcript-style-dna into Catalyst Works pre-discovery prep next (the next-after-A bite from the 2026-04-29 Sankofa Council).

**Reference:** `skills/transcript-style-dna/SKILL.md` (single-criterion success measure, post-Sankofa 2026-04-29). Memory: `project_channel_style_dna_audit.md`, `reference_firecrawl_pricing_2026.md`. Plan: `docs/superpowers/plans/2026-04-29-style-dna-wirein-and-channel-branding-kit.md`.

---

### H-newsletter: The Weekly Signal distribution flywheel

**Status:** LIVE. Issue 3 sent 2026-05-07.
**Platform:** Listmonk v6.1.0 (self-hosted, `mail.srv1040886.hstgr.cloud`) — Beehiiv replaced (Enterprise-only send gating).
**List ID:** 3. **List UUID:** `e78a3008-c023-4eb5-a03f-f4202bf7ce8c`.

**What shipped (2026-05-06 session):**

- Listmonk deployed + wired into orchestrator/beehiiv.py as primary send path
- Issue 3 written (shadow AI, CTQ 9/10), designed (email HTML + web archive), sent
- Archive pages live at `catalystworks.consulting/signal` (index + `/signal/issue-3`)
- Style guide at `docs/styleguides/newsletter.md` — canonical source of truth for all agents
- API orchestrator user token (plaintext in users.password) + LISTMONK_API_TOKEN env var

**Growth path:** 500 subscribers → Substack mirror. Paid tier when monetization-ready.

**Why this is harvest:** Signal fuels CW discovery call pipeline. Each issue = one qualified touchpoint for 497-3500 tier buyers. Compounding SEO asset at `/signal`.

**Upcoming (12-week cycle):**

- Issue 4 anchor topic: Boubacar confirms Sunday 18:00 MT via Telegram
- AI Exposure Score assessment promoted via Signal (humanatwork.ai lead magnet)
- Beehiiv subscriber migration to Listmonk (one-time CSV import)

---

### H-brand-guides: CW / SW / Studio brand guide audit and rebuild

**Status:** Queued. Target: Week 7 (complete by 2026-06-17).
**Trigger:** Dedicated brand session. Skills to reference: `frontend-design`, `ui-ux-pro-max`, `design-audit`.

**Scope:** CW, SW (geolisted.co), Studio (3 channels), humanatwork.ai — consistency audit, token alignment, guide rebuild. Colors may change if consistency requires it.

**Why:** Multiple assets in production with divergent palettes and no single source of truth. One week of work now prevents months of visual debt.

---

### H1g: Enrichment pipeline rebuild + harvest-until-50 + thesis launch (2026-05-07)

**Status:** SHIPPED 2026-05-07.

**What broke:** Daily lead harvest produced 0/50 emails on 2026-05-06 morning report. Two compounding bugs:
1. `enrich_missing_emails` never called Hunter (paid Starter $49/mo, 2000 searches, completely unwired).
2. `discover_leads` Step 4 extracted domain from `linkedin_url` field, hitting `play.google.com` and `instagram.com` → returning `thom@google.com`, `jefferynelson@instagram.com` as "owner emails."

**Phase 1 surgical fixes (committed 467259b + e0d7ed5):**
- `apollo_client.find_owner_by_company` rewritten as two-step org→people. Was sending `q_organization_name` to `mixed_people/api_search` which Apollo silently ignores. Now: `mixed_companies/search` → `organization_ids[]` → `mixed_people/api_search`. Result: 663:1 miss → 25-50% on Apollo-known orgs.
- `hunter_client.domain_search` rewritten with three-tier server-side filter cascade. T1: `type=personal + seniority=executive + department=executive` (confidence ≥80). T2: senior fallback. T3: any deliverable ≥60.
- `enrich_missing_emails` wires Hunter as step 2b after scrape, before Prospeo.
- Bad LinkedIn-URL-as-domain bug fixed in `discover_leads` Step 4 elif branch.

**Phase 2 daily target = 50 emails (committed 2cc9711):**
- `signal_works/harvest_until_target.py` (new): loops SW + CW topup until 50 email-verified leads saved or 3 passes / stall detected. SW=35, CW=15.
- `topup_leads.py` modified: phone-only / website-only leads still saved with `email_source` flag, excluded from 50-count.
- Hunter daily cap raised 200 → 400.
- Telegram alert on completion (success or ladder-exhausted).

**Thesis launch (truth-loop):**
- Brand spine failure anchor: founder cannot get straight answers from people closest to them.
- Site: thesis block above offer card on catalystworks.consulting (committed + merged to main 3d17e86).
- Memo signoff: handwritten signature image + right-aligned letter format, full Spectral typography.
- CW T1 hook rewritten (`cold_outreach.py`). Subject: "What your team is not telling you".
- 3 LinkedIn posts queued in Notion Content Board: 5/8 (truth-loop story), 5/9 (AI without truth-loop), 5/12 (cultural bridge / language).

**Today's snapshot (2026-05-07 noon MT):**
- Total leads in DB: 2,545
- With verified email: 423 (was 422 before manual run, +27 today's harvest)
- Today's hit rate: 27/29 fresh leads (93%). Was 0/50 yesterday morning.

**Memory rules saved:**
- `feedback_enrichment_hunter_not_wired.md` — paid tools must be wired to BOTH harvest + enrichment paths.
- `feedback_no_loom.md` — never propose Loom.
- `feedback_first_name_only.md` — content uses "Boubacar", not "Boubacar Barry".
- `feedback_already_have_answers.md` — grep codebase before asking strategic Qs.

**Success criterion (2026-05-13 measurement day):**
- Harvest-until-50 hits 50/50 daily for 5 consecutive days.
- Site capture rate ≥ 1.2x baseline OR flat (drop = revert thesis block).
- CW T1 reply rate on new-cohort leads (added 2026-05-08+) ≥ baseline at Day 6 with n≥30.
- LinkedIn post 1 produces ≥1 DM that becomes a Signal Session conversation.

---

### H-notion-sever: Severing Notion-Supabase CRM Link and Archiving Notion DB (Sync Code Deleted)

**Status:** Sync code DELETED 2026-05-07. Supabase = sole CRM system of record.
**Trigger:** Notion API performance slowdowns, full-table scan delays, and sync timeouts.

**Milestones & Tasks:**

- `[x]` **Step 1 — Sever live writes (2026-05-07).** Bypass guards landed in `crm_tool.py`, `scheduler.py`, `db.py`.
- `[x]` **Step 2 — Delete sync code (2026-05-07).** Removed `_sync_lead_to_notion`, `_sync_lead_status_to_notion`, `_run_notion_sync`, `_listen_for_supabase_changes`, `sync_supabase_to_notion`. No flag, no commented blocks, no zombie functions. Single source of truth: Supabase.
- `[x]` **Step 3 — Parity audit (2026-05-07).** Ran `scripts/reconcile_leads_one_shot.py` inside `orc-crewai`. Report at `docs/audits/notion_sever_parity_2026-05-07.md`. Findings: 0 Notion-only orphans (no backfill needed). 1,670 Supabase-only leads (expected post-sever). 2,024 status drift rows (Notion stale because writes were already off — also expected, no action).
- `[ ]` **Step 4 — Archive Notion CRM DB (manual, by Boubacar).** Archive in Notion UI when ready. Eventually delete entirely.
- `[ ]` **Step 5 — Build replacement Atlas `/crm` dashboard.** Tracked as **Atlas M19** (`docs/roadmap/atlas.md`). No longer blocking sever.

**Success Criterion:**

- ✅ Zero Notion API write traffic from CRM Leads code path.
- ✅ Supabase confirmed sole system of record (parity audit).
- ⏳ Notion CRM DB archived in Notion UI (manual).
- ⏳ Atlas `/crm` dashboard live (tracked under Atlas M19).

---

## Cross-References

- Pipeline playbook: `docs/playbooks/pipeline-building-playbook.md`
- Memory: `project_pipeline_playbook.md`, `project_outreach_playbook.md`, `project_discovery_call_system.md`, `feedback_no_client_engagements_yet.md`, `feedback_facilitator_not_hero.md`, `feedback_enrichment_hunter_not_wired.md`, `feedback_first_name_only.md`, `feedback_no_loom.md`
- Skills: `cold-outreach`, `local_crm`, `apollo_skill`, `hunter_skill`, `boub_voice_mastery`, `ctq-social`

---

## Session Log

### 2026-05-11 — H1e Tier 2 Partial Ship (T2.1 + T2.5 + T2.6 + T2.8 + T2.9)

Branch: `dev-v3-WOW` on `bokar83/catalystworks-site`. Two commits: `f63e5f2` (T2 bundle) + `aba107d` (image case + perf hints). Submodule pointer bumped in `output` (`b22c27a`).

#### T2.1 Outcomes Strip (90 min)

- New `.offer-outcomes` block below the Signal Session price card.
- Three anonymized composite cases (Professional Services / Residential Trades / Healthcare SMB) — constraint + 30-day outcome, with metric in amber.
- CSS tokens: `rgba(22,29,39,0.5)` bg, `1px solid var(--line)`, amber gradient top accent, cyan CASE tags, mono labels.
- Responsive: 3-col desktop, single-col stack at `<880px`. Hover lifts the card 2px + brightens border to amber-32%.
- Composite-outcomes disclaimer in fineprint preserves honesty.

#### T2.5 SEO polish (4 min)

- `<title>`, `<meta name="description">`, `og:title`, `og:description`, `twitter:title`, `twitter:description` all weave "Salt Lake City", "Utah", "fractional advisor", "diagnostic business consulting".
- Premium tone preserved — no keyword stuffing.

#### T2.6 Mobile a11y (4 min)

- `@media (max-width: 480px)` rule enforces `min-height: 44px; min-width: 44px` on every `.foot-links a` + `footer .brand` via `inline-flex` centering.
- WCAG 2.5.5 ✓. Verified live in Playwright (`getBoundingClientRect().height === 44` on all four footer links).

#### T2.8 Worker fallback hardening (front-end only — deploy still pending)

- Wrapped live-Worker fetch in `AbortController` + 12s timeout + `try/catch/finally` with guaranteed `clearTimeout`.
- Simulated five-lens stub remains seamless fallback when `WORKER_URL=''`.
- Not yet: `wrangler deploy`, set `OPENROUTER_API_KEY` / `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` / `HASH_SALT`, paste deployed URL into `WORKER_URL` constant.

#### T2.9 Console errors triage + production safety (bonus)

- Earlier Playwright run logged `ERR_CONNECTION_RESET` on `CatalystWorks_logo.jpg` and `Boubacar.JPG`. Root cause = `python -m http.server` is single-threaded; six parallel image fetches overrun its accept queue. Cloudflare/nginx in prod handles concurrency fine, so prod behaviour was unaffected — but:
- Real prod risk caught: `Boubacar.JPG` (uppercase ext) would 404 on Linux/Hostinger (case-sensitive FS). Renamed via `git mv` to `Boubacar.jpg`; updated the one `<img src>` reference.
- Added `loading="lazy" decoding="async"` to below-fold images; `decoding="async" fetchpriority="high"` to header logo. Tightens LCP budget in prod, reduces concurrent-fetch pressure in local dev.
- Local-dev workflow tip (no code change): use `npx serve -p 8745` or `npx http-server -p 8745` instead of `python -m http.server` to get a threaded socket and silence the dev-only console noise.

#### Still open on H1e Tier 2 after this session

- T2.2 / T2.3 — programmatic SEO pages (5 lens + 3 industry). Big unlock, ~5 hr.
- T2.4 — migrate Three.js off deprecated UMD build. 10 min, prevents silent breakage.
- T2.7 — paid Calendly event type wired to Stripe. ~30 min on Calendly side.
- T2.8 deploy half — `wrangler deploy` + secrets + paste `WORKER_URL`. ~20 min.
- Then merge `dev-v3-WOW` → `main` and ship live to <https://catalystworks.consulting/>.

### 2026-05-07 — Notion CRM Sync DELETED + Parity Audit + Atlas M19 Queued

**Completed (later session, post-Sankofa + Karpathy review):**

- **Deleted lead-sync code outright** (rejected the multi-week phased plan; collapsed to one-day cleanup):
  - `skills/local_crm/crm_tool.py`: removed `_sync_lead_to_notion`, `_sync_lead_status_to_notion`, `_notion_headers`, `_NOTION_DB_ID/_NOTION_API/_NOTION_VERSION` constants, `import httpx`, `import os`, all bypass-log lines.
  - `orchestrator/scheduler.py`: removed `_run_notion_sync`, `_listen_for_supabase_changes`, listen_thread spawn block, `notion_sync_hours`/`last_notion_sync_date` from `_periodic_sync`, all commented-out callsites.
  - `orchestrator/db.py`: removed `sync_supabase_to_notion` (entire 184-line function).
  - `orchestrator/tools.py`: cleaned stale "auto-sync to Notion" docstring on `CRMAddLeadTool`.
- **Parity audit:** Wrote `scripts/reconcile_leads_one_shot.py` (in repo, not scratch). Ran inside `orc-crewai` container. Report committed: `docs/audits/notion_sever_parity_2026-05-07.md`. **Result: 0 Notion-only orphans, 1,670 Supabase-only (expected), 2,024 status drift (expected, Notion stale).**
- **Atlas M19 queued:** New milestone "Atlas CRM Dashboard (`/crm`)" added to `docs/roadmap/atlas.md`. Replaces Notion CRM as the visual sales board. Trigger gate: Notion DB archived + predicate confirmed.
- **No flag, no phased migration, no compatibility shim.** Supabase is now the sole CRM system of record. Code no longer references Notion CRM Leads DB at all.

### 2026-05-07 — Severing Notion CRM Sync & System Lockout Resolution

**Completed:**
- **Deactivated live Notion writes:** Modified `skills/local_crm/crm_tool.py`, `orchestrator/scheduler.py`, and `orchestrator/db.py` to sever the active bidirectional synchronization between Supabase and Notion CRM Leads DB.
- **Harden Sync Disablement (Step 1.1):** Hardcoded a robust, module-level `NOTION_SYNC_ENABLED = False` flag across the three components to fail-closed and ensure writes cannot be resurrected.
- **Database Reconciliation Audit (Step 1.2):** Created `scratch/reconcile_leads.py` script to fetch, paginate, and match 100% of Notion database records (1,800+) against local Supabase/PostgreSQL entries to ensure full parity and zero lead loss.
- **Scope Atlas Dashboard Endpoints (Step 2.1):** Scheduled `/atlas/crm` endpoint scoping in `atlas_dashboard.py` to retrieve pipeline states and "Outreach Needed Today" leads directly from Supabase, fully bypassing the Notion API.
- **System Lockout Recovery:** Successfully terminated 19 zombie Python/HTTP processes that were locking files and ports (such as `.pytest_tmp/` and `tests/pytest_tmp2/`), and deleted a stale `branch:fix/newsletter-safety-and-json-parsing` lock from Supabase, restoring full workspace speed and access.

### 2026-05-06 — Traffic Strategy + Newsletter Infrastructure

**Completed:**

- **Studio batch send:** successfully marked 50 morning drafts (15 Catalyst Works + 35 Signal Works) as sent/messaged in Supabase and fully synced all 50 to Notion CRM Leads database via autonomous agentsHQ `mark_outreach_sent` crew.
- Full asset inventory (54 rows) in Notion Forge 2.0 Asset Register + Weekly Asset Review ritual + New Asset Rule gate
- Hotel Club de Kipe full rebuild spec at `docs/handoff/hotelclubkipe-rebuild-prompt.md`
- **HCK staff portal BUILT + PUSHED 2026-05-07** — login, dashboard (weekly 12-room grid), monthly calendar, clients, invoices (print + history + cancel/archive with notes), admin (settings + tarifs). Supabase live. RLS fixed. Repo: bokar83/hotelclubkipe-site. Go-live pending: delete TEST_ data, deploy to Hostinger, wire public booking form.
- Traffic strategy Sankofa-reviewed for 3 assets: geolisted.co (SW $997), catalystworks.consulting (CW $3,500), calculatorz.tools (AdSense)
- Marketing plan email sent to both addresses
- Listmonk deployed as Beehiiv replacement; Issue 3 written, designed, sent, archived
- Newsletter style guide written (`docs/styleguides/newsletter.md`)
- Master Calendar built in Notion Forge 2.0 (28 rows, Cycle 1 May 6 - Jul 29)
- 12-Week Year + Smart Brevity saved to memory as core execution principles
- Brand guide audit task queued (R-brand-guides, Week 7)

**Week 1 execution queue (May 6-12):**

1. Apply for Work Elevated HR Conference CFP [Boubacar action — utahworkelevated.com]
2. Build /hvac /roofing /dental pages on geolisted.co
3. calculatorz.tools: schema fix (46 pages) + state variants + Date/Time + Conversion categories
4. Finish HVAC pitch reel (publish by May 9)
5. Route 35+ worker/fear posts (humanatwork.ai / X / Archive)
6. Delete 15 junk Content Board records
7. Contact Utah SHRM chapter for webinar slot

**Next session priorities:**

- **Monitor tomorrow's Studio draft generation batch.** If it matches today's success, we are fully ready to flip the automation switch (`AUTO_SEND_CW=true` and `AUTO_SEND_SW=true` in VPS `.env`) for SW and CW.
- Content board cleanup (15 deletes, 30+ collapse, route worker/fear posts)
- geolisted.co trade pages (/hvac /roofing /dental)
- [x] Rod follow-up completed 2026-05-07 (first touch sent; awaiting reply)
- [ ] Rod case study documentation after first SW engagement (upon reply/conversion)

---

### 2026-05-04: R2 Drive link corrected: fresh PDF re-uploaded, old file deleted

Old Drive file 132_DHAct81kC6Obhrksyixq9lFuCSYQD deleted (broken render). Fresh upload from local disk. New ID: 1ctmqUjhxa5hBkIj47AMDPvgbJzXwkETd. sw_t5.py and harvest.md updated.

### 2026-05-04: R2 SHIPPED: SaaS Audit upsell wired into SW sequence

PDF already existed (`workspace/articles/2026-04-28-saas-audit-assets/saas-audit.pdf`, built 2026-04-28).
Uploaded to Google Drive (file ID `1ctmqUjhxa5hBkIj47AMDPvgbJzXwkETd`, public anyone-with-link).
Built `templates/email/sw_t5.py`: Day 17 upsell, niche-personalized, links to Drive PDF, $500 flat CTA.
Extended SW sequence from 4 to 5 touches (Day 17 added). TOUCH_DAYS_SW + TEMPLATES both updated.
R2 milestone status flipped to SHIPPED.

Branch: `feature/saas-audit-upsell` [READY].

### 2026-05-04: R1c website-teardown skill SHIPPED

`skills/website-teardown/` built and pushed on `feature/website-teardown` [READY].

**What shipped:**

- `skills/website-teardown/SKILL.md` - 6-phase thin orchestrator. Chains website-intelligence (Ph1), web-design-guidelines (Ph2), seo-strategy (Ph3), kie_media (Ph4), then writes both reports (Ph5-6). No logic duplication. Verification checklist + pricing reference included.
- `skills/website-teardown/templates/internal-viability-report.html` - Dark-themed internal report. Verdict block (PURSUE/DROP), 5-dimension weighted score, hard stops, fit signals, price band, red flags, competitor table, research file links.
- `skills/website-teardown/templates/client-teardown-report.html` - Light-themed client report. Gift framing (not audit framing). Findings with verify-in-60s instructions, competitor gaps, CSS drag-slider before/after, outcomes list, single CTA block. Zero internal framing.

**Note on coordination claim:** Postgres not reachable from Windows dev session. Single agent, no contention risk. Branch claimed implicitly via git checkout -b.

**Next:** run end-to-end against next SW prospect after Elevate. Confirm both reports generate, no internal leakage, em-dash sweep clean, slider renders.

### 2026-05-04: Design quality lift session SHIPPED - taste-skill absorbed, 4 skills upgraded, followup queue cleared

Absorbed `leonxlnx/taste-skill` (MIT, 12 SKILL.md files). Security scan: STATIC-CLEAN. Sankofa + Karpathy both ran. Chairman: "gap is in Kie prompt construction, not art direction vocabulary." Karpathy: SHIP.

**What shipped:**

- `skills/frontend-design/SKILL.md` - Kie prompt block replaced with 6-field structured template (Composition Anchor + Subject + Lighting/Mood + Palette + Background Mode + Anti-Slop Prohibition per site type). 3 worked examples (roofing hero, pediatric dental, before/after pair).
- `skills/frontend-design/references/design-audit.md` - New. 80+ item anti-generic checklist (typography, color, layout, interactivity, content, components, icons, code, strategic omissions, slop final check). Wired into Step 5 pre-launch gate.
- `skills/kie_media/SKILL.md` - Studio Art Direction section added. 6-field prompt template, per-channel palette anchors (Under the Baobab / AI Catalyst / 1stGen Money), anti-slop prohibitions per channel, 3 worked examples, Ken Burns still rule.
- `scripts/markitdown_helper.py` - markitdown v0.1.5 wrapper. URL, local file, YouTube to Markdown. Validated on 3 artifacts.
- rtk v0.38.0 installed in WSL2 (`/root/.local/bin/rtk`). Global hook registered. Run `rtk gain` after 5 sessions.
- `absorb-followups.md` - All 2026-05-02/03/04 entries confirmed shipped or pre-existing. Queue clean.

**Open / blocked:**
- context-mode MCP: installed, failing to connect - needs `/ctx-upgrade` or restart (user action)
- MemPalace pilot: dedicated session when ready (target 2026-05-11)
- Studio M3 first render: waiting on qa-passed candidates
- Rod/Elevate R1: Boubacar's court

**Karpathy P4 WARN:** Verify on next live SW/CW site build that Kie prompt contains 2+ compositional vocabulary terms (composition anchor / background mode / anti-slop prohibition).

### 2026-05-04: R-automation milestone added - n8n-mcp installed, agency methodology absorbed

Absorbed `czlonkowski/n8n-mcp` (MCP server, MIT, 1,650 nodes, 2,352 templates). Security scan: STATIC-CLEAN. Verdict: install-only - MCP wired via `claude mcp add n8n-mcp -- npx n8n-mcp`. No skill wrapper needed; value is in Claude having node knowledge, not in a thin README skill.

Separately absorbed X-thread 6-phase AI automation agency playbook (@eng_khairallah1). Sankofa+Karpathy audits: real leverage is the engagement methodology, not the tool. Chairman verdict: n8n-mcp is a dependency; `cw-automation-engagement` skill is the actual producing motion.

R-automation milestone added. Karpathy WARN: v1 scoped to Phase 3 only (case study acquisition). Full 6-phase skill only after first paid engagement closes. Target: skill built by 2026-05-18, first engagement by 2026-07-04.

Strategic context locked: this is the "AI automation agency adjacent to CW" model. Same buyer, same discovery motion, natural upsell. Market window noted - supply of builders still thin vs demand.

Next: build `skills/cw-automation-engagement/SKILL.md` v1 (Phase 3 only). Accept criterion at top of file before any content.

### 2026-04-29 (afternoon): transcript-style-dna wired into CW outreach (R7 active)

`voice_personalizer.py` shipped. Every CW lead now gets a personalized opener via Serper company-website lookup + BeautifulSoup scrape + transcript-style-dna extract. `_opening()` short-circuits to the voice line when present. `morning_runner.py` Step 4.5 personalizes the day's CW leads between Apollo topup and CW sequence.

Smoke test on 3 real CW leads succeeded. Galen Murdock's opener referenced his BBC interview. Ben Teerlink's named his domain. Adam Ingersoll's referenced Lehi.

Three structural fixes were forced by the smoke test:

1. CW Apollo leads have no `website_url`. Added `find_company_website` (Serper search by company name + city, skips aggregators) so personalizer can derive one.
2. Firecrawl free tier exhausted (HTTP 402). Swapped `fetch_site_text` to plain `requests + BeautifulSoup`. Decision: don't pay $16-20/mo Hobby until lift test KEEP verdict. Memory: `reference_firecrawl_pricing_2026.md`.
3. scan_line in voice short-circuit was injecting lead name into "what {name} could look like": read as AI slop when {name} was a person. Made generic.

Em-dash hook also updated to scan staged diff only, not whole file (Karpathy + Sankofa both rejected bundling pre-existing dirt).

R7 milestone added with full eval procedure for 2026-06-01. Calendar reminder also set.

Branch: `feature/style-dna-wirein` (11 commits). Not pushed to remote yet. VPS deploy gate held until Boubacar approves.

### 2026-04-29: Email sequences + GeoListed site launch

Full CW + SW email sequence engine built (`skills/outreach/sequence_engine.py`). CW = 5-touch (Day 0/6/9/14/19), SW = 4-touch (Day 0/3/7/12). SaaS audit PDF wired into CW T2. All legacy one-shot senders disabled. Both pipelines verified dry-run clean on VPS.

Signal Works landing page launched at geolisted.co (Hostinger, bokar83/geolisted-site). LLM chat preloader + particle network hero. Nav, favicon, gold cursor. "You were not in the answer." gut-punch subhead.

Auto-send is OFF. Both pipelines are draft-only. To enable: `AUTO_SEND_CW=true` / `AUTO_SEND_SW=true` in VPS `.env`.

Next: review first batch of drafts, flip auto-send, wire Studio into runner, confirm geolisted.co Hostinger connection.

### 2026-04-28: First revenue session. YC RFS S26 strategy analysis

YC RFS Summer 2026 fetched and analyzed through Sankofa Council + Karpathy Audit. Key finding: YC has published enterprise names for what agentsHQ is already building at SMB scale (Company Brain, AI OS, AI-Native Service Companies). Direction validated. Constraint is the sales story, not capability.

Milestones R1-R6 defined. Status snapshot populated. Three immediately actionable items this week: subject line test, SaaS audit one-pager, "We are your AI department" offer page.

Full analysis artifact: `docs/strategy/yc-rfs-s26-analysis.md`

Next: R1 closes when first Signal Works contract signs. Then R2 (SaaS audit) and R3 (CW Signal Session) run in parallel.

### 2026-04-25: Stub created

Created alongside autonomy roadmap. Boubacar said revenue work runs in parallel to autonomy build but in separate sessions. This stub is a holding place.

---
