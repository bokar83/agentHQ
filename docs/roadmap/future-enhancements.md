# agentsHQ — Future Enhancements Backlog

This file tracks enhancements that are architecturally sound but not yet prioritized.
Add here instead of letting ideas get lost. Review at the start of each planning session.

---

## thepopebot Integration — Phase 5: Bidirectional Conversation Sync

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

See: `docs/memory/MEMORY.md` → "Agent Memory Architecture" entry

Must build before system scales past ~20 task types. Currently per-session only.

---

## WhatsApp Bridge (waha)

Commented out in `docker-compose.yml`. Wire up when WhatsApp access is a real need.
Config is already written -- just uncomment and test.

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
- **Consolidated API:** Reduces the need to maintain separate integrations for Midjourney, 
  Runway, Pika, etc.
- **Flexibility:** Allows the system to swap underlying models for the best output 
  quality without changing code.
- **Workflow Speed:** Simplifies the pipeline for HyperFrames and social content generation.

**Tasks/Reminders:**
- [ ] Add `KIE_AI_API_KEY` to the `.env` file.
- [ ] Implement a `kie_media` skill that wraps the API for both image and video prompts.
- [ ] Wire the skill into the `app_builder` and `hyperframes` workflows.

---

_Last updated: 2026-04-17_


