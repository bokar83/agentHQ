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

**Status:** In progress. Email pipeline live. First contract target 2026-05-02.

**Actions before this milestone closes:**

- **A/B TEST PAUSED (2026-04-28):** All leads get Variant A (original score framing). Variant B code preserved in `email_builder.py` with `AB_TEST_ACTIVE = False`. Re-enable after 2026-05-12 once SW sequence performance data exists. To activate: flip `AB_TEST_ACTIVE = True` and define reply-rate criterion before sending.
- Follow up on any inbox reply within 24 hours
- Close at Signal Works Tier 1 pricing ($500 setup + $497/month)

**Success criterion:** Signed contract + first payment received.

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
