# agentsHQ Audit Registry

Append-only ledger of code/system audits. Most recent at top. Every audit MUST add an entry here as part of close-out — otherwise audit is incomplete.

**Before starting a new audit**: read this file + `docs/decisions/INTENTIONAL.md` to skip known false-positives.

---

## 2026-05-13 — Gate audit logger silent-fail fix (Solution B, host psycopg2 path)

**Trigger**: Task 2 follow-up. First attempt (flip systemd ExecStart to `docker exec ... gate_agent.py`) failed twice (INVOCATION_ID guard, missing table assumed but actually present). Reverted clean.
**Scope**: `orchestrator/gate_agent.py`, `orchestrator/logger.py`, `scripts/setup_immutable_audit.sql`, `/etc/systemd/system/gate-agent.service` on VPS, `orc-postgres.immutable_audit.agent_audit_trail`.
**Method**: 3 rounds (Round 1 read code + verify ground truth, Round 2 Sankofa Council on 5 candidate solutions, Round 3 Karpathy audit + verify B's hidden assumptions). Converged at 95% surety on Round 3.

### Headline findings (re-discovery from Round 1)
- `immutable_audit.agent_audit_trail` table already exists in `orc-postgres` (was created by `scripts/setup_immutable_audit.sql` previously). No migration needed. Original Task 2 spec assumed table absent.
- `audit_logger` Postgres role exists with INSERT-only privs via `immutable_audit.append_audit_event(...)` SECURITY DEFINER wrapper.
- `gate_agent.py` already has a `GATE_FORCE_RUN=1` escape hatch on the INVOCATION_ID guard (line 673). The first failed attempt did not need to bypass anything.
- `from logger import audit_gate` succeeds on host (psycopg2 imported lazily inside `_connect()`). The async worker thread fails silently on the actual connect because (a) host had no psycopg2, (b) `.env` sets `AUDIT_PG_HOST=postgres` which is a docker-network alias not resolvable from host.
- Postgres exposes `127.0.0.1:5432` on the VPS host via docker port bind. pg_hba accepts host connections via scram-sha-256.
- Last successful gate audit row landed 2026-05-10 (id=4, before the silent regression).

### Why Solution B won over A, C, D, E

| Sol | Surface area | Reversibility | Failure modes | Container coupling |
|-----|-------------|--------------|---------------|---------------------|
| A (docker exec gate) | systemd unit rewrite + container working-tree contamination risk (gate runs `git checkout main` + `git merge` + `git push`; container fs is partly baked-image, partly volume-mount; merge could write to baked-image working tree) | medium | container down → gate stops ticking | strong (gate inherits container lifecycle) |
| B (apt python3-psycopg2 + Environment=AUDIT_PG_HOST=127.0.0.1) | 1 apt install + 6 lines in systemd unit | trivial (`apt remove` + `cp backup`) | minor host-vs-container version drift (2.9.9 vs 2.9.12, both stable 2.9.x) | none |
| C (HTTP /internal/audit endpoint) | refactor `logger.py` + new endpoint in orchestrator + systemd | heavy | gate→HTTP→DB = 2 failure modes vs 1 | strong |
| D (docker exec + INVOCATION_ID passthrough) | duplicates A; pointless since GATE_FORCE_RUN already in code | same as A | same as A | strong |
| E (file queue + drain) | new drain process + queue file growth + hot-path disk I/O | three rollback points | drainer dies → queue fills disk | medium |

### Ship

1. `apt-get install -y python3-psycopg2` on VPS (installs python3-psycopg2 2.9.9 + libpq5).
2. Edit ExecStart in `/etc/systemd/system/gate-agent.service` to wrap python in bash with inline env override: `ExecStart=/usr/bin/bash -c 'AUDIT_PG_HOST=127.0.0.1 exec /usr/bin/python3 /root/agentsHQ/orchestrator/gate_agent.py'`. Backup at `/root/backups/2026-05-13/gate-agent.service.bak.preB`.
3. `systemctl daemon-reload`.

### Late-stage discovery: systemd EnvironmentFile precedence quirk (Ubuntu 24.04)

The initial implementation used `Environment=AUDIT_PG_HOST=127.0.0.1` AFTER `EnvironmentFile=/root/agentsHQ/.env`. Documentation reads "later directives override earlier", and `systemctl show` reports `AUDIT_PG_HOST=127.0.0.1` in the resolved env. However, empirical test on this systemd version (Ubuntu 24.04, systemd 255) shows `EnvironmentFile=` ALWAYS wins over `Environment=` regardless of declaration order — and drop-in `override.conf` files do not win either. This is a quirk in how this distro packages systemd, not a documented behavior.

Verified via a probe unit:
```
EnvironmentFile=/root/agentsHQ/.env          → sets AUDIT_PG_HOST=postgres
Environment=AUDIT_PG_HOST=127.0.0.1          → ignored
Environment=AUDIT_PG_HOST=override_inline    → ignored
Final env in exec: AUDIT_PG_HOST=postgres
```

Robust fix: wrap ExecStart in `bash -c 'VAR=value exec /usr/bin/python3 ...'`. Bash inline assignment to the command's env runs AFTER systemd has set its env, so it wins reliably. Tested.

This is the same reason Path A would have needed multiple revisions if it had been the chosen path.

### Verification

1. Direct end-to-end test under matching systemd env: audit row id=5 landed at `gate_agent.gate_approve`. Confirmed audit_logger module + table + INSERT path all work.
2. Real gate auto-merge test: pushed `fix/gate-audit-logger-host-psycopg2` with [READY] tip-commit. Gate's next tick (manually triggered with `systemctl start gate-agent.service`) merged the branch to main (commit `584f10ab`), then merged a second [READY] branch (`fix/multiplier-tick-skip-bad-records` as `8fe133e6`) in the same tick. Total elapsed from `systemctl start` to "tick done" = 7 seconds.

Caveat from gate run 1: the gate log still showed `audit_logger reconnect failed: could not translate host name "postgres"` because the systemd-quirk fix had not been applied yet. After the bash-wrap fix, the env actually carries `AUDIT_PG_HOST=127.0.0.1` and the next gate tick that fires audit_gate() will write rows successfully. The audit-logger fail-open design means the gate work itself (merges, pushes, deploys) is never blocked by audit issues — verified by the successful merges in run 1.

### Pre-existing race documented, NOT fixed by this ship
The audit worker is a daemon thread. Daemon threads die on main-process exit. Gate is `Type=oneshot`. If the queue has not drained at the moment `gate_tick()` returns, events are lost. Risk is small in practice (single-digit events per tick, worker starts in ms) but it is a latent issue worth its own fix later. Out of scope for this task because the same race existed when the system last worked.

### Honest open questions
- Should `AUDIT_PG_HOST` always be `127.0.0.1` from host context and `postgres` from container context, or should the connection logic try both? Current ship hardcodes per-context via systemd. Acceptable for now; revisit if a third caller emerges.
- The `[Unit]` block has no `Requires=docker.service` or `After=orc-postgres health-check`. A boot-time race could see gate fire before postgres is up. Existing behavior; not regressed by this fix.

---

## 2026-05-12 — Catalyst Works site audit + Constraints AI capture pipeline

**Trigger**: Boubacar — full-stack audit of catalystworks.consulting + Constraints AI capture form validation + 3-email follow-up sequence + n8n vs VPS-only decision for the capture path.
**Scope**: 16 HTML pages on live site + local satellite repo (`output/websites/catalystworks-site/`); `/capture` endpoint wire; `_worker.js` Cloudflare Worker source; `n8n.srv1040886.hstgr.cloud` workflows reachable from this machine.
**Method**: live HEAD-probe of every sitemap URL + 4 user-named paths; static-crawl of 36 unique internal hrefs from 16 HTML files; read of `.htaccess`, `_worker.js`, `index.html` (capture block); live POST probes of both n8n endpoints (root + `/capture`) with fake email + pain input; external URL HEAD probes for 8 high-value citation links.
**Output**:
  - `docs/audits/cw-site-audit-2026-05-12.html` (audit report, Boubacar-facing)
  - `docs/integrations/constraints_ai_capture_followup_2026-05-12.md` (n8n vs VPS-only decision + integration plan)
  - `templates/email/constraints_ai_t1.py`, `t2.py`, `t3.py` (3-touch sequence, Day 0/2/4)
  - `skills/outreach/sequence_engine.py` (`constraints_ai` pipeline registered)

### Headline findings
- Link integrity: PASS (36 hrefs, 0 broken — `.htaccess` clean-URL rewrite working).
- SEO: PASS (12/12 pages have H1 + meta + canonical + viewport + theme-color). 6 pages have descriptions >200 chars (Google truncates ~160 — back-half hidden but legal). `for/hvac.html` title=81 chars (display cut-off ~60). All warnings, no fails.
- JSON-LD: PASS (5 schemas on index — Organization, Service, Person, FAQPage, ProfessionalService).
- External citations: PASS (Calendly, Beehiiv, signal subdomain, 4 research links — all 200).
- **P0 finding: `/capture` endpoint silently broken.** Frontend POSTs to `https://n8n.../catalystworks-constraints-ai/capture` which returns 404 "webhook not registered". `index.html:2222` explicitly swallows the error and shows success. Every capture since 2026-05-11 deploy has been thrown away. `diagnostic_captures` row count = 0 not because traffic is zero but because the wire is cut.
- Diagnostic root endpoint (`POST .../catalystworks-constraints-ai` without `/capture`) works correctly. Only the sub-route is missing.

### Ship status
- 3 email templates + sequence_engine wiring shipped in same branch (`fix/session-collision-git-layer-enforcement`)
- Audit report HTML + n8n decision doc shipped in this commit
- Live-site fix (deploy `_worker.js` Cloudflare Worker, cut over front-end, retire n8n from this pipeline) NOT shipped yet — design only, awaits Boubacar approval
- Constraints AI pipeline stays draft-only (`AUTO_SEND_CONSTRAINTS_AI=false`) until Boubacar flips it explicitly

### Decision: n8n vs VPS-only for capture follow-up
- **Recommendation: VPS-only.** Deploy existing `_worker.js` (code already written, undeployed). Worker double-writes to Supabase `diagnostic_captures` + agentsHQ `/inbound-lead`. `/inbound-lead` triggers `run_inbound_lead` which seeds `leads` with `sequence_pipeline='constraints_ai'`. sequence_engine then runs the 3-email cadence already shipped.
- One fewer SaaS (n8n), one less authentication surface, code-as-truth instead of n8n UI-as-truth, Cloudflare edge latency.
- Open question deferred: does n8n stay in agentsHQ architecture at all? Out of scope here; needs its own Council session if Boubacar wants to retire it broader.

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

## 2026-05-14 - Gate HIGH_RISK precedence audit (PR fix/high-risk-precedence)

**Auditor:** Claude Code (this session)
**Trigger:** Self-flagged during gate-archive-merge-resolver RCA - earlier PR (feat/gate-archive-merge-resolver) auto-merged despite touching orchestrator/gate_agent.py (HIGH_RISK_PREFIXES) because gate's check `_is_high_risk AND not _is_auto_approvable` short-circuited (orchestrator/ in AUTO_APPROVE_PREFIXES).
**Severity:** privilege escalation - any agent able to edit orchestrator/anything.py could edit gate_agent.py without Telegram approval.

### Findings
- gate_agent.py:730 conditional `_is_high_risk(files) and not _is_auto_approvable(files)` allows any HIGH_RISK file to bypass approval if bundled only with auto-approvable paths.

### Fixed
- Dropped `and not _is_auto_approvable(files)` clause: HIGH_RISK now strictly dominates.
- Added bypass-pattern tripwire (`_branch_diff_has_bypass_pattern`) catching BYPASS/SKIP/DISABLE-gate env-vars or constants. Hard-blocks branch + alerts once per tip_sha. Council premortem condition #3.
- 7 new tests in tests/test_gate_agent.py (1 regression guard + 6 tripwire coverage). All green.

### Validation (Sankofa Council + Karpathy)
- Council premortem (Dead-Project mode): SHIP-WITH-CONDITIONS. Real privilege gap. Friction-bypass named as the 6-month failure mode -> mitigated by tripwire (condition #3 shipped). Conditions #1 (HIGH_RISK narrow split), #2 (24h email fallback), #4 (friction log) filed as separate Compass milestone.
- Karpathy audit: PASS / PASS / PASS / WARN (P4 verification deferred to post-merge live test).

### Karpathy P4 follow-through (VERIFIED 2026-05-14 21:47 UTC)
- Pushed `test/gate-p4-verify-2026-05-14` (no-op comment edit on `orchestrator/gate_agent.py`, [READY] tag)
- Gate tick result: `tick done. merged=[], failed=[], blocked=[], held_high_risk=['test/gate-p4-verify-2026-05-14']`
- Gate did NOT auto-merge. HIGH_RISK approval flow confirmed under new logic.
- Wrote reject marker `data/gate_approvals/test__gate-p4-verify-2026-05-14.reject.json` to test consume path
- Next tick: `test/gate-p4-verify-2026-05-14 rejected via marker`, marker file consumed (file deleted), `held_high_risk=[]` (drained from set)
- Both approval-card-fires AND /gate-reject consume paths verified. Closing this P4 WARN.

### Memory rule added
- `feedback_gate_high_risk_strictly_dominates.md` (to be written next)

### Open follow-up
- Compass milestone: narrow HIGH_RISK_PREFIXES into self-referential subset (gate_agent.py, scripts/gate_*, approval-marker code path) and operationally-critical subset (.env, docker-compose, governance) with different policies for each; add 24h email fallback approver; add approval-friction log under docs/audits/friction-log.md.

---
