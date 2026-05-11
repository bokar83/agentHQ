# agentsHQ Audit Registry

Append-only ledger of code/system audits. Most recent at top. Every audit MUST add an entry here as part of close-out — otherwise audit is incomplete.

**Before starting a new audit**: read this file + `docs/decisions/INTENTIONAL.md` to skip known false-positives.

---

## 2026-05-11 — Adversarial Code Review (full agentsHQ)

**Trigger**: User-initiated full adversarial review across local + VPS
**Scope**: orchestrator/, skills/, scripts/, configs, docker-compose, .env, Postgres schema, autonomy state, gate logs
**Method**: 2 parallel review agents (local + VPS) → memory/handoff verification pass → Karpathy + Council synthesis → 2 RCAs → 6 mechanical fix sessions
**Save point tag**: `savepoint-pre-codex-adversarial-2026-05-10-2030` (local + VPS)
**Save point backup**: `/root/backups/2026-05-10-2030/` (pg_dump, .env, docker state)

### Original findings: 68 (2 P0, 11 P1, 55 lower)

### Real bugs shipped: 5
- VR1 JWT 12-byte `ORCHESTRATOR_API_KEY` rotated to 43-byte token_urlsafe (PyJWT `InsecureKeyLengthWarning` cleared)
- VB4 leads table 4 missing columns added: `phone`, `last_contacted_at`, `email_drafted`, `email_drafted_at`
- B8 db.py duplicate `ensure_leads_columns` + `get_resend_queue` removed (commit `a3f132a` via gate auto-merge)
- VR3 cost ceilings set on chairman ($0.10), auto_publisher ($0.05), studio ($0.20)
- LISTMONK_PW orphan removed from .env (never consumed by any code)

### Bonus fix: 1
- RCA-B Notion 400s — stale container module cleared by JWT-rotation restart (no code change needed; commit 5537ea2 was correct on disk)

### False positives skipped: 9
- VR4 gate `_run_tests` returns True — INTENTIONAL per archive/2026-05-05-gate-overhaul-and-codex-review.md
- R15 `orchestrator/` in AUTO_APPROVE_PREFIXES — INTENTIONAL per 2026-05-10-compass-m6-m7-session.md
- VR2 paramiko AutoAddPolicy in concierge_crew — INTENTIONAL per 2026-05-08-m4-concierge-crew.md (crew disabled anyway)
- B1 local minion_worker.py — EXISTS (shipped M23 2026-05-10)
- B4 flat-module imports — both paths work in container (verified live)
- VB3 startup_check sentinels — INTENTIONAL defensive pattern per 2026-05-02-chat-ui-routing-fix-session.md
- B9 TELEGRAM_BOT_TOKEN alias — INTENTIONAL legacy compat per 2026-04-27-full-sync-and-infra-cleanup.md
- VB5 hermes uses `git checkout -b` not worktree — KNOWN_DEFERRED per 2026-05-10-m24-hermes-shipped.md
- VR7 hermes `claude-haiku-4-5` slug — FALSE POSITIVE (OpenRouter accepts both dash + dot, verified live)

### Deferred (still open, not blockers)
- VC1 `agents/security-agent/security_agent.py` cron points at missing file — SecureWatch retired, remove cron when convenient
- VC2 `/root/agentsHQ/waha_sessions/` 14MB orphan — gitignored, safe to rm
- VR5 `gate-deploy-watchdog.sh` not in VPS crontab — gate `_deploy_vps` writes trigger no watchdog reads. Either install cron OR change `_deploy_vps` to call docker compose restart directly
- B6 `INTERVAL '%s'` pattern in 11 files — works today (Python `%` interpolation), lint-level injection-shape risk
- VB1 thepopebot-runner crash loop (2982 restarts/13 days) — separate stack, nothing depends, stop container when convenient
- VB6 12 stuck branches in gate_log — manual triage backlog
- VB9 `GOOGLE_SERVICE_ACCOUNT_JSON` passthrough with no consumer — remove from compose when confident
- C8 commented WAHA block in docker-compose.yml has plaintext `agentshq123`/`admin123` — delete commented block

### Memory rule added
- `feedback_audit_read_handoffs_first.md` — audits must read docs/handoff/ + routing-architecture.md + MEMORY.md before flagging severity

### Process learnings
- Original audit produced ~91% noise (62 of 68 findings)
- Verification pass + Council overrode 9 P0/P1 calls as intentional/deferred/fixed
- Codex pass aborted (AGENTS.md blocks VPS edits for autonomous agents; direct session executed instead)
- Final ship time: ~2 hours for 5 real fixes after verification

### Full session transcript
- This conversation (2026-05-11) — not saved as discrete handoff yet. If needed, write `docs/handoff/2026-05-11-adversarial-audit-session.md`

---
