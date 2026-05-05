# Session Handoff - Chat Attachments + Sonnet Swap + Permanent Fixes - 2026-04-30 (afternoon)

## TL;DR
Long arc. Started with the recurring "Sorry, I hit an error" in `/atlas/chat`. Did a true RCA (the bug shipped 2026-04-26 and went undetected for 4 days because no probe exercised the chat). Permanently fixed both layers (backend empty-model defeat + frontend hostile 401 reload), shipped a 10-minute synthetic monitor with Telegram/email alerts, then layered on file attachments (paperclip + paste-image), swapping the chat model from Haiku-4.5 to Sonnet-4.6 via the DB config layer. Five commits to main, VPS in sync, monitor green.

## What was built / changed

**Morning: backend chat fix (commit `5b94712`):**
- [orchestrator/llm_helpers.py:21-24](orchestrator/llm_helpers.py#L21) - `os.environ.get("KEY") or _DEFAULT_MODEL`. Empty-string env vars from compose substitution no longer defeat the Python default.
- [orchestrator/startup_check.py:36-55](orchestrator/startup_check.py#L36) - post-import assertion that resolved model slugs are non-empty. Container refuses to boot if defaults somehow get bypassed.

**Morning: synthetic monitor (commit `1c7b3b0`):**
- [scripts/chat_healthcheck.py](scripts/chat_healthcheck.py) - stdlib-only probe of `/atlas/chat` + Telegram Bot API `getMe`. ~120ms when green.
- VPS systemd: `chat-healthcheck.{service,timer}` running every 10 min, logging to `/var/log/chat_healthcheck.log`, alerting via Telegram + email on failure.

**Afternoon: frontend 401 recovery (commit `5f1f14a`):**
- [thepopebot/chat-ui/atlas.js:84-160](thepopebot/chat-ui/atlas.js#L84) - `apiFetch` no longer calls `location.reload()` on 401. Pops PIN screen back over dashboard, awaits fresh JWT, retries the original request transparently. Concurrent 401s coalesce on `_reauthPromise`.

**Afternoon: chat attachments (commit `ade94bc`):**
- [thepopebot/chat-ui/atlas.html](thepopebot/chat-ui/atlas.html) - paperclip button on LEFT of textarea, hidden file input, attachment chip strip above input. Cache-bust `v=20260430b`.
- [thepopebot/chat-ui/atlas.css](thepopebot/chat-ui/atlas.css) - paperclip + chip styling.
- [thepopebot/chat-ui/atlas-chat.js](thepopebot/chat-ui/atlas-chat.js) - `_addFiles()`, `_renderChips()`, `_buildContent()`, paste-event handler. Caps: 4 files / 10MB each. Supported: image/* / application/pdf / text-like extensions.
- [orchestrator/handlers_chat.py](orchestrator/handlers_chat.py) - `_extract_text_content()`, `_summarize_attachments()` helpers. Defensive str|list handling at 3 sites (artifact-ref resolve, READ-intent pre-filter, history save). History saves text + "[attached: foo.png]" marker only - base64 payload never persisted.

**Afternoon: model swap (DB-only, no commit):**
- `agent_config` Postgres row: `ATLAS_CHAT_MODEL = anthropic/claude-sonnet-4.6`. Hot-swappable via `docker exec orc-postgres psql -U postgres -d postgres -c "UPDATE agent_config SET value='<slug>' WHERE key='ATLAS_CHAT_MODEL';"`. No rebuild needed.

**Afternoon: VPS .env hygiene (host-only, no commit):**
- Stripped CRLF line endings (whole file was Windows-style).
- Quoted two values with unquoted spaces (`SMTP_PASS`, `SIGNAL_WORKS_SENDER`).
- Backup at `/root/agentsHQ/.env.bak.crlf.20260430-*`.

**Memory:**
- New: `feedback_chat_empty_model_compose_substitution.md`, `feedback_atlas_401_reload_kills_input.md`, `reference_atlas_chat_attachments.md`, `feedback_env_shell_safety.md`
- Indexed all four in `MEMORY.md`. Trimmed `MEMORY.md` from 210→198 lines (moved 9 low-traffic engineering entries to `MEMORY_ARCHIVE.md` under new "Engineering reference" section).

## Decisions made

- **Daily LLM-driven code-review cron rejected** (Sankofa + Karpathy converged). Synthetic monitor of the actual user journey is higher-fidelity and lower-noise. Reverse only after seeing the monitor work for a week and still wanting prevention layered on top.
- **Switched chat model Haiku-4.5 → Sonnet-4.6.** Vision was the prompt; routing-quality lift is the real headline (Sonnet handles the 4-tool routing in `handlers_chat.py:153` better than Haiku, which has had multiple correctness fixes over time). 3x cost is acceptable at chat volume.
- **No file persistence.** User explicitly chose ephemeral. Attachments live only in the in-flight LLM request. History saves text + a short "[attached: X]" marker so the assistant has a memory cue. Re-asking about an old screenshot requires re-uploading.
- **Model in DB config, not .env.** Per the M11b design intent ([feedback_chat_model_env_vs_db_config.md](feedback_chat_model_env_vs_db_config.md)). This avoids re-creating today's morning RCA bug pattern.
- **Verify wire contract before coding.** Before any frontend work, ran two curl probes: vision (`anthropic/claude-sonnet-4.6` returned a vision-grounded answer to a 1x1 PNG) and PDF (extracted planted "FORTYTWO" password from a synthesized PDF). Confirmed Anthropic's `document` block ONLY accepts `application/pdf`; text-like files cannot use that path and must be inlined as text in the message body.
- **Drag-drop deferred to v2.** Karpathy hold for scope creep. Click + paste covers the use case.
- **Backend Pydantic schema is permissive enough as-is.** `_AtlasChatRequest.messages: list` already accepts list-of-dicts content; no schema rewrite needed.

## What is NOT done (explicit)

- **v2 of `chat_healthcheck.py`:** tool-calling probe + Telegram conversation roundtrip via separate test-user account. Defer until v1 has 48 hours of clean runs.
- **v2 of attachments:** drag-drop, server-side caps (currently only client-enforced), .docx / .xlsx / .pptx support. Wait for actual usage signals.
- **Repo-wide `os.environ.get(KEY, default)` audit.** Same defect class as today's morning bug lurks at other call sites. Single-PR sweep to convert to `or` form.
- **Two unrelated pre-existing modifications** in the working tree from parallel sessions (`orchestrator/atlas_dashboard.py`, `docs/reference/TOOLS_ACCESS.md`) - not mine, deliberately not bundled.

## Open questions

- **Why did Boubacar's specific JWT go invalid mid-session at 14:33:32 UTC today?** Frontend 401 fix makes this self-healing now (re-PIN modal preserves typed input), so root-cause-of-rotation is no longer urgent. Worth checking next session if 401s keep appearing in `chat_healthcheck.log`.
- **Will Sonnet-4.6's higher cost be visible at the wallet?** Chat volume is low and sporadic, but worth a check after a week.

## Next session must start here

1. **Read `chat_healthcheck.log` on the VPS** (`ssh root@agentshq.boubacarbarry.com 'tail -100 /var/log/chat_healthcheck.log'`) to confirm 24+ hours of clean runs since 14:00 UTC today.
2. **If clean for 48h:** ship v2 of healthcheck (tool-calling probe + Telegram conversation roundtrip).
3. **If 401s appear:** investigate JWT invalidation root cause before adding more probes.
4. **If chat attachment usage shows up in logs and feels limited:** consider drag-drop + .docx/.xlsx via client-side conversion. Do NOT add server-side caps unless a real bypass attempt happens.
5. **Quick win when convenient:** repo-wide audit of `os.environ.get(KEY, default)` and convert to `or` form. Single-PR sweep, low risk.

## Files changed this session

``
orchestrator/llm_helpers.py           (modified)
orchestrator/startup_check.py         (modified)
orchestrator/handlers_chat.py         (modified)
scripts/chat_healthcheck.py           (NEW)
thepopebot/chat-ui/atlas.html         (modified)
thepopebot/chat-ui/atlas.css          (modified)
thepopebot/chat-ui/atlas.js           (modified)
thepopebot/chat-ui/atlas-chat.js      (modified)

`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_chat_empty_model_compose_substitution.md`  (NEW)
`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_atlas_401_reload_kills_input.md`           (NEW)
`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_atlas_chat_attachments.md`                (NEW)
`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_env_shell_safety.md`                       (NEW)
`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md`                                          (modified)
`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY_ARCHIVE.md`                                  (modified)
``

VPS-only (not in git):
``
/etc/systemd/system/chat-healthcheck.service       (NEW)
/etc/systemd/system/chat-healthcheck.timer        (NEW)
/root/agentsHQ/.env                                (CRLF stripped + 2 values quoted)
agent_config postgres row                          (ATLAS_CHAT_MODEL=anthropic/claude-sonnet-4.6)
``

## Commits on main

- `5b94712` fix(chat): empty CHAT_MODEL/ATLAS_CHAT_MODEL env defeats default
- `1c7b3b0` feat(monitor): chat_healthcheck.py + systemd timer @ 10min
- `5f1f14a` fix(atlas-ui): non-destructive 401 recovery
- `176f605` Merge fix/atlas-401-no-reload to main
- `ade94bc` feat(chat): paperclip attachments + Sonnet vision/PDF
- `b50122c` Merge feature/chat-attachments to main

All pushed to `origin/main`. VPS at `b50122c`.
