# Session Handoff - Atlas /atlas/chat Routing Fix - 2026-04-28

## TL;DR

Fixed three independent bugs that caused "What's in my approval queue?" to route to a 400-second app-building crew run instead of returning a direct 2-second answer. The primary fix was adding live approval queue data to `_query_system()` - the model had no accurate tool for queue queries, so it reached for `forward_to_crew`. A deterministic pre-filter was added as structural protection. An HTML rendering bug and JSON code-fence leak were also closed. All three locations are at commit `5455ca7`, VPS is healthy, and live test confirms 2.5s reply with clean plain-text output.

## What was built / changed

- `orchestrator/handlers_chat.py`
  - Deterministic READ-intent pre-filter in `run_atlas_chat()` (lines ~631-680): 28 patterns trigger `_query_system()` directly, bypassing LLM tool-choice entirely
  - `_extract_reply()`: strips ` ```json ``` ` code fences before JSON parse; guards against raw `<!DOCTYPE html>` in both JSON-wrapped and plain-text paths
  - `query_system` tool description: now explicitly lists "approval queue, pending items" with usage examples
  - `forward_to_crew` tool description: now explicitly excludes system-state queries
  - System prompt: updated to accurately describe what `query_system` retrieves

- `orchestrator/utils.py`
  - `_query_system()`: now calls `approval_queue.list_pending()` and formats each pending item with id/crew/proposal_type/title

- VPS `/root/agentsHQ/.env` (NOT committed - runtime config only)
  - Added: `CHAT_TEMPERATURE=0.7`, `ATLAS_CHAT_MODEL=anthropic/claude-sonnet-4-6`, `CHAT_MODEL=anthropic/claude-sonnet-4.6`, `CHAT_SANDBOX=false`
  - These were missing and caused container to crash on restart with `ValueError: float("")`

## Decisions made

- Deterministic pre-filter is the structural fix; description changes (Fixes A+B) are secondary reinforcement only. Per Karpathy: "don't be clever" - keyword match beats LLM disambiguation for read/write routing decisions.
- Sankofa Council + Karpathy principles must run BEFORE any code on RCA tasks. Boubacar corrected this mid-session; it is now a saved feedback rule.
- The 403-second/ZIP incident reported in the session context happened via the OLD `/run-async` path (before today's session), not `/atlas/chat`. The two bugs were separate. `/run-async` misrouting is no longer reachable for web chat.
- Model slugs in `.env` are a stop-gap; long-term they belong in the DB config layer (M11b agent_config). Do not move them yet.

## What is NOT done (explicit)

- VPS orphan archive (`/root/_archive_20260421/`) - sunset was 2026-04-28, nothing broke, safe to delete next session
- `_READ_PATTERNS` list is a static tuple - if new phrasings appear that misroute, add them to the tuple in `handlers_chat.py`. No test suite exists for this list yet.
- `run_chat()` (Telegram path) does NOT have the pre-filter - only `run_atlas_chat()` (web path) does. Telegram still uses the 4-tool LLM choice. Queue questions on Telegram will correctly use `query_system` with the improved description, but they are not structurally protected. Low priority since Telegram has a different UX flow.

## Open questions

- Should `CHAT_MODEL` / `ATLAS_CHAT_MODEL` be migrated to the M11b `agent_config` DB table? Currently a .env stop-gap. See `feedback_chat_model_env_vs_db_config.md`.
- The VPS orphan archive at `/root/_archive_20260421/` is past its 2026-04-28 sunset. Verify nothing in production depends on it, then delete.

## Next session must start here

1. Check VPS orphan archive: `ssh root@agentshq.boubacarbarry.com "ls /root/_archive_20260421/"` - if still there, delete it (sunset was today)
2. Verify live /atlas/chat still routes correctly: send "What's in my approval queue?" through the web UI at agentshq.boubacarbarry.com/chat and confirm reply is under 5 seconds with no JSON/HTML leakage
3. Pick up from the task backlog - see `docs/roadmap/atlas.md` for next milestone

## Files changed this session

```
orchestrator/
  handlers_chat.py   - pre-filter, _extract_reply, tool descriptions, system prompt
  utils.py           - _query_system() approval queue fetch

VPS only (not committed):
  /root/agentsHQ/.env  - CHAT_TEMPERATURE, ATLAS_CHAT_MODEL, CHAT_MODEL, CHAT_SANDBOX added
```
