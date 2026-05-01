# LinkedIn MVM - AI Governance Flagship Motion

**Owner:** Boubacar Barry
**Created:** 2026-04-30
**Last updated:** 2026-04-30 (launch day journal appended at bottom)
**Authority:** This is the LinkedIn execution layer of the AI Governance Playbook V3 (`docs/ai-governance/Bou_CW-AI-Governance-Final-Playbook-2026-04-16.md`). Playbook V3 is the source of truth for positioning, pricing, and revenue targets. This file is the operational SOP for the LinkedIn channel only.

> **For context on why the headline / About / Featured look the way they do, jump to the Session Journal at the bottom of this file. Every decision today was deliberate, Sankofa-tested, and logged with reasoning.**

---

## The One Job

Sit at the same chair every morning at 9 AM MT. Send 5 DMs. Post if it is M/W/F. Reply to inbox. Move on. The job is conversations, not assets, not systems, not posts.

Day 30 cash target: $3,500 SHIELD invoiced and collected (per Playbook V3 §1.4).
Day 60: $7,000 running total (second SHIELD).
Day 90: $12,000 to $16,500 (third SHIELD or first Governance Sprint).

If Day 30 is missed by more than 7 days, stop content and infrastructure and run cold outreach only until the first paid Assessment is booked. This is Playbook V3 §1.4 verbatim. Read it again on May 30.

---

## The Daily 30-Minute Ritual (CW Hour)

**Time:** 9:00 to 9:30 AM MT, Mon to Fri. Calendar block: `pedu4h779gptfmscakqrtu3lss` ([open in calendar](https://www.google.com/calendar/event?eid=cGVkdTRoNzc5Z3B0Zm1zY2FrcXJ0dTNsc3NfMjAyNjA1MDFUMTUwMDAwWiBib2thcjgzQG0)).

| Min | Action |
|---|---|
| 0-5 | Mon/Wed/Fri only: pick + post the day's draft from `docs/playbooks/linkedin-posts-may-2026.md`. T/Th: skip. |
| 5-10 | Send 5 DMs. Telegram morning nudge has them ready. Copy, paste, send, mark sent. |
| 10-20 | Reply to inbox. Replies beat everything. If a reply asks for the call, send the Calendly link. |
| 20-25 | 3 high-signal comments on ICP posts. |
| 25-30 | Update lead DB. Mark the 5 you sent as `messaged`. Mark replies as `replied`. Mark booked calls as `booked`. |

**Hard rule:** stop at 9:30. Discipline is stopping, not starting.

---

## Channel KPIs (Friday review only, 5 min)

Three numbers, every Friday, written in the lead DB or a Notion log:

1. **DMs sent this week.** Target: 25 (5/day x 5 days).
2. **Calls booked this week.** Target: 1-2 by week 2, 2-3 by week 4.
3. **Cash invoiced this month.** Target: $3,500 by May 30; $12K-$16.5K by Jun 29.

If those move, the system works. If they do not, run a Sankofa diagnostic, do not blindly continue.

---

## The DM (one template, period)

Per Playbook V3 §1.5, the daily floor is 5 cold emails OR 3 cold LinkedIn DMs. We run 5 DMs/day on LinkedIn. Same template every time. No 3-touch sequence for the first two weeks. One bump if no reply after 7 days. That is it.

Template stored at: `templates/linkedin/dm_v1.py` (single source of truth, same pattern as `templates/email/cold_outreach.py`).

DM generation: drop new prospects in `workspace/linkedin-mvm/target_list.csv`. Run `python -m skills.linkedin_mvm.generate_dms` (built 2026-04-30). Output: `workspace/linkedin-mvm/dms_to_send_<DATE>.md` with one DM per prospect, LinkedIn URL above each, copy-paste ready.

---

## The List

Lead DB = Supabase `leads` table + Notion CRM Leads (`619a842a-0e04-4cb3-8d17-19ec67c130f0`). Both auto-write via `skills.local_crm.crm_tool.add_lead`. Source value: `LinkedIn`. Pipeline statuses: `new -> messaged -> replied -> booked -> paid`.

**Initial batch:** 50 names. Boubacar curates manually via LinkedIn search per Playbook V3 §1.8 (Utah owner-operator pro services 5-200 emp; trigger-event-driven; existing network; adjacent regional pro services).

**CSV columns:** name, company, title, location, linkedin_url, industry, hook (one sentence: why them, what they do, what's relevant). The `hook` column is what powers the DM personalization.

---

## The Post

3x/week, M/W/F at 9:05 AM MT. Step-8 contrarian-opinion format only (per Logan Gott framework: attach a specific opinion to a frustration the audience already feels).

Voice: Boubacar voice from `docs/styleguides/styleguide_linkedin.md`. Hook in the first 210 chars (above the "see more" cutoff). One bold idea per post. Land on the most quotable sentence. Zero emojis as bullets. Implicit CTA, not "DM me to work together."

12 posts pre-drafted at `docs/playbooks/linkedin-posts-may-2026.md`. Scheduled in Blotato for May 5, 6, 8, 11, 13, 15, 18, 20, 22, 25, 27, 29 (M/W/F for 4 weeks).

If Blotato fails (it returned 201 on 2026-04-27, fix is in `orchestrator/blotato_publisher.py`), Telegram nudge falls back to manual paste at 9:05 MT.

---

## The Calendar of Truth

Mon and Fri = post + DMs + inbox.
Tue and Thu = DMs + inbox only (no post).
Wed = post + DMs + inbox.

If a discovery call is booked, it lands afternoon (low-energy time is fine for in-the-room work; high-energy morning stays for outbound). The afternoon discovery slot is the only place afternoon energy is acceptable for this motion.

---

## What this MVM does NOT include (deliberately)

| Not in MVM | Why |
|---|---|
| Public AI Governance Field Guide PDF | Playbook V3 says Featured = catalystworks.consulting/governance + Tool Inventory Worksheet + Calendly. Do those three first. PDF is Day 31+ if at all. |
| AMPLIFY 50-question scorecard | Same reason. Playbook V3 already specifies a 15-question intake form linked from Calendly. Build that one (per §1.3 Day 2), not a new scorecard. |
| 3-touch sequence templates | Single DM + single bump for first 2 weeks. Earliest revisit: May 14. |
| Drive uploads, NotebookLM ingestion | Zero impact on Day 30 cash. Day 31+ if still useful. |
| Notion Content Board pre-loading | Blotato handles scheduling. Content Board adds 25 min of friction per post. |
| Signal Works channel-partner motion | Same audience, different offer. Run after CW Day 30 hits. |

---

## What's wired in for you

- **Calendar:** 9 AM MT recurring block, May 1 to Jun 29 (created 2026-04-30, event ID `pedu4h779gptfmscakqrtu3lss`).
- **Calendly:** "AI Governance Assessment Call (20 min)" event - created 2026-04-30 [PENDING re-auth, see todo].
- **Lead DB:** existing Supabase `leads` + Notion CRM Leads. No new tables.
- **DM generator:** `python -m skills.linkedin_mvm.generate_dms` reads `workspace/linkedin-mvm/target_list.csv` and outputs personalized DMs.
- **Telegram morning nudge:** queues 5 next-up DMs at 8:55 AM MT daily, drops in Telegram. Built 2026-04-30.
- **Posts:** 12 drafts in `docs/playbooks/linkedin-posts-may-2026.md`, scheduled in Blotato.
- **Profile rewrite copy:** `docs/playbooks/linkedin-profile-rewrite-2026-04-30.md`.

---

## Cross-References

- **Playbook V3 (authority):** `docs/ai-governance/Bou_CW-AI-Governance-Final-Playbook-2026-04-16.md`
- **Cold email (sister channel):** `templates/email/cold_outreach.py`, `skills/cold-outreach/SKILL.md`
- **LinkedIn voice/style:** `docs/styleguides/styleguide_linkedin.md`
- **Pipeline playbook (broader funnel):** `docs/playbooks/pipeline-building-playbook.md` (LinkedIn section now points here)
- **Content review:** `skills/ctq-social/` (Sankofa Council on social drafts before publish)

---

## Decision Gates

**May 14 (Day 14):** First Sankofa Council review of the motion. Adjustments allowed only after this date.
**May 30 (Day 30):** Hard gate. $3,500 SHIELD invoiced AND collected. If miss by >7 days, stop content + infra, cold outreach only.
**Jun 29 (Day 60):** $7,000 total invoiced. Adjust ICP / DM / posts if missed.

---

## Procrastination Tells (Self-Audit at End of Each Week)

If you spent more time this week on:

- Editing the LinkedIn profile after May 1 → procrastination
- Tweaking the DM template before May 14 → procrastination
- Designing a lead magnet → procrastination
- Building a Notion dashboard → procrastination
- Reading a new LinkedIn book / course / post → procrastination
- "Researching" prospects beyond the hook line → procrastination

If you spent time on:
- Sending DMs → real
- Replying to inbox → real
- Talking to prospects → real

Anything not on the second list is delay. Cash is king.

---

# Session Journal - 2026-04-30 (LAUNCH DAY)

This section captures every consequential decision made on launch day, with the reasoning. If you ever wonder "why does the headline say X?" or "why is the Featured section laid out this way?" - read here first.

## What shipped today

| Asset | Status | Where it lives |
|---|---|---|
| LinkedIn headline | LIVE | linkedin.com/in/boubacarbarry |
| LinkedIn About | LIVE | same |
| Featured #1: Catalyst Works link | LIVE | leads to catalystworks.consulting |
| Featured #2: AI Governance Assessment Call | LIVE | calendly.com/boubacarbarry/ai-governance-assessment-call |
| Featured #3: pre-existing post graphic | LIVE | "u know something wrong" - kept it, stronger than a generic tile |
| AI Governance Playbook (public PDF) | IN PROGRESS | will be Featured #4 once finalized |
| 50 leads | LIVE in Supabase + Notion CRM | IDs 1520-1569 |
| 50 personalized DMs ready to send | LIVE | workspace/linkedin-mvm/target_list.csv (dm_text col) and dms_to_send_2026-04-30.md |
| Calendly AI Governance Assessment Call | LIVE | 20 min, created via PAT |
| Calendly PAT (permanent fix) | LIVE | CALENDLY_PERSONAL_ACCESS_TOKEN in VPS .env |
| Daily 06:13 UTC cron | LIVE | pulls ~75 new leads/day, fills hooks, ingests to CRM. Targets 500 by Day 7 |
| 9 AM MT recurring CW Hour calendar block | LIVE | May 1 → Jun 29, Mon-Fri |
| 12 LinkedIn posts (M/W/F May 5-30) | IN PROGRESS | agentsHQ job 50675fa7 |
| Telegram morning nudge | NOT YET | next build |
| AI Governance book - Ideas DB entry | LIVE | https://app.notion.com/p/352bcf1a30298115b470f2f89615c227 |

## Headline - why it reads the way it does

**Final headline (162 chars):**
> Your AI risk is not in your AI strategy. It is in the many tools your team is already using that nobody wrote down. I find them. Author, AI Governance Playbook.

### Why not the original

Original was: "Most AI problems aren't AI problems. I find what's actually wrong and fix that first | Global HR Leader | AI Strategy & Diagnostics"

Three problems with the original:
1. **"Global HR Leader" + "AI Strategy & Diagnostics"** dilute the AI Governance flagship. Buyer cannot tell what we sell. Cuts the SHIELD-tier conversion path.
2. **"Fix that first"** over-promises. An assessment finds and recommends. It does not fix. Skeptical CPA partner reads "fix" and bounces.
3. **No proof anchor.** Original ended on services, not credibility.

### Why we chose the new one

Ran 8 options through CTQ + Sankofa. Final landed on the contrarian-frame version because:
- **"Your AI risk is not in your AI strategy"** - pure Boubacar contrast structure. Tells a buyer who has been worrying about "AI strategy" they have been worrying about the wrong thing.
- **"the many tools your team is already using that nobody wrote down"** - specific anomaly hook. Buyer self-recognizes in 2 seconds.
- **"I find them"** - smallest, truest claim. No fix-promise. No superhero pose. Operator-honest.
- **"Author, AI Governance Playbook"** - earned proof, not a self-claim.

### What we deliberately rejected

- **"Fractional AI Risk Officer"** as the lead title - category invention, buyer does not have the term in their vocabulary, paying a vocabulary tax. Lives in the About paragraph 3 instead.
- **"$3,500 fixed fee"** in the headline - hard rule from Boubacar: never put price in the headline. Filters out budget-having buyers who want to qualify by fit before money.
- **"Based in Utah, working nationwide"** - geographic filler, location field already covers it.
- **"SMBs"** - vendor language, not buyer language. Owner-operators do not call themselves SMBs.
- **"Fix it in 14 days"** - same over-promise problem as original. Cut.
- **"Most AI problems are not AI problems. I build better users of AI."** - voice anchor lives in About P3 verbatim. Headline duplicating it = wasted real estate. The headline must say something the About does not.

### Final edit Boubacar made

Replaced "four tools" with "many tools." Reason: "four" boxed us into a number we cannot defend at every firm size. Some firms have 4 tools, some have 30. "Many" scales. Keeps the specificity-of-claim energy without committing to a number that fails some prospects.

### When to revisit

- **Day 30 (May 30)** if the headline is producing under 50% of expected profile-view-to-DM-reply rate. Sankofa pass first.
- **Never before May 14**. Every edit before then is procrastination dressed as optimization.

## About - why it reads the way it does

**Final About (1,278 chars, well under the 2,600 LinkedIn cap):**

```
Your team is pasting client data into ChatGPT. Your CRM quietly turned on AI features. Nobody can tell you which vendors are training on your data.

That is the conversation worth having, and most firms your size are six months late to it.

I do not build AI tools. I build better users of AI. The risk in 2026 is not what AI can do. It is what your team is already doing with it that nobody has written down.

I work with owner-operator firms where the founder still runs the business. The kind of firm without a CISO, without a general counsel, without a dedicated compliance function. Two weeks in, you have a written diagnostic of where AI is being used, where the exposure lives, and a policy you can implement the day you get it. From there, some firms keep going. Most do.

Author, AI Governance Playbook (April 2026), in the Featured section. What I see most often inside firms like yours, and what to look at first.

Featured section also has a free 20-minute call. Different from the work above. We map the biggest AI risk surfaces in your stack so you can decide on your own whether a deeper conversation makes sense.
```

### Why this version

Ran 4 versions through CTQ + Sankofa. Final landed because:

1. **Hook lands on a scene** (P1 - three concrete moments). Buyer self-recognizes in 8 seconds.
2. **P2 names the urgency** without manufactured panic ("six months late" is honest, common, not exaggerated).
3. **P3 keeps the voice anchor** ("I do not build AI tools. I build better users of AI.") right where it lands hardest, immediately after the recognition.
4. **P4 names the buyer profile and the deliverable** without naming a price or the SHIELD acronym. "Two weeks in, you have a written diagnostic..." is operator-honest.
5. **P5 is the social proof** ("Most do") that we earned without claiming a number.
6. **P6 + P7 are the offers** - Playbook in Featured, Calendly call in Featured. Each pointed at, not duplicated.

### What we deliberately cut

- **Pricing ($3,500, $8,500, retainer)** - Boubacar rule, no prices in About. Pricing comes up on the call when the room can be read. Public price filters too aggressively at SHIELD-tier register.
- **SHIELD methodology details** - internal IP, never goes public. The Playbook public PDF strips this entirely.
- **"Governance Sprint" / "Fractional AI Risk Officer" as named offers** - internal labels do not earn their place over plain English. "Some firms keep going. Most do." replaces the offer ladder.
- **15-year career history paragraph** - career biography hurts conversion on a sales-page About. Belongs in Experience section.
- **"What I believe" manifesto bullets** - three abstract beliefs on a sales page reads as drift. Beliefs go in posts, not bios.
- **"Decision architecture" and similar consulting jargon** - style guide ban.

### What we kept against early instinct

- **"I do not build AI tools. I build better users of AI."** - initial Sankofa Contrarian voice flagged this as conflicting with the risk-officer offer. Resolution: kept the line because it IS the voice anchor and bridged it to the offer with the next sentence ("The risk in 2026 is not what AI can do..."). Compose, do not choose.

### When to revisit

- **Day 30 (May 30)** if profile-view-to-Calendly-booking rate is below 5%. Sankofa pass first.
- **Never edit before May 14.** Tweaking copy before signal arrives is procrastination.

## Featured section - current state

**Featured #1: Catalyst Works link**
- Type: External link to catalystworks.consulting
- Description: "AI governance and operations consulting for owner-operator firms."
- Job: catch readers who want to learn about the firm in general (not the specific 20-min call).

**Featured #2: AI Governance Assessment Call (Calendly)**
- Type: External link to calendly.com/boubacarbarry/ai-governance-assessment-call
- Description: "We map the biggest AI risk surfaces in your stack. No pitch. You decide on your own whether a deeper conversation makes sense."
- Edit Boubacar made: removed "three" (was "three biggest AI risk surfaces"). Reason: "biggest" scales, "three" boxes us in.
- Job: primary conversion path. The CTA the About points to.

**Featured #3: existing pinned post - "u know something wrong / Catalyst Works"**
- Type: Post (pre-existing)
- Job: Catalyst Works brand image, complementary to #1 (which is a link). Visual variety. Strong first impression for design-conscious viewers.
- Decision: KEPT this. Originally planned to replace with the Playbook PDF but the post is stronger than a static tile. Playbook PDF will become Featured #4 when ready.

**Featured #4 (pending): AI Governance Playbook PDF**
- Title: "AI Governance Playbook for Owner-Operator Firms (April 2026)"
- Description: "What I see most often inside firms like yours, and what to look at first."
- Job: deepest credibility signal. The Author claim in the headline is unverifiable until this PDF is in Featured.
- Status: v3 written (5,000 words, ~12 pages). Boubacar called for a tighter 5-10 page version. v4 in progress.

## Lead generation - what we built today

Total leads: 50 in CSV with personalized DMs, ingested to Supabase (IDs 1520-1569) and Notion CRM Leads DB.

Pipeline architecture:

```
Daily 06:13 UTC cron on VPS
  └─ skills.linkedin_mvm.serper_pull
       ├─ runs 10 Google site:linkedin.com/in/ queries (rotating from a 75-query bank)
       ├─ pacing: 2-second jitter between queries, 1-day spread
       └─ writes new rows to workspace/linkedin-mvm/target_list.csv (deduped)
  └─ skills.linkedin_mvm.fill_hooks
       ├─ for each row with empty `hook` column
       ├─ calls Firecrawl (currently 402 - credits exhausted) OR falls back to metadata-only
       ├─ generates hook via OpenRouter (claude-haiku-4.5, $0.0001/hook)
       └─ writes hook back to CSV

When you run generate_dms (already inside orc-crewai container):
  └─ reads CSV
  └─ renders DM via templates.linkedin.dm_v1.render_dm
  └─ ingests to Supabase + auto-syncs to Notion CRM
  └─ writes dm_text column back to CSV
  └─ writes dms_to_send_YYYY-MM-DD.md (paste-ready)
```

Volume forecast: 75 queries × 10 results × ~70% unique = ~525 unique URLs by Day 7. Hits the 500 target Boubacar set.

## DM mechanic - Path A locked in

Free LinkedIn does not allow DMs to non-connections. The "Message" button is grayed out unless 1st-degree.

The motion uses **Path A:** connection request with note (Day 1) → full DM after accept (Day they accept) → one bump (Day 7-10 if no reply, then move on).

CSV now carries TWO message columns per prospect:

- `connection_note` - 300-char cap. Paste into LinkedIn connection request on Day 1.
- `dm_text` - full DM. Paste after they accept.

Function lives at `templates/linkedin/dm_v1.py:render_connection_note()`. Auto-trims hook to fit the cap. Verified: all 50 current rows have `connection_note` ≤ 296 chars.

Daily volume: 5 connection requests + 5 DMs to fresh accepters + 5 bumps to non-repliers from 7 days ago. Total LinkedIn time inside CW Hour: 15-20 min.

**Realistic funnel from 50 connection requests:** 40% accept → 20 connections → 100% receive DM → 25% reply → 5 conversations → 40% book the call → 2 calls → 50% qualify for SHIELD → 1 SHIELD-qualified lead.

100 connection requests/month = ~2 SHIELD-qualified leads/month. Day 30 needs 1.

**Day 30 decision gate:**
- On track for $3,500 → keep Path A, free LinkedIn is enough.
- Behind → upgrade to Sales Nav, add InMail to non-accepters, run Path C.

**Hard rules for first 14 days:**
- 5 connection requests/day max. LinkedIn ramps trust slowly.
- Never click Connect without the note. Acceptance drops 60%.
- Never send connection note AND InMail to the same person. One channel per prospect.
- Mass-accepting random new connections during this period dilutes the algorithm signal. Only accept ICP.

Reference memory: `reference_linkedin_dm_mechanics.md`.

---

## Critical infra moves logged

1. **Calendly PAT method established** (canonical). The MCP path expires; the PAT does not. Memory: `feedback_calendly_pat_method.md`. Token in VPS .env as CALENDLY_PERSONAL_ACCESS_TOKEN.
2. **Division-of-labor rule formalized.** Most non-code work passes to agentsHQ via the orchestrator. Claude Code + Codex own code changes only. Memory: `feedback_division_of_labor.md`.
3. **Friction-audit rule formalized.** Before proposing manual user action, audit existing tools (Apollo, Hunter, Serper, Firecrawl, autocli, gws, MCPs, agentsHQ crews). Manual is fallback, not proposal. Memory: `feedback_friction_audit_before_proposing_manual.md`.
4. **Apollo free-tier dead-end documented.** The /mixed_people/api_search endpoint returns obfuscated rows without LinkedIn URLs unless credits are spent. Pivoted to Serper. Saved to skill SKILL.md.
5. **Firecrawl credits exhausted.** Hook fill falls back to metadata-only generation via OpenRouter. Quality verified strong. If credits restore, Firecrawl scrape resumes automatically.

## What did NOT ship today (and why)

| Not shipped | Why | When |
|---|---|---|
| Playbook PDF in Featured #4 | v3 was 12 pages, Boubacar called for 5-10 of pure signal | Today, after collapse |
| 12 LinkedIn posts in Blotato | agentsHQ job 50675fa7 still running / pending Telegram delivery | Today or tomorrow |
| Telegram morning nudge skill | Lower priority than getting first 5 DMs sent today | Tomorrow |
| MEMORY.md index update | Last task of the session, after Playbook lands | End of session |

## Decision tree for "should I change this?"

If you want to change the headline:
1. Re-read this journal (you wrote it for this exact reason).
2. Has signal arrived? (Day 14 minimum.) If no, reject the urge.
3. If yes, run /sankofa on the proposed change before editing.

If you want to change the About:
1. Same flow.
2. The voice anchor ("I do not build AI tools. I build better users of AI.") is non-negotiable. Anything else can be tested.

If you want to change Featured:
1. The Calendly link stays - it is the primary conversion path.
2. Anything else can be tested if signal supports it.

If you want to change the DM:
1. The single-template rule holds for 14 days minimum.
2. After May 14, A/B test only the hook line, never the offer.

---
- Replying to inbox → real
- Talking to prospects → real

Anything not on the second list is delay. Cash is king.
