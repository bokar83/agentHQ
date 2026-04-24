# Phase 1: Episodic Memory and Approval Queue

**Date:** 2026-04-24
**Owner:** Boubacar Barry
**Branch:** `feat/episodic-memory-and-queue`
**Save point tag:** `savepoint-pre-phase-1-20260424` (to be created before branch)
**Status:** Draft (Council-reviewed, owner-approved, writing-plans pending)

## Context

Phase 0 shipped the safety rails (kill switch, per-crew flags, spend cap). Nothing autonomous runs yet. Phase 1 builds the substrate that every later phase depends on:

- **Approval queue:** where autonomous crews drop proposals for Boubacar's last-mile review
- **Episodic memory:** where every autonomous task logs its outcome so future work can learn from past results

| Phase | Status |
|---|---|
| 0. Safety rails | SHIPPED 2026-04-23 |
| **1. Episodic memory + approval queue (this spec)** | DRAFT |
| 2. Smart heartbeat | queued |
| 3. Griot pilot | queued |
| 4. Concierge (self-healing) | queued |
| 5. Chairman learning loop | queued |
| 6. Hunter pilot | queued |

## Goals

1. Give autonomous crews a place to queue proposals and receive approve/reject/edit decisions from Boubacar
2. Log every autonomous task's outcome so patterns are queryable by Phase 5 Chairman
3. Capture structured rejection feedback so the system learns Boubacar's taste, not just his preferences
4. Work from both phone (Telegram reply) and laptop (HTTP endpoint)
5. No changes to existing behavior; additive migration only; Phase 0 rails still apply to any future autonomous call

## Non-goals

- Any crew running autonomously (Phase 3+)
- Smart heartbeat / scheduled wakes (Phase 2)
- Chairman learning loop or prompt mutation (Phase 5)
- Logging user-initiated tasks (autonomous-only for Phase 1)
- Web dashboard (laptop access is HTTP API only)
- Voice-note replies (Phase 1 is text/emoji only; voice is a future enhancement)
- Vector similarity search in `find_similar` (text-prefix match for Phase 1; vectors in Phase 5)
- Supabase tables (Phase 1 operational data lives on local Postgres per db split rule)

## Parameters locked with owner

| Parameter | Value | Source |
|---|---|---|
| Queue storage | Local Postgres (`orc-postgres`) | Owner + DB split rule |
| Approval UX | Reply-to-message with natural-language + emoji | Owner 2026-04-23 |
| Approval fallback | Most-recent-pending-within-2-hours when reply target missing | Council (Contrarian) |
| Rejection feedback | Structured tag (off-voice / wrong-hook / stale / too-salesy / other) | Council (Expansionist) |
| Laptop parity | HTTP POST approval endpoint, API-key-gated | Council (Outsider) |
| Task signature | First 50 chars of normalized plan_summary for Phase 1 | Council (Contrarian) |
| Expiry | None in Phase 1; revisit after 2 weeks of real data | Council (Contrarian) |
| `crew_lessons` table | Dropped from Phase 1; Phase 5 builds it with Chairman | Council (First Principles) |

## Council-surfaced fixes applied

1. Fallback-to-latest-pending when `reply_to_message_id` is missing
2. `crew_lessons` dropped from Phase 1 (scaffolding rule)
3. `approval_status` denormalization dropped; always join `approval_queue` when reading
4. `task_signature` strategy defined (first 50 chars of normalized plan_summary)
5. Expiry dropped; revisit after data
6. `boubacar_feedback_tag` TEXT column on `approval_queue`
7. HTTP `POST /autonomy/approve/:queue_id` endpoint behind API key
8. Mid-day proactive push (if pending > 30 min) flagged as Phase 1.5, not Phase 1

## Architecture

Two new tables on local Postgres, two new modules in the orchestrator, one extension to the existing Telegram handler, one new HTTP endpoint, one enrichment to the morning digest.

```
orchestrator/
├── approval_queue.py       <- NEW: enqueue, approve, reject, edit, find helpers
├── episodic_memory.py      <- NEW: start_task, complete_task, link_approval, find_similar, crew_stats
├── handlers_chat.py        <- EXTEND: reply-to-message approval handler, text-alias expansion
├── orchestrator.py         <- EXTEND: new HTTP endpoint, /queue /outcomes Telegram commands
├── scheduler.py            <- EXTEND: morning digest adds "Pending approvals" section
└── migrations/
    └── 005_autonomy_memory.sql   <- NEW: two tables (approval_queue, task_outcomes)
```

No changes to router, crews, agents, council, notifier.

## Database schema

Migration `005_autonomy_memory.sql` (additive; both tables new):

### Table 1: `approval_queue`

```sql
CREATE TABLE IF NOT EXISTS approval_queue (
    id                       BIGSERIAL PRIMARY KEY,
    ts_created               TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts_decided               TIMESTAMPTZ,
    crew_name                TEXT NOT NULL,
    proposal_type            TEXT NOT NULL,
    payload                  JSONB NOT NULL,
    telegram_msg_id          BIGINT,
    status                   TEXT NOT NULL DEFAULT 'pending',
    decision_note            TEXT,
    boubacar_feedback_tag    TEXT,
    edited_payload           JSONB,
    task_outcome_id          BIGINT
);

CREATE INDEX idx_approval_queue_status_ts ON approval_queue (status, ts_created DESC);
CREATE INDEX idx_approval_queue_telegram_msg
    ON approval_queue (telegram_msg_id)
    WHERE telegram_msg_id IS NOT NULL;
```

**Column notes:**
- `status`: `pending` | `approved` | `rejected` | `edited`
- `boubacar_feedback_tag`: free text with a controlled vocabulary enforced in application code, not DB (YAGNI on ENUM; tags will evolve). Starting vocab: `off-voice`, `wrong-hook`, `stale`, `too-salesy`, `other`
- `payload` and `edited_payload` are `JSONB` so any crew can store arbitrary shape. Schema validation is crew-side, not DB-side.
- `task_outcome_id` references `task_outcomes(id)` but we skip the FK constraint to keep the migration trivially reversible (application maintains the link).

### Table 2: `task_outcomes`

```sql
CREATE TABLE IF NOT EXISTS task_outcomes (
    id                       BIGSERIAL PRIMARY KEY,
    ts_started               TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts_completed             TIMESTAMPTZ,
    crew_name                TEXT NOT NULL,
    task_signature           TEXT NOT NULL,
    plan_summary             TEXT,
    result_summary           TEXT,
    total_cost_usd           NUMERIC(10,6) NOT NULL DEFAULT 0,
    success                  BOOLEAN,
    approval_queue_id        BIGINT,
    boubacar_feedback        TEXT,
    llm_calls_ids            BIGINT[] NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_task_outcomes_ts         ON task_outcomes (ts_started DESC);
CREATE INDEX idx_task_outcomes_crew_ts    ON task_outcomes (crew_name, ts_started DESC);
CREATE INDEX idx_task_outcomes_signature  ON task_outcomes (task_signature);
```

**Column notes:**
- `success` is `NULL` while the outcome is open, `true` if approved or edited-and-published, `false` if rejected
- `approval_status` is **deliberately not stored** (read it by joining `approval_queue`; Council fix 3)
- `task_signature` generation lives in `episodic_memory.py` (see Modules)
- `llm_calls_ids` is a Postgres array; join back to `llm_calls` for cost drilldown

### Tables deliberately NOT created in Phase 1

- `crew_lessons`: deferred to Phase 5 (Chairman writes it; creating it now is scaffolding)

## Modules

### `orchestrator/approval_queue.py` (~180 lines)

Public API (typed with dataclasses matching `autonomy_guard.py` style):

```python
@dataclass
class QueueRow:
    id: int
    crew_name: str
    proposal_type: str
    payload: dict
    status: str                  # pending | approved | rejected | edited
    ts_created: datetime
    ts_decided: Optional[datetime]
    telegram_msg_id: Optional[int]
    decision_note: Optional[str]
    boubacar_feedback_tag: Optional[str]
    edited_payload: Optional[dict]
    task_outcome_id: Optional[int]

def enqueue(crew_name, proposal_type, payload, outcome_id=None) -> QueueRow: ...
def approve(queue_id, note=None) -> QueueRow: ...
def reject(queue_id, note=None, feedback_tag=None) -> QueueRow: ...
def edit(queue_id, new_payload, note=None) -> QueueRow: ...
def find_by_telegram_msg_id(reply_to_msg_id) -> Optional[QueueRow]: ...
def find_latest_pending(max_age_hours=2) -> Optional[QueueRow]: ...
def list_pending(limit=10) -> list[QueueRow]: ...
def get(queue_id) -> Optional[QueueRow]: ...
```

**`enqueue` side effects:** inserts row, sends Telegram message with crew+type+payload preview, stores returned `msg_id` back on the row, returns the updated `QueueRow`. If Telegram send fails, row still exists with `telegram_msg_id=NULL` and shows up on `/queue`.

**`find_latest_pending`:** the Council-mandated fallback when a reply has no `reply_to_message_id`. Returns the most-recent `status=pending` row (any crew) created within the last `max_age_hours`. Returns `None` otherwise.

**Notification behavior:** approve/reject/edit all send a confirmation Telegram message back to Boubacar so he knows the decision registered.

### `orchestrator/episodic_memory.py` (~150 lines)

```python
@dataclass
class OutcomeRow:
    id: int
    ts_started: datetime
    ts_completed: Optional[datetime]
    crew_name: str
    task_signature: str
    plan_summary: Optional[str]
    result_summary: Optional[str]
    total_cost_usd: float
    success: Optional[bool]
    approval_queue_id: Optional[int]
    boubacar_feedback: Optional[str]
    llm_calls_ids: list[int]

def start_task(crew_name, plan_summary) -> OutcomeRow: ...
def complete_task(outcome_id, result_summary=None, total_cost_usd=0.0, llm_calls_ids=None) -> OutcomeRow: ...
def link_approval(outcome_id, approval_queue_id) -> None: ...
def record_approval_result(outcome_id, success, feedback=None) -> None: ...
def find_similar(task_signature, limit=5) -> list[OutcomeRow]: ...
def crew_stats(crew_name, days=7) -> dict: ...
def build_signature(plan_summary) -> str: ...
```

**`build_signature` strategy (Council-surfaced):** lowercase the plan_summary, strip dates/ISO timestamps/UUIDs/numeric IDs via regex, collapse whitespace, take the first 50 chars. Good enough for Phase 1 similarity. Phase 5 upgrades to embedding-based.

**`find_similar` strategy for Phase 1:** `WHERE task_signature LIKE $1 || '%' ORDER BY ts_started DESC LIMIT $2`. Cheap, deterministic, index-friendly.

**`crew_stats` returns** `{total: N, approved: N, rejected: N, edited: N, approval_rate: 0.xx, avg_cost_usd: 0.xx, top_feedback_tags: [...]}` for the given crew and window.

### `orchestrator/handlers_chat.py` extension (~80 lines added)

**`_TEXT_ALIASES` expansion** (add natural-language approvals to the existing dict):

Existing: `yes / confirm / approved / approve / flag / discard / reject`. Add: `no / not approved / rejected / nope / yep / yeah`.

**New reply-to-message handler:**

1. If message has `reply_to_message_id`:
   - `approval_queue.find_by_telegram_msg_id(reply_to_message_id)` → `QueueRow?`
   - If matched, route to approve/reject/edit based on message text
2. If no reply target or no match, AND message looks like an approval (emoji in `_EMOJI_COMMANDS` or word in `_TEXT_ALIASES`):
   - `approval_queue.find_latest_pending()` → `QueueRow?`
   - If matched, route to that row with a confirmation message: "Assuming latest pending: post_draft from griot 23m ago. Approve? Reply `yes confirm` to confirm."
   - Rationale: ambiguous "yes" shouldn't silently act; require a second-step confirmation only in the fallback path
3. If reject, prompt for a feedback tag via **both** channels (option C, owner choice 2026-04-24): a Telegram inline keyboard shows buttons `off-voice`, `wrong-hook`, `stale`, `too-salesy`, `other`, `skip`, **and** any text reply within the next 5 minutes is accepted too. If Boubacar types free text, we pattern-match against the known tag vocabulary (case-insensitive, normalize hyphens/spaces); unmatched text is stored verbatim as the tag (so "stale angle" becomes the tag value). This requires inline-button callback handling plus a short pending-feedback lookup window on incoming text messages.
4. If `edit: <text>` or `edit <text>` pattern, treat rest-of-message as new payload text; replaces `payload.body` in the stored row and marks `status=edited`.

**Why inline buttons for feedback tags only:** we keep the main approve/reject flow on natural-language/emoji replies (simple, robust), and reserve inline buttons for the one place where categorical choice beats free text (rejection reason).

### `orchestrator/orchestrator.py` extensions (~100 lines added)

**New Telegram commands** (placed with the other slash commands introduced in Phase 0):

- `/queue`: show up to 10 pending rows (`ID | crew | type | age`)
- `/approve <id> [note]`: fallback command-based approval for when reply-to-message fails
- `/reject <id> [tag] [note]`: fallback for rejection with optional feedback tag inline
- `/outcomes [crew] [days]`: last 10 completed outcomes, optionally filtered by crew; shows approval_status joined live from approval_queue

**New HTTP endpoint** (API-key-gated via existing `verify_api_key`):

```
POST /autonomy/approve/:queue_id
Headers: X-API-Key: <ORCHESTRATOR_API_KEY>
Body (JSON):
  {"decision": "approve|reject|edit", "note": "...", "feedback_tag": "...", "edited_payload": {...}}
```

Returns the updated `QueueRow` as JSON. Mirrors the Telegram reply flow for laptop parity.

### `orchestrator/scheduler.py` morning digest enrichment (~20 lines added)

The existing 07:00 MT digest adds a "Pending approvals" section:

```
Pending approvals: 3
  #47 griot     post_draft      (2h ago)
  #48 griot     post_draft      (2h ago)
  #49 hunter    outreach_email  (30m ago)
```

If zero pending, shows `Pending approvals: 0`. Full queue is one Telegram message away via `/queue`.

## Data flow: happy path (approve from Telegram)

```
Phase 3+ crew decides to propose something
    v
episodic_memory.start_task(crew="griot", plan_summary="Draft LinkedIn post about...")
    v
    -> task_outcomes row (id=T, success=NULL, approval_queue_id=NULL)
    v
approval_queue.enqueue(crew="griot", type="post_draft", payload={...}, outcome_id=T)
    v
    -> approval_queue row (id=Q, status=pending, telegram_msg_id=NULL)
    -> Telegram msg sent: "griot post_draft proposal #Q ..." -> msg_id M returned
    -> row updated: telegram_msg_id=M
    v
episodic_memory.link_approval(T, Q)
    v
    (crew done; both rows open)

... later ...

Boubacar replies "yes" (or 'approve') to Telegram msg M
    v
handlers_chat reads reply_to_message_id = M
    v
approval_queue.find_by_telegram_msg_id(M) -> QueueRow(Q)
    v
approval_queue.approve(Q, note=None)
    v
    -> queue row: status=approved, ts_decided=now
    -> Telegram confirmation: "approved queue #Q (griot post_draft)"
    v
episodic_memory.record_approval_result(T, success=True, feedback=None)
    v
    -> task_outcomes row: success=true
    v
crew reads queue row (status=approved OR edited, whichever), uses edited_payload if present
    v
crew publishes, then calls episodic_memory.complete_task(T, result_summary, cost, llm_calls_ids)
    v
    -> task_outcomes row: ts_completed=now, result_summary=..., total_cost_usd=...
```

## Data flow: fallback (no reply target)

```
Boubacar types "yes" in the main chat (no reply)
    v
handlers_chat: no reply_to_message_id
    v
text is in _TEXT_ALIASES (approve)? YES
    v
approval_queue.find_latest_pending(max_age_hours=2)
    -> QueueRow(Q) if any pending < 2h, else None
    v
If Q found:
    Telegram asks: "Did you mean queue #Q (griot post_draft from 23m ago)? Reply 'yes confirm' to approve."
    -> Boubacar replies "yes confirm" -> approve(Q)
    -> or Boubacar ignores -> nothing happens
If None:
    Telegram: "No pending proposal to approve. /queue to see all."
```

## Data flow: HTTP approval (laptop)

```
laptop: curl -X POST http://vps/autonomy/approve/47 \
    -H "X-API-Key: ..." \
    -d '{"decision":"approve","note":"good one"}'
    v
verify_api_key
    v
approval_queue.approve(47, note="good one")
    v
    [same downstream as Telegram path]
    v
returns JSON of updated QueueRow
```

## Error handling

| Failure | Behavior |
|---|---|
| Telegram send fails during enqueue | Row persists with `telegram_msg_id=NULL`; shows on `/queue`; Boubacar can approve by ID |
| DB insert fails during enqueue | Transaction rolls back; crew gets exception; autonomy_guard logs `guard_decision='queue-write-failed'` on the llm_call |
| Boubacar replies "yes" but the queue row was already decided | handler returns "Already decided: approved by you at 10:32am" |
| Boubacar replies "yes" but no matching queue row and no pending in last 2h | handler returns "No pending proposal matches. /queue to review." |
| HTTP approve called on already-decided row | HTTP 409 with current status in body |
| `approval_queue.find_by_telegram_msg_id` returns >1 row | Impossible (msg_id is per-message unique) but defensive: return most recent; log warning |
| JSON payload is malformed | Stored as-is; Phase 3+ crews are responsible for validating their own payloads on read |

## Testing plan

Same discipline as Phase 0:

**Unit tests** (`orchestrator/tests/test_approval_queue.py`, `test_episodic_memory.py`):
- DB mocked; cover enqueue round-trip with Telegram send and without, approve/reject/edit state transitions, find_by_telegram_msg_id, find_latest_pending edge cases (none, one fresh, one stale), feedback_tag capture, task_signature generation with various plan_summaries, find_similar hit/miss, crew_stats with zero data and populated data.

**Integration test** (`tmp/test_phase1_e2e.py`):
- In-process SQLite mirroring the migration; full round-trip: start_task -> enqueue (mocked Telegram) -> approve -> record_approval_result -> complete_task -> find_similar returns the row.
- HTTP approve path using FastAPI TestClient.

**Regression**: all 35 existing tests must still pass; Phase 0 autonomy tests must still pass.

**Live sanity on VPS after deploy** (before Phase 3):
- Shell-exec enqueue a fake proposal from inside orc-crewai (`python -c "from approval_queue import enqueue; enqueue(...)"`).
- Verify Telegram message arrives with a queue ID.
- Reply "yes" from phone; verify DB row updated, confirmation received.
- Reply "no off-voice" from phone on a second fake; verify `boubacar_feedback_tag=off-voice`.
- HTTP approve from laptop via curl; verify HTTP 200 + DB state.

## Deploy plan

Follows Phase 0 runbook template:

1. Save point tag: `savepoint-pre-phase-1-YYYYMMDD` before branch
2. Branch: `feat/episodic-memory-and-queue`
3. Merge to main after Council + review + tests
4. VPS pull main
5. Apply `005_autonomy_memory.sql` to `orc-postgres`
6. `docker compose up -d --build orchestrator`
7. Verify logs, live sanity script, then YOUR Telegram/HTTP smoke tests
8. Tag `savepoint-phase-1-shipped-YYYYMMDD`
9. Memory updates (project_autonomy_layer.md, savepoints.md)

## Rollback

```
git reset --hard savepoint-pre-phase-1-YYYYMMDD
docker compose up -d --build orchestrator
```

Migration 005 is additive; unused columns/tables don't affect anything else. No migration reversal needed.

## Success criteria

- Migration 005 applied on VPS Postgres with both tables present
- `/queue` returns empty list when nothing is pending (proves the read path works)
- Live-sanity enqueue produces a Telegram message with a queue ID
- Reply "yes" to that message flips the row to `approved` and logs to `task_outcomes`
- Reply to a fresh enqueue with "no" + feedback tag produces `rejected` with `boubacar_feedback_tag` set
- HTTP POST /autonomy/approve/:id works with API key and matches DB state
- Morning digest at 07:00 MT shows "Pending approvals: 0" (or correct count)
- No regressions in Phase 0 Telegram commands (`/autonomy_status`, `/pause_autonomy`, `/resume_autonomy`, `/spend`)
- All existing tests green

## What this does NOT do

- No autonomous crew runs (Phase 3+)
- No scheduled wakes (Phase 2)
- No auto-expiry of stale proposals (deferred; revisit after data)
- No prompt/skill mutation proposals (Phase 5)
- No vector similarity search (text-prefix for Phase 1)
- No batched approval (one decision per reply)
- No Web UI (HTTP API only for laptop access)
- No cross-crew queue visibility for crews (Chairman reads all in Phase 5)

## What ships AFTER Phase 1

Phase 2 (smart heartbeat) will call `approval_queue.enqueue` for its proposals and `episodic_memory.start_task` / `complete_task` around every autonomous run. Phase 3 (Griot) is the first crew to actually use this. Phase 5 (Chairman) writes to the deferred `crew_lessons` table by reading `approval_queue` + `task_outcomes` cross-joined.

Phase 1 delivers the shelves. Phase 3 puts stock on them.
