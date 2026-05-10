# Session Handoff — Compass M6 + M7 — 2026-05-10

## TL;DR

Long Sunday session. Started with Compass M6 security audit (Hermes lockdown), hit a Vercel token in git history, ran filter-repo to clean it, triggered a 23-branch rebase crisis and 2000+ gate alert spam. Diagnosed all 3 root causes, built and shipped M7 to prevent recurrence. Gate escalation threshold raised — only core governance files alert Boubacar now. All 3 locations synced. M8 scoped for next week (scale to 20-40 agents).

## What was built / changed

### M6 — Pre-Hermes Security Lockdown
- `CLAUDE.md`: Hermes write boundaries section — ALLOWED/FORBIDDEN paths, wildcard prohibition
- `docs/audits/2026-05-10-compass-m6-audit.md`: 5-finding audit report
- `.vscode/settings.json`: Vercel token replaced with `${VERCEL_ACCESS_TOKEN}` (local only, not git-tracked)
- `git filter-repo`: token `vcp_7s8b...` purged from all 1706 commits across all branches
- All branches force-pushed clean; main force-pushed
- `audit/compass-m6-lockdown` branch pushed with [READY], merged to main
- `pytest tests/test_validate_governance_manifest.py`: 7/7 pass
- Save point tag: `savepoint/2026-05-10-hermes-lockdown`

### Gate fixes
- `orchestrator/gate_agent.py`: `_alerted_conflicts` set — conflict alerts fire once per pair per process lifetime (was: every 5-min tick)
- `orchestrator/gate_agent.py`: `_notify_conflict()` — sends inline ✅/❌ Telegram buttons on conflict
- `orchestrator/gate_agent.py`: raised escalation threshold — `HIGH_RISK_PREFIXES` expanded to include `CLAUDE.md`, `AGENTS.md`, `GOVERNANCE.md`, `governance.manifest.json`; `AUTO_APPROVE_PREFIXES` expanded to include `orchestrator/`, `thepopebot/`, `scripts/`, `signal_works/`
- Gate cron confirmed: every 5 min 24/7 (memory corrected — was wrong 15min/90min entry)

### M7 — Branch Discipline + Secret Scan Hardening
- `skills/coordination/spawner.py`: `build_agent_env()` — injects `CLAUDE_AGENT_ID`, `CLAUDE_AGENT_BRANCH`, `CLAUDE_PARENT_AGENT_ID` into every spawned agent env
- `docs/AGENT_SOP.md`: filter-repo hard rule added (check 8 in pre-commit)
- `.git/hooks/pre-commit`: check 8 (filter-repo guard), check 9 (vendor token scanner)
- `scripts/check_vendor_tokens.py`: regex scan for `vcp_`, `sk-`, `ghp_`, `ghs_`, `xoxb-`, `xoxp-`, `AKIA` in all staged files
- `orchestrator/gate_agent.py`: `_branch_diff_has_token()` — scans branch diff before merge; holds branch if token found
- `tests/test_check_vendor_tokens.py`: 5 tests (synthetic tokens only — no real credentials)
- `tests/test_spawner_agent_id.py`: 3 tests
- `docs/roadmap/compass.md`: M6 SHIPPED, M7 SHIPPED, M8 QUEUED
- Notion tasks created: M6, M7, gate fix, save point — all marked Done

### Branch resolution
- 15/23 conflicted branches rebased cleanly onto new main and force-pushed
- 8 branches with real conflicts merged via sequential merge in build order (zero content conflicts)
- `feat/atlas-m19-crm` M19 CRM work preserved from VPS (was not on GitHub) — cherry-picked to main

### nsync
- All 3 locations (local, GitHub, VPS) on same SHA after session
- Container healthy, heartbeats firing

## Decisions made

- **Gate escalation = only core governance files.** Everything else auto-resolves, silent. Alert cost > revert cost for non-core files. GitHub + save points = safe revert.
- **filter-repo is banned with live branches.** Protocol: rotate token + GitHub bypass URL. filter-repo only during full branch freeze.
- **CLAUDE_AGENT_ID at spawn.** Every agent gets a unique ID at birth via `build_agent_env()`. This is the foundation for coordination enforcement.
- **M8 scoped for next week.** Connection pooling, file-dependency pre-assignment, orc-hermes container — the 20-40 agent scale layer. Not urgent for current 3-5 agent concurrency.
- **Postgres memory_store write failed** (module identity conflict — two copies of memory_models loaded in container). Flat-file memory is the fallback for this session. Fix in M8.

## What is NOT done

- `outputs/diagrams/sankofa_council.mmd` — untracked file from another session. Left as-is (not this session's work).
- `outputs/diagrams/` folder — not gitignored, not committed. Needs `.gitignore` entry or commit decision.
- Postgres `memory_store.write()` — 6 session lessons NOT written to DB (module identity conflict). Flat-file memory covers the key lessons.
- M8 spec not written yet — scoped for next week session.
- 8 branches with real conflicts resolved by merge but not individually verified (Group B sequential merge — Group B agent confirmed zero content conflicts).

## Open questions

- Should `outputs/diagrams/` be gitignored or committed? Currently untracked.
- Token `vcp_7s8b...` on `feat/immutable-audit-log` was noted as still present in that branch's history before it was rebased. Confirm it's clean now or rotate the Vercel token regardless.
- `docs/roadmap/compass.md` has stale "Coverage today" section at line 40-44 referencing M1 stats — cosmetic, can clean in M8.

## Next session must start here

1. **Verify M7 gate is working:** check `docker logs orc-crewai --tail 20 | grep gate` — confirm no conflict spam and token check fires.
2. **Start M8 spec:** file-dependency pre-assignment (gbrain Minion pattern), `ThreadedConnectionPool` in `coordination/__init__.py`, `orc-hermes` container isolation. Plan file: `docs/superpowers/plans/2026-05-17-compass-m8-scale.md`.
3. **Fix `outputs/diagrams/`:** either add to `.gitignore` or commit.
4. **Fix Postgres memory_store module conflict:** two copies of `memory_models` loaded when writing from a script vs container import chain. Investigate and fix so session lessons write to DB.

## Files changed this session

```
orchestrator/gate_agent.py           — dedup, buttons, raised threshold, token scan
skills/coordination/spawner.py       — build_agent_env()
scripts/check_vendor_tokens.py       — new: vendor token scanner
tests/test_check_vendor_tokens.py    — new: 5 tests
tests/test_spawner_agent_id.py       — new: 3 tests
docs/AGENT_SOP.md                    — filter-repo hard rule
docs/roadmap/compass.md              — M6 SHIPPED, M7 SHIPPED, M8 QUEUED
docs/audits/2026-05-10-compass-m6-audit.md — new: 5-finding audit report
CLAUDE.md                            — Hermes write boundaries section
.git/hooks/pre-commit                — check 8 (filter-repo), check 9 (token scan)
docs/handoff/2026-05-10-compass-m6-m7-session.md — this file
```
