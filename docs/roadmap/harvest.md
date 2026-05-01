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

### R1: First Signal Works contract (trigger: email reply converts)

**Status:** In progress. Email pipeline live. First contract target 2026-05-02. **Elevate Roofing & Construction (Rod, Medford OR) is the live R1 conversion attempt.**

**Actions before this milestone closes:**

- **A/B TEST PAUSED (2026-04-28):** All leads get Variant A (original score framing). Variant B code preserved in `email_builder.py` with `AB_TEST_ACTIVE = False`. Re-enable after 2026-05-12 once SW sequence performance data exists. To activate: flip `AB_TEST_ACTIVE = True` and define reply-rate criterion before sending.
- Follow up on any inbox reply within 24 hours
- Close at Signal Works Tier 1 pricing ($500 setup + $497/month)

**Success criterion:** Signed contract + first payment received.

#### R1a: Score-report conversion methodology (NEW . added 2026-05-01 mid-session)

**Why this exists:** First conversion attempt (Rod / Elevate) surfaced a gap in the SW pitch . the v1 "Before/After scorecard" report was internally proof-strong but cold-read weak. Sankofa Council 2026-05-01 verdict: judgment-call scores torch trust, "GEO" jargon gates comprehension, no money line, no real CTA, project-plan masquerading as a call-to-action. The fix is a repeatable 8-step playbook every SW prospect now goes through.

**Operator framing (locked 2026-05-01):** "Removing pain that's worth paying me to remove." Every Rod-facing artifact must read as *I see a problem costing you money, I already started fixing it, here's the easiest way to look at it.* Not *here's an audit of what you got wrong.*

**Status:** In flight. Live artifacts at `projects/elevate-built-oregon/_build/` + localhost:8771.

**The 8-step playbook (becomes the SW conversion standard):**

1. **Soften the verdict . acknowledge the business the prospect actually built before naming what's missing.** *(Done for Rod 2026-05-01.)*
2. **Drop industry jargon . "GEO" → "AI search visibility (ChatGPT, Perplexity, Gemini)" . speak the prospect's vocabulary.** *(Done for Rod 2026-05-01.)*
3. **Replace the project-plan CTA with a single ask . "Text 'site' to [number]" . phone + name + verb.** *(Done for Rod 2026-05-01; needs real number, currently `[YOUR PHONE NUMBER]` placeholder.)*
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

#### R1a-v3: Hook-and-deliverable architecture (locked 2026-05-01 mid-session, post-v2 Sankofa)

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

### R1c: website-teardown skill (one-trigger master diagnostic)

**Status:** Skill scaffolded 2026-05-01. Ready to test on next prospect.
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

### R1d: catalystworks.consulting v1 self-teardown (eat our own food)

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

### R1e: catalystworks.consulting v3-WOW (cinematic + Constraints AI live demo)

**Status:** Tier 1 shipped 2026-05-01 to `dev-v3-WOW` branch. Sankofa Council + design+SEO audit run. Tier 2 + Tier 3 planned below, not yet built.

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
| T2.1 | Anonymized 30-day-outcome strip below offer (3 rows: industry / what was stuck / what changed). Use real informal Signal Sessions Boubacar has run; composite if needed (clearly labeled). | 90 min | Closes the "no social proof" cold-read gap (Sankofa Outsider) |
| T2.2 | Programmatic SEO: 5 lens-explainer pages (`/lens/throughput`, `/lens/friction`, `/lens/decision`, `/lens/information`, `/lens/inference`) | 3 hr | Site has 3 ranking pages today. 8 pages rank for ~8x more long-tail. |
| T2.3 | Programmatic SEO: 3 industry-specific pages (`/for/professional-services`, `/for/hvac`, `/for/healthcare-smb`) | 2 hr | Adds vertical entry points |
| T2.4 | Migrate Three.js off deprecated UMD build (`build/three.min.js` → ES module or pin `three@0.149`) | 10 min | Prevents silent breakage on next CDN update (audit #11) |
| T2.5 | Title + meta rewrite with "Salt Lake City", "Utah", "fractional advisor" keywords | 4 min | Closes local-SEO gap (audit #8) |
| T2.6 | Footer link tap targets to 44x44 min height on mobile | 4 min | Mobile a11y standard (audit #12) |
| T2.7 | Create paid `Executive Signal Session` Calendly event type (90-min, $497, Stripe-wired) and switch CTA from discovery-call URL to direct booking | 30 min on Calendly side | Removes one funnel step. Currently using free discovery as stepping stone. |
| T2.8 | Deploy `_worker.js` to Cloudflare Workers; set OPENROUTER_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, HASH_SALT secrets; paste deployed URL into `WORKER_URL` constant in `index.html` | 20 min | Activates real Claude/GPT diagnoses + Supabase capture (currently simulated mode) |

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

### R2: SaaS Audit offer live ($500 flat)

**Status:** Not yet built. Unblocked now.
**Trigger:** Can build immediately. Target: this week.

**What it is:** One-page PDF showing 5 common SMB SaaS tools (Zapier, HubSpot Starter, Monday.com, Calendly Pro, ActiveCampaign), their monthly cost, and what an agent replacement costs. Priced at $500 flat for the audit + replacement plan. Add as upsell sequence for Signal Works prospects who do not respond to the AI presence pitch.

**Why:** Buyer calculates ROI in 30 seconds. Fastest path to a cash transaction from cold email. No new infrastructure required.

**Success criterion:** One paying audit client within 30 days of offer going live.

---

### R3: First CW Signal Session sold ($497)

**Status:** Waiting on R1 social proof or direct LinkedIn outreach conversion.
**Trigger:** After R1 closes OR first LinkedIn discovery call books.

**Actions:**

- Run Discovery Call OS v2.0 on first call
- Diagnostic output: one named problem, written, specific, with implications and clear next action
- Close at $497 Signal Session

---

### R4: "We are your AI department" unified SKU designed

**Status:** Concept only. Design phase.
**Trigger:** After R1 + R3 both close (need proof that both brands convert independently before bundling).

**What it is:** Combined offer: CW diagnostic + Signal Works AI presence + monthly operations report = $997/month. One SKU. One pitch. Removes decision complexity for buyers who want the full picture.

**Build required:** One offer page on Signal Works or CW site. Pricing decision. Zero infrastructure work.

---

### R5: Client portal pilot (Atlas dashboard white-labeled)

**Status:** Parked until R1 closes.
**Trigger:** First Signal Works client asks for more visibility into their data.

**What it is:** Permission gate on existing Atlas dashboard showing that client's AI presence data. One afternoon of work per client. Adds $97/month to existing plan.

**WARN (Karpathy):** Do not build until one client explicitly requests it. Test with weekly automated email report first. If that creates enough perceived value, build the portal. If not, skip it.

---

### R6: Repeatable lead source identified

**Status:** Not yet measurable. Needs 30 days of outreach data.
**Trigger:** After 100+ contacts reached and reply/close rates logged.

**Measure:** Which source (cold email, LinkedIn, BNI, referral) produces the lowest cost-per-conversation.

---

### Quality follow-ups (small, opportunistic)

These are paper cuts surfaced during 2026-04-29 work. None block the cash path. Pull when a session has a 15-30 min gap.

- **email_builder.py pre-existing em-dashes (~15-20 instances).** Diff-aware em-dash hook (`scripts/check_no_em_dashes.py`) now ignores them, but they will fire if anyone passes `--full`. Run `python scripts/check_no_em_dashes.py --full signal_works/email_builder.py`, scrub each prose `--` to `:` or `,`, commit as one cleanup.
- **scan_line `{name}` injection bug for CW leads.** In `_opening()` template branches (lines ~285, 296, 318+ on `feature/style-dna-wirein`), scan_line uses `{name}` which for CW leads is a person's name, producing "a quick demo showing what Adam Ingersoll could look like with a site built for AI visibility." The voice-line short-circuit at line 255 already de-personalized; the template branches still have the bug. SW leads are unaffected because `name` is the business there. Fix: detect when lead is CW (source contains "apollo") and use generic phrasing, OR add `business_name` field that maps to lead.company for CW and lead.name for SW.

---

### R7: transcript-style-dna lift-test verdict (KEEP or DELETE)

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

## Cross-References

- Pipeline playbook: `docs/playbooks/pipeline-building-playbook.md`
- Memory: `project_pipeline_playbook.md`, `project_outreach_playbook.md`, `project_discovery_call_system.md`, `feedback_no_client_engagements_yet.md`, `feedback_facilitator_not_hero.md`
- Skills: `cold-outreach`, `local_crm`, `apollo_skill`, `hunter_skill`
- Catalyst Works site: `output/websites/catalystworks-site/`

---

## Session Log

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
