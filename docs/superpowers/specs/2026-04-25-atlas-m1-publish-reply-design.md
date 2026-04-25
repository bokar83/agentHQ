# Atlas M1: Publish Reply (Notion Status Reconcile)

**Roadmap:** `docs/roadmap/atlas.md` (codename: atlas)
**Milestone:** M1 (closes loop L4 Reconcile)
**Branch:** `feat/atlas-m1-reply`
**Date:** 2026-04-25

## Problem

The publish brief sends Boubacar a daily Telegram digest of posts to publish. After he taps the share URL and posts on LinkedIn or X, **nothing tells Notion the post went live.** Status stays at Queued forever. Today he flips it manually. Without M1, Monday's first auto-published post will sit Queued indefinitely, and the system is not actually closed-loop.

## Goal

Boubacar replies `posted` or `skip` to a brief message in Telegram. The system flips the Notion record to `Posted` or `Skipped`, writes a `task_outcomes` row, and confirms back. Idempotent on double-reply.

Test target: Monday 2026-04-27 morning fire on queue #3, "One constraint nobody has named yet."

## Non-goals

- Auto-publishing (M7 territory: Blotato or LinkedIn/X OAuth)
- Reconciliation polling (M3 territory: query the platform directly)
- Capturing "was this edited" signal (Phase 5 Chairman territory; revisit when L5 starts)
- Editing the post body in Telegram (you edit in the share-URL composer; no value in re-editing here)

## Design

### One-line summary

Store an in-memory `_PUBLISH_BRIEF_WINDOWS` dict in `state.py` (keyed by telegram_msg_id) when the brief sends each per-post message. Add a `handle_publish_reply` function to `handlers_approvals.py` that reads from the dict on a reply, flips Notion, writes task_outcomes, and evicts the dict entry. No persistent storage, no approval_queue rows, no migrations.

**Council reframe (2026-04-25):** Original spec extended approval_queue with `proposal_type='publish_brief'` rows. Sankofa Council rejected: that overloads the approval semantics, contaminates `/queue` / `find_latest_pending` / `count_pending`, and creates a real misroute bug where a stray `yes confirm` reply to a publish-brief message would silently flip the row to `approved` without any Notion write. In-memory dict avoids the bug entirely (different storage = no overlap with approval_queue's `find_by_telegram_msg_id`).

### Data flow

```text
07:30 MT publish_brief_tick:
  for each post in today's Queued list:
    msg_id = send Telegram message (notifier.send_message returns int|None)
    if msg_id is not None:
      _PUBLISH_BRIEF_WINDOWS[msg_id] = {
        notion_page_id: <id>,
        title: <title>,
        platform: 'LinkedIn' | 'X',
        chat_id: <chat>,
        ts_sent: time.time(),
      }
  evict any entries older than 24h before populating new ones

User replies "posted" or "skip" to one of those per-post messages:
  process_telegram_update -> handle_publish_reply (runs after handle_approval_reply,
    so existing reply-to-proposal flow stays intact; runs before handle_naked_approval)
    if reply_to_msg_id is None: return False
    if first_word not in (POSTED_ALIASES | SKIP_ALIASES): return False
    entry = _PUBLISH_BRIEF_WINDOWS.get(reply_to_msg_id)
    if entry is None: return False (let other handlers try; harmless miss)
    notion_status = read current Notion Status
    if notion_status in ('Posted', 'Skipped'):
      reply f"Already marked {notion_status} in Notion."
      write task_outcomes row (single, captures the no-op)
      _PUBLISH_BRIEF_WINDOWS.pop(reply_to_msg_id, None)
      return True
    target = 'Posted' if first_word in POSTED_ALIASES else 'Skipped'
    notion.update_page(entry['notion_page_id'], properties={
        "Status": {"select": {"name": target}}
    })
    write task_outcomes row
    _PUBLISH_BRIEF_WINDOWS.pop(reply_to_msg_id, None)
    reply f"Marked {target}: {entry['title'][:60]}"
    return True
```

**Idempotency on the dict:** because the entry is evicted on first successful handle, a second tap finds `entry is None` and the handler returns False. No double-write. If a stale dict entry survives (e.g., container hot-reload re-populated), the Notion-Status read-before-write still catches "already Posted/Skipped" and no-ops.

### Files touched

| File | Change |
|---|---|
| `orchestrator/state.py` | Add `_PUBLISH_BRIEF_WINDOWS: dict[int, dict] = {}` next to `_PENDING_FEEDBACK_WINDOWS`. Module-level singleton. |
| `orchestrator/publish_brief.py` | Capture telegram_msg_id from `send_message` return; populate `_PUBLISH_BRIEF_WINDOWS` for each per-post message; evict entries older than 24h on each tick; append a one-line `Reply \`posted\` or \`skip\` to mark this post.` footer to each per-post message. |
| `orchestrator/notifier.py` | Verify `send_message` returns the message id. If it currently returns None, change it to return `int \| None` (the Telegram API response already contains `result.message_id`). |
| `orchestrator/handlers_approvals.py` | Add `handle_publish_reply(text, chat_id, first_word, reply_to_msg_id)`. Add `POSTED_ALIASES = {"posted", "published", "done"}` and `SKIP_ALIASES = {"skip", "skipped", "pass"}`. Reuse case-folding pattern (compare against `first_word.lower()`). |
| `orchestrator/handlers.py` | Wire `handle_publish_reply` into `process_telegram_update`. Order: AFTER `handle_pending_feedback_tag` and `handle_approval_reply` (so existing flows still work), BEFORE `handle_naked_approval`. Why: `posted` and `skip` are NOT in APPROVE_ALIASES or REJECT_ALIASES, so `handle_approval_reply` will return False on these words and fall through cleanly. |
| `orchestrator/episodic_memory.py` | No code change. Reuse `start_task` + `complete_task`. |
| `orchestrator/tests/test_publish_reply.py` | NEW. 5 tests (see Test plan section). |

**No DB migration. No new tables. No approval_queue change.**

### State lifecycle for `_PUBLISH_BRIEF_WINDOWS`

`(send brief)` → entry inserted → `(reply received)` → entry evicted on success OR (`24h elapsed`) → entry evicted by next tick's prune.

No persistent storage. The container hot-reload risk is acceptable: brief sends at 07:30, Boubacar typically replies within hours. A restart between send and reply means he flips one Notion record manually that day. No data loss (Notion remains the source of truth).

The Sankofa Council's earlier draft proposed reusing `approval_queue`. Rejected because:
1. `approval_queue` semantically holds *proposals awaiting decision*. Publish-brief messages are not proposals.
2. Existing consumers (`/queue`, `count_pending`, `find_latest_pending`) would surface publish_brief rows incorrectly.
3. A stray `yes confirm` reply to a publish-brief message would call `_aq_approve` and silently flip the row without Notion write. Real bug. In-memory dict avoids it: `find_by_telegram_msg_id` returns nothing for these msg_ids.

### task_outcomes shape

Each reply writes one row, in two calls (start then complete) since the existing `episodic_memory` API has no single-shot helper:

```python
from episodic_memory import start_task, complete_task
out = start_task(crew_name='griot', plan_summary=f"publish:{notion_page_id}:{action}")
complete_task(out.id,
              result_summary=f"{action} via Telegram reply to msg {reply_to_msg_id}",
              total_cost_usd=0.0,
              llm_calls_ids=[])
```

Action is `posted` or `skipped`. The plan_summary prefix `publish:<page_id>:` lets Phase 5 dedupe by Notion page id if it cares. We accept the small inefficiency of two DB calls; refactoring to a one-shot helper is out of scope.

### Idempotency contract

The check has TWO layers:

1. **Dict-eviction layer.** First successful handle evicts the entry. A second tap finds nothing, handler returns False, no double-write.
2. **Notion read-before-write layer.** Even if the dict entry survives (rare: hot-reload, restart-then-tap-fast), read Notion Status first. If `Posted` or `Skipped` already, no-op the update_page call, write one task_outcomes row capturing the no-op, evict the dict entry. Reply `Already marked {status} in Notion.`

Both layers are idempotent in the no-op direction. Notion `select` writes are also idempotent at the API layer, so even if both layers fail the worst case is a duplicate task_outcomes row.

### Brief message change

Each per-post message gets one extra line at the bottom, before the existing `Notion: ...` link:

```text
1. X: One constraint nobody has named yet

[draft body]

Tap to publish: https://twitter.com/intent/tweet?...
Reply `posted` or `skip` to mark this post.
Notion: https://www.notion.so/...
```

The header message gets no change.

### Empty-brief case

When there are no posts queued for today, `_format_empty_brief` is sent. **No approval_queue rows are written and no reply hint is shown.** There is nothing to mark.

### Weekend case

Brief skips on weekends. No approval_queue rows. Identical to today's behavior.

### Notion API write

Status update payload (already verified live for griot_scheduler):

```python
notion.update_page(page_id, properties={
    "Status": {"select": {"name": "Posted"}}  # or "Skipped"
})
```

No other property writes. Posted-Date timestamp lives in the Notion page's last_edited_time and in `task_outcomes.created_at`.

## Test plan

6 unit tests in `tests/test_publish_reply.py`:

1. **happy_path_posted.** Reply `posted` to a brief msg present in the dict. Notion update_page called with Status=Posted; one task_outcomes row written; dict entry evicted; reply `Marked Posted: <title>`.
2. **happy_path_skip.** Reply `skip`. Status=Skipped, otherwise same.
3. **idempotent_double_reply.** Two `posted` replies to the same msg. First call processes normally. Second call: dict entry is gone, handler returns False (no Notion call, no second task_outcomes row).
4. **out_of_band_notion_flip.** Notion Status is already Posted when reply arrives. Handler reads Notion, sees Posted, evicts dict, writes ONE task_outcomes row, replies `Already marked Posted in Notion.` (no second update_page).
5. **stray_yes_reply_to_publish_brief.** Reply `yes` to a brief msg present in the dict. `handle_approval_reply` runs first, calls `find_by_telegram_msg_id` (returns None because we never wrote to approval_queue), returns False. `handle_publish_reply` runs, but `yes` is not in POSTED_ALIASES or SKIP_ALIASES, returns False. Notion never touched. Dict entry preserved (window stays open). This is the bug the Council caught.
6. **multi_post_day.** Brief sent 2 messages, both in dict. Reply `posted` to message 1. Notion page 1 flipped, dict entry 1 evicted. Reply `skip` to message 2. Notion page 2 flipped to Skipped, dict entry 2 evicted. Independent.

Plus 1 manual integration check on VPS post-deploy via `/trigger_heartbeat publish-brief` (verifies dict is populated; not automated).

## Deploy plan

1. Branch off `main` at commit `b5a04a6`.
2. Implement.
3. Tests pass locally + in container.
4. SCP to VPS.
5. Restart `orc-crewai`. Manual trigger of publish brief (populates the dict for any Queued posts; today is Saturday so none expected; verify with `/queue` and dict introspection).
6. On Monday morning real fire, watch:
   - Telegram brief lands.
   - Reply "posted" to the brief.
   - Verify Notion Status flips to Posted in the Content Board.
   - Verify task_outcomes row appears via `/outcomes griot 1`.
7. Roadmap session log entry.
8. Commit, PR, merge, nsync.

## Rollback

Single commit revert reverts the module changes. No persistent state to clean (dict is in-memory). If catastrophic, `savepoint-pre-atlas-m1-2026-04-25` tag.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| `send_message` does not return telegram_msg_id reliably | Verify in `notifier.py`; modify to return `int \| None` from the Telegram API response (`result.message_id`). |
| Reply lands on the header message (no dict entry) | `_PUBLISH_BRIEF_WINDOWS.get(reply_to_msg_id)` returns None. Handler returns False. Existing handlers run. No regression. |
| User types `posted` without replying to anything | `reply_to_msg_id` is None. Handler returns False at the first check. No false positive. |
| Multiple posts on the same day, user replies to wrong one | Posts are numbered (1., 2., 3.). User's reply target gives unambiguous dict lookup. Worst case: they reply `skip` to the wrong post; they edit Notion manually to fix. |
| Container restart between brief send and reply | Dict is empty after restart. Handler returns False on the reply. Boubacar flips Notion manually for that day. Cosmetic loss, not a data loss. Acceptable per Sankofa Council. |
| Stray `yes confirm` reply to a publish-brief message | `handle_approval_reply` calls `find_by_telegram_msg_id` against approval_queue. We never wrote there. Returns None. `handle_naked_approval` runs but matches against `find_latest_pending`, not the brief msg. The brief reply harmlessly falls through. No misroute. |
| ALLOWED_USER_IDS scoping | Inherits from existing `process_telegram_update` filter. No new gate needed. |

## Out of scope (for M1)

- Edit-after-publish ("edited" keyword); Phase 5 territory
- Multi-day batches
- Mark-all-skipped
- Buttons (cosmetic; reply-text is simpler and matches existing approve flow)
- M2 Skip self-heal (separate roadmap milestone)

## Cross-references

- Roadmap: `docs/roadmap/atlas.md` § M1
- Notion schema: memory `reference_notion_content_board_schema.md`
- Substrate gate pattern: memory `feedback_substrate_gates_before_callbacks.md`
- Schema-first rule: memory `feedback_inspect_notion_schema_first.md`
- Phase 1 approval pattern: `orchestrator/handlers_approvals.py:handle_approval_reply`
- Phase 3.75 publish brief: `orchestrator/publish_brief.py`
- Phase 1 spec: `docs/superpowers/specs/2026-04-24-phase-1-episodic-memory-and-approval-queue-design.md`
