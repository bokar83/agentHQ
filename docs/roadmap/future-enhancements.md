# agentsHQ: Future Enhancements Backlog

This file tracks enhancements that are architecturally sound but not yet prioritized.
Add here instead of letting ideas get lost. Review at the start of each planning session.

---

## thepopebot Integration: Phase 5: Bidirectional Conversation Sync

**What it is:**
Full bidirectional sync between thepopebot's browser chat history (SQLite) and the agentsHQ
orchestrator's PostgreSQL session memory. Today (after Phase 1-4), browser sessions and Telegram
sessions share a `session_key` namespace but write to separate databases.

**Why it matters:**

- Start a task from Telegram, pick it up in the browser with full context
- Start a task in the browser, receive a Telegram follow-up that knows what happened
- Single unified conversation thread across all access methods

**Options when you're ready to build:**

1. **One-direction bridge (easy, 1 day):** Browser sessions POST a summary to `/run` with the
   same `session_key` as the Telegram session after completion. Orchestrator memory accumulates
   context. No database sync required.
2. **Shared session store (medium, 3-5 days):** thepopebot writes to PostgreSQL instead of SQLite
   by swapping its `DATABASE_PATH` for a Postgres-compatible ORM adapter. Both Telegram and
   browser queries read from the same store.
3. **Sync daemon (heavy, 1 week+):** A background process reconciles SQLite and PostgreSQL on
   an interval. Most resilient but most complex. Only justified if thepopebot's SQLite must stay
   as-is (e.g., upstream package constraints).

**Recommendation when ready:** Start with option 1 (minimal risk, immediate value), evaluate
whether option 2 is worth it after 30 days of real usage.

**Dependencies:** thepopebot Phase 1-3 must be live and stable first.

---

## Memory Architecture: Cross-Agent Shared Memory

See: `docs/memory/MEMORY.md` ("Agent Memory Architecture" entry)

Must build before system scales past ~20 task types. Currently per-session only.

---

## WhatsApp Bridge (waha)

Commented out in `docker-compose.yml`. Wire up when WhatsApp access is a real need.
Config is already written. Just uncomment and test.

---

## Metaclaw: Reinforcement Learning Phase

Currently running in `skills_only` mode. RL phase (adaptive skill weighting based on outcomes)
is the next evolution. No timeline set.

---

## Antigravity Permission & Environment Alignment

**What it is:**
Updating all agent instructions and system configurations to align with the new unified
permission model (Allow/Deny/Ask) and path constraints.

**Why it matters:**

- **Literal Absolute Paths:** Antigravity now requires absolute paths (no `~` or globs)
  for file operations. agentsHQ currently uses relative paths in many places.
- **Autonomy via Allowlist:** Pre-populating the Antigravity "Allow" list with core
  prefixes (`command(npm)`, `command(git)`, `read_file(d:/Ai_Sandbox/agentsHQ/)`)
  is necessary to maintain our "Output-first" principle without constant manual prompts.
- **Strict Mode Awareness:** Managing the tradeoffs between security (Strict Mode)
  and speed in our autonomous loops.

**Tasks when ready:**

1. Update `AGENT_INSTRUCTIONS.md` with "Absolute Path First" rule.
2. Provide a "Setup Guide" artifact for user permission configuration.
3. Review `orchestrator/tools.py` for relative path resolution bugs.

---

## Inbound Lead Routine (Claude Code Routines + Webhook)

**What it is:**
A webhook-triggered Claude Code Routine that fires when a prospect submits the discovery
intake form. The Routine researches the lead's business, drafts a personalized welcome
email in Boubacar's voice, and logs details to the Notion Consulting Pipeline.

**Why it matters:**

- Immediate response to hot leads with high-context research.
- Automates the CRM logging and initial outreach drafting phase.
- Maintains brand voice consistency without manual intervention.

**Architecture & Implementation Notes:**

- **Trigger:** API webhook (not cron).
- **Memory:** Stateless by design. Output written to Notion/PostgreSQL.
- **Connectors:** Notion, Gmail (draft mode only).
- **n8n Role:** Plumbing and routing. Routine role: judgment and drafting.
- **Dependencies:** After first revenue / first inbound lead received.

---

## Media & Video Production: kie.ai Integration

**What it is:**
Integration of **kie.ai** as the primary engine for image and video generation. Similar to
OpenRouter, kie.ai provides a unified API to access multiple state-of-the-art media
creation tools and models.

**Why it matters:**

- **Consolidated API:** Reduces the need to maintain separate integrations for Midjourney, Runway, Pika, etc.
- **Flexibility:** Allows the system to swap underlying models for the best output quality without changing code.
- **Workflow Speed:** Simplifies the pipeline for HyperFrames and social content generation.

**Tasks when ready:**

- [ ] Add `KIE_AI_API_KEY` to the `.env` file.
- [ ] Implement a `kie_media` skill that wraps the API for both image and video prompts.
- [ ] Wire the skill into the `app_builder` and `hyperframes` workflows.

---

## Local Business Brain: Signal Works Moat

**Source:** YC RFS S26 strategy session 2026-04-28. Full analysis: `docs/strategy/yc-rfs-s26-analysis.md`

**What it is:**
The AI Visibility Report delivered to each Signal Works client is the customer-facing output of
an underlying Local Business Brain being built for free as a byproduct of delivering the service.
Every monthly run indexes that client's reviews, content performance, competitor signals, AI search
rankings, and schema health. Over time this becomes a proprietary longitudinal dataset no
competitor can replicate.

**Why it matters:**
After 10 clients and 6 months, Signal Works has the best dataset of local SMB AI visibility
dynamics in the Wasatch Front. That dataset feeds better benchmarks, better reporting, and
eventually a differentiated "AI Visibility Score" that no one else can offer because no one
else has the history.

**What to do now:**
Nothing to build. The data is collected as a byproduct of delivering the service. The only
action is to name it internally ("Local Business Brain") and lock the data schema before
client #1 onboards so it can be aggregated across clients later.

**Gate:** Before first client onboards. Schema decision only. No build.

---

## "We Are Your AI Department": Unified SKU

**Source:** YC RFS S26 strategy session 2026-04-28.

**What it is:**
A single combined offer: Catalyst Works diagnostic + Signal Works AI presence + monthly
operations report at $997/month. One pitch. One price. Removes decision complexity for
buyers who want the full picture but do not know which brand to engage first.

**Why it matters:**
CW and Signal Works are currently separate brands with separate offers. Most SMB owner-operators
who need both will buy one and never discover the other. The unified SKU captures full wallet
share in one transaction and eliminates the cross-sell problem.

**What to build:**
One offer page (Signal Works or CW site). A pricing decision ($997 or $1,497?). Zero
infrastructure work. agentsHQ already delivers all three components.

**Gate:** R1 + R3 in harvest.md must both close first. Need proof both brands convert
independently before bundling.

---

## Client Portal: Atlas Dashboard White-Labeled Per Client

**Source:** YC RFS S26 strategy session 2026-04-28.

**What it is:**
A permission gate on the existing Atlas dashboard showing each Signal Works client their own
AI presence metrics, content performance, and task queue. Not a new build: a slug-based
data filter on the existing UI. One afternoon of work per client once the pattern is established.

**Why it matters:**
Converts Signal Works from a black-box monthly service into a transparent platform. Creates
stickiness. Justifies adding $97/month as a "platform access" tier.

**Gate:** Do not build until one client explicitly asks for more visibility into their data.
Test with a weekly automated email report first. If clients engage with the report, portal
demand will emerge on its own.

---

## Newsletter as Market Intelligence Infrastructure

**Source:** YC RFS S26 strategy session 2026-04-28.

**What it is:**
The beehiiv newsletter reframed from content marketing to market intelligence. Every issue is
structured around a signal observed in the market (a question, a fear, a tool people are talking
about) rather than a topic Boubacar wants to cover. Over 12 months this becomes the best dataset
of SMB AI adoption psychology in the Wasatch Front.

**Why it matters:**
The newsletter is a Company Brain for the market. Insights feed the Catalyst Works diagnostic --
Boubacar knows what the market is ready to hear before walking into a discovery call. That is a
structural advantage no generalist consultant has.

**What changes:**
Editorial calendar framing only. Reader-pull not author-push. One 1-hour rewrite of the
newsletter crew prompt.

**Gate:** When beehiiv REST API wiring is live (target 2026-05-03). Wire the intelligence
framing into the newsletter crew prompt at that point.

---

Last updated: 2026-04-28
