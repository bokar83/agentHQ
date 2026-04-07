# Router Hardening + agentsHQ Ideas Database — Design Spec

**Date:** 2026-04-07
**Author:** Boubacar Barry / Claude Code

---

## Problem

The agentsHQ orchestrator router misclassifies a significant class of requests as `chat`, causing tasks to silently vanish into a conversational response with no action taken. Root causes:

1. `_classify_obvious_chat()` pre-filter runs before keyword shortcuts, eating short messages under 60 chars.
2. No task type exists for Notion writes (add idea, capture note) — only `notion_overhaul` (redesign).
3. Compound requests ("do X AND email me about it") route to one intent; the second is dropped.
4. GWS requests ("what's on my calendar") under 60 chars bypass the LLM router entirely.
5. No Ideas database exists to receive brain dumps from Telegram.
6. "Remember this" / "save this to memory" is misclassified as `agent_creation`.

---

## Solution Overview

### 1. Fix `_classify_obvious_chat` execution order

Move critical keyword shortcuts out of `classify_task()` and into a check that runs **before** `_classify_obvious_chat()`. This is the root fix for bugs 1, 4, and 8 from the pressure test.

Pattern: `process_telegram_update()` and `/run` API endpoint both call `_classify_obvious_chat()` before `classify_task()`. A new `_shortcut_classify()` function runs first, returns a task type or `None`, and is checked before the obvious-chat pre-filter.

### 2. New `notion_capture` task type

Handles: add to ideas, note this, capture this, brain dump, put in backlog, remember this for later.

Two modes:
- **write**: extract title + full content, create a page in "agentsHQ Ideas" Notion DB.
- **review**: query the Ideas DB and return a formatted summary to Telegram.

The crew is a single lightweight agent (no planner overhead). It calls `NotionCreateIdeaTool` (write mode) or `NotionQueryIdeasTool` (review mode) directly.

### 3. New `notion_skill` functions

Add to `skills/notion_skill/notion_tool.py`:
- `create_database(parent_page_id, title, properties)` — creates a new Notion DB
- `query_database(database_id, filter=None, sorts=None)` — queries records from a DB

Add to `orchestrator/tools.py`:
- `NotionCreateIdeaTool` — wraps `create_page()` with fixed Ideas DB ID from env
- `NotionQueryIdeasTool` — wraps `query_database()` with fixed Ideas DB ID
- `NOTION_CAPTURE_TOOLS` bundle

### 4. Compound request detection + post-crew GWS hook

Router extracts metadata: `has_email_followup` (bool) — set when message contains both a primary task verb AND email-to trigger ("send me an email", "email me about this", "email me a summary").

`_run_background_job()` checks `has_email_followup` after primary crew finishes. If true, it assembles a minimal `gws_crew` task with the primary result as context and creates a Gmail draft.

### 5. GWS keyword shortcuts promoted

Short GWS phrases ("what's on my calendar", "add event", "delete event") added to `_shortcut_classify()` so they never hit the obvious-chat pre-filter.

### 6. `save_memory_tool` added to chat's tool list

Chat LLM already has `query_system` and `retrieve_output_file` as function-call tools. Add `save_memory` as a third tool so the chat LLM can persist facts (brand colors, preferences, notes) without spinning a crew. Calls `save_conversation_turn()` with a `[MEMORY]` prefix tag and `save_to_memory()`.

### 7. Notion Ideas DB creation + seeding

A one-time bootstrap script creates the "agentsHQ Ideas" Notion DB under the agentsHQ workspace page. The resulting DB ID is written to `.env` and `docker-compose.yml` as `IDEAS_DB_ID`. The Practice Runner idea is seeded as the first record.

---

## Data Model — agentsHQ Ideas Database

| Property | Type | Notes |
|---|---|---|
| Name | title | Auto-extracted from message or user-supplied |
| Content | rich_text | Full idea description |
| Source | select | Telegram / Manual |
| Status | select | New / Reviewed / Archived |
| Category | select | Tool / Agent / Feature / Business / Personal |
| Created | date | Auto-set on creation |

---

## Routing Logic After This Change

```
Telegram message arrives
  → _shortcut_classify(text)          ← NEW: runs first, catches GWS + notion_capture + enrich + etc.
    → if match: skip classify_task(), go to crew
    → else: _classify_obvious_chat(text)
      → if True: run_chat()
      → else: classify_task() LLM call
  
After crew completes (_run_background_job):
  → check metadata["has_email_followup"]   ← NEW
    → if True: spin gws_crew to draft summary email
```

---

## Fixes Summary

| Bug # | Fix |
|---|---|
| 1. obvious-chat eats short task messages | `_shortcut_classify()` runs before pre-filter |
| 2. No notion write task type | `notion_capture` task type + crew |
| 3. Compound requests drop second intent | `has_email_followup` metadata + post-crew GWS hook |
| 4. GWS phrases under 60 chars go to chat | GWS shortcuts in `_shortcut_classify()` |
| 5. No Ideas DB exists | Bootstrap script + seeding |
| 6. No `create_database` / `query_database` | Added to `notion_tool.py` |
| 7. `create_page` stub silently fails | Guard check before crew runs |
| 8. LLM conflates notion_overhaul / notion_capture | Explicit routing rule in router prompt |
| 9. "Remember this" → agent_creation | `save_memory` tool in chat; keyword shortcut |
| 10. DB ID found by name every time | `IDEAS_DB_ID` env var |

---

## Files Changed

| File | Change |
|---|---|
| `orchestrator/orchestrator.py` | `_shortcut_classify()`, promote shortcuts, `has_email_followup` post-hook, `save_memory` chat tool |
| `orchestrator/router.py` | `notion_capture` task type, GWS shortcuts moved, routing rule update, `extract_metadata()` compound detection |
| `orchestrator/tools.py` | `NotionCreateIdeaTool`, `NotionQueryIdeasTool`, `NOTION_CAPTURE_TOOLS` |
| `orchestrator/crews.py` | `build_notion_capture_crew()`, register in `CREW_REGISTRY` |
| `orchestrator/agents.py` | `build_notion_capture_agent()` |
| `orchestrator/notifier.py` | Labels + crew name for `notion_capture` |
| `skills/notion_skill/notion_tool.py` | `create_database()`, `query_database()` |
| `scripts/bootstrap_ideas_db.py` | One-time DB creation + seeding script |
| `docker-compose.yml` | `IDEAS_DB_ID` env var passthrough |
| `.env` (VPS) | `IDEAS_DB_ID` value after bootstrap |
