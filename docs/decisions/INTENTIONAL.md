# Intentional Designs — DO NOT FLAG

Patterns that look like bugs to a fresh auditor but are deliberate design decisions. Greppable index of "skip this finding."

**Before flagging a new finding**: search this file for the file path or pattern. If listed, the finding is INTENTIONAL — push back on the decision via the handoff link if you disagree, but do not file as a bug.

**Format**: `file:line` — one-line description. **Decision**: [handoff link]. **Why**: [one-line reason].

---

## Gate / Autonomy

`orchestrator/gate_agent.py:293-296` — `_run_tests` returns `(True, "skipped (host)")` unconditionally.
**Decision**: archive/2026-05-05-gate-overhaul-and-codex-review.md
**Why**: Gate runs on VPS host outside container. Host Python has no container deps. Gate trusts [READY] commit marker; tests run pre-commit by the agent.

`orchestrator/gate_agent.py:71-93` — `AUTO_APPROVE_PREFIXES` includes `orchestrator/`, `thepopebot/`, `scripts/`, `signal_works/`.
**Decision**: 2026-05-10-compass-m6-m7-session.md
**Why**: Alert cost > revert cost for non-core files. GitHub history + save points make rollback cheap. Only `HIGH_RISK_PREFIXES` (CLAUDE.md, AGENTS.md, .env, docker-compose, gate_agent.py itself) require LLM review.

`orchestrator/concierge_crew.py:34-35` — `paramiko.AutoAddPolicy()` on SSH connections.
**Decision**: 2026-05-08-m4-concierge-crew.md
**Why**: Spec-approved approach. Crew currently `enabled: false` in autonomy_state.json anyway.

`data/autonomy_state.json` — null `cost_ceiling_usd` allowed for some crews.
**Decision**: 2026-04-26-autonomous-crew-contract.md
**Why**: null = inherits global cap. Default for new crews. Per-crew ceiling is optional override. (Note: 2026-05-11 audit added ceilings to chairman/auto_publisher/studio since they run live with dry_run=false.)

---

## Imports / Module Layout

`orchestrator/llm_helpers.py:31-37` — `_DEPRECATED_CONST_SENTINEL` constants for `CHAT_MODEL`, `HELPER_MODEL`, `ATLAS_CHAT_MODEL`.
**Decision**: archive/2026-05-02-chat-ui-routing-fix-session.md
**Why**: Defensive sentinel pattern. Legacy imports loud-fail at call site instead of silent-wrong routing. Use `model_key=` param at call sites; constants are decoys.

`orchestrator/scheduler.py:669,682,695` — `from orchestrator.X import Y` (package-style) alongside flat imports.
**Verified 2026-05-11**: Both `from orchestrator.X import Y` and `from X import Y` resolve inside container. WORKDIR=/app and /app/orchestrator both on path.
**Why**: Mixed style works; no bug.

---

## Env / Compose

`docker-compose.yml:129-130` — `TELEGRAM_BOT_TOKEN` aliased to `ORCHESTRATOR_TELEGRAM_BOT_TOKEN`.
**Decision**: archive/2026-04-27-full-sync-and-infra-cleanup.md
**Why**: Legacy compat alias. Canonical is ORCHESTRATOR_*; code reads either via fallback.

`orchestrator/Dockerfile` + `docker-compose.yml` — both ship code (baked COPY + volume mount). `scripts/docker-entrypoint.sh` syncs at start.
**Why**: Entrypoint sync covers volume-mount precedence. Restart required after `git pull` to re-sync. See `feedback_git_pull_no_restart.md`.

---

## Slugs / Models

`orchestrator/hermes_worker.py:124` — `_HERMES_MODEL = "anthropic/claude-haiku-4-5"` (dashes).
**Verified 2026-05-11**: OpenRouter accepts both `anthropic/claude-haiku-4-5` AND `anthropic/claude-haiku-4.5` (HTTP 200 on both).
**Why**: Older MEMORY rule said "dots not dashes" — rule is outdated. Either slug works. Do not flip without re-verifying.

---

## Known Deferrals (still open, not bugs)

`orchestrator/hermes_worker.py` checkout pattern uses `git checkout -b` instead of `git worktree`.
**Decision**: 2026-05-10-m24-hermes-shipped.md
**Why**: Worktree noted as architecturally cleaner but deferred — not blocking M24.

`thepopebot-runner` container crash loop.
**Decision**: archive/2026-05-02-notion-task-audit-and-poller-shipped.md
**Why**: Known stuck since 2026-04-27. Not blocking, nothing depends on it.

---

## How to add an entry

When an audit confirms a finding is intentional:
1. Add a row above with `file:line`, decision link, and one-line "why"
2. Update `docs/audits/REGISTRY.md` to note the skip
3. If memory rule is missing, add one in `MEMORY.md`

When a prior intentional design is no longer correct (requirements changed):
1. Add new audit entry to REGISTRY.md
2. Remove the row here
3. Link to the new handoff that supersedes the old decision
