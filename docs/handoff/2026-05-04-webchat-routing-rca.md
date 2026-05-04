# Session Handoff : Webchat Routing RCA : 2026-05-04

## TL;DR

Full RCA + structural fix for three webchat bugs: confirm button on every message, raw JSON leaking into chat bubble, and LLM fabricating content. Followed by a second-round routing architecture fix (LLM reformulation + clarification rules). All deployed to VPS, pushed to GitHub, pulled to local. Branch: `feat/studio-m3-production`.

## What was built / changed

- `orchestrator/handlers_chat.py`
  - Added `query_content_board` tool to `_TOOLS` list (direct Notion read, no confirm gate)
  - Added `query_content_board` dispatch handler in `run_atlas_chat` tool loop with `explicit_task_type="content_board_fetch"`
  - Hardened `_extract_reply()` : mid-prose JSON scan as last resort
  - Replaced entire TOOL DISCIPLINE section in `_SYSTEM_PROMPT_TEMPLATE`:
    - AMBIGUITY RULE: ask one clarifying question (2 options) when intent unclear
    - COMPOUND RULE: ask which action first on multi-intent requests
    - REFORMULATION RULE: LLM must rewrite task_text as clean action-verb phrase before calling forward_to_crew
    - Removed stale content board routing bullets

- `orchestrator/crews.py`
  - Added ANTI-FABRICATION RULE to `social_content` crew `task_write` task description

- `orchestrator/router.py`
  - `content_board_fetch` keywords: added `approve post`, `approve the post`, `approve queued`, `approve content`
  - `social_content` keywords: added `schedule post`, `schedule a post`, `schedule for linkedin`
  - `notion_tasks` keywords: added `analytics`, `engagement stats`, `performance stats`

## Decisions made

- **Reads never go through `forward_to_crew`** : structural rule. `query_content_board` tool handles all Notion reads with `explicit_task_type` bypassing engine classifier.
- **Pre-filters (pattern lists) rejected** : Sankofa + Karpathy both killed the `_CONTENT_READ_PATTERNS` proposal. Adds a third classifier to a system already fragile from two.
- **`explicit_task_type` is the right pattern** : LLM tool choice = classification. Pass it explicitly to engine. Engine keyword classifier is Telegram/legacy fallback only.
- **LLM reformulates before forwarding** : Engine keyword matcher gets clean action-verb phrases, not raw conversational user messages.
- **Ambiguity → ask, not guess** : System now clarifies before acting when intent is ambiguous.
- **Save point tagged** `rca-webchat-20260504` on VPS git.

## Commits
- `0e02d51` : initial structural fix (query_content_board tool + extract_reply + anti-fabrication)
- `750b933` : explicit_task_type fix (bypass engine classifier for content board reads)
- `3cc1e18` : reformulation + ambiguity + keyword patches

## What is NOT done

- Compound requests ("write AND post now") : clarification fires correctly but no single-shot compound execution path exists. Product decision needed if Boubacar wants that.
- `run_chat` (Telegram path) shares the same `_SYSTEM_PROMPT_TEMPLATE` so reformulation/ambiguity rules apply there too : but Telegram has not been re-tested post-fix.
- `analytics` / `engagement stats` routed to `notion_tasks` as closest crew : no dedicated analytics crew exists. Product gap.

## Open questions

- Does Telegram path need separate testing after routing changes?
- Should compound requests ever execute both actions in sequence, or always ask?
- Studio M3 render failures (ffmpeg zoompan errors) visible in logs : separate issue, not addressed this session.

## Next session must start here

1. Test Telegram path with a content board read: "send me post 1" via Telegram bot : confirm no confirm gate fires, correct content returned.
2. Test "approve the queued post" end-to-end : queue something first, then try to approve via chat.
3. Check Studio M3 render failures: `docker logs orc-crewai 2>&1 | grep "render failed" | tail -20` : ffmpeg zoompan errors on shorts/square renders need investigation.
4. Consider merging `feat/studio-m3-production` → `main` : M3 is working per memory entry.

## Files changed this session

```
orchestrator/handlers_chat.py   : tool surface, dispatch, system prompt, _extract_reply
orchestrator/crews.py           : social_content anti-fabrication
orchestrator/router.py          : 3 keyword patches
docs/handoff/2026-05-04-webchat-routing-rca.md  : this file
memory/feedback_webchat_confirm_gate_rca.md     : updated with full session log
```
