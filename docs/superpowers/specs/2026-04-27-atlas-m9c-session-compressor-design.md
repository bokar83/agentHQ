# Atlas M9c: Cross-Session Memory Compressor

**Date:** 2026-04-27
**Status:** approved (post-Sankofa Council 2026-04-27)
**Branch:** feat/atlas-m9c-session-compressor

---

## Problem

`run_chat` and `run_atlas_chat` load the last 100 raw turns from Postgres on every
request. After a gap of 30+ minutes the session is effectively a new conversation,
but the model starts cold with no awareness of what happened before. The user has
to re-establish context manually.

---

## Solution

A background heartbeat tick runs every 30 minutes. It finds sessions that have been
inactive for 30-90 minutes and have not yet been summarized for their last active
window. It calls Haiku to produce a compact summary (max 400 tokens) and writes it
to a new `session_summaries` table. On the next message, `run_chat` and
`run_atlas_chat` silently prepend the summary to the system prompt. No UI change,
no extra latency, works on all three surfaces (Telegram, /chat, /atlas).

---

## Architecture

### New table: session_summaries

```sql
CREATE TABLE IF NOT EXISTS session_summaries (
    id            SERIAL PRIMARY KEY,
    session_id    TEXT NOT NULL,
    summary       TEXT NOT NULL,
    turn_count    INTEGER NOT NULL,       : how many turns were summarized
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    window_end_at TIMESTAMPTZ NOT NULL,   : timestamp of last turn included
    tags          TEXT[]                  : reserved for future project tagging (NULL default)
);
CREATE INDEX IF NOT EXISTS idx_session_summaries_session
    ON session_summaries (session_id, created_at DESC);
```

Raw turns in `agent_conversation_history` are never deleted. The summary is an
additive layer only.

### New module: orchestrator/session_compressor.py

Three functions:

**`find_sessions_to_compress()`**
Queries `agent_sessions` for rows where:
- `last_active_at` is between 30 and 90 minutes ago (session went quiet but not ancient)
- No `session_summaries` row exists for this session with `created_at` > `last_active_at - 30min`

Returns list of `(session_id, last_active_at)` tuples.

**`compress_session(session_id)`**
1. Loads last 100 turns for the session from `agent_conversation_history`
2. If fewer than 4 turns, skips (not worth summarizing)
3. Calls Haiku with a tight prompt: "Summarize this conversation in 3-5 bullet
   points. Focus on decisions made, tasks completed, and open items. Be specific."
4. Writes result to `session_summaries`
5. Logs result

**`compressor_tick()`**
Heartbeat callback. Calls `find_sessions_to_compress()`, then `compress_session()`
for each. Non-fatal on any individual session failure.

### Modified: orchestrator/db.py

Add `ensure_session_summaries_table()` called at startup alongside existing table
migrations. Add `save_session_summary()` and `get_latest_session_summary()` helpers.

`get_latest_session_summary(session_id, max_age_hours=24)`: summaries older than
24 hours are not injected. SQL gate: `AND created_at > NOW() - INTERVAL '24 hours'`.
Prevents stale summaries from accumulating silently across days.

### Modified: orchestrator/handlers_chat.py

Both `run_chat()` and `run_atlas_chat()` get a new step after history load:

```python
# Check for a prior session summary (silent injection)
summary_injection = ""
try:
    from db import get_latest_session_summary
    row = get_latest_session_summary(session_key)
    if row:
        summary_injection = (
            f"PRIOR SESSION CONTEXT (summarized):\n{row['summary']}\n\n"
            f"Refer to this naturally if relevant. Do not repeat it verbatim."
        )
except Exception:
    pass  # non-fatal

# Prepend to system prompt
if summary_injection:
    system_prompt = summary_injection + "\n\n" + system_prompt
```

The injection is prepended to the system prompt, not inserted as a message turn.
This keeps the message array clean and avoids confusing the model with a synthetic
assistant message it did not generate.

### Modified: orchestrator/scheduler.py

```python
from session_compressor import compressor_tick
_heartbeat.register_wake(
    "session-compressor",
    crew_name=_heartbeat.SELF_TEST_CREW,
    callback=compressor_tick,
    every="30m",
)
```

Uses `every=` (interval) not `at=` (time-of-day) since compression should happen
continuously, not at a fixed clock time.

---

## Key decisions

| Decision | Choice | Reason |
|---|---|---|
| Raw turns deleted? | No, kept permanently | Lossless; storage is cheap; needed for L5 learning |
| Injection method | System prompt prepend | No latency, no synthetic message turns, invisible to user |
| Trigger | 30-90 min inactivity window | Short enough to be useful; upper bound avoids summarizing dead sessions |
| Min turns to summarize | 4 | Below 4 turns there is nothing meaningful to compress |
| Summary model | Haiku 4.5 | Fast, cheap, sufficient for bullet-point summarization |
| Summary max length | 400 tokens output | Keeps injection small; does not crowd out live history |
| Surfaces | All three (Telegram, /chat, /atlas) | Same session_key mechanism, same Postgres history |
| Retry on failure | No retry; next tick will catch it | Compression is best-effort, not mission-critical |

---

## What is NOT in this spec

- Summary UI: no "here is what we discussed" card on the dashboard (can add later)
- Summary editing: no way to correct a bad summary (re-summarize on next gap)
- Per-surface summary: one summary per session_id regardless of surface
- Archiving old summaries: all summaries kept; `get_latest_session_summary` returns most recent within 24h
- Cross-surface session unification: Telegram, /chat, and /atlas use different session_id values for the same user. Each surface has its own summary. This is acceptable for M9c; unification is a future milestone.

---

## Files changed

| File | Change |
|---|---|
| `orchestrator/db.py` | `ensure_session_summaries_table()`, `save_session_summary()`, `get_latest_session_summary()` |
| `orchestrator/session_compressor.py` | NEW: `find_sessions_to_compress()`, `compress_session()`, `compressor_tick()` |
| `orchestrator/scheduler.py` | Register `session-compressor` heartbeat wake every 30m |
| `orchestrator/handlers_chat.py` | Summary injection in `run_chat()` and `run_atlas_chat()` |
| `orchestrator/tests/test_session_compressor.py` | NEW: unit tests |

---

## Test plan

1. `test_find_sessions_to_compress`: mock `agent_sessions` with 3 rows:
   one in window, one too recent, one too old. Assert only the in-window row returned.
2. `test_compress_session_skips_short`: fewer than 4 turns, assert no DB write.
3. `test_compress_session_writes_summary`: mock history + LLM call, assert
   `save_session_summary` called with correct session_id and non-empty summary.
4. `test_compressor_tick_nonfatal`: one session raises on compress, assert tick
   continues and processes remaining sessions.
5. `test_summary_injection_in_run_chat`: mock `get_latest_session_summary` to
   return a row, assert system prompt contains "PRIOR SESSION CONTEXT".
6. `test_no_injection_when_no_summary`: mock returns None, assert system prompt
   unchanged.
