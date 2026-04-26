# Session Handoff: Atlas M9a + M11b Parallel Launch: 2026-04-26

## TL;DR

Long architecture session. Ran Sankofa Council twice, blue/red team, code reviewer, model research across three parallel agents. Result: M11a (3 live bug fixes + named constants) shipped at commit `6d0dcf4`. M9a (Telegram push alerts + correctness fixes) and M11b (OpenRouter capability routing for crew engine) are both ready to build in separate tabs. This handoff covers what each tab should do.

## What was built / changed this session

- `orchestrator/crews.py`: fixed malformed `"openai/anthropic/claude-sonnet-4-5"` -> `get_llm("claude-sonnet")`. Was silently 404ing every content review run.
- `orchestrator/agents.py:744`: `select_llm("voice", "high")` -> `select_llm("voice", "complex")`. Invalid complexity key silently fell through to DEFAULT_MODEL.
- `orchestrator/crews.py`: added `_IDEA_CLASSIFIER_MODEL` module-level constant.
- `orchestrator/router.py`: added `ROUTER_LLM_MODEL` constant.
- `orchestrator/memory.py`: added `LESSON_EXTRACTION_MODEL` constant.
- `orchestrator/notifier.py`: added `BRIEFING_MODEL` constant.
- `orchestrator/llm_helpers.py`: already had `CHAT_MODEL`, `ATLAS_CHAT_MODEL`, `HELPER_MODEL` env-var driven. Missing: `CHAT_SANDBOX` and `CHAT_TEMPERATURE` (M9a adds these).
- `docs/roadmap/atlas.md`: M11 milestone block added (renamed from M10a since M10 = Topic Trend Scout). Approval surface design documented. Dashboard badge added to M9b scope.
- `docs/roadmap/atlas/m9-atlas-chat-design.md`: v4 full spec written. Model strategy, architecture decisions, all milestone details, system prompt, build checklist.
- Save points: `savepoint-pre-atlas-m9-design-2026-04-26`, `savepoint-pre-m10a-bug-fixes-2026-04-26`
- Commits: `6d0dcf4` (M11a bugs), `91312cd` (badge + approval surfaces), `0e25942` (llm_helpers centralize)

## Decisions made

- OpenRouter is the single routing layer for ALL providers. Not locked to Anthropic. Best model for each job across Anthropic, Google, OpenAI, DeepSeek, xAI, Mistral, Qwen.
- `TASK_MODEL_MAP` approach rejected. `COUNCIL_MODEL_REGISTRY` + `select_by_capability()` is the correct pattern: extend it to the crew engine (M11b), not a new third system.
- Gemini default rejected for chat layer. Haiku 4.5 stays as default (tool-use reliability risk > $30/mo cost delta).
- M11 renumbered (was M10a, but M10 = Topic Trend Scout already existed in roadmap).
- Three approval surfaces: Telegram push (M9a), Atlas dashboard card (live since M8), web chat (M9b). Dashboard badge for pending count added to M9b scope.
- `handlers_chat.py` already uses `llm_helpers.CHAT_MODEL`. M9a's Fix 2 is partially superseded: only `CHAT_SANDBOX` + `CHAT_TEMPERATURE` need adding to `llm_helpers.py`.
- Update roadmap BEFORE writing code so parallel agents see current state (new hard rule).

## What is NOT done

- M9a: all 9 items on the build checklist (Postgres leak, structured JSON return, double-send fix, system prompt upgrade, docker-compose allowlist, Telegram buttons, smoke test).
- M11b: ROLE_CAPABILITY migration in `agents.py` (replaces ROLE_MODEL with capability-based selection).
- M11c: research_engine.py two-phase rewrite (Perplexity + Firecrawl).
- M11d: weekly model review agent.
- M9b, M9c: web chat panel, artifact rendering.

## Open questions

None blocking. Both M9a and M11b are fully specced and ready to build.

## Next session must start here

**Two tabs, run in parallel:**

### Tab 1: M9a

Prompt:
```
Continue from docs/handoff/2026-04-26-m9a-handoff.md and docs/roadmap/atlas/m9-atlas-chat-design.md.

Context:
- Main at commit 91312cd, 266 tests passing (ignore pre-existing test_atlas_dashboard + test_doc_routing failures)
- M11a already shipped: crews.py malformed model string fixed, agents.py voice/high fixed, named constants added to router/memory/notifier
- handlers_chat.py already uses llm_helpers.CHAT_MODEL -- Fix 2 from the handoff is partially done; only CHAT_SANDBOX + CHAT_TEMPERATURE need adding to llm_helpers.py (not handlers_chat.py directly)
- llm_helpers.py has CHAT_MODEL, ATLAS_CHAT_MODEL, HELPER_MODEL -- add CHAT_SANDBOX and CHAT_TEMPERATURE there

First actions:
1. Update atlas.md M9a entry to show "IN PROGRESS" before touching any code
2. git tag savepoint-pre-atlas-m9a-$(date +%Y%m%d) && git checkout -b feat/atlas-m9a-telegram-push
3. Fix Postgres connection leaks in atlas_dashboard.py (6 functions need finally: conn.close())
4. Then: CHAT_SANDBOX + CHAT_TEMPERATURE to llm_helpers.py, run_chat() structured JSON return, double-send fix, system prompt upgrade, docker-compose allowlist, Telegram buttons, smoke test
```

### Tab 2: M11b

Prompt:
```
Continue from docs/roadmap/atlas.md M11b section.

Context:
- Main at commit 91312cd, 266 tests passing
- M11a shipped: named constants added, malformed model string fixed, voice/high bug fixed
- M11b is the ROLE_CAPABILITY migration in orchestrator/agents.py: replace ROLE_MODEL dict (4 hardcoded Anthropic aliases) with ROLE_CAPABILITY (capability tag + cost ceiling per role/complexity), rewrite select_llm() to call select_by_capability() across all 18 models in COUNCIL_MODEL_REGISTRY
- Do NOT touch handlers_chat.py, atlas_dashboard.py, handlers.py, docker-compose.yml -- those are M9a's files

First actions:
1. Update atlas.md M11b entry to show "IN PROGRESS" before touching any code
2. git tag savepoint-pre-m11b-capability-routing-$(date +%Y%m%d) && git checkout -b feat/m11b-capability-routing
3. Read orchestrator/agents.py in full (COUNCIL_MODEL_REGISTRY, ROLE_MODEL, select_by_capability, select_llm, ROLE_TEMPERATURE) before writing a single line
4. Build ROLE_CAPABILITY dict from the mapping in atlas.md M11b section, rewrite select_llm(), delete ROLE_MODEL, keep ROLE_TEMPERATURE
5. Run pytest orchestrator/tests/ --ignore=test_atlas_dashboard --ignore=test_doc_routing; all 266 must pass
```

## Files changed this session

```
orchestrator/
  agents.py          -- voice/high -> voice/complex bug fix
  crews.py           -- malformed model string fix, _IDEA_CLASSIFIER_MODEL constant
  handlers_chat.py   -- linter touched (no functional changes from this session)
  llm_helpers.py     -- already centralized (earlier commit in session)
  memory.py          -- LESSON_EXTRACTION_MODEL constant
  notifier.py        -- BRIEFING_MODEL constant
  router.py          -- ROUTER_LLM_MODEL constant

docs/
  roadmap/atlas.md                          -- M11 added, M9 updated, approval surfaces, badge
  roadmap/atlas/m9-atlas-chat-design.md     -- v4 spec (full)
  handoff/2026-04-26-m9a-handoff.md         -- existing, read for context
  handoff/2026-04-26-atlas-m9a-m11b-parallel-handoff.md  -- this file

memory/
  project_atlas_m9_m11_state.md             -- new
  feedback_update_roadmap_before_code.md    -- new
  feedback_openrouter_routing_philosophy.md -- new
  MEMORY.md                                 -- 3 new pointers added
```
