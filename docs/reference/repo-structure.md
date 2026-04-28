# agentsHQ Repository Structure

Last updated: 2026-04-27. Verified against live directory scan.

## Legend

- **Owner**: who controls this folder (production / workspace / archive / external / tooling)
- **Routing**: what goes here and what does not
- **Status**: active / orphan / archive / submodule / gitignored

---

## Top-Level Folders

### Production System

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `orchestrator/` | production | All Python app code: agents, crews, tools, handlers, engine, saver, skills. The only place new backend code goes. | active |
| `signal_works/` | production | Signal Works outreach pipeline code. Separate from orchestrator by design (different team/product). | active |
| `skills/` | production | Canonical skill library. New skills created here first, then copied to `~/.claude/skills/`. Never create skills only in the global folder. | active |
| `config/` | production | App configuration files (non-secret). | active |
| `sql/` | production | SQL migration files and schema snapshots. | active |
| `templates/` | production | Email and document templates used by agents. | active |
| `scripts/` | production | One-off operational scripts (skool harvester, pre-commit hooks, etc.). Not imported by orchestrator. | active |
| `tests/` | production | Root-level test suite. Orchestrator-level tests live in `orchestrator/tests/`. | active |
| `docs/` | production | All documentation: roadmaps, handoffs, playbooks, reference, SOP. Source of truth for session context. | active |

### Agent Output Sinks

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `outputs/` | production | **Primary agent output sink.** All live code writes here via `AGENTS_OUTPUT_DIR` env var (default `/app/outputs`). Gitignored. Do not move or rename. | active / gitignored |
| `agent_outputs/` | workspace | Manual/one-off agent outputs (e.g. capital allocation doc). Not written to by production code. Candidate for merge into `workspace/` at cleanup. | orphan |
| `logs/` | production | Application logs. Gitignored. | active / gitignored |

### Human Workspace

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `workspace/` | workspace | Boubacar's working area: demo sites, mocks, articles, media, AB tests. Not imported by any production code. | active |
| `data/` | workspace | Datasets, clusters, local DB snapshots. | active |
| `sandbox/` | workspace | Experimental code that is not production-ready. | orphan - candidate for zzzArchive |
| `scratch/` | workspace | Throwaway notes and fragments. | orphan - candidate for deletion |
| `tmp/` | workspace | Temporary files. | orphan - candidate for deletion |
| `tmp_upload/` | workspace | Temporary upload staging. | orphan - candidate for deletion |
| `n8n-workflows/` | workspace | n8n workflow JSON exports. Separate from `n8n/` (see below). | active |

### External / Submodule

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `output/` | submodule | Git submodule pointing to `bokar83/attire-inspo-app` (Next.js). Gitignored. NOT an agent output folder - the name is coincidental. Do not write agent output here. | submodule / gitignored |
| `skills/community/` | submodule | Git submodule: `sickn33/antigravity-awesome-skills`. Community skill library. | submodule |
| `external/` | external | Third-party repos cloned for reference (CLI-Anything, OpenSpace). Not imported by production. | archive |
| `tools/` | external | External CLI tools (opencli-rs binary). | active |
| `node_modules/` | tooling | JS dependencies for mermaid-cli / HyperFrames. Gitignored. | active / gitignored |

### Candidate for Separate Repo or Archive

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `Dashboards4Sale/` | external product | Entirely separate product (Arabic/French/English budget dashboards). No relation to agentsHQ runtime. Should live in its own repo. | orphan - separate repo on next cleanup |
| `thepopebot/` | abandoned | Separate bot project with its own skills and chat UI. No active development. | orphan - archive |
| `remote-access-auditor/` | abandoned | One-time security audit tool. Skill exists at `skills/remote-access-auditor/`. | orphan - archive |
| `codex_ssh/` | abandoned | SSH config experiment for Codex access. Superseded by current setup. | orphan - archive |
| `server-setup/` | archive | VPS provisioning scripts from initial setup. One-time use. | archive |

### n8n

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `n8n/` | production | n8n workflow imports (JSON). `n8n/imported/` holds synced workflows. | active |
| `n8n-workflows/` | workspace | n8n workflow exports/drafts. Should consolidate with `n8n/` at cleanup. | orphan - merge into n8n/ |

### Workflows

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `workflows/` | archive | Old workflow definitions. `workflows/legacy/` confirms these are superseded. | archive - candidate for zzzArchive |

### Hidden / Dot Folders

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `.agents/` | tooling | Skills and workflows for non-Claude agents. | active |
| `.windsurf/` | tooling | Windsurf IDE skills. Parallel to `.agents/` and `~/.claude/skills/`. | active |
| `.claude/` | tooling | Claude Code worktrees. | active |
| `.superpowers/` | tooling | Brainstorm artifacts from superpowers skill. | active |
| `.worktrees/` | tooling | Git worktrees. | active |
| `.venv/` | tooling | Python virtual environment. Gitignored. | active / gitignored |
| `.vscode/` | tooling | VSCode settings. | active |
| `.github/` | tooling | GitHub Actions workflows. | active |
| `.codex_ssh/` | abandoned | Duplicate of `codex_ssh/` (hidden version). | orphan - delete |
| `.tmp/` | workspace | Temporary files (hidden). Duplicate of `tmp/`. | orphan - delete |

---

## Top-Level Files (Non-Standard)

| File | Status | Note |
|------|--------|------|
| `a-b testing.xlsx` | orphan | Should live in `workspace/` or `data/` |
| `adversarial_report.md` | orphan | One-time security report. Move to `docs/reference/` or `zzzArchive/` |
| `code_review_20260422.md` | orphan | Move to `docs/handoff/` or `zzzArchive/` |
| `ideas_full_list.txt` / `ideas_full_list_utf8.txt` | orphan | Superseded by Notion Ideas DB. Delete or move to `zzzArchive/` |
| `search_output.txt` | orphan | Scratch file. Delete. |
| `test_sankofa.py` | orphan | Test script at root. Move to `tests/` |
| `run_council_strat.py` | orphan | One-off script. Move to `scripts/` |
| `schema_v2.sql` | orphan | Move to `sql/` |
| `setup-database.sql` | orphan | Move to `sql/` |
| `system-status.sh` | active | Keep at root for convenience (ops script) |
| `deploy.sh` | active | Keep at root |
| `ignite.bat` | active | Keep at root |
| `MakeShortcut.ps1` | orphan | Windows shortcut helper. Move to `scripts/` |
| `Run-Local-SecureWatch.bat` | orphan | Move to `scripts/` |
| `ninja.ico` | orphan | Move to `workspace/` or delete |
| `skills-lock.json` | active | Skill version lock. Keep at root. |
| `pyrightconfig.json` | active | Python type checking config. Keep at root. |
| `vercel.json` | active | Vercel config. Keep at root. |

---

## Platform With Satellites Rule (LOCKED 2026-04-27)

**agentsHQ is the AI operations platform. It is NOT a monorepo.**

> If the thing being built has its own URL, its own customer, or its own revenue stream - it gets its own GitHub repo (satellite).
> If it is infrastructure, tooling, or an AI capability that powers agentsHQ - it lives here.

**Satellites referenced in `docs/roadmap/` but code never lives in agentsHQ:**

| Satellite | Status | Repo |
| --- | --- | --- |
| `Dashboards4Sale` | Create own repo, remove submodule | bokar83/dashboards4sale (pending) |
| `signal_works/` | Platform-adjacent, stays at root until imports refactored | future: own repo |

**Client work lives in `workspace/clients/[slug]/` - never in orchestrator code.**

---

## Weekend Cleanup Sequence (from Council verdict)

1. Tag savepoint before touching anything.
2. Create `Dashboards4Sale` as its own GitHub repo, remove from agentsHQ.
3. Move `thepopebot/`, `remote-access-auditor/`, `codex_ssh/`, `.codex_ssh/` to `zzzArchive/`.
4. Delete `tmp/`, `.tmp/`, `scratch/`, `search_output.txt`.
5. Move orphan root files to their correct folders (see table above).
6. Merge `n8n-workflows/` into `n8n/`.
7. Evaluate `sandbox/` and `workflows/` - archive or delete.
8. Merge `agent_outputs/` into `workspace/` or delete.
9. Consolidate `.agents/skills/` and `.windsurf/skills/` documentation - confirm which agents read from which path.
