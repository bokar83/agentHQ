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

- **A/B TEST LIVE (2026-04-28):** Odd-ID leads get Variant B ("Your competitors just got a 20-person AI team"). Even-ID leads get Variant A (original score framing). Routing: `signal_works/email_builder.py:_ab_variant()`.
- **Revert criterion:** If Variant B does not outperform Variant A in reply rate by 2026-05-03, delete the variant-B branches in `_subject()` and `_opening()`. Check replies that day.
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

## Cross-References

- Pipeline playbook: `docs/playbooks/pipeline-building-playbook.md`
- Memory: `project_pipeline_playbook.md`, `project_outreach_playbook.md`, `project_discovery_call_system.md`, `feedback_no_client_engagements_yet.md`, `feedback_facilitator_not_hero.md`
- Skills: `cold-outreach`, `local_crm`, `apollo_skill`, `hunter_skill`
- Catalyst Works site: `output/websites/catalystworks-site/`

---

## Session Log

### 2026-04-28: First revenue session. YC RFS S26 strategy analysis

YC RFS Summer 2026 fetched and analyzed through Sankofa Council + Karpathy Audit. Key finding: YC has published enterprise names for what agentsHQ is already building at SMB scale (Company Brain, AI OS, AI-Native Service Companies). Direction validated. Constraint is the sales story, not capability.

Milestones R1-R6 defined. Status snapshot populated. Three immediately actionable items this week: subject line test, SaaS audit one-pager, "We are your AI department" offer page.

Full analysis artifact: `docs/strategy/yc-rfs-s26-analysis.md`

Next: R1 closes when first Signal Works contract signs. Then R2 (SaaS audit) and R3 (CW Signal Session) run in parallel.

### 2026-04-25: Stub created

Created alongside autonomy roadmap. Boubacar said revenue work runs in parallel to autonomy build but in separate sessions. This stub is a holding place.

---
