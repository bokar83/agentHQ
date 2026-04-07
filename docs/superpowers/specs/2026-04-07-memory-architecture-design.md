# agentsHQ Memory Architecture — Cross-Session Learning System
**Date:** 2026-04-07
**Status:** Approved for implementation
**Save point:** `cd19ba5` — revert here if build causes regressions

---

## Problem Statement

Every agentsHQ crew starts cold. No crew knows what any other crew has done. No crew improves from past runs. The code audit confirmed this as the #1 architectural gap.

**Goal:** Agents that self-improve over time. Priority order:
1. Task patterns — crews learn what approaches work for each task type
2. Voice/tone — copywriter learns Boubacar's style from approved outputs
3. Client context — agents remember what they know about specific people and companies

---

## Feedback Signal (Final)

| Signal | Meaning | Action |
|---|---|---|
| Explicit praise ("good job", "great", "well done") | Strong positive | Write positive lesson immediately |
| Silence for 30+ minutes after delivery | Neutral | No lesson written |
| Natural language critique ("this table wasn't done well", "I don't like how this was written") | Negative + reason | Extract negative lesson immediately |

The 30-minute window applies to silence only. Praise and critiques are written instantly.

---

## What Exists Today (Foundation)

| Component | Status | Notes |
|---|---|---|
| Qdrant container | Running | `orc-qdrant:6333`, collection `agentshq_memory` |
| PostgreSQL container | Running | `orc-postgres`, several tables |
| `memory.py` | Exists | `save_to_memory()`, `query_memory()`, conversation history, job queue, overflow |
| `QueryMemoryTool` | Exists | CrewAI tool wrapping `query_memory()` — but agents rarely call it |
| Embeddings via OpenRouter | Working | `text-embedding-3-small` |
| `EMBEDDER_CONFIG` in `crews.py` | Defined | Ready to use, OpenRouter-backed |
| `memory=False` on all crews | Broken | 20+ crews, all disabled |

### Missing Tables (confirmed via VPS audit in Phase 0)

Three tables are referenced in `memory.py` but may not exist in `setup-database.sql`:
- `agent_conversation_history` — session chat turns
- `job_queue` — async task tracking
- `pending_overflow` — chunked output delivery

**Phase 0 must run a VPS table inventory before any DDL is written.**

---

## Architecture — 3 Layers

```
Layer 1: Operational Memory    — PostgreSQL (conversation history, job queue, overflow)
Layer 2: Semantic Memory       — Qdrant (task embeddings, pattern recall)
Layer 3: Learning Memory (NEW) — Qdrant agentshq_learnings + Postgres agent_learnings
```

### Full Task Lifecycle

```
User sends task via Telegram
        |
Step 0: [GATED — complex crews only]
        Query agentshq_memory (past similar tasks, top 3)
        Query agentshq_learnings (positive + negative lessons for this task type, top 5)
        Inject as context block into enriched_task (capped at 6000 chars total)
        |
Crew executes with enriched context
        |
Result delivered to Telegram
        |
        +-- [Explicit praise within ~5 min] --> write positive lesson immediately (daemon thread)
        |
        +-- [Natural language critique]     --> extract negative lesson immediately (daemon thread)
        |
        +-- [Silence for 30+ min]           --> no lesson written
```

---

## Phase 0 — Pre-Migration VPS Inventory
**Before touching any code.**

Run:
```bash
docker exec orc-postgres psql -U postgres -c "\dt"
```

Cross-check every table name referenced in `memory.py` against what exists. Produce a migration script that uses `CREATE TABLE IF NOT EXISTS` for every table. Do not write DDL that assumes tables are absent — they may already exist from out-of-band creation.

---

## Phase 1 — Fix Broken Foundation (SQL Tables)

**File:** `setup-database.sql`

Add the following tables (all with `IF NOT EXISTS`):

### `agent_conversation_history`
```sql
CREATE TABLE IF NOT EXISTS agent_conversation_history (
  id          SERIAL PRIMARY KEY,
  session_id  TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content     TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_conv_history_session ON agent_conversation_history(session_id, created_at DESC);
```

### `job_queue`
```sql
CREATE TABLE IF NOT EXISTS job_queue (
  job_id         TEXT PRIMARY KEY,
  session_key    TEXT,
  from_number    TEXT,
  task           TEXT,
  status         TEXT DEFAULT 'pending',
  task_type      TEXT,
  result         TEXT,
  files_created  JSONB DEFAULT '[]',
  execution_time FLOAT,
  error          TEXT,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  updated_at     TIMESTAMPTZ DEFAULT NOW()
);
```

### `pending_overflow`
```sql
CREATE TABLE IF NOT EXISTS pending_overflow (
  session_id      TEXT PRIMARY KEY,
  full_output     TEXT,
  delivered_chars INTEGER DEFAULT 0,
  task_type       TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### `agent_learnings` (new)
```sql
CREATE TABLE IF NOT EXISTS agent_learnings (
  id               SERIAL PRIMARY KEY,
  task_type        TEXT NOT NULL,
  learning_type    TEXT NOT NULL CHECK (learning_type IN ('pattern', 'preference', 'lesson', 'negative')),
  content          TEXT NOT NULL,
  entities         JSONB DEFAULT '[]',
  confidence       FLOAT DEFAULT 0.8,
  use_count        INTEGER DEFAULT 0,
  last_used_at     TIMESTAMPTZ,
  lesson_status    TEXT DEFAULT 'auto' CHECK (lesson_status IN ('auto', 'reviewed', 'purged')),
  sanitized_export BOOLEAN DEFAULT FALSE,
  qdrant_point_id  TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_learnings_type ON agent_learnings(task_type, learning_type);
CREATE INDEX IF NOT EXISTS idx_learnings_status ON agent_learnings(lesson_status);
```

**Deployment:** `docker exec orc-postgres psql -U postgres` — run at a moment of zero active jobs (restart orchestrator container, apply DDL, restart container).

---

## Phase 2 — Pre-Task Memory Recall

**File:** `orchestrator.py` — `run_orchestrator()` function

**Gate:** Only run for these task types:
`research_report`, `consulting_deliverable`, `website_build`, `web_builder`, `3d_web_builder`, `notion_architect`, `copywriting`, `cold_outreach`, `email_draft`

**Changes to `memory.py`:**

Add `collection` parameter to `query_memory()`:
```python
def query_memory(query: str, top_k: int = 3, collection: str = None) -> list:
    collection = collection or QDRANT_COLLECTION  # default: agentshq_memory
    ...
```

**Step 0 injection in `orchestrator.py`:**
```python
MEMORY_GATED_TASK_TYPES = {
    "research_report", "consulting_deliverable", "website_build",
    "web_builder", "3d_web_builder", "notion_architect",
    "copywriting", "cold_outreach", "email_draft"
}

memory_context = ""
if task_type in MEMORY_GATED_TASK_TYPES:
    try:
        past_work = query_memory(task_request, top_k=3)          # agentshq_memory
        past_lessons = query_memory(                              # agentshq_learnings
            task_request, top_k=5, collection="agentshq_learnings"
        )
        # Build context block — positive lessons first, negative lessons flagged
        # Cap total at 6000 chars before prepending to enriched_task
    except Exception as e:
        logger.warning(f"Memory recall failed (non-fatal): {e}")
```

**Max-length guard:** After building the context block, measure `len(memory_context + enriched_task)`. If over 6000 chars, truncate `memory_context` from the bottom (keep the task request intact).

---

## Phase 3 — Post-Task Learning Extraction

**Files:** `memory.py`, `orchestrator.py`

### New function: `extract_and_save_learnings()`

```python
def extract_and_save_learnings(
    task_request: str,
    task_type: str,
    result_summary: str,
    learning_type: str = "pattern",  # "pattern", "preference", "lesson"
    from_number: str = "unknown"
) -> bool:
```

**LLM:** Claude Haiku (`anthropic/claude-haiku-4.5`) via existing OpenRouter connection. No new API keys.

**Extraction prompt asks for:**
- What approach or structure worked well for this task type?
- What tone/style was used?
- What entities appeared (people, companies, tools)?
- One-sentence lesson summary

**Qdrant storage:** Collection `agentshq_learnings`. Point ID = `sha256(task_type + lesson_content)[:16]` — deterministic, prevents duplicates on retries.

**Qdrant payload schema (locked):**
```json
{
  "job_id": "...",
  "task_type": "research_report",
  "crew_name": "research_crew",
  "lesson_type": "positive",
  "extracted_pattern": "Used 3-section structure: context, findings, recommendations",
  "entities": ["Catalyst Works", "SMB"],
  "timestamp": "2026-04-07T...",
  "source": "auto_extraction",
  "lesson_status": "auto"
}
```

**Execution:** Must run in a daemon thread — same pattern as `_trigger_evolution`:
```python
threading.Thread(
    target=extract_and_save_learnings,
    args=(task_request, task_type, result_summary),
    daemon=True
).start()
```

Fire AFTER `send_result()` delivers to Telegram — never before.

---

## Phase 4 — Critique Detection and Negative Lesson Extraction

**File:** `orchestrator.py`

### Session tracker

Add an in-memory dict (persisted to Postgres for VPS restarts):
```python
_last_completed_job: dict[str, dict] = {}
# key: chat_id
# value: {job_id, task_type, delivered_at, result_summary}
```

Populated in `_run_background_job()` after `send_result()` fires successfully.

### Praise detection

After message classification, before crew dispatch — check if message is explicit praise:
```python
PRAISE_SIGNALS = {"good job", "great", "well done", "perfect", "excellent",
                  "love it", "nice", "brilliant", "solid", "nailed it"}

def _is_praise(text: str) -> bool:
    t = text.lower().strip()
    return any(p in t for p in PRAISE_SIGNALS) and len(t) < 80
```

If praise detected AND `chat_id` has a recent completed job (within 60 minutes):
- Immediately call `extract_and_save_learnings(..., learning_type="positive")` in daemon thread
- Do not dispatch a crew

### Critique detection

If message is NOT praise AND NOT a new task AND `chat_id` has a recent completed job (within 60 minutes):
- Route to `extract_negative_lesson(feedback_text, prior_task_type, prior_result_summary)`

```python
def extract_negative_lesson(
    feedback: str,
    task_type: str,
    original_output: str,
    from_number: str = "unknown"
) -> bool:
```

Extraction LLM prompt asks:
- What specifically was wrong with the output?
- What should be avoided next time for this task type?
- One-sentence negative lesson

Saved to Qdrant `agentshq_learnings` with `lesson_type: "negative"` and `lesson_status: "auto"`.

### Distinguishing critique from new task

Use existing `_classify_obvious_chat()` + `_shortcut_classify()` logic. Add one additional check:

```python
def _is_feedback_on_prior_job(text: str, chat_id: str) -> bool:
    if chat_id not in _last_completed_job:
        return False
    elapsed = (datetime.utcnow() - _last_completed_job[chat_id]["delivered_at"]).seconds
    if elapsed > 3600:  # 1 hour window
        return False
    # If it classified as chat (not a crew task) AND it's within the window
    # AND it's not praise AND it references critique signals — treat as feedback
    CRITIQUE_SIGNALS = {"wrong", "bad", "not good", "don't like", "fix", "redo",
                        "wasn't", "wasn't done", "missed", "forgot", "too long",
                        "too short", "off", "incorrect", "weird", "not what"}
    t = text.lower()
    return any(s in t for s in CRITIQUE_SIGNALS)
```

**Fallback:** If confidence is low (no critique signals but classified as chat), treat as neutral — do nothing. Never write a lesson on ambiguous signals.

---

## Phase 5 — Entity and Preference Memory (Deferred)

Build after Phases 1-4 are stable. Adds:
- `agentshq_entities` Qdrant collection
- `save_entity()`, `query_entities()`, `save_preference()`, `get_preferences()` in `memory.py`
- New CrewAI tools in `tools.py`

---

## Phase 6 — CrewAI `memory=True` (Removed from this sprint)

CrewAI's built-in memory defaults to ephemeral ChromaDB inside the container — destroyed on every deploy. Custom Qdrant injection (Phase 2) already covers the same use case durably. Phase 6 is not in scope until CrewAI memory can be configured to use the persistent Qdrant backend.

---

## Audit and Rollback Tools

### Telegram commands (new)

| Command | Action |
|---|---|
| `/lessons [task_type]` | List last 10 auto-extracted lessons for that task type |
| `/purge-lesson [id]` | Mark a lesson as `purged` — excluded from all future recall |

These go in `orchestrator.py` alongside existing `/status`, `/more` commands.

### Feature flag

Add env var `MEMORY_LEARNING_ENABLED=true` to `.env` on VPS. All Phase 3/4 logic is gated by this flag. Set to `false` to disable extraction without a code rollback.

### Git save point

`cd19ba5` — revert here if build causes regressions.

---

## Files Changed — Complete List

| File | Phase | Change |
|---|---|---|
| `setup-database.sql` | 1 | Add 4 tables with `IF NOT EXISTS` |
| `memory.py` | 2, 3, 4 | Add `collection` param to `query_memory()`; add `extract_and_save_learnings()`; add `extract_negative_lesson()`; add Qdrant collection init for `agentshq_learnings` |
| `orchestrator.py` | 2, 3, 4 | Add Step 0 recall (gated); add `_last_completed_job` session tracker; add praise detection; add critique detection; add `/lessons` and `/purge-lesson` commands; add `MEMORY_LEARNING_ENABLED` flag guard |
| `tools.py` | 3 | Wire `extract_and_save_learnings` as a CrewAI tool so agents can explicitly save a lesson mid-run |

**Not changed:** `crews.py` (Phase 6 removed), `agents.py`, all crew files.

---

## Time Estimate

| Phase | Work | Estimate |
|---|---|---|
| 0 | VPS table inventory | 15 min |
| 1 | SQL tables | 30 min |
| 2 | Pre-task recall | 1-2 hours |
| 3 | Post-task extraction | 2-3 hours |
| 4 | Critique/praise detection | 2-3 hours |
| Audit tools | `/lessons`, `/purge-lesson`, feature flag | 1 hour |
| **Total** | | **7-10 hours** |

---

## Verification Plan

1. `docker exec orc-postgres psql -U postgres -c "\dt"` — confirm all 4 new tables exist
2. Send a task via Telegram — confirm Step 0 fires (check logs for `Memory recall:`)
3. Reply "good job" — confirm positive lesson appears in `agent_learnings` table
4. Reply "the table formatting was wrong" — confirm negative lesson appears with `lesson_type=negative`
5. Run same task type again — confirm recalled lessons appear in Step 0 log
6. Run `/lessons research_report` — confirm command returns stored lessons
7. Run `/purge-lesson [id]` — confirm lesson_status changes to `purged` and it no longer appears in recall
