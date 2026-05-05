# Structural Cleanup v2: Path Translation Table: 2026-05-02

**Purpose:** single source of truth for every path change made on 2026-05-02 across the structural cleanup session. Old code, old handoffs, old memory entries reference old paths. This doc maps old to new without rewriting 30+ historical handoffs.

**Session arc:** governance scaffolding (Compass M0+M1) → Dashboards4Sale extraction → external/ + task_progress/ relocations → output/ documentation (full restructure deferred to Compass M5) → outputs/ → agent_outputs/ migration.

**Final commit chain on `main` (chronological):**

```text
edb4df1 chore(repo): Phase 4 outputs/ -> agent_outputs/ migration
51e4955 roadmap(compass): add M5 output/ submodule reconciliation + restructure
42c4058 docs(output): document output/ folder anatomy + critical do-not-merge warning
5fa6e58 chore(repo): Phase 2 hygiene moves: external -> docs/research/external-references, task_progress -> data/codex
c3fe253 satellite(dashboards4sale): extracted to bokar83/dashboards4sale, original archived
ec9bac8 governance(compass M0+M1): GOVERNANCE.md + AGENTS.md compliance + folder-purpose hook
adeb1a0 docs(handoff): Move Day action log + harvest CTA note SUPERSEDED
092900f perf(chat): drop conversation history limit 50 to 20 in handlers_chat.py
7fe5d6d chore(repo): Move Day structural cleanup + Folder Governance + Ventures Registry
```

**Savepoint tag:** `savepoint-pre-archive-cleanup-20260502` (from Move Day, covers the entire 2026-05-02 session).

---

## Path translation table (old -> new)

### Folder relocations

| Old path | New path | When | Reason |
|---|---|---|---|
| `Dashboards4Sale/` | satellite repo `bokar83/dashboards4sale` (cloned to `d:/tmp/dashboards4sale-extract` then pushed) | Phase 1 | Platform-with-Satellites Rule: products with own URL/customer/revenue get own repo |
| `Dashboards4Sale/` (local copy) | `zzzArchive/_pre-cleanup-20260502/Dashboards4Sale-original/` | Phase 1 | No-delete rule; original preserved alongside the satellite extraction |
| `external/CLI-Anything/` | `docs/research/external-references/CLI-Anything/` | Phase 2 | Research artifacts belong in docs/, not at top-level |
| `external/OpenSpace/` | `docs/research/external-references/OpenSpace/` | Phase 2 | Research artifacts belong in docs/, not at top-level |
| `task_progress/codex-task-progress.txt` | `data/codex/task_progress.txt` | Phase 2 | Runtime ephemera belongs under data/, not at top-level |
| `outputs/` (272 files, agent task output sink) | `agent_outputs/` (same 272 files) | Phase 4 | Align host folder name with AGENTS_OUTPUT_DIR env var + docker-compose mount target |

### Folder NOT relocated (preserved due to live-mount or scale)

| Path | Why kept | Reference |
|---|---|---|
| `output/` (singular submodule, 14 websites + 5 nested submodules, 996 MB) | Live submodule + 30+ doc refs + vercel-launch.sh dependency. Restructure deferred to Compass M5. | `docs/reference/output-folder-anatomy.md` |
| `setup-database.sql` (root) | Postgres init mount | `docker-compose.yml:32` |
| `agent_outputs/` (now houses former `outputs/` content) | `/app/outputs` container mount | `docker-compose.yml:204` |
| `tmp_upload/` | Transcribe skill `WORK_DIR` | `skills/transcribe/transcribe.py:37` |
| `thepopebot/` + `thepopebot/chat-ui/` | docker-compose.thepopebot.yml + GH Actions path filter | `.github/workflows/deploy-agentshq.yml:8` |
| `codex_ssh/` | Active Codex tool | gitignored, in active use |

### Reference updates

| File | Old reference | New reference |
|---|---|---|
| `agents/security_agent/scripts/audit_git.py:35` | `"outputs/"` | `"agent_outputs/"` |
| `.gitignore` lines 52-53 | `agent_outputs/` + `outputs/` (both listed) | only `agent_outputs/` |
| `.gitignore` external entry | `external/` | `docs/research/external-references/` |
| `.gitignore` task_progress entry | `task_progress/` | `data/codex/` |
| `AGENTS.md` (root) | 3 references to `outputs/` and `/outputs/` | updated to `agent_outputs/` |
| `scripts/check_folder_purpose.py` exempt list | included `external`, `task_progress`, `outputs` | removed (those folders no longer top-level); added `output`, `Dashboards4Sale`, `zzzArchive`, `scratch`, `.playwright-mcp` |
| `feedback_codex_sandbox_commit_pattern.md` (memory) | `task_progress/codex-task-progress.txt` | `data/codex/task_progress.txt` |
| `n8n/AGENTS.md` | references to `workflows/` subfolder | consolidated into `n8n/imported/` description |
| `docs/roadmap/dashboards4sale.md` M0 | "Queued. Trigger: dedicated 30-60 min extraction session" | "✅ SHIPPED 2026-05-02 with verification result" |
| `docs/roadmap/README.md` Ventures Registry | D4S URL "TBD" | live `bokar83/dashboards4sale` URL |

### New artifacts created

| File | Purpose |
|---|---|
| `docs/GOVERNANCE.md` | Constitution / routing table (64 lines) for the 8 governance surfaces |
| `docs/roadmap/compass.md` | Governance roadmap with M0-M5 milestones |
| `docs/reference/output-folder-anatomy.md` | Full anatomy of output/ submodule including the do-not-merge warning |
| `scripts/check_folder_purpose.py` | Pre-commit hook enforcing every-folder-has-AGENTS.md rule |
| `~/.claude/projects/.../memory/reference_governance_constitution.md` | Memory pointer to GOVERNANCE.md |
| `~/.claude/projects/.../memory/reference_folder_governance.md` | Memory pointer to Folder Governance rule (was created earlier in session) |
| `~/.claude/projects/.../memory/feedback_make_educated_decisions.md` | Memory pointer to triage-autonomy rule |
| `~/.claude/projects/.../memory/feedback_rod_send_freeze_until_wed_2026_05_06.md` | Memory hard rule on Rod outreach freeze |
| 11 new folder-level `AGENTS.md` files | config, data, deliverables, migrations, projects, research, sql, templates, tests, thepopebot, zzzArchive: bringing folder coverage from 32% to 100% |
| 6 existing `AGENTS.md` files updated | docs, orchestrator, scripts, signal_works, skills, workspace: added GOVERNANCE.md cross-references |

---

## What is NOT done (explicit deferrals tracked in roadmaps)

| Item | Where tracked | Why deferred |
|---|---|---|
| `output/` submodule .gitmodules reconciliation (attire-inspo-app vs signal-works-demo-hvac mismatch; the two are SEPARATE repos, never merge) | Compass M5 in `docs/roadmap/compass.md` | Two-repo decision requires Boubacar's call; high blast radius (996 MB, 14 websites, 5 nested submodules) |
| `output/websites/` and `output/apps/` promotion to top-level | Compass M5 | Same as above |
| `attire-inspo-app` move to `workspace/aminoa/` per Aminöa-folder pattern | Compass M5 | Same as above |
| `thepopebot/chat-ui/` -> `ui/atlas/` | Original 04-27 handoff; Compass M5 backlog | Coordinated GitHub Actions + docker-compose + VPS window required |
| 5 more enforcement hooks (memory frontmatter, session-log, redundancy, retirement, doc-size) | Compass M2 | Bigger build out (5 hooks, ~30 lines each); separate session |
| Quarterly purge cadence | Compass M3 | Date-gated, first run 2026-08-02 |
| LLM-readable governance manifest (governance.manifest.json) | Compass M4 | After M2 stabilizes |

---

## Three-way nsync at session end

| Surface | Commit | State |
|---|---|---|
| Local `D:\Ai_Sandbox\agentsHQ` | `edb4df1` | working tree clean (modulo gitignored content) |
| GitHub `bokar83/agentHQ` `main` | (push pending in Phase 6) | pending |
| VPS `/root/agentsHQ` | (pull pending in Phase 6) | pending |
| New satellite `bokar83/dashboards4sale` | `4b87d5d` (init commit) | live |

---

## How to revert any individual item

- **Revert the entire 2026-05-02 session:** `git reset --hard savepoint-pre-archive-cleanup-20260502` and re-extract the gitignored backup tarball at `zzzArchive/_pre-cleanup-20260502/_backup-gitignored.tar.gz`.
- **Revert a specific commit:** `git revert <commit-sha>` from the chain above.
- **Revert a specific file move:** consult the Path Translation Table above; file is at the new path, was at the old path. `git mv <new> <old>` to undo, or restore from the savepoint tag.
- **Revert the Dashboards4Sale extraction:** the satellite repo at `bokar83/dashboards4sale` stays as evidence of the extraction; the original tracked content is preserved at `zzzArchive/_pre-cleanup-20260502/Dashboards4Sale-original/Dashboards4Sale/` and can be `git mv`'d back to the root.

---

## Session memory + ruleset locked today

- **Word "delete" retired** (locked Move Day morning): items not used go to `zzzArchive/<batch>/<path>/` with manifest. Never deleted.
- **Make educated decisions on routine triage:** don't paginate three-way verdicts to Boubacar; surface only irreversible/strategic/genuinely-ambiguous calls.
- **Folder Governance rule:** every folder has AGENTS.md or README.md. Now enforced by `scripts/check_folder_purpose.py` pre-commit hook.
- **`output/` repo separation hard rule:** `bokar83/attire-inspo-app` and `bokar83/signal-works-demo-hvac` are two separate repos; never merge. Compass M5 reconciles.
- **Rod / Elevate send freeze until Wed 2026-05-06** (locked Move Day afternoon).
- **Path B governance shape:** `docs/GOVERNANCE.md` is routing table, `docs/AGENT_SOP.md` is rules library. AGENT_SOP stays load-bearing.
- **Conflict resolution precedence:** user > hooks > AGENT_SOP > memory > local AGENTS.md.
