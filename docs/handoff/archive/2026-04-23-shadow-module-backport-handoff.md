# Session Handoff: Shadow Module Backport

**Date created:** 2026-04-22 (evening session)
**Target execution date:** 2026-04-23 or later (fresh, rested session)
**Estimated time:** 3 to 4 hours focused, or two 90-minute halves
**Risk:** High. This flips the Dockerfile entrypoint in production. Must not break browser chat, Telegram polling, Claude Code, or n8n.

---

## Context from the previous session (2026-04-22)

A full 8-phase deep code review was delivered (see code_review_20260422.md at repo root). Steps 0 through 6 of the action plan shipped in 6 commits (merged to origin at 1a38b0e):

1. P0 security fixes. Port 8000 + 5432 bound to 127.0.0.1, UFW firewall active on VPS, 7 routes gained Depends(verify_api_key), verify_api_key is fail-closed, hardcoded "fallback-secret" JWT default removed, CORS narrowed.
2. handlers_doc.py completed (all 5 emoji handlers now implemented).
3. router_log migration applied + writer pointed at local Postgres.
4. LaunchVercelAppTool hardened (no more shell=True).
5. _trigger_evolution now has entry/skip/exit logging.
6. Metaclaw container decommissioned and archived on VPS at /root/_archive_20260423/metaclaw (sunset 2026-04-29).
7. Misc cleanup: send_diagram_email.py deleted, duplicate hyperframes doc removed, VPS IP env-driven, legacy task_queue table dropped, Dockerfile no longer copies tests/.

**What was NOT shipped:** the big one, flipping the Dockerfile entrypoint from `uvicorn orchestrator:app` to `uvicorn app:app`. That is this handoff.

**Current state:**
- Dockerfile CMD: `uvicorn orchestrator:app --host 0.0.0.0 --port 8000 --log-level info`
- Live module: `orchestrator/orchestrator.py` (2,748 lines, hardened but still a monolith)
- Dormant modules: `app.py`, `engine.py`, `handlers.py`, `handlers_chat.py`, `handlers_doc.py`, `worker.py`, `state.py`, `constants.py`, `schemas.py`, `utils.py`, `health.py`
- The shadow modules form a closed island: only `utils.sanitize_text` and `health.health_registry` are imported into the live path.

---

## Why not finish it on 2026-04-22

The shadow modules are approximately 40 percent of the monolith's functionality. A naive flip would regress:

1. The rich `run_chat` with Simpsons persona + 4 tools (query_system, retrieve_output_file, save_memory, forward_to_crew) + history loading + memory injection. Shadow version is a 20-line generic CrewAI wrapper.
2. Six slash commands: `/cost`, `/projects`, `/status <job_id>`, `/lessons`, `/purge-lesson`, `/scan-drive`. Shadow has only `/switch` and a minimal `/status`.
3. Praise/critique detection regex drift.
4. Compound email follow-up after non-chat tasks.
5. Hunter report email.
6. `_trigger_evolution` call from the background job.
7. `extract_and_save_learnings` call on success.
8. Telegram polling loop 3-attempt deleteWebhook retry + 401 halt.
9. `_shortcut_classify` and `_classify_obvious_chat` drift. The shadow versions violate rules from docs/routing-architecture.md.

These were written deliberately in the monolith. The session that flips must port every one first.

---

## Required reading before starting

Read these three files, in order, before editing anything:

1. `docs/refactor-status.md` at the repo root. Has the ordered 10-step plan with gap-by-gap detail.
2. `docs/routing-architecture.md`. Explicitly names the five critical rules around `_shortcut_classify`, `_classify_obvious_chat`, Haiku model slug, notion_capture LLM, and `extract_metadata` call pattern. Rule 4 says "never expand `_classify_obvious_chat` with length checks or prefix lists" and the shadow version in handlers.py violates that.
3. `code_review_20260422.md` at the repo root. Full review context, especially the P1-1 section with the duplicate-symbol table.

---

## The plan (ordered, no skipping)

**Step 0: Save point.**

```bash
git tag savepoint-pre-shadow-backport-2026-04-23
git push origin savepoint-pre-shadow-backport-2026-04-23
```

**Step 1: Align the classifiers.** Highest risk, touch first while fresh.

- In `handlers.py`, delete the existing `_shortcut_classify` and `_classify_obvious_chat` implementations.
- Copy the monolith's versions from `orchestrator.py:1227-1259` verbatim. The monolith uses `router._keyword_shortcut` and a tight greeting allowlist (hi, hey, hello, thanks, thank you, morning, good morning, good evening).
- Update `process_telegram_update` in handlers.py to call the monolith's shortcut-first-then-obvious-chat-then-classify_task sequence, same as orchestrator.py:1889-1904.

**Step 2: Port the rich run_chat.**

- In `handlers.py` (or a new `handlers_chat_rich.py`), replace the generic 20-line `run_chat` with the monolith's 330-line version from `orchestrator.py:305-637`.
- This includes: Simpsons persona system prompt, 4 tool definitions (query_system, retrieve_output_file, save_memory, forward_to_crew), tool call handling, conversation history loading from Postgres (limit=10, strip trailing assistant messages), OpenAI client via OpenRouter.
- Keep the memory.query_memory injection (orchestrator.py:1913-1926) at the caller site in process_telegram_update.

**Step 3: Port the 6 slash commands to `handlers_commands.py` (new file).**

One function per command. Call them from the main dispatch in handlers.py. Source lines:
- `/scan-drive`: orchestrator.py:1685-1699
- `/lessons [task_type]`: orchestrator.py:1701-1716
- `/purge-lesson [id]`: orchestrator.py:1718-1729
- `/status [job_id]`: orchestrator.py:1731-1755 (replace the minimal handlers.py version)
- `/projects`: orchestrator.py:1757-1785
- `/cost [days]`: orchestrator.py:1787-1839

All use `memory._pg_conn()` or query llm_calls/job_queue directly. Good chance to fold DB helpers here.

**Step 4: Expand worker.py.**

Current `worker.py` is 91 lines. The monolith's `_run_background_job` is 158 lines. Missing pieces to add:
- Compound email follow-up when classification has `has_email_followup=True` (orchestrator.py:1127-1142)
- Hunter task email via `notifier.send_hunter_report` (orchestrator.py:1145-1151)
- `_trigger_evolution` call in finally block (orchestrator.py:1170-1178)
- `extract_and_save_learnings` call in finally block (orchestrator.py:1183-1196)
- `_last_completed_job` bookkeeping from state.py (orchestrator.py:1115-1121). Both old and new paths must share this dict during the transition.

**Step 5: Align praise/critique regex.**

Merge the two versions:
- Monolith word lists at orchestrator.py:1266-1277 (_PRAISE_SIGNALS and _CRITIQUE_SIGNALS).
- Shadow handlers_chat.py uses regex patterns with emoji support.

Pick one. Recommend: union of both. Write tests if time allows.

**Step 6: Harden telegram_polling_loop in handlers.py.**

Current shadow version at handlers.py:135-160 is a single-attempt polling loop. Replace with the monolith's version at orchestrator.py:1945-1992:
- 3-attempt deleteWebhook retry with 2s sleep between attempts
- Warning log if webhook not cleared after 3 tries
- 401 response stops the loop (invalid token)
- Non-401 errors sleep 5s and retry
- 30s timeout on the long-poll itself (already present in shadow)

**Step 7: Rewrite the richer _query_system in utils.py.**

Current shadow is 27 lines. Monolith at orchestrator.py:231-302 is 72 lines. Add:
- Agent descriptions (not just names)
- Recent output files section (list last 10 from AGENTS_OUTPUT_DIR)
- Infrastructure block (VPS IP env, Public URL, Telegram bot, n8n, GitHub, memory store)

**Step 8: Fold in DB connection consolidation.**

During the above ports, every inline `psycopg2.connect(...)` call becomes `memory._pg_conn()` or `db.get_local_connection()`. Net: fewer lines in new modules than equivalent lines in orchestrator.py.

**Step 9: Local smoke test.**

Run locally without flipping:

```bash
cd d:/Ai_Sandbox/agentsHQ
# Copy VPS env vars
scp root@agentshq.boubacarbarry.com:/root/agentsHQ/.env .env.test
# Run shadow on a different port
cd orchestrator
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

Test (in another terminal):
```bash
# With the API key from .env.test
export KEY=$(grep ORCHESTRATOR_API_KEY .env.test | cut -d= -f2)
curl http://localhost:8001/health
curl -X POST http://localhost:8001/run-sync -H "Content-Type: application/json" -H "X-Api-Key: $KEY" -d '{"task":"hi"}'
curl -X POST http://localhost:8001/run-sync -H "X-Api-Key: $KEY" -d '{"task":"what is 2+2"}'  # rich chat path
curl "http://localhost:8001/classify?task=find+me+dentists+in+84095" -H "X-Api-Key: $KEY"
```

Expect: same responses as the monolith produces.

**Step 10: Flip the Dockerfile entrypoint.**

```diff
- CMD ["uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
+ CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
```

**Step 11: Deploy and verify.**

```bash
scp orchestrator/*.py root@agentshq.boubacarbarry.com:/root/agentsHQ/orchestrator/
scp orchestrator/Dockerfile root@agentshq.boubacarbarry.com:/root/agentsHQ/orchestrator/Dockerfile
ssh root@agentshq.boubacarbarry.com "cd /root/agentsHQ && docker compose up -d --build orchestrator"
```

Note: a rebuild is required because Dockerfile changed.

Verify (use the check list from code_review_20260422.md):
1. /health returns 200
2. /chat via Traefik returns 200
3. /api/orc/health via Traefik returns 200
4. /run-sync unauth returns 401
5. /run-sync authed returns 200 AND produces a chat-style response (with Simpsons persona)
6. Send a real Telegram message. Bot replies.
7. /inbound-lead accepts a synthetic payload.
8. /cost via Telegram shows ledger data.
9. /projects via Telegram shows recent jobs.
10. An emoji command (filing or flag) completes a doc routing cycle.

**Step 12: Keep orchestrator.py in repo for one week.**

Do NOT delete orchestrator.py after the flip. Leave it as a rollback reference for at least one week. If everything runs clean through Sunday 2026-04-29 or so, then rename `app.py` → `orchestrator.py` so the Dockerfile CMD can stay at `uvicorn orchestrator:app` permanently and delete the old one.

Rollback if anything breaks: `git reset --hard savepoint-pre-shadow-backport-2026-04-23` and `docker compose up -d --build orchestrator`.

---

## Files you will modify

- `orchestrator/handlers.py` (major: classifiers, telegram loop, dispatch logic)
- `orchestrator/handlers_chat.py` (minor: align regex)
- `orchestrator/handlers_commands.py` (new file: 6 slash commands)
- `orchestrator/worker.py` (major: compound workflows, evolution, learning, last-job)
- `orchestrator/utils.py` (minor: rewrite _query_system)
- `orchestrator/app.py` (minor: wire in new handlers_commands, verify route list matches orchestrator.py)
- `orchestrator/Dockerfile` (1 line: CMD swap)

Files you will NOT touch:
- `orchestrator/orchestrator.py` (the monolith stays as rollback for one week)
- `orchestrator/router.py` (protected, critical rules)
- `orchestrator/crews.py`, `agents.py`, `tools.py` (unchanged)
- `orchestrator/research_engine.py`, `kie_media.py`, `usage_logger.py`, `content_board_reorder.py`, `scrub_titles.py` (recent, protected)
- `docs/routing-architecture.md` (reference, not modified)
- `skills/**` (unchanged)

---

## Deploy protocol reminder

From memory `feedback_container_file_sync`: the orc-crewai container is NOT volume-mounted. git pull alone does not update running code. Always:

```bash
scp orchestrator/FILE.py root@agentshq.boubacarbarry.com:/root/agentsHQ/orchestrator/FILE.py
ssh root@agentshq.boubacarbarry.com "docker cp /root/agentsHQ/orchestrator/FILE.py orc-crewai:/app/FILE.py"
ssh root@agentshq.boubacarbarry.com "docker compose -f /root/agentsHQ/docker-compose.yml restart orchestrator"
```

For the Dockerfile flip, a rebuild is required:

```bash
ssh root@agentshq.boubacarbarry.com "cd /root/agentsHQ && docker compose up -d --build orchestrator"
```

Pre-commit will catch em dashes. Windows git push is unreliable: if it hangs, use the bundle-via-SSH fallback (see commit 5817904 message for the working pattern, or just commit and push from the VPS side).

---

## Success criteria for this session

The session is done when:
1. Dockerfile uses `CMD ["uvicorn", "app:app", ...]`
2. All 12 verification checks pass post-deploy
3. A real Telegram round-trip completes with Simpsons-persona chat response
4. /cost shows ledger data over Telegram
5. An emoji command succeeds end-to-end
6. orchestrator.py is still in the repo (not deleted)
7. Rollback tag exists on origin
8. Memory entry updated: `project_shadow_module_backport.md` → status COMPLETE with commit hash

If any check fails, rollback is one command.
