# Session Handoff - Webchat Fixes + Schedule Content Crew - 2026-05-04

## TL;DR
This session fixed 5 bugs in the agentsHQ webchat (agentshq.boubacarbarry.com/chat): confirm appearing on reads, raw JSON in chat bubbles, fabricated content from wrong crew, wrong routing for "send me post 1", and missing chat_id in two studio Telegram notifiers. We also designed and shipped a new `schedule_content_crew` that writes to the Notion Content Board instead of calling Blotato, resolving the "schedule it" ambiguity for good. All changes are on `feature/schedule-content-crew` branch, pending gate merge.

## What was built / changed

- `orchestrator/handlers_chat.py`
  - Added `query_content_board` tool (no confirm gate, read-only)
  - Dispatch handler calls `run_orchestrator(explicit_task_type="content_board_fetch")`
  - Replaced TOOL DISCIPLINE section with AMBIGUITY RULE + COMPOUND RULE + REFORMULATION RULE
  - Fixed `_extract_reply()` double-wrap JSON bug (nested JSON re-parse)
  - Added `schedule_content_crew` tool entry with reformulation example in system prompt

- `orchestrator/crews.py`
  - Added ANTI-FABRICATION RULE to `social_content` task_write description
  - Added `build_schedule_content_crew()` : pure code, no LLM agent
    - Parses date: today / tomorrow / monday / ISO string
    - Parses platform: LinkedIn / X
    - Searches Content Board by title, updates Status=Queued + Scheduled Date if found
    - Creates new record if not found
  - Registered as `"schedule_content_crew"` in CREW_REGISTRY

- `orchestrator/router.py`
  - Added `schedule_content` task type with keywords ("schedule it", "schedule this post", "schedule for today/tomorrow/monday")
  - Added to `_PRIORITY_CHECKED` set
  - Added approve keywords → `content_board_fetch`
  - Added schedule keywords → `social_content`
  - Added analytics keywords → `notion_tasks`

- `orchestrator/studio_production_crew.py`
  - Fixed `_notify_qa_fail()` : was calling `send_message(text)` missing `chat_id`
  - Commit: `5b20787`

- `orchestrator/studio_blotato_publisher.py`
  - Fixed by another agent (commit `f76ea7d`) : same missing chat_id pattern

## Decisions made

1. **"Schedule it" = Content Board, not Blotato.** Blotato only on explicit "post to Blotato" / "publish now". Product decision made by Boubacar 2026-05-04.

2. **`explicit_task_type` pattern is canonical.** LLM tool choice IS the classification. Do not re-classify downstream via engine keyword matcher. Pre-filter pattern lists are wrong (3rd classifier on a 2-classifier system).

3. **Reads never get confirm gate.** `query_content_board` bypasses via `explicit_task_type`. Only writes go through `forward_to_crew` + confirm.

4. **REFORMULATION RULE is in system prompt.** LLM must rewrite user phrasing as clean action-verb phrase before calling `forward_to_crew`. This gives engine's keyword matcher clean signal.

## What is NOT done (explicit)

- Gate has NOT yet merged `feature/schedule-content-crew` into main. Branch is on origin. Gate cron runs every 60s.
- VPS container NOT yet rebuilt with schedule_content changes. Will happen automatically after gate merges + cron triggers `orc_rebuild.sh`.
- Telegram path manual end-to-end test not done (logs confirmed correct routing logic, Boubacar agreed low priority).
- Music vault for Studio not built (`workspace/media/music/` dir missing) : separate concern.

## Open questions

- After gate merges and VPS rebuilds: test "schedule this for tomorrow" in webchat and confirm Notion Content Board gets updated.
- First Studio Short quality review : 3 Drive links in `project_studio_m3_state.md`. Need Boubacar confirmation.
- Blotato auto-post at 09:00 MT : did first one land? Check Studio Pipeline DB for Status=posted records.

## Next session must start here

1. `git fetch origin && git log origin/main --oneline -3` : confirm gate merged `feature/schedule-content-crew`
2. `docker logs orc-crewai --tail 50` (via SSH) : confirm container rebuilt with new code
3. Test "schedule this for tomorrow" in webchat, verify Notion Content Board updated
4. Check Studio Pipeline DB for any Status=posted records (Blotato auto-post confirmation)
5. If all good: no immediate work queued. Check roadmap for next task.

## Files changed this session

```
orchestrator/
  handlers_chat.py    : query_content_board tool, routing fix, _extract_reply fix, schedule_content_crew entry
  crews.py            : build_schedule_content_crew(), anti-fabrication guardrail
  router.py           : schedule_content task type + keywords
  studio_production_crew.py  : _notify_qa_fail chat_id fix (commit 5b20787, merged)
  studio_blotato_publisher.py : _send_telegram chat_id fix (commit f76ea7d, merged by other agent)
```

Pending branch: `feature/schedule-content-crew` (origin) : gate merge in progress.
