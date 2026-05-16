# Lighthouse — 12-Week Revenue Sprint

**Codename:** lighthouse
**Status:** ACTIVE
**Lifespan:** 2026-05-12 → 2026-08-04 (12 weeks)
**Owner:** Boubacar Barry
**One-line:** master revenue roadmap. ONE channel for W1-3 (Daily Fast-Feedback Sprint), Brandon as accountability partner, 3 paying clients across SW + GW + CW by 2026-08-04.

## Why Lighthouse exists

Until Lighthouse closes (3 paying clients by 2026-08-04), it is the **only** active strategic roadmap. All other roadmaps (harvest, ghost, atlas, compass, studio) feed INTO this one. They are sub-systems. Lighthouse is the parent.

**Why this name:** strategy is what guides you when fog hits. Lighthouse fires on a fixed cycle (10:00 MDT sprint, Sat review, Thursday check-in). It signals from a fixed point on land (South Jordan, UT). Sankofa fit: lighthouse hosts, doesn't hunt.

## Done definition

Land 3 paying clients across SW + GW + CW combined by 2026-08-04. At least 1 in each brand.

12 weeks. One number. Three brands. If 0/3 at mid-cycle 2026-06-23 review → re-council, full rewrite. If 1/3 → continue. If 2-3/3 → scale what works.

## Status Snapshot (2026-05-12)

- Day 0 Action 1 (Brandon accountability invite) sent ~20:30 MDT. Awaiting reply.
- Strategy doc v8 served at localhost:8801 + emailed digest (msg id `19e1f1454a5bb2e5`)
- Atlas sub-page built at `thepopebot/chat-ui/atlas-lighthouse.html` (deploy pending)
- Tracker at `data/inbound-signal-log.md` scaffolded
- Calendar wire-up pending — Google Calendar MCP next
- Brand: Catalyst Works = public. agentsHQ = internal tool, never in outbound.

## Live deliverables

- **Master strategy HTML (v8):** `docs/strategy/lead-strategy-2026-05-12.html`
- **Atlas sub-page:** `thepopebot/chat-ui/atlas-lighthouse.html` → `agentshq.boubacarbarry.com/atlas/lighthouse`
- **Sankofa Council premortem:** `outputs/council/2026-05-12-20-20-24.html`
- **Sankofa Council template review:** `outputs/council/2026-05-12-22-32-40.html`
- **Email-events ledger:** `migrations/009_email_events.sql` (branch `feat/email-events-canonical-ledger` [READY])
- **Daily tracker:** `data/inbound-signal-log.md`
- **Memory:** `project_lead_strategy_2026-05-12.md`

## The 8 prevention mechanics (L-R1 through L-R8)

> **Naming convention:** Lighthouse Routine milestones use `L-R<n>` prefix. Lifecycle (weekly) milestones use `L<n>` (L0-L7). Future codenames mirror: Ghost = G-R<n> / G<n>, Atlas = A-R<n> / A<n>, etc.

| ID | What | Trigger | Targets |
|---|---|---|---|
| **L-R1** | Daily Fast-Feedback Sprint | M-F 10:00 MDT | Feedback Blackout |
| **L-R2** | First Win Ceremony — Telegram 🚀 on first REAL reply | Once, auto | No First Win |
| **L-R3** | Guilt-Free Reset Trigger | Daily 10:30 if L-R1 missed | Shame Spiral |
| **L-R4** | Weekly Priority Triad Lock — 3 lanes max | Sat 10:00 MDT | Cognitive Overload |
| **L-R5** | Conversion Scorecard | Sat 10:30 MDT | Automation as Enabler |
| **L-R6** | Auto-Close Script — T+24h value, T+72h ask | Post-session | Avoidance of Closure |
| **L-R7** | Idea Vault Lock | Anytime | Shiny-Drift |
| **L-R8** | List Hygiene Gate + Reply Classifier Fix | Before any cold send | Sender Reputation Cliff |

## Milestones

### L0 — Day 0 (Tuesday 2026-05-12) — IN PROGRESS

- ✅ Brandon accountability invite text sent
- [ ] Warm Utah contact list (10 names)
- [ ] Pre-slot 5 outbound messages for Wed-Fri
- [ ] Google Calendar wire-up

### L1 — Week 1: Reply Velocity (5/13-5/17)

**Daily M-F:** 10:00 sprint (V1/V2) + 10:05 Brandon morning ping + 17:30 EOD ledger if landed + 21:00 log+pre-slot.
**Expected:** ≥3 replies + ≥1 audit delivered. **Gate:** ≥4 of 5 days.

### L2 — Week 2: Open the Funnel (5/19-5/24)

Mix V3 (dormant) + V4 (referral-fresh). **Expected:** ≥5 audits delivered, ≥1 "tell me more". **Gate:** ≥4 of 5 days.

### L3 — Week 3: First Conversion (5/26-5/31)

Convert 1 "tell me more" → paid Signal Session offer. **Expected:** ≥1 paid Signal Session booked OR ≥10 audits delivered. **Gate:** ≥4 of 5 days.

### L4 — Weeks 4-6: Expand (6/2-6/21)

Gated on L1-L3 hitting ≥10 audits + ≥1 paid call. Add: LinkedIn discipline (Logan 5x/wk) + paid Signal Session $250 Wed afternoons. **Expected:** 2 sessions completed + 1 client landed.

**Candidate tactic (Brandon Lunch Reconnect):** 1 lunch/wk with friend or past associate, reconnect-first not sell. Surfaces "what you got going on" naturally, generates referrals downstream. Lag mechanic, not reply-velocity. Decide at Sat 5/16 L-R4 Triad Lock whether to start as W4+ ritual or hold to L5 mid-cycle review. Sourced from Brandon accountability reply 2026-05-14. Distinct from descoped "Coffee meetings as default" (lunches, not default, referral-mechanism not first-touch close).

### L5 — Week 7: Mid-Cycle Council (6/23-6/28)

Mandatory inflection. Pull data. Re-run Sankofa Council. Decide scale/pivot/rewrite.

### L6 — Weeks 8-11: Scale (6/30-7/26)

Gated on first paying client. Bring back ONE bigger play: Hive 2.0 OR Reddit deepening OR cold-mode Utah outbound. **Expected:** ≥2 more clients.

### L7 — Week 12: Close (7/28-8/2)

Wrap engagements. Write `docs/strategy/lead-strategy-2026-08-04.html` for next cycle.

## Accountability partner — Brandon

**Status:** Invite text sent 2026-05-12 ~20:30 MDT. Awaiting reply.

**Mechanic:** daily 10:05 MDT M-F morning ping (4 lines) + optional 17:30 MDT EOD ledger when something landed. 4-week commitment, then evaluate.

**Brandon's role:** reply within the hour to morning ping. "Got it" works. Silence does NOT work.

**Reciprocity (deferred to Monday 2026-05-19):** V5 LinkedIn audit offer to Brandon. Don't crowd partnership ask with service offer this week.

## Descoped Items

- Public audit of named/identifiable people (values violation; only private audits, Tier 1/2/3 escalation if any public)
- Naming Catalyst Works or agentsHQ in outbound (the work speaks)
- Free Signal Sessions as default (paid $250 trial replaces)
- Cold email volume (warm-only W1-3)
- 8 parallel lanes (Sankofa premortem killed this v3 approach)
- Facebook anywhere
- Loom anywhere
- Coffee meetings as default
- New ideas / new roadmaps (Idea Vault locks until 3 paying clients)

## Idea Vault (locked until 3 paying clients)

- **LinkedIn Page Analysis Tool** (added 2026-05-13). Productized multi-section LinkedIn profile audit, sibling to SW website-teardown. Scrapes profile (r.jina.ai or LinkedIn API), runs Headline + About + Featured + Experience + media + Recommendations + Activity audit, outputs HTML report with before/after mockup. 2-4 hour delivery vs 22-min for the 1-page audit. Pilot candidate: Brandon reciprocity 2026-05-19 IF W1 reply velocity is weak per Saturday L-R4 Triad Lock review. Productize for L4 Weeks 4-6 IF L1-L3 gate clears AND pilot validates demand. Anchor: Brandon profile observation 2026-05-13 (creative director with outstanding work that does not show on his profile).

## Cross-references

- Master strategy: `docs/strategy/lead-strategy-2026-05-12.html`
- Sankofa premortem: `outputs/council/2026-05-12-20-20-24.html`
- Sankofa template review: `outputs/council/2026-05-12-22-32-40.html`
- harvest.md H1j SHIPPED
- Memory: `project_lead_strategy_2026-05-12.md`, `feedback_agent_time_perception_broken.md`
- Tracker: `data/inbound-signal-log.md`

## Session Log

### 2026-05-14 (W1 Day 2 morning) - Nate V1 LinkedIn + Chad Thu check-in + PGA reschedule

**Sprint operations (Day 2 morning):**
- 10:00 V1 sent to Nate Tanner via LinkedIn (channel pivot from queued text)
- 10:00 Thursday check-in to Chad Burdette via LinkedIn audit message + text bridge ("doesn't log in daily")
- Brandon morning ping queued 10:05 MDT (user handles outbound)
- `data/inbound-signal-log.md` +2 events. `data/lighthouse-warm-list.md` Nate flipped to sent.
- Commit `f5d08a2` rebased on origin (which had `49102c59` autonomous studio firecrawl report) and pushed as `8c2c71f3`. VPS synced.

**Scheduling shift:** PGA Kickstart Call rescheduled Thu 5/14 to Fri 5/15 (time TBD). Today freed for audit prep window if Nate replies yes. Fri 10:00 Chase V1 send may collide with PGA depending on call time. Reslot pending time confirmation. PGA prep doc filename has stale date suffix (`pga-call-extraction-questions-2026-05-14.md`); content still valid, rename optional.

**Score:**

| Day | Sent | Reply | Audit delivered |
|---|---|---|---|
| 1 Wed | 1 (Chad text) | 0 | 0 |
| 2 Thu AM | 1 (Nate LinkedIn) + Chad Thu check-in | 0 (pending) | 0 |

**Pending Thursday PM:**
- 17:30 EOD ledger if Nate/Chad reply lands
- 21:00 ritual: pre-slot Mon Chris V1 send + confirm/reslot Fri Chase against PGA time
- If Nate replies yes by ~12:00 MDT, owe audit by 17:00 MDT

**Brandon accountability reply (2026-05-14):** "Something that has been useful for me is to schedule lunches with friends and associates to reconnect. Naturally people want to know what you've got going on. It's never a selling opportunity but it gets your skill into their network and usually results in some referrals down the road. Got it! Keep going brother." Captured as L4 candidate tactic (Brandon Lunch Reconnect, 1/wk, reconnect-first not sell). NOT added to W1-3 sprint mechanic (preserves 1-channel reply-velocity focus + Sankofa premortem killed 8-lane sprawl). Decision point: Sat 5/16 L-R4 Triad Lock alongside Brandon-pilot decision. Distinct from descoped "Coffee meetings as default" per L4 block note.

---

### 2026-05-14 (W1 Day 2 evening close, ~14:00 MDT) - Nate delivered EARLY, Chad drafted + held, pattern catalog locked

**Two deliverables for the day:**

- **Nate Tanner audit DELIVERED 13:39 MDT**, 3 hours 21 minutes EARLY on the 5 PM SLA. 5 rounds of Sankofa Council pressure. Peer-in-field pattern. Email msg `19e27fad4a12c892` from `boubacar@catalystworks.consulting` verified, BCC to self confirmed. See `feat/nate-tanner-audit-2026-05-14` branch (pending Gate merge).
- **Chad Burdette audit DRAFTED through 4 rounds.** v4 locked. 3-paragraph anchor honoring 20+ year friendship + recent absence without splashing (his wife's cancer last year, Boubacar's own difficulties this stretch). Body = headline rewrite (surgical) + post strategy with cadence, 4 lanes, 3 industry-specific example hooks. HELD: no Gmail draft until Boubacar gives explicit go. See `feat/chad-burdette-audit-2026-05-14` branch (parked, NOT [READY]).

**Per-recipient audit pattern catalog (3 variants now established):**

| Variant | When to use | Structure |
|---|---|---|
| Chad-cold (original playbook v3) | Cold prospect (W2+ dormant V3 sends, no prior relationship) | 1 finding, 1 rewrite + conviction, ~1 page |
| Nate-peer | Friend who IS a peer in field (coach, consultant, fellow operator) | Dual finding, 2 options + recommendation, bespoke operator-lens, ~1.3 page |
| Chad-friend-voice (new) | Close friend whose profile needs voice-coaching (posting cadence + types + examples) | Surgical fix + strategic push, cadence + lanes + example hooks, ~1.5 page |

Future audits map to one of these on send-decision. Per-recipient deviation logged in audit commit message.

**Memory rules added today** (all in `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/`):

- `feedback_linkedin_audit_html_mobile_accessible.md` (HTML email body INLINE canonical, Vercel fallback, ask-for-email after V1-yes, both-paths-always)
- `feedback_audit_sla_holding_note.md` (preventive principle, T-30 holding ping if not send-ready)
- `feedback_audit_review_before_email_draft.md` (render+preview before Gmail draft; draft creation needs explicit verbatim go)
- `feedback_audit_local_storage_stable_path.md` (mirror to `D:/Ai_Sandbox/agentsHQ-audits/`, NOT D:/tmp)
- `feedback_audit_pattern_catalog.md` (the 3 variants above + decision rule)

**Boubacar momentum signal (2026-05-14 ~14:11 MDT):** "I've never had this much momentum with the other plans we've had in the past. This feels better. Feels like we're going the right way." Logged as leading indicator that Lighthouse cadence + Sankofa rigor + per-recipient pattern discipline is the right shape. Track through W1 close (Sat 5/17 L-R4 Triad Lock) for first formal validation.

**Score Day 2 final:**

| Day | Sent | Reply | Audit delivered |
|---|---|---|---|
| 1 Wed | 1 (Chad text) | 0 | 0 |
| 2 Thu | 1 (Nate LinkedIn) + Chad Thu check-in | 1 (Nate yes 11:30) | 1 EARLY (Nate 13:39, 3:21 ahead of SLA) |

W1 gate (>=3 replies + >=1 audit delivered): **1 reply / 1 audit toward 3 / 1**. 3 weekday sprints remaining (Fri Chase, Mon Chris, Tue Dan).

**Day 3 Friday 2026-05-15 plan:**

- 10:00 MDT Chase Weed V1 send (pre-slotted, text channel per warm list)
- Confirm PGA Kickstart Call time (rescheduled Thu to Fri, time TBD); reslot Chase if collision
- Pre-write Mon check-in for Nate (matches his audit footnote promise)
- Pre-write Mon V1 opener for Chris Whitaker (sister, V1 close-friend tag)
- Watch Nate inbox for reply
- Watch Chad inbox for V1 reply (if yes: send drafted audit same day)
- Brandon morning ping 10:05 MDT
- Brandon Monday reciprocity decision held to Sat 5/16 L-R4 Triad Lock

**Status snapshot: 2/12 weeks of Lighthouse complete. First audit shipped, ahead of SLA. Pattern catalog locked. Momentum positive.**

### 2026-05-13 (W1 Day 1) - Sprint executed, audit template shipped + Council-edited, Idea Vault opened

**Sprint operations (Day 1):**
- 09:50 sprint pre-read done at the mechanic
- 10:00 V1 sent to Chad Burdette (text, "Need a favor", free LinkedIn audit promised by 5 PM)
- 10:05 Brandon morning ping sent
- Warm list locked at `data/lighthouse-warm-list.md`: 5 V1-eligible W1 (Chad, Nate, Chase, Dan, Chris-sister) + 5 V3-eligible W2 (Doug, Benjamin, Brody, Bruce, Dawn)
- `data/inbound-signal-log.md` Day 1 SENT event logged

**Audit deliverable + playbook shipped:**
- `data/lighthouse-audit-template.html` (HTML, 1-pager, 9 slots after Council revision)
- `data/lighthouse-audit-playbook.md` (7-min diagnostic + Cole hook formats + Strategic Bridge guard + CTQ 5-item self-check)
- Commits `151e0fa`, `2811417` for v1, then `ced966a`, `3ec5d68` for v2 (Council edits)
- Localhost preview: http://127.0.0.1:8802/lighthouse-audit-template.html

**Sankofa Council ran on audit template + playbook.** Verdict: SHIP WITH 2 EDITS.
1. Witness-anchor sentence at top of HTML template (slot `[WITNESS_ANCHOR]`). Converts document from system output to human gesture. 30 sec per send.
2. Strategic Bridge footnote replaces "check back Thursday, not to pitch" closer. Names the $250 Signal Session, 7-section deluxe option, "Signal" reply trigger, by-Friday scheduling. Frames audit as sample of method, not conclusion.
Both shipped. Council HTML report at `/outputs/council/2026-05-13-17-53-06.html` on VPS.

**LOCKED 2026-05-13 PM** per Boubacar approval after mobile preview review. Template v2 (commit `ced966a`) + playbook v2 (commit `3ec5d68`) are the canonical W1-3 deliverable. Any future revision MUST re-run Sankofa Council + Karpathy before shipping. No silent edits.

**REVISED 2026-05-13 PM (Council Pass 2: user override)** after Boubacar caught that the Strategic Bridge in the audit footnote violates the V1 promise ("Free. No pitch, no calendar link."). Pricing the 50 Signal Session on the audit itself reads as bait-and-switch even when the audit is real value. Reverted Edit 2: template footnote restored to v1 closer ("check back Thursday, not to pitch"). Edit 1 (witness anchor) kept. New playbook section "When to introduce the 50 Signal Session" added with decision tree for post-Thursday-check-in conversation. CTQ check #5 now enforces zero pitch in footnote. Commits: `66d309a` (template) + `e0b50c2` (playbook). Canonical revised state: template v3 + playbook v3. Lock holds against silent agent edits; explicit user override is a valid Council Pass 2 path.

**Idea Vault opened:** LinkedIn Page Analysis Tool (sibling to SW website-teardown, 2-4 hour multi-section profile audit). Pilot candidate: Brandon reciprocity 2026-05-19 IF W1 reply velocity is weak per Saturday L-R4 Triad Lock. Productize for L4 Weeks 4-6 IF L1-L3 gate clears + pilot validates. Anchor: Brandon's profile observation today (creative director with outstanding work hidden by thin profile).

**Pending Wednesday afternoon:**
- If Chad replies yes: deliver audit by 5 PM via canonical CW OAuth path
- 21:00 ritual: pre-slot Thu (Nate) + Fri (Chase) V1 sends, pre-write Thu check-in note for Chad, log day

**Thursday 2026-05-14 (PGA Kickstart Call):** prep already shipped at `docs/analysis/pga-call-extraction-questions-2026-05-14.md`. No buy decision on the call. $1K cap. Steer to sales/pricing/ICP. 24-hour cooldown before any spend.

**Cross-ref:** `docs/handoff/2026-05-13-main-session-pm.md` for full main-session log including non-Lighthouse work (watcher hardening, recursive submodule fix, mobile hamburger, session-collision followups, multiplier_tick fix).

### 2026-05-12 — Lighthouse created + Day 0 Action 1 done

**Shipped:**
- Strategy v8 HTML written + served localhost:8801 + emailed digest (msg id `19e1f1454a5bb2e5`)
- Atlas sub-page built at `thepopebot/chat-ui/atlas-lighthouse.html` with nav link (deploy pending)
- Lighthouse roadmap created
- Sankofa Council ran 2x: premortem on plan v3 + template review on V1-V5
- Email-events ledger shipped on `feat/email-events-canonical-ledger` branch [READY]
- 4 ground-truth corrections: 500 sends not 100+, 0 real replies, 9.4% delivery failure, two-DB drift

**Day 0 Action 1:** Brandon accountability invite text sent ~20:30 MDT. Awaiting reply.

**Decisions locked:**
- Project name = Lighthouse
- Catalyst Works = public brand. agentsHQ = internal tool.
- $250 paid Signal Session trial (not free)
- Brandon V5 audit ask deferred to Monday 2026-05-19
- Public audit of named people = BANNED. Tier 1/2/3 escalation only.
- No coffee meetings as default
- 10:00 MDT all timings
- .md tracking for W1-W3, escalate to Postgres in W4 if cycle continues

**Pending overnight / Wed morning:**
- Brandon reply
- Day 0 Actions 2-4 (warm list, sprint pre-slots, calendar alarms)
- Google Calendar MCP wire-up
- Atlas sub-page deploy to VPS

### 2026-05-14 (W1 Day 2 PM) — Studio pipeline-spine RCA (sub-roadmap, not W1 deliverable)

Side track from W1 Day 2 evening: Boubacar asked Studio status. RCA exposed 3 coupled defects (em-dash sanitizer asymmetry, missing scouted→Ready filter, no silence watchdog). Pipeline silently broken for 22+ hours. Fix shipped via `fix/studio-emdash-spine` (gate-merged `d3651e7`). Engagement scraper bug surfaced + shipped same session (`fix/engagement-scraper-locale`, 22/22 tests). Bulk-reset cleared 13 qa-failed records. 29 records now scheduled, awaiting next blotato fan-out at 09:00 UTC. Full RCA: `docs/handoff/2026-05-14-studio-pipeline-spine-rca.md`. Studio session log appended at `docs/roadmap/studio.md`.

Lighthouse-relevant note only: Studio is a sub-system feeding Lighthouse later (channels are revenue stub); this fix did NOT change W1 score (W1 = SW + GW + CW reply velocity, not Studio publish count).

**W1 Day 2 close confirmed by Sankofa subagent:** No formal Thursday demo writeup required. W1 close is Saturday 2026-05-16 10:30 MDT (L-R5 Conversion Scorecard). Day 2 evening close already committed at `fedc16b8`.

### 2026-05-15 (W1 Day 3) - closed

**Sprint operations:**
- ~10:00 MDT V1 sent to Chase Weed via **personal email** (`bokar83@gmail.com`), NOT text as pre-slotted. Channel deviation from sprint queue. Fired from Lagoon amusement park = first remote-location stress test of sprint mechanic.
- ~10:05 MDT Brandon morning ping fired (queued from Lagoon, sent on traffic clearance). Brandon replied "Got it! Nice job" within minutes. Accountability mechanic holding.
- Nate Tanner: no new event Day 3. Day 2 ~13:49 ack ("will reply next week, Dad's 70th") backfilled to signal log Day 3 morning.
- Chad Burdette: no reply Day 3. Audit still parked on `feat/chad-burdette-audit-2026-05-14` tip `fb97e67`. No Gmail draft.
- Branch `chore/day3-sprint-log-2026-05-15` commit `59f8a1ac` [READY] shipped Chase SENT + Nate NOTE backfill. Gate auto-merged.

**Channel surprise:** Boubacar emailed Chase from personal address (`bokar83@gmail.com`), not from the cw OAuth path used for Nate's audit. Reasoning surfaced Sat 5/16 morning: warm leads should feel friendship not consulting funnel. Personal email From-line matches LinkedIn mental model + drops the cw-domain sales signal. Audit itself still ships from `boubacar@catalystworks.consulting` (the audit IS the pivot - no body-copy announcement of channel change needed).

**Boubacar reframe (2026-05-16 AM, captured pre-L-R4):** warm leads = referral sources, not direct buyers. Reframes the W1 score gate. Reply velocity matters less than audit quality + relationship preservation. W2-3 success criterion shifts from "paid Signal Session conversion" to "warm leads initiating referral conversations." Sat L-R4 must wrestle with this.

**Next:** Sat 2026-05-16 10:00 MDT L-R4 Triad Lock + 10:30 MDT L-R5 Conversion Scorecard. Decide channel default + bridge timing + referral-thesis implications. See § 2026-05-16 below for full agenda.

### 2026-05-16 (W1 Day 4 - Saturday L-R4 Triad Lock + L-R5 Conversion Scorecard)

**L-R4 agenda (10:00 MDT, 3-lane lock):**

*Pre-existing items:*
1. Brandon Monday reciprocity decision: lean audit vs LinkedIn Page Analysis Tool (Idea Vault pilot)
2. Brandon Lunch Reconnect activation/hold: W4+ ritual or L5 mid-cycle review
3. First validation of momentum signal logged Day 2 (`project_lighthouse_momentum_signal_2026-05-14.md`)

*New items surfaced Day 3 / Sat morning:*
4. **Channel default for warm leads.** Current evidence: Chad text=silent 3 days, Nate LinkedIn DM=90-min reply + audit ack, Chase email-personal=too early. Sample n=3, but LinkedIn DM is the only converter so far. Boubacar's lean: **LinkedIn DM first → personal email bridge 24-48hr later**. Decide: per-recipient channel matrix OR single default with 24hr bridge OR keep text/DM/email-personal split as-is. Goal = shortest path with least friction for sender + recipient.
5. **Bridge timing rule.** 24hr (urgency) vs 48hr (warm friend cadence). Lean: 24hr for LinkedIn-active types, 48hr for friends in 6+ month cold-zone. Per-recipient, not blanket.
6. **Bridge wording.** Tone, not clock, prevents pestering. Draft: *"Hey, sent you a quick note Friday - might have buried it in your inbox/LinkedIn. Same offer if you saw it."* Lock or revise.
7. **Pre-announce cw pivot in V1 body? NO.** Decision flagged Sat morning. V1 fires from personal email; audit ships from `boubacar@catalystworks.consulting`. The audit IS the pivot. No body-copy announcement of channel change. Confirmed in L-R4.
8. **Referral-thesis reframe.** Treat warm leads as referral sources first, direct buyers second. Implications:
   - W1 reply velocity gate less critical than W1 audit quality
   - W2-3 success = referrals initiated, not Signal Session conversions
   - Audit must signal "this is the quality I produce" to anyone the recipient passes it to
   - New tracking: add REFERRAL event type to signal log if a warm lead names someone
   - Mid-cycle review at L5 should track referral conversation count, not just paid call count
9. **Shareable-audit redesign.** Downstream of #8. Current audit format is Nate-specific and not forwardable. If referral thesis is real, audit needs to be SHAREABLE: a CEO friend Nate forwards it to should see "this is the kind of work this guy does" without exposing Nate's profile internals. Three options to decide between:
   - **9a. Two-layer artifact:** Nate-specific page (private) + anonymized "audit sample" page (forwardable). Costs ~30 min extra per delivery.
   - **9b. Companion deck:** keep current audit, ADD a 1-page "here's what I do" companion that's forwardable. Lower friction.
   - **9c. Verbal-mention path:** accept referrals come via word-of-mouth not artifact forward; double down on follow-up conversations with each warm lead instead of redesigning audit. Cheapest, slowest.
   Lean: **9b**. Adds shareability without disturbing the personal gesture. Decide today, lock format before W2 sends start Mon.
10. **Dual-track sprint vs single-track.** Honest timing math: referrals take 4-12 weeks to land. If W1-W3 = warm-leads-only and they all convert via referral path, no cash hits until W6-W8 = half the sprint gone with zero revenue + zero fallback. Decide between:
    - **10a. Single-track (current):** warm-referral only through L5 mid-cycle review. Risk: W6 arrives with no cash + no fallback prepared.
    - **10b. Dual-track:** maintain warm-referral track + add direct-buyer track in parallel (CW cold outbound to SMB founders OR SW audit-to-paid funnel). One feeds referral learning + relationship, other feeds revenue. Adds 1 hour/day load.
    - **10c. Sequenced:** warm-only W1-W3 (per current plan), trigger dual-track W4 if no paid call by L3 gate. Compromise — same cap on parallel work, but adds optionality.
    Lean: **10c** if L3 looks weak by Day 12 (2026-05-24). Premature 10b in W1-W2 = scope creep. But waiting until L5 (6/23) to add direct-buyer = too late to recover sprint.

**L-R5 agenda (10:30 MDT, Conversion Scorecard):**
- W1 numbers: 3 V1 sent (Chad text, Nate LinkedIn, Chase email-personal), 1 audit delivered (Nate), 1 ack-defer (Nate), 0 confirmed yes-replies on rewrite quality, 0 paid calls
- Gate check: W1 expected ≥3 replies + ≥1 audit. Audit YES (Nate). Replies UNDER (Nate ack = 1, Chad silent, Chase too-early). 
- Score Day 4: depends on whether Chase replies Sat AM
- If gate misses: trigger L1→L2 reset decision per playbook

**Next:** L-R4 lock 3 lanes + capture decisions in `data/lighthouse-warm-list.md` (channel matrix) + `data/lighthouse-audit-playbook.md` (bridge mechanic). L-R5 score table closes W1. Open Monday 5/18 with Chris V1 + Brandon V5 lean-audit decision executed.
