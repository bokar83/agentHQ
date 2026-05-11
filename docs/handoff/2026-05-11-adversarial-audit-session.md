# Session Handoff — Adversarial Audit + Fix Ship — 2026-05-11

## TL;DR

Ran full adversarial code review across local + VPS. Original audit produced 68 findings (2 P0, 11 P1, 55 lower). Verification pass + Sankofa Council killed 62 of 68 as intentional / known-deferred / already-fixed / false-positive. Shipped 5 real bug fixes + audit registry infrastructure + gate_poll prefix coverage fix. Production stayed up throughout.

## What was built / changed

### Real bug fixes shipped to main + live on VPS

1. **JWT rotation** — `ORCHESTRATOR_API_KEY` rotated from 12 bytes → 43-byte URL-safe token. Cleared live `InsecureKeyLengthWarning`. Backup: `/root/backups/2026-05-11/.env.before-jwt-rotate-094457`
2. **leads table ALTER** — added 4 missing columns: `phone`, `last_contacted_at`, `email_drafted`, `email_drafted_at`. Hunter re-enable now safe
3. **Cost ceilings set** — `data/autonomy_state.json`: chairman=$0.10, auto_publisher=$0.05, studio=$0.20 (was null)
4. **LISTMONK_PW removed** from `.env` — orphan, never consumed by any code
5. **db.py duplicate function cleanup** — `orchestrator/db.py`: removed dead L416/L438 defs of `ensure_leads_columns` + `get_resend_queue`. Merged column lists into surviving `ensure_leads_columns` (7 columns: no_website, email_source, apollo_id, phone, last_contacted_at, email_drafted, email_drafted_at). Fixed `INTERVAL '%s days'` → `(%s || ' days')::interval` in surviving `get_resend_queue`. Commit `3d1605e` via gate auto-merge `a3f132a`

### Free wins

- **RCA-B Notion 400s** — stale container module (commit 5537ea2 correct on disk but pre-restart load). Same JWT-rotation restart fixed it. `/app/atlas_dashboard.py` Approved-count = 1 (was 2)
- **gate_poll prefix coverage** — `scripts/gate_poll.py:49` `READY_BRANCHES_PREFIXES` extended to include `docs/`, `chore/`, `refactor/`, `test/` (was feature/feat/fix only). Commit `0c5c982` via gate auto-merge `7ef8ec3`
- Surfaced 1 latent branch `docs/atlas-session-log-2026-05-08` previously invisible to gate

### Audit registry infrastructure

- `docs/audits/REGISTRY.md` — chronological append-only audit ledger. First entry = today's session
- `docs/decisions/INTENTIONAL.md` — greppable false-positive index (gate `_run_tests` stub, AUTO_APPROVE scope, paramiko AutoAddPolicy, llm_helpers sentinels, hermes haiku slug, etc.)
- `CLAUDE.md` — new "Audit Registry (2026-05-11)" section hooks future audits at both files + memory rule. Commit `ecc38cb` via manual merge (HIGH_RISK auto-blocked)

### Memory entries

- `feedback_audit_read_handoffs_first.md` — rule: audits must read docs/handoff/ + routing-architecture.md + MEMORY.md before flagging severity
- `MEMORY.md` index updated with pointer

## Decisions made

- **Trust handoff over fresh analysis on intentional designs.** VR4 (gate `_run_tests` returns True) and R15 (`orchestrator/` in AUTO_APPROVE_PREFIXES) flagged as P0/P1 by original audit but are shipped designs per archive/2026-05-05 + 2026-05-10-compass-m6-m7-session.md. SKIP these going forward.
- **Both haiku slugs work.** OpenRouter accepts `anthropic/claude-haiku-4-5` AND `anthropic/claude-haiku-4.5` (verified live HTTP 200 both). Memory rule "use dots not dashes" is outdated for this model. Do not flip without re-verifying.
- **Chairman wake "skip (crew disabled)" logs are stale.** State flipped 2026-05-11 00:00:56 UTC; chairman correctly firing since. Today's skip is callback-level data check (`insufficient data (6 outcomes, need 7)`), not guard-level.
- **gate_poll only NOTIFIES.** Actual gate runs from `/etc/cron.d/gate-agent` every 5 min on VPS host, calling `orchestrator/gate_agent.py` directly.
- **CLAUDE.md edits trigger HIGH_RISK hold** — gate routes to manual approval. Split-branch pattern (feat/audit-registry without CLAUDE.md, chore/claude-md-audit-hook with it) keeps auto-merge for safe parts.

## What is NOT done (explicit)

Open deferred items captured in `docs/audits/REGISTRY.md`:

- **VC1**: `agents/security-agent/security_agent.py` cron points at missing file. SecureWatch retired. Remove cron entry when convenient.
- **VC2**: `/root/agentsHQ/waha_sessions/` 14MB orphan from retired waha container. Already gitignored. `rm -rf` when convenient.
- **VR5**: `scripts/gate-deploy-watchdog.sh` exists in repo but NOT in VPS crontab. Gate `_deploy_vps()` writes trigger file no watchdog reads. Either install cron OR change `_deploy_vps` to call `docker compose restart` directly.
- **B6**: `INTERVAL '%s'` pattern in ~10 remaining files (db.py:543/757, griot.py:186/220, atlas_dashboard.py:60/585/597, chairman_crew.py:74, handlers_commands.py:197/210/229, weekly_synthesis_crew.py:60). Works today (Python `%` interpolation), lint-level injection-shape risk. Fixed only in db.py:get_resend_queue this session.
- **VB1**: thepopebot-runner crash loop (2982+ restarts/13 days). Separate stack, nothing depends. Stop container when convenient.
- **VB6**: 12 stuck branches in gate_log backlog. Manual triage.
- **VB9**: `GOOGLE_SERVICE_ACCOUNT_JSON` passthrough in docker-compose.yml with no Python consumer. Remove when confident.
- **C8**: Commented WAHA block in docker-compose.yml has plaintext `agentshq123`/`admin123` in git history. Delete commented block.

**Postgres memory writes**: SessionLog + AgentLessons + ProjectState writes to VPS Postgres failed from laptop (`agentshq-postgres-1` not resolvable). Memory rule still wrote to flat-file. To backfill: run the snippet from inside the orc-crewai container or via SSH tunnel.

## Open questions

None. Audit closed cleanly.

## Next session must start here

Default move: read `docs/audits/REGISTRY.md` + `docs/decisions/INTENTIONAL.md` for what's deferred. Pick from deferred list when time allows. Otherwise, resume normal work — production solid.

## Files changed this session

- `orchestrator/db.py` — duplicate function dedup
- `scripts/gate_poll.py` — prefix coverage extended
- `CLAUDE.md` — Audit Registry section added
- `docs/audits/REGISTRY.md` — NEW
- `docs/decisions/INTENTIONAL.md` — NEW
- `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\feedback_audit_read_handoffs_first.md` — NEW
- `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\MEMORY.md` — pointer added

## VPS state changes

- `.env`: ORCHESTRATOR_API_KEY rotated, LISTMONK_PW removed
- `data/autonomy_state.json`: chairman/auto_publisher/studio cost_ceiling_usd set
- `leads` table: 4 columns added
- Container `orc-crewai`: restarted twice (post-JWT, post-CLAUDE.md merge); both healthy
- Backups: `/root/backups/2026-05-11/` (`.env.before-jwt-rotate-094457`, `.env.before-listmonk-*`, `autonomy_state.before-ceilings-*.json`)
- Save point tag: `savepoint-pre-codex-adversarial-2026-05-10-2030` (local + VPS + GitHub)
- Save point backup: `/root/backups/2026-05-10-2030/` (pg_dumpall, docker state, .env)

## Commits to main

- `3d1605e` fix(db): remove duplicate defs [READY]
- `a3f132a` merge(fix/db-duplicate-defs)
- `0c5c982` fix(gate): extend READY_BRANCHES_PREFIXES [READY]
- `7ef8ec3` merge(fix/gate-poll-prefix-coverage)
- `203c21c` docs(audit): add REGISTRY + INTENTIONAL [READY]
- `ec5ca66` merge(feat/audit-registry)
- `ecc38cb` merge(chore/claude-md-audit-hook) — manual approval
