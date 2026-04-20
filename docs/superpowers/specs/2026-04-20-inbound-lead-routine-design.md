# Inbound Lead Routine: Design Spec

**Date:** 2026-04-20
**Owner:** Boubacar Barry
**Source task:** Notion Idea `345bcf1a-3029-81e1-9eb2-d5631927aa6b` ("Inbound Lead Routine (Claude Code Routines + Webhook)")
**Status:** Design approved, ready for plan

## Goal

Build a webhook-triggered routine that fires when a prospect books a Calendly discovery call (or submits a Formspree form as secondary path). The routine researches the lead, drafts a personalized welcome email in Boubacar's voice, logs the lead into the Forge 2.0 Consulting Pipeline Notion database, and pings Telegram with links to the draft and row.

## Non-goals

- Auto-sending the welcome email (draft only, never send)
- Replacing n8n as the plumbing layer
- Scoring or prioritizing leads (the lens_entry_point is a note, not a router)
- Building the n8n workflow in code (Boubacar builds in n8n UI)
- Pre-call brief generation (the research brief IS the brief)
- Follow-up sequences after no-show

## Principles applied

- **Fit what we have, no MUDA.** Read the Pipeline DB schema live, map to existing fields. Do not invent parallel schemas.
- **n8n = plumbing. Routine = judgment.** Deterministic writes stay in n8n. Research and drafting stay in the routine.
- **Skill + crew always.** Package as skill under `skills/inbound_lead/`; crew in orchestrator calls skill functions.
- **Fail-soft.** Partial enrichment is better than blocking the deterministic Notion row n8n already wrote.
- **No framework names in client-facing copy.** 8 lenses are internal diagnostic tools only.

## Architecture

```
Calendly invitee.created
        │
        ▼
n8n webhook workflow: "CW | Calendly → agentsHQ Inbound"
        │
        ├──▶ Branch 1: deterministic Notion Pipeline row write
        │       (name, email, company, meeting_time, source=Calendly, status=New)
        │
        └──▶ Branch 2: POST /run-async with task_type=inbound_lead
                │
                ▼
           orchestrator routes to skills/inbound_lead
                │
                ├─ Idempotency check (Postgres inbound_lead_enrichment)
                │     └─ email already enriched → rebook path (update meeting time, Telegram ping, exit)
                │
                ├─ CrewAI crew (2 agents)
                │     ├─ Researcher (Firecrawl scrape + Serper search) → ResearchBrief
                │     └─ Voice drafter (boub_ai_voice polish) → DraftedEmail
                │
                ├─ Logger (deterministic, post-crew)
                │     ├─ Update Notion row with research + draft URL
                │     ├─ Create Gmail draft labeled "Catalyst Works/Inbound"
                │     └─ Mark enriched in Postgres
                │
                └─ Telegram ping with Notion + Gmail draft links
```

Formspree (secondary path) routes through the same n8n workflow with `source=formspree`. Same routine, different source field.

## Components

### Skill: `skills/inbound_lead/`

```
SKILL.md          # when to invoke, inputs, outputs, voice rules
__init__.py
inbound_tool.py   # BaseTool wrappers registered in orchestrator/tools.py
researcher.py     # research() function
drafter.py        # draft_email() function
logger.py         # log_to_notion_and_gmail()
idempotency.py    # has_been_enriched() / mark_enriched()
schema.py         # Pydantic models
```

### Crew integration (orchestrator)

- `agents.py`: `inbound_researcher`, `inbound_drafter`
- `crews.py`: `build_inbound_lead_crew(payload)`
- `router.py`: explicit task_type `inbound_lead` (webhook sets it; no keyword routing)
- `tools.py`: `InboundResearchTool`, `InboundDraftTool`, bundled as `INBOUND_TOOLS`
- `routines/inbound_lead_runner.py`: entry point called by `/run-async` dispatch

### Data contracts

```python
class InboundPayload(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str]
    booking_id: str
    meeting_time: Optional[datetime]
    source: Literal["calendly", "formspree"]
    notion_row_id: Optional[str]
    raw_company_url: Optional[str]

class ResearchBrief(BaseModel):
    company_domain: Optional[str]
    what_they_do: str
    industry_signals: list[str]              # up to 5
    likely_friction: list[str]               # up to 3
    conversation_hooks: list[str]            # 2-3
    lens_entry_point: str                    # INTERNAL ONLY
    sources: list[str]
    research_confidence: Literal["high", "medium", "low", "none"]
    notes: Optional[str]

class DraftedEmail(BaseModel):
    subject: str                             # ≤60 chars
    body_markdown: str                       # ≤150 words
    tone_note: Optional[str]

class LogResult(BaseModel):
    notion_row_url: str
    gmail_draft_id: str
    gmail_draft_url: str
    fields_written: list[str]
    fields_skipped: list[str]
    warnings: list[str]

class InboundRoutineResult(BaseModel):
    status: Literal["enriched", "rebook_update", "partial", "failed"]
    payload: InboundPayload
    brief: Optional[ResearchBrief]
    email: Optional[DraftedEmail]
    log: Optional[LogResult]
    telegram_sent: bool
    error: Optional[str]
```

### Notion field mapping (live-read)

At first call of the logger (or module import), read the Pipeline DB schema once, cache a `FIELD_MAP` mapping logical concepts to actual property names. Concepts without matching fields go to `LogResult.fields_skipped` and are flagged in Telegram rather than crashing. The Pipeline DB ID is `249bcf1a302980f58d84cbbf4fa4dbdb` (already in `.env` as `FORGE_PIPELINE_DB`; aliased to `NOTION_FORGE_PIPELINE_DB_ID` for naming consistency).

### Idempotency table

```sql
CREATE TABLE IF NOT EXISTS inbound_lead_enrichment (
  email           TEXT PRIMARY KEY,
  first_booking   TEXT NOT NULL,
  enriched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_booking   TEXT NOT NULL,
  last_meeting_at TIMESTAMPTZ,
  status          TEXT NOT NULL
);
```

`INSERT ... ON CONFLICT (email) DO UPDATE` triggers the rebook path (update Notion meeting time + Telegram ping, skip research/draft).

## Voice and guardrails

Voice target: an analyst who did quick homework. Not a sales bot. Low friction.

Hard guardrails enforced in drafter prompt + post-draft linter:

1. No framework names (Theory of Constraints, TOC, Jobs to Be Done, JTBD, Lean, Behavioral Economics, Systems Thinking, Design Thinking, OD). Regex-reject, regenerate once, ship partial if second draft fails.
2. No em dashes. Ever. No double hyphens.
3. No sales-bot phrases: "circle back", "touch base", "just wanted to", "reach out", "synergy", "leverage your", "unlock", "transform your business", "game-changer", "thought leadership".
4. Body ≤150 words. Subject ≤60 chars.
5. No attachments, no external links, no calendar links (already booked).
6. No mention of the research process. Sound like someone who knows, not like someone who looked.
7. End with one specific question tied to one friction hypothesis.

Email structure (4 lines):

1. One line acknowledging the booking (not generic "thanks").
2. One line showing context (phrased as knowledge, not research).
3. One line naming a friction to explore (plain English, no lens names).
4. One specific question.

### Researcher prompt (outline)

Analyst role. Resolve company domain from email or URL. Firecrawl homepage, /about, /services, with fallbacks. Serper for "{company} news" and "{name} LinkedIn" (3 results each). Synthesize to `ResearchBrief` JSON. Plain English in all fields. `lens_entry_point` is the one field allowed to name a lens (for Boubacar's internal use). If no web presence, set `confidence=none` and return minimal brief.

### Drafter prompt (outline)

Write as Boubacar. ≤150 words body, ≤60 chars subject. Obey 7 guardrails above. Pass through `boub_ai_voice` polish. Return `DraftedEmail`.

### Linter

Regex-checks body and subject against guardrails. On fail: regenerate once with errors appended to prompt. On second fail: ship with `status=partial` and include errors in Telegram warnings.

### Telegram ping formats

**Enrichment success:**

```
🎯 New inbound lead

Name:     {name}
Company:  {company}
Booked:   {meeting_time in MT}
Source:   {source}

Research:  {confidence}. {one-line what_they_do}
Lens:     {lens_entry_point}   [INTERNAL]

📝 Notion:  {notion_row_url}
✉️  Gmail:   {gmail_draft_url}

{warnings if any}
```

**Rebook:**

```
🔁 Rebook

{name} at {company} moved to {new_meeting_time}.
Previous: {old_meeting_time}

📝 Notion:  {notion_row_url}
```

## Failure modes

- Researcher fails → drafter runs with empty brief, writes minimal "thanks for booking" note, Telegram flags "research incomplete".
- Drafter fails → skip Gmail draft, Notion row updated with brief only, Telegram flags "draft skipped".
- Logger Notion write fails → Gmail draft kept, Telegram sends raw research + email text inline.
- Logger Gmail fails → Notion has email text in fallback field, Telegram sends gmail-ready text inline.
- Idempotency table missing → fall back to "always enrich" with warning log (non-fatal).

## Testing

### Unit tests (`tests/test_inbound_lead.py`)

1. `test_idempotency_first_booking`
2. `test_idempotency_rebook_same_email`
3. `test_idempotency_different_email_same_company`
4. `test_researcher_resolves_domain_from_email`
5. `test_researcher_handles_404_on_homepage`
6. `test_researcher_handles_no_web_presence`
7. `test_linter_blocks_framework_names`
8. `test_linter_blocks_em_dash`
9. `test_linter_blocks_sales_phrase`
10. `test_linter_passes_clean_draft`
11. `test_drafter_regenerates_on_lint_fail`
12. `test_drafter_ships_partial_after_two_lint_fails`
13. `test_logger_maps_fields_to_live_schema`
14. `test_logger_reports_missing_fields`
15. `test_routine_fail_soft_research_fails`
16. `test_routine_fail_soft_logger_fails`

### Integration tests

17. `test_e2e_real_calendly_payload`: fake payload to `/run-async`, verify Notion row, Gmail draft, Telegram ping.
18. `test_e2e_rebook_path`: second payload for same email, verify meeting time updated, no duplicate draft.

## Rollout

**Phase 0: scaffolding**
1. Save point: `nsync` tag `pre-inbound-lead-routine`
2. Read Pipeline DB schema, document actual field names in an addendum
3. Pydantic models, Postgres idempotency table, skill scaffolding
4. All unit tests written (TDD red)
5. Implement researcher, drafter, linter, logger → tests green

**Phase 1: local integration**
6. Synthetic payload through local orchestrator → end-to-end verified

**Phase 2: VPS deploy**
7. SCP `.env` additions, git push, `docker compose build orchestrator`, force-recreate
8. Synthetic payload to production `/run-async`

**Phase 3: n8n wiring**
9. Boubacar builds "CW | Calendly → agentsHQ Inbound" in n8n UI
10. Activate Calendly webhook, publish workflow

**Phase 4: canary**
11. First real booking → watch logs live. Good → leave running. Bad → disable Calendly webhook, diagnose.

### Verification before "done"

Per `feedback_verification_before_deploy.md`: show actual Notion row, actual Gmail draft body, actual Telegram message, actual Postgres row. No "I think it worked."

## Out of scope

- Formspree webhook wiring (already exists; routine just consumes whatever n8n passes)
- n8n workflow JSON (Boubacar builds in UI)
- Auto-sending emails (never)
- Follow-up sequences
- Lens-based routing
- Pre-call brief generation
- Weekly digest (logged as future Phase 5)

## Dependencies

- Firecrawl scrape tool (live in `orchestrator/firecrawl_tools.py`)
- Serper search tool (live in `skills/serper_skill/`)
- `boub_ai_voice` agent (live)
- NotionClient (live in `skills/notion_skill/` or `skills/forge_cli/`)
- Gmail draft creation via GWS CLI on VPS
- Postgres (existing, for idempotency table)
- `.env` updates: no new secrets needed; optionally alias `NOTION_FORGE_PIPELINE_DB_ID=$FORGE_PIPELINE_DB`

## Open items for writing-plans phase

- Confirm actual NotionClient method names for schema-read and row-write
- Confirm GWS CLI command for creating Gmail draft with label
- Confirm whether `orchestrator/app.py` or `orchestrator/orchestrator.py` is the live FastAPI app (backlog mentions both; likely one is legacy)
- Decide whether to place the FastAPI dispatch entry in `handlers.py` or `orchestrator.py`
