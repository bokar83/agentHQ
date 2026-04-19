# agentsHQ Routing Architecture

## What we built and why

Before April 2026, every message from Telegram and web chat was routed by keyword matching — a list of trigger phrases per task type in `router.py`. Any natural phrasing that didn't match a keyword exactly fell to `unknown_crew`, which submitted agent proposals instead of doing work.

The fix: **LLM-backed routing**. Keywords still run as a fast path for obvious matches. When keywords return `unknown`, a single Haiku call reads the message and picks the right task type from a 29-line registry of agent descriptions. Cost is ~$0.00004 per fallback call. The user can now speak naturally and the system routes correctly.

---

## How routing works (flow)

```
User message (Telegram or web chat)
        |
        v
_shortcut_classify()          -- keyword fast-path in router.py
        |
  match? --> run_orchestrator(task_type)
        |
   no match
        |
        v
_classify_obvious_chat()      -- exact greeting strings only: hi, hey, hello, thanks, good morning
        |
  is greeting? --> run_chat()
        |
   not a greeting
        |
        v
classify_task()               -- calls _classify_raw() then _llm_classify() if unknown
        |
  task_type returned
        |
        v
build_*_crew(user_request)    -- correct crew assembled and executed
```

---

## Key files

| File | Role |
|------|------|
| `orchestrator/router.py` | `_classify_raw()` keyword fast-path, `_llm_classify()` Haiku fallback, `classify_task()` combining both |
| `orchestrator/orchestrator.py` | `_classify_obvious_chat()` greeting gate, `_shortcut_classify()` keyword shortcut, main request handlers |
| `orchestrator/crews.py` | `_notion_capture_is_review()` LLM-based retrieve vs save mode for notion_capture_crew |

---

## Critical rules — do not break these

### 1. Never add `chat` back to keyword matching
Chat keywords like "help me", "what is", "how do" appear in almost every functional request. Chat is decided by `_classify_obvious_chat()` (exact greetings only) or by the LLM fallback. If you add keywords to the `chat` TASK_TYPE entry, conversational task requests will silently route to chat_crew and produce `propose_new_agent`.

### 2. Never use `_classify_raw()` where `classify_task()` is needed
`_classify_raw()` is keyword-only. `classify_task()` includes the LLM fallback. `extract_metadata()` calls `classify_task()` — keep it that way. The old pattern of calling `extract_metadata()` then `.update()`-ing the result from `classify_task()` was overwriting the LLM result with a keyword-only result. That pattern is deleted and must not return.

### 3. Model slug is `anthropic/claude-haiku-4.5` (dot, not dash)
OpenRouter uses `anthropic/claude-haiku-4.5`. Using `claude-haiku-4-5` (dashes) returns a 404 that is silently caught and falls back to `unknown`. Check this first if LLM routing stops working.

### 4. `_classify_obvious_chat()` must stay narrow
It currently matches only: `hi`, `hey`, `hello`, `thanks`, `thank you`, `morning`, `good morning`, `good evening`. Do not expand it with length checks, prefix lists, or keyword exclusions. Those heuristics blocked the LLM fallback for short natural-language task requests.

### 5. `notion_capture_crew` retrieve/save mode is decided by LLM
The function `_notion_capture_is_review()` in `crews.py` calls Haiku to determine whether the user wants to retrieve ideas or save a new one. Do not replace this with a keyword list — that approach broke repeatedly as phrasing varied.

---

## How to debug if routing breaks

**Symptom: message returns a proposal instead of doing work**
- Check container logs: `docker logs orc-crewai --tail 50`
- Look for `task_type 'unknown'` or `task_type 'chat'` for a message that should have been a functional task
- If you see `LLM router exception`: check the model slug (issue 3 above) and check that `OPENROUTER_API_KEY` is set in the container env
- Test routing directly: `docker exec orc-crewai python3 -c "from router import classify_task; print(classify_task('your message here'))"`

**Symptom: LLM router not firing (every miss goes to unknown without a log line)**
- Check that `_classify_obvious_chat()` wasn't expanded — it must not be catching the message before `classify_task()` is called
- Check the call site in orchestrator.py — `classify_task()` must be called after the obvious-chat gate, not before

**Symptom: notion_capture routes correctly but still saves instead of retrieving**
- Check `_notion_capture_is_review()` in crews.py — the LLM call uses the same `OPENROUTER_API_KEY` and model slug
- Test: `docker exec orc-crewai python3 -c "from crews import _notion_capture_is_review; print(_notion_capture_is_review('show me my ideas'))"`

**After any code change to these files:**
```bash
scp orchestrator/router.py orchestrator/crews.py orchestrator/orchestrator.py root@72.60.209.109:/root/agentsHQ/orchestrator/
ssh root@72.60.209.109 "docker cp /root/agentsHQ/orchestrator/router.py orc-crewai:/app/router.py && docker cp /root/agentsHQ/orchestrator/crews.py orc-crewai:/app/crews.py && docker cp /root/agentsHQ/orchestrator/orchestrator.py orc-crewai:/app/orchestrator.py && cd /root/agentsHQ && docker compose restart orchestrator"
```
The container is NOT volume-mounted — `git pull` alone does not update running code. Always `docker cp` after SCP.

---

## What was broken before (April 2026 fix session)

1. **7 crew name mismatches** — router emitted names not in CREW_REGISTRY, every matched task fell to unknown_crew
2. **JWT key too short** — 12-byte secret caused InsecureKeyLengthWarning on every token
3. **`notion_tasks_crew` unreachable** — crew existed but zero keywords pointed to it
4. **Notion 400 errors** — wrong property name `"Due"` (should be `"Due Date"`) and wrong filter type `"status"` (should be `"select"`)
5. **Chat layer gatekeeping** — LLM in `run_chat` explained limitations instead of forwarding to orchestrator
6. **Gmail returning IDs only** — `GWSGmailSearchTool` stopped after `messages.list`, never fetched metadata
7. **Keyword routing too brittle** — replaced with LLM fallback (this document)
8. **Model slug mismatch** — `haiku-4-5` vs `haiku-4.5` silently broke every LLM classify call
9. **`extract_metadata().update()`** — overwrote LLM-classified result with keyword-only result
10. **`_classify_obvious_chat` too broad** — length/prefix heuristic swallowed short task requests before LLM fired
