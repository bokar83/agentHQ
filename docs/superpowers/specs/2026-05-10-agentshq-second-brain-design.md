# agentsHQ Second Brain + Shared Agent Memory — Design Spec

**Date:** 2026-05-10
**Status:** Approved for implementation
**Owner:** Boubacar Barry
**Reviewed by:** Karpathy audit (HOLD resolved), Sankofa Council, Code Architect

---

## Problem Statement

agentsHQ accumulates knowledge across 3 active pipelines (SW, CW, Studio), 5 roadmap codenames, 34 crew types, 25 Telegram commands, and 160+ memory files — all trapped on one Windows laptop or scattered across Notion, Drive, Gmail, and Google Keep. Every agent starts cold. Every session loses context. Boubacar cannot query what he knows. No tool except Claude Code can write to memory, and even that only works on one machine.

**Two goals:**

1. **Shared Agent Memory:** Every agent — Claude Code, Codex, VPS orchestrator crews, future tools — reads and writes the same memory. No cold starts. Lessons, decisions, project state, and hard rules persist across sessions and tools.

2. **Second Brain:** Boubacar can query everything he knows — SW leads, CW clients, Studio state, ideas, research, Drive files, Notion pages — from Telegram or Webchat using natural language or structured filters.

---

## Architecture

### Three Layers (mapping Cyril's vault to agentsHQ stack)

| Cyril (Obsidian) | agentsHQ |
|---|---|
| Markdown vault | VPS Postgres `memory` table |
| Filesystem MCP | Orchestrator HTTP POST `/api/memory` |
| N8N workflows | VPS cron crews (already running) |
| Obsidian UI | Telegram `/query` + Webchat (Phase 2) |

### Storage: One Table

Single `memory` table in VPS Postgres. No second table until forced by real data (>50k rows or query latency regression).

```sql
CREATE TABLE memory (
    id              SERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    -- 'claude-code' | 'telegram' | 'notion' | 'drive' | 'gmail' | 'orchestrator' | 'codex'
    category        TEXT NOT NULL CHECK (category IN (
                        'agent_lesson', 'project_state', 'lead_record',
                        'client_record', 'idea', 'hard_rule',
                        'asset', 'session_log')),
    title           TEXT,
    content         TEXT NOT NULL,
    tags            TEXT[],
    entity_ref      TEXT,
    -- structured: 'sw:elevate-roofing' | 'cw:acme' | 'project:atlas' | 'rule:content'
    external_id     TEXT,
    -- Notion page ID, Drive file ID, Gmail message ID — dedup key
    agent_id        TEXT,
    -- which agent wrote this: 'tab-shutdown' | 'gate-agent' | 'griot' | 'codex' | etc.
    pipeline        TEXT,
    -- 'sw' | 'cw' | 'studio' | 'atlas' | 'compass' | 'echo' | 'general'
    relevance_boost FLOAT NOT NULL DEFAULT 1.0,
    -- agent_lesson=1.5, hard_rule=2.0, external_doc=0.8
    expires_at      TIMESTAMPTZ DEFAULT NULL,
    -- NULL = keep forever. Set for Gmail snapshots (90 days), transient notes
    content_tsv     TSVECTOR GENERATED ALWAYS AS (
                        to_tsvector('english',
                        coalesce(title, '') || ' ' || content)) STORED,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX memory_external_id_idx
    ON memory(source, external_id) WHERE external_id IS NOT NULL;
CREATE INDEX memory_tsv_idx ON memory USING GIN(content_tsv);
CREATE INDEX memory_category_idx ON memory(category);
CREATE INDEX memory_entity_idx ON memory(entity_ref);
CREATE INDEX memory_pipeline_idx ON memory(pipeline);
CREATE INDEX memory_expires_idx ON memory(expires_at) WHERE expires_at IS NOT NULL;

CREATE OR REPLACE FUNCTION memory_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER memory_updated_at_trigger
BEFORE UPDATE ON memory
FOR EACH ROW EXECUTE FUNCTION memory_updated_at();
```

### Write Contract: 8 Categories

Each category has a required structure enforced by a Pydantic model. Invalid category values fail at the Postgres CHECK constraint. Free-text dumps are rejected at the write path.

#### 1. `agent_lesson` — boost 1.5
What the system learned. Wrote by tab-shutdown, orchestrator crews, Codex.
```python
class AgentLesson(BaseModel):
    what_happened: str   # "Studio VFR bug caused Blotato rejections"
    outcome: str         # "FAILED" | "SUCCEEDED" | "PARTIAL"
    rule: str            # "Always encode CFR before uploading to Drive"
    pipeline: str        # "sw" | "cw" | "studio" | "atlas" | "general"
    cost_estimate: str   # "" | "$12 wasted" | "3 hrs lost"
```

#### 2. `project_state` — boost 1.0
Current state of a roadmap codename. Written by tab-shutdown and orchestrator.
```python
class ProjectState(BaseModel):
    codename: str        # "atlas" | "harvest" | "studio" | "compass" | "echo"
    milestone: str       # "M9d-A" | "M3.7.3" | "" if not milestone-specific
    status: str          # "on-track" | "blocked" | "shipped" | "paused"
    last_action: str     # "Deployed gate agent cron 2026-05-09"
    next_action: str     # "Wire Weekly Synthesis to session start"
    blockers: str        # "" if none
```

#### 3. `lead_record` — boost 1.0
Signal Works prospects. T1-T5 sequence state. Written by SW crews and Telegram.
```python
class LeadRecord(BaseModel):
    company: str         # "Elevate Roofing"
    contact: str         # "Rod"
    gmb_score: int       # 0-4 GMB qualification score
    sequence: str        # "T1" | "T2" | "T3" | "T4" | "T5"
    last_touch: str      # "Sent audit 2026-05-07"
    response: str        # "" | "No reply" | "Interested" | "Booked"
    audit_url: str       # "" | "https://geolisted.co/audits/elevate"
```
`entity_ref` = `sw:<company-slug>`, e.g. `sw:elevate-roofing`

#### 4. `client_record` — boost 1.0
Catalyst Works engagements. Different motion from SW. Written by CW crews and Telegram.
```python
class ClientRecord(BaseModel):
    company: str         # "Acme Corp"
    contact: str         # "Jane Smith"
    offer: str           # "Signal Session" | "SaaS Audit" | "custom"
    stage: str           # "prospect" | "signal-session" | "discovery" | "active" | "closed"
    last_touch: str      # "Discovery call 2026-05-01"
    mrr: str             # "" | "$2500/mo"
    notes: str
```
`entity_ref` = `cw:<company-slug>`

#### 5. `idea` — boost 0.9
Captured ideas. Maps to existing Ideas DB in Notion. Written via Telegram `/idea` or `/remember`.
```python
class Idea(BaseModel):
    title: str           # "Build roofing landing page for SW"
    context: str         # what triggered it
    pipeline: str        # "sw" | "cw" | "studio" | "atlas" | "personal"
    priority: str        # "now" | "soon" | "someday"
```

#### 6. `hard_rule` — boost 2.0
Highest boost. Agent-critical constraints Boubacar has stated explicitly.
Loaded at every session start before anything else.
```python
class HardRule(BaseModel):
    rule: str            # "Never say FGM — always 1stGen or 1stGen Money"
    reason: str          # "Boubacar's explicit brand naming rule"
    applies_to: str      # "all" | "content" | "outreach" | "code" | "deploy"
```

#### 7. `asset` — boost 0.8
Findable files and links. Drive docs, Notion pages, audit reports, sites.
```python
class Asset(BaseModel):
    title: str           # "Elevate Roofing Audit"
    asset_type: str      # "drive_doc" | "notion_page" | "video" | "report" | "site"
    url: str             # direct link
    pipeline: str        # "sw" | "cw" | "studio" | "general"
    notes: str           # "Canonical SW audit template — use for all prospects"
```

#### 8. `session_log` — boost 1.2
What happened in a Claude Code session. Written by tab-shutdown.
Feeds the weekly synthesis crew directly.
```python
class SessionLog(BaseModel):
    codename: str        # "atlas" | "harvest" | "studio" | etc.
    summary: str         # 2-3 sentences: what shipped, what changed, what's next
    date: str            # "2026-05-10"
```

---

## Write Paths

| Path | Trigger | Categories written | When |
|---|---|---|---|
| Telegram `/remember <text>` | User message | idea, agent_lesson | Immediate |
| Telegram `/note sw <company> <text>` | User message | lead_record update | Immediate |
| Tab-shutdown skill | Claude Code session end | agent_lesson (3-5), project_state (1), session_log (1) | Each session |
| Orchestrator crews | After each crew run | agent_lesson | Automatic |
| Nightly Notion sync | VPS cron 02:00 | asset, idea (from Ideas DB) | Nightly |
| Nightly Drive sync | VPS cron 02:15 | asset | Nightly — GATED (OAuth confirm first) |
| Nightly Gmail sync | VPS cron 02:30 | asset | Nightly — GATED (after Drive) |
| Hard rules seeding | One-time migration | hard_rule | Seed from MEMORY.md on launch |
| HTTP POST `/api/memory` | Any external tool | any | On demand |

**Deduplication:** `external_id` + `UNIQUE INDEX ON memory(source, external_id)` prevents nightly syncs from doubling rows. Use `ON CONFLICT (source, external_id) DO UPDATE SET content = EXCLUDED.content, updated_at = NOW()`.

**Existing system migration:** `agent_learnings` table in `memory.py` and Qdrant `agentshq_learnings` collection are deprecated on first successful week of the `memory` table. Migration rows get `source='agent_learnings_migration'`. The existing `/lessons` Telegram command is updated to query `memory` instead.

---

## Query Paths

### Natural Language (primary)
```
/query tell me about Elevate Roofing
/query what did we learn about Studio VFR this week
/query what are my hard rules for content
```
Flow: tsvector search (`plainto_tsquery`) → ORDER BY `ts_rank * relevance_boost DESC` → LIMIT 20 → LLM synthesis (Sonnet) → Telegram reply.

**Degradation:** If LLM call fails (402, timeout), return raw top-5 rows formatted. Never silence.

### Structured (secondary)
```
/query --filter pipeline=sw category=lead_record
/query --filter entity=sw:elevate-roofing
/query --filter category=hard_rule
```
Flow: SQL WHERE filter → formatted table → Telegram reply. No LLM needed.

### Session Start Injection
```sql
SELECT category, title, content
FROM memory
WHERE created_at > NOW() - INTERVAL '7 days'
  AND agent_id != current_session_id
  AND category IN ('hard_rule', 'agent_lesson', 'project_state')
ORDER BY relevance_boost DESC, created_at DESC
LIMIT 15;
```
Injected as system context before first message. `hard_rule` rows always included regardless of age.

### Morning Digest Integration
Prepend top 3 `agent_lesson` or `project_state` rows from last 24h to existing `griot_morning_tick`. Non-fatal — digest sends normally if memory table has 0 rows or query fails.

---

## Intelligence Layer (VPS Cron)

| Crew | Schedule | Reads | Writes | Already built? |
|---|---|---|---|---|
| Weekly Synthesis | Sunday 20:00 MT | `memory` last 7 days | `weekly_synthesis` Postgres table + Telegram | YES (M9d-A) |
| Memory Distillation | 1st of month 06:00 MT | `memory` all rows | `memory_distillation` Postgres table + Telegram | YES (M9d-B) |
| Content Connection Finder | Monday 07:00 MT | content board + `memory` | content board `Type=Connection Insight` | YES (M9d-C) |
| Daily Context (future) | Weekday 06:30 MT | `memory` last 48h | Telegram morning message | GATED (M9d trigger) |

**Update:** Weekly Synthesis and Memory Distillation crews (already built) will be updated to read from `memory` table instead of flat files once Step 2 is validated.

---

## Build Sequence (Gated)

### Step 0: Write Contract (prerequisite — no code ships without this)
- Pydantic models for all 8 categories in `orchestrator/memory_models.py`
- `memory` table created on VPS Postgres
- Postgres CHECK constraint on category column confirmed working (invalid insert fails)
- `hard_rule` rows seeded from MEMORY.md hard personal rules section

**Gate metric:** Invalid category INSERT raises constraint violation. At least 10 `hard_rule` rows exist after seeding.

### Step 1: Telegram write + query (MVP — proves end-to-end)
- `/remember <text>` → INSERT `category=idea`
- `/query <text>` → tsvector search → LLM synthesis → reply
- `/query --filter` → SQL filter → formatted reply
- Test: insert "Elevate Roofing, Rod, T1, audit sent 2026-05-07" → `/query tell me about Elevate Roofing` returns accurate result in <3s

**Gate metric:** Accurate /query result in <3s for a known manually-inserted entity.

### Step 2: Tab-shutdown write + session-start injection
- Tab-shutdown skill writes 3-5 `agent_lesson` + 1 `project_state` + 1 `session_log` at session end
- Session start reads last 7 days + all `hard_rule` rows → inject as context
- Deprecate flat-file memory write path for lessons (keep flat files as human-readable backup only)

**Gate metric:** Boubacar confirms next session started with at least 1 useful lesson from previous session that changed what the agent would do.

### Step 3: Nightly Notion sync
- Pull modified Notion pages (Ideas DB + Content Board + Task DB) → UPSERT `memory`
- Alert Telegram on failure

**Gate metric:** Row count increases after first run. Alert fires on simulated failure.

### Step 4: Drive sync (GATED)
**Prerequisite:** Drive read OAuth confirmed working from VPS container with documented refresh path.
- Pull modified Drive docs → UPSERT as `asset` rows with `expires_at = NULL`

### Step 5: Gmail sync (GATED)
**Prerequisite:** Step 4 proven.
- Pull starred/labeled Gmail → UPSERT as `asset` rows with `expires_at = NOW() + INTERVAL '90 days'`

### Step 6: Update Weekly Synthesis + Memory Distillation to read `memory` table
Replace flat-file reads in `weekly_synthesis_crew.py` and `memory_distillation_crew.py` with SQL queries against `memory` table.

### Step 7: Webchat query surface (separate milestone)
Same query API as Telegram, different UI. Not part of this spec.

---

## Success Criteria (per step)

| Step | Metric |
|---|---|
| 0 | Invalid INSERT fails. 10+ hard_rule rows exist. |
| 1 | /query returns accurate result <3s for known entity. |
| 2 | Session starts with 1+ useful prior-session lesson. Boubacar confirms. |
| 3 | Row count grows. Failure alert fires. |
| 4 | Drive OAuth confirmed. First Drive doc appears in memory. |
| 5 | Gmail rows appear. expires_at set correctly. TTL cron deletes expired rows. |
| 6 | Weekly synthesis references a lesson from memory table, not flat files. |

---

## What This Replaces / Deprecates

| Current system | Replaced by | Migration path |
|---|---|---|
| `agent_learnings` table + Qdrant collection | `memory` table, category=agent_lesson | Migrate existing rows, source='agent_learnings_migration' |
| Flat-file `~/.claude/projects/.../memory/*.md` | `memory` table + backup flat files | Flat files remain as human-readable backup only |
| `/lessons` Telegram command | Updated to query `memory` WHERE category=agent_lesson | In-place update |
| `NOTION_OUTPUTS_DB_ID` artifact sync | `memory` table, category=asset or session_log | Parallel initially, deprecate after Step 2 |

---

## Hard Constraints

- pgvector NOT installed on VPS Postgres 16 (Alpine). Do not add for v1. tsvector only.
- Drive OAuth from VPS container unconfirmed. Nightly Drive sync is HARD GATED.
- Weekly synthesis + memory distillation already ship to Postgres `weekly_synthesis` and `memory_distillation` tables. Do not replace those tables — they store synthesized output. `memory` stores raw inputs.
- `/api/memory` HTTP endpoint requires auth (bearer token from `.env`). Never expose unauthenticated.
- TTL cleanup cron: weekly, DELETE FROM memory WHERE expires_at < NOW(). Non-fatal.
- Webchat is a separate milestone. Not part of this spec.

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `orchestrator/memory_models.py` | CREATE | Pydantic models for all 8 categories |
| `orchestrator/memory_store.py` | CREATE | write() and query() functions against `memory` table |
| `orchestrator/tests/test_memory_models.py` | CREATE | Validation tests for all 8 models |
| `orchestrator/tests/test_memory_store.py` | CREATE | write/query tests with Postgres mock |
| `orchestrator/handlers_commands.py` | MODIFY | Add /remember, /query, /note commands |
| `skills/tab-shutdown/SKILL.md` | MODIFY | Add memory write step at session end |
| `orchestrator/weekly_synthesis_crew.py` | MODIFY (Step 6) | Read from memory table, not flat files |
| `orchestrator/memory_distillation_crew.py` | MODIFY (Step 6) | Read from memory table, not flat files |

---

## Spec Self-Review

**Placeholder scan:** None. All fields have examples. All gate metrics are behavioral.

**Internal consistency:** `entity_ref` format (`sw:elevate-roofing`, `cw:acme`, `project:atlas`) is consistent across LeadRecord, ClientRecord, and query filter examples.

**Scope:** Steps 0-3 are this milestone. Steps 4-7 are gated subsequent milestones. Webchat explicitly excluded.

**Ambiguity resolved:** tsvector only (pgvector not installed). One table (no split until forced). Hard rules always loaded at session start regardless of age. `/query` degrades gracefully if LLM fails.
