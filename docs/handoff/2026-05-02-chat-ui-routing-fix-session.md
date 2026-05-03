# Session Handoff - Chat UI Overhaul + Content Board Routing Fixed - 2026-05-02/03

## TL;DR

8-hour session. Started with 3 live bugs (chat hallucinations, Haiku running instead of Sonnet, no confirm buttons). Ended with the full content board draft pipeline working end-to-end for the first time. Cost: ~$50 in Claude Code session tokens (see cost discipline memory). agentsHQ itself was $1.14.

## What was built / changed

**Chat hallucination fix:**
- `orchestrator/handlers_chat.py`: ABSOLUTE RULES system prompt block, `_sanitize_history_for_model()`, tool result renamed to AWAITING_USER_CONFIRMATION
- `scripts/chat_healthcheck.py`: v2 with 4 probes including write-gate hallucination check

**Haiku/Sonnet fix (commit 1779945):**
- `orchestrator/llm_helpers.py`: `call_llm(model_key=)` param, deprecated import-time constants with `_DEPRECATED_CONST_SENTINEL`, `_resolve_model` rewrite, `response._resolved_model` attached
- `orchestrator/handlers_chat.py`: 5 call sites changed from `model=ATLAS_CHAT_MODEL` to `model=None, model_key="ATLAS_CHAT_MODEL"`
- `orchestrator/session_compressor.py`: 1 site changed to `model_key="HELPER_MODEL"`
- `orchestrator/tests/test_llm_helpers_resolve.py`: NEW, 11 unit tests
- `orchestrator/app.py`: `model: Optional[str] = None` added to `_AtlasChatResponse` (commit c1a9a6f)

**Chat UI fix (the big one):**
- Root cause: `/chat/` is `thepopebot/chat-ui/index.html` (different app from `/atlas/`)
- `/chat/` had no `actions` rendering at all: buttons were never built
- `thepopebot/chat-ui/index.html`: added `actions` param to `appendMessage`, confirm/cancel fetch handlers, CSS for buttons, `requestAnimationFrame` scroll
- `thepopebot/chat-ui/atlas-chat.js`: fixed `showDashboard` init timing bug (cached-token auto-login fired before atlas-chat.js loaded), removed `_updateModelFooter` call, textarea height reset after send, auto-resize listener
- `thepopebot/chat-ui/atlas.html`: version bumped through `v=20260503a` to `v=20260503d`
- `thepopebot/chat-ui/atlas.css`: `.chat-model-footer { display: none }`
- `thepopebot/chat-ui/nginx.conf`: removed `$uri/` from `try_files` (was serving index.html instead of atlas.html for `/atlas/` route)
- `docker-compose.thepopebot.yml`: split `nginx-static` into `nginx-chat` and `nginx-atlas` (Traefik conflict)

**Content board routing fix:**
- `orchestrator/router.py`: moved content board check to ABSOLUTE TOP of `_classify_raw()` before CRM shortcut. CRM shortcut fires on "show me" + "draft": was intercepting "Show me all posts from the Notion Content Board with status Draft"
- `orchestrator/router.py`: `classify_task()` now extracts `CURRENT REQUEST:` from engine history format before classifying (engine injects conversation history into `enriched_task` but classifier receives raw `task_request`)
- `orchestrator/crews.py`: `build_content_draft_crew()`: new crew fetches Notion Draft posts, picks one LinkedIn post, writes 2 variations in Boubacar's voice, returns inline without touching Notion status
- `orchestrator/crews.py`: `"social_crew"` registry entry now maps to `build_content_draft_crew`
- `outputs/README.md`: NEW: satisfies folder governance hook

## Decisions made

- `/chat/` and `/atlas/` are completely separate apps. Always ask which URL before debugging chat UI.
- Content board status is "Draft" (16 posts), not "Idea" (0 posts). The "Idea" status does not exist.
- agentsHQ only burned $1.14 today. The $50 was Claude Code session tokens, not OpenRouter. No config change needed to agentsHQ routing.
- `thepopebot-event-handler` uses OpenRouter with Sonnet 4.5 for GitHub webhooks: not the burn source today but worth watching.
- Router debugging rule: always test `classify_task()` inside the container with the EXACT failing string from logs, not a paraphrase.

## What is NOT done (explicit)

- Capability-routing migration (chat to `agents.select_by_capability` instead of key-based resolution): deferred, separate week-long ticket, track in roadmap
- Boubacar's "approve/reject/enhance" flow after seeing a draft post: the crew returns the draft, but the approve/reject/queue actions aren't wired yet
- `/chat/` still shows Confirm button on the initial send turn (before content is shown). Boubacar flagged this but deferred as non-critical
- `thepopebot-runner` is crash-looping (config error, not burning money): needs separate fix

## Open questions

- What does Boubacar want to do with the `design_upgrade/` project? It has 7 phases of work from another session. No one asked for it explicitly this session.
- Does the "approve 1 / reject / enhance: [feedback]" response format in the crew output need to be wired to actual Notion status updates and queue actions?

## Next session must start here

1. Test `/chat/` with "Draft one LinkedIn post from the content board": verify crew returns 2 full post variations (not CRM result)
2. If working: wire "approve 1" / "reject" / "enhance: feedback" responses to actual Notion status flips and content_review_crew
3. Fix the `thepopebot-runner` crash loop (config error: "Cannot configure runner, already configured")
4. Run `/compact` if context is already large: this session cost $50; start fresh

## Files changed this session

```
orchestrator/
  handlers_chat.py       -- hallucination fix, model_key migration, crew routing hints
  llm_helpers.py         -- model_key param, sentinel, _resolve_model rewrite
  session_compressor.py  -- model_key="HELPER_MODEL"
  app.py                 -- model field on _AtlasChatResponse
  engine.py              -- (read only, not changed)
  router.py              -- content board check moved to top, CURRENT REQUEST extraction
  crews.py               -- build_content_draft_crew, social_crew registry update
  tests/test_llm_helpers_resolve.py  -- NEW, 11 tests

thepopebot/chat-ui/
  index.html             -- actions rendering, confirm/cancel handlers, CSS, larger textarea
  atlas-chat.js          -- init timing fix, textarea height, no model footer call
  atlas.html             -- version v=20260503d
  atlas.css              -- hide .chat-model-footer
  nginx.conf             -- remove $uri/ from try_files

docker-compose.thepopebot.yml  -- Traefik nginx-chat/nginx-atlas split
outputs/README.md              -- NEW
docs/roadmap/atlas.md          -- session log appended
docs/handoff/this file

memory/
  feedback_chat_ui_ask_which_url.md        -- NEW
  feedback_router_debugging_discipline.md  -- NEW
  feedback_session_cost_discipline.md      -- NEW
  feedback_container_deploy_protocol_v2.md -- updated: SCP thepopebot/chat-ui/ rule
```
