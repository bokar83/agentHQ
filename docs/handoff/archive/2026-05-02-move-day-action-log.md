# Move Day Action Log: 2026-05-02

**Purpose of this doc:** complete record of every change made during the 2026-05-02 Move Day session, structured so any item can be reviewed and reverted individually if needed.

**Session arc:** session opened on the 04-27 architecture handoff, ran /sankofa + /karpathy on the original 16-step plan (caught 5 production-mount footguns), reframed scope, executed the full plan with NOTHING DELETED rule, three-way synced.

**Final commit chain on `main`:**

```
092900f perf(chat): drop conversation history limit 50 to 20 in handlers_chat.py
7fe5d6d chore(repo): Move Day structural cleanup + Folder Governance + Ventures Registry
0cc3563 docs(handoff): 2026-05-02 notion task audit + poller + /task add shipped  ← prior session
```

**Savepoint tag:** `savepoint-pre-archive-cleanup-20260502` (before any Move Day change)
**Backup tarball:** `zzzArchive/_pre-cleanup-20260502/_backup-gitignored.tar.gz` (53 MB, gitignored content snapshot)
**Manifest:** `zzzArchive/_pre-cleanup-20260502/MANIFEST.md`

---

## How to revert any individual item

**To revert the entire session:** `git reset --hard savepoint-pre-archive-cleanup-20260502` and `tar -xzf zzzArchive/_pre-cleanup-20260502/_backup-gitignored.tar.gz`

**To revert a single archived file:** `git mv zzzArchive/_pre-cleanup-20260502/<path> <original-path>`. The MANIFEST.md preserves original paths.

**To revert the token fix only:** `git revert 092900f`.

---

## Change inventory by category

### A. New rules locked in `docs/AGENT_SOP.md`

| Rule | Purpose | Revert: edit AGENT_SOP, remove the bullet |
|---|---|---|
| Word "delete" retired | All non-used items go to `zzzArchive/<batch>/<path>/` with MANIFEST.md, never deleted | line ~40 in Hard Rules |
| Make educated decisions on routine triage | Don't paginate three-way verdicts to Boubacar; execute and document | line ~41 in Hard Rules |
| **New section: Folder Governance** | 7 rules: AGENTS.md or README.md per folder, no folder without purpose, 14d-untouched + zero refs = archive candidate, live mounts never move, triple-verify before archive, zzzArchive never archived itself, sandbox monthly sweep | new section after Hard Rules |

### B. New memory entries

| File | Purpose | Revert: delete the file + the MEMORY.md index line |
|---|---|---|
| `feedback_make_educated_decisions.md` | Triage autonomy rule | linked from MEMORY.md |
| `reference_folder_governance.md` | Full 7-rule folder governance + decision flow + mount footgun list | linked from MEMORY.md |
| `feedback_rod_send_freeze_until_wed_2026_05_06.md` | No Rod send before Wed 2026-05-06 | linked from MEMORY.md |

### C. Folder archives (in `zzzArchive/_pre-cleanup-20260502/`)

| Original location | Archive location | Reason | Reference-grep result |
|---|---|---|---|
| `remote-access-auditor/SKILL.md` | `remote-access-auditor/SKILL.md` | Duplicate of `skills/remote-access-auditor/SKILL.md` (canonical at skills/) | only references in docs and skill index |
| `server-setup/harden-vps.sh` | `server-setup/harden-vps.sh` | One-time VPS bootstrap from 2026-03-16, superseded by current VPS state | zero callers |
| `server-setup/setup-database.sql` | `server-setup/setup-database-OLDER.sql` | Older (80 lines) than root version (166 lines), root is docker-compose mounted | only ref is in docs |
| `workflows/README.md` | `workflows/README.md` | Legacy n8n exports folder, content consolidated into `n8n/imported/` | no active callers |
| `workflows/legacy/workflow-whatsapp-v6.json` | `workflows/workflow-whatsapp-v6-LEGACY.json` | Older (Mar 19) than n8n-workflows version (Apr 12) | no active callers |
| `workflows/workflow-daily-news-brief.json` | `n8n-workflows-old/workflow-daily-news-brief-DUPLICATE.json` | Identical to n8n-workflows version | no active callers |
| `n8n-workflows/workflow-SUB-always-save.json` | `n8n-workflows-old/workflow-SUB-always-save-OLDER.json` | Older content than workflows/ version | no active callers |
| `tmp/codex-commit-2..8.txt` (8 files) | `tmp/codex-commit-drafts/` | Codex commit drafts from 2026-04-30, no longer relevant | n/a |
| `tmp/check_apollo_*.py`, `test_apollo_*.py`, `test_voice.py`, `migrate_db.py`, `adversarial_stress_test.py` | `tmp/old-apollo-probes/` | Old probes 2026-03-29 to 2026-04-22, untouched 14+ days | zero references |
| `scratch/` (12 files) | `scratch/` | Old probes 2026-04-12 to 2026-04-20, all gitignored | zero references |
| `.tmp/CLAUDE.md` | `dot-tmp/CLAUDE.md` | Old (2026-04-08), pytest cache + antivirus quarantine left in place | zero references |
| `tmp_upload/LEARNING_*.txt`, `yt_*.mp3` (11 files) | `tmp_upload-old/` | Old transcripts 2026-04-16; folder kept as transcribe skill WORK_DIR | folder still active |
| `agent_outputs/capital-allocation/` | `agent_outputs-old/capital-allocation/` | Old (2026-04-08); folder kept as `/app/outputs` live mount | folder still active |
| `schema_v2.sql` (root) | `root-files/schema_v2-OLDER-2026-03-29.sql` | Older (48 lines, 2026-03-29) than `docs/database/schema_v2.sql` (53 lines, 2026-04-02) | only error-message ref in test_growth_engine.py |
| `ideas_full_list.txt`, `ideas_full_list_utf8.txt`, `search_output.txt` | `root-files/` | Notion Ideas DB is source of truth; all gitignored | gitignored, no callers |

### D. Folder consolidations (n8n)

All three current versions copied to `n8n/imported/` with descriptive `n5x-` prefix; older duplicates archived.

| New location | Source | Notes |
|---|---|---|
| `n8n/imported/n50-sub-always-save.json` | `workflows/workflow-SUB-always-save.json` (newer of two versions) | 7111 bytes, 2026-04-12 14:52 |
| `n8n/imported/n51-daily-news-brief.json` | `workflows/workflow-daily-news-brief.json` (identical to n8n-workflows version) | 9859 bytes |
| `n8n/imported/n52-whatsapp-v6.json` | `n8n-workflows/workflow-whatsapp-v6.json` (only place this version lived) | 8545 bytes, 2026-04-12 14:51 |

Empty `workflows/` and `n8n-workflows/` folders removed after consolidation.

### E. Root file relocations (preserved git blame via `git mv`)

| From | To | Reason |
|---|---|---|
| `code_review_20260422.md` | `docs/handoff/code_review_20260422.md` | Belongs with handoff docs |
| `adversarial_report.md` | `docs/reference/adversarial_report.md` | Belongs with reference docs |
| `MakeShortcut.ps1` | `scripts/MakeShortcut.ps1` | Operational script |
| `Run-Local-SecureWatch.bat` | `scripts/Run-Local-SecureWatch.bat` | Operational script |
| `run_council_strat.py` | `scripts/run_council_strat.py` | Operational script |
| `test_sankofa.py` (gitignored at root) | `tests/test_sankofa.py` | Belongs with tests |
| `a-b testing.xlsx` (gitignored) | `workspace/a-b testing.xlsx` | Working data |
| `ninja.ico` (was tracked) | `workspace/ninja.ico` | UI asset, working space |

### F. Test graduations (NEW location, copies preserved in archive backup)

| From | To | Reason |
|---|---|---|
| `tmp/test_phase1_e2e.py` | `tests/integration/test_phase1_e2e.py` | Real Phase 1 e2e test (autonomy + approval queue), not throwaway |
| `tmp/test_autonomy_e2e.py` | `tests/integration/test_autonomy_e2e.py` | Real autonomy guard e2e test |

### G. New artifacts created

| File | Purpose |
|---|---|
| `docs/roadmap/dashboards4sale.md` | D4S satellite stub, M0 = repo extraction |
| `docs/roadmap/README.md` (Ventures Registry table appended) | "Where do my businesses live" answer; 6 ventures |
| `sandbox/README.md` (rewritten) | In-flight work rules + monthly sweep + no secrets + graduate-or-archive |
| `zzzArchive/_pre-cleanup-20260502/MANIFEST.md` | Full audit trail of this batch |
| `zzzArchive/_pre-cleanup-20260502/_backup-gitignored.tar.gz` | Pre-state backup of gitignored folders |
| `docs/reference/repo-structure.md` (full rewrite) | Live mount section added, 04-27 errors fixed (agent_outputs and tmp_upload were not orphans) |
| `docs/AGENT_SOP.md` (Folder Governance section + 2 new hard rules) | Locked rules |
| `tests/integration/` (new dir) | Home for real e2e tests |
| `sandbox/.tmp/` | Gitignored throwaway corner |

### H. Config changes

| File | Change | Why |
|---|---|---|
| `.gitignore` | Added `sandbox/.tmp/` rule | Sandbox tracked, only `.tmp/` corner ignored |
| `.pre-commit-config.yaml` | Added `exclude: ^zzzArchive/` to no-em-dashes hook | Archived files preserve original em-dashes; hook would fail otherwise |

### I. Code change (separate commit, VPS-deployed)

| File | Change | Effect |
|---|---|---|
| `orchestrator/handlers_chat.py` | `limit=50` → `limit=20` (2 occurrences: web chat path L322, Telegram path L652) | ~2.5x reduction on chat call token cost |

VPS deployed via `bash scripts/orc_rebuild.sh` on 2026-05-02 ~18:32 UTC. Container `orc-crewai` Up healthy with new limit verified via `docker exec grep limit= /app/handlers_chat.py`.

### J. Notion task closeouts

| Task ID | Title | Status before | Status after |
|---|---|---|---|
| T-260306 | Create savepoint tag before archive cleanup | Not Started | Done (with Outcome note) |
| T-260307 | Archive dead folders | Not Started | Done (with detailed Outcome note) |

### K. Five production-mount footguns CAUGHT and PRESERVED

These would have broken production if archived/moved. The 04-27 plan had them as "orphan" candidates. Sankofa + Karpathy caught all five.

| Path | Why kept | Reference |
|---|---|---|
| `setup-database.sql` (root) | Postgres init mount | `docker-compose.yml:32` |
| `agent_outputs/` | Container `/app/outputs` mount + thepopebot ALLOWED_PATHS | `docker-compose.yml:204` |
| `tmp_upload/` | Transcribe skill `WORK_DIR` | `skills/transcribe/transcribe.py:37` |
| `thepopebot/chat-ui/` | Path-watched by GitHub Actions | `.github/workflows/deploy-agentshq.yml:8` |
| `codex_ssh/` | Active Codex tool | gitignored, in active use |

### L. Explicitly NOT done today (deferred)

| Item | Why deferred | Where tracked |
|---|---|---|
| `thepopebot/chat-ui/` → `ui/atlas/` | Coordinated GitHub Actions + docker-compose + VPS window required | repo-structure.md Live Mount Points; original 04-27 handoff |
| `Dashboards4Sale/` extraction to `bokar83/dashboards4sale` repo | 30-60 min focused session needed | `docs/roadmap/dashboards4sale.md` M0 |

---

## Three-way sync at session end

| Surface | Commit | State |
|---|---|---|
| Local `D:\Ai_Sandbox\agentsHQ` | `092900f` | working tree clean (modulo gitignored content) |
| GitHub `bokar83/agentHQ` `main` | `092900f54ef824aa63921a9c27d0cdee7bdfdf59` | mirrored |
| VPS `/root/agentsHQ` | `092900f` | mirrored |
| `orc-crewai` container | running with `limit=20` verified live | Up healthy |

---

## Atlas roadmap entry

Full session log appended to `docs/roadmap/atlas.md` (search for `2026-05-02 (Friday afternoon): Move Day`).
