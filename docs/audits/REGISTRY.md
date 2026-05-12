# agentsHQ Audit Registry

Append-only ledger of code/system audits. Most recent at top. Every audit MUST add an entry here as part of close-out — otherwise audit is incomplete.

**Before starting a new audit**: read this file + `docs/decisions/INTENTIONAL.md` to skip known false-positives.

---

## 2026-05-12 — Email Data Wiring Audit + Canonical Ledger Ship

**Trigger**: Boubacar — "how many emails were sent across all 3 brands (CW, SW, GW) all-time" had no canonical answer. sw_email_log (164 rows, 2026-05-11+), email_jobs (2 rows unused), leads (0 rows), Notion (severed) — none authoritative. Strategy decisions were made on wrong numbers.
**Scope**: every send-call site in repo; every email-related table in orc-postgres; Gmail Sent folder of both OAuth identities (cw + bokar83)
**Method**: read-only inventory of send paths + tables → Gmail API paginated counts (NOT resultSizeEstimate) → Phase 2 schema design → migration 009 + backfill + wiring patches → Phase 4 validation
**Output**:
  - `docs/audits/email-data-wiring-2026-05-12.md` (audit)
  - `docs/audits/email-data-wiring-2026-05-12-validation.md` (post-ship numbers)
  - `migrations/009_email_events.sql`
  - `scripts/backfill_email_events.py` + `scripts/sync_replies_from_gmail.py`
  - `signal_works/email_events.py` (shared writer)
  - wiring: `skills/outreach/sequence_engine.py`, `signal_works/send_scheduler.py`

### Headline findings
- All-time cold-outreach sent (Gmail ground truth): **446** (not 100+ as believed)
- All-time replies: **3** (0.67% reply rate, n=446 — solid sample)
- All-time bounces: **44** (9.9% — above 2% kill-switch threshold)
- Brand split (CW vs SW) does NOT exist at wire level — both send from `boubacar@catalystworks.consulting`. Only sw_email_log's `pipeline` column carries it, and only from 2026-05-11+.
- `send_scheduler._send_draft` never logged a `sent` event — 372 of the last 14d sends had no DB trail at all.
- `_bounce_rate_kill_switch` queries sw_email_log (50-row sample) instead of Gmail (real bounces). Never tripped despite 9.9% real bounce rate.

### Ship status
- Migration 009 applied to VPS orc-postgres
- Backfill complete: email_events now has 500 sent + 114 drafted + 44 bounced + 3 replied rows
- Reply-sync cron written but not yet installed (deferred to next session)
- Open/click tracking: deferred (requires pixel CDN — separate decision)
- Branch `feat/email-events-canonical-ledger` [READY] — awaits Gate merge

---

## 2026-05-11 — Skill Mirror Audit (local vs repo + architecture compliance)

**Trigger**: Boubacar standing rule — every skill in `~/.claude/skills/` must mirror to `agentsHQ/skills/` for VPS CrewAI access. Plus extension: enforce skill architecture spec (boubacar-skill-creator).
**Scope**: 81 local skills + 75 repo skills + 8 hidden-agent Python files + 6-criteria architecture compliance check across 74 SKILL.md files
**Method**: Read-only inventory → diff/spot-check → hidden-agent scan → 6-criteria scoring → Karpathy + Sankofa on rogue skills (>5 found)
**Output**: `docs/audits/2026-05-11-skill-mirror-audit.md`

### Findings
- 70 skills aligned, 11 LOCAL-ONLY (8 universal + 3 empty placeholders to skip)
- 2 SKILL.md DRIFT: `karpathy` (full content divergence), `sankofa` (each side has unique sections)
- 2 STRUCTURAL DRIFT: `ui-ux-pro-max` (1.9M local vs 49K repo, 35 files missing), `frontend-design` (12 reference docs + 2 templates missing in repo)
- 6 ROGUE skills (architecture violators): `active`, `library`, `CatalystWorksSkills`, `superpowers` (delete — pure registry placeholders), `library/agentshq-dispatch`, `memory/qmd_semantic_retrieval` (audit — nested under rogue parents)
- 0 truly hidden agents blocking VPS workflows; 1 ambiguous case (`ui-ux-pro-max/scripts/*.py` — Boubacar review on author-only vs runtime)
- `rca` skill local-only is the most urgent miss — already cited in CLAUDE.md but not in repo

### Read-only — no copies executed
Awaiting Boubacar approval to proceed with Batch 1 (8 universal SKILL.md mirrors). Architecture cleanup gates everything: 4 rogue placeholders must be deleted before mirroring, OR sync proposal will propagate the drift to VPS.

### Karpathy + Sankofa verdicts
- Karpathy on rogue: 4 of 6 (`active`, `library`, `CatalystWorksSkills`, `superpowers`) are pure pollution — DELETE
- Sankofa on rogue: 5 voices converge on DELETE the 4 placeholders; AUDIT the 2 nested

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
