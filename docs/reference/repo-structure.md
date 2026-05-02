# agentsHQ Repository Structure

Last updated: 2026-05-02 (Move Day). Verified against live directory scan and `docker-compose.yml` mount points.

## Legend

- **Owner**: who controls this folder (production / workspace / archive / external / tooling)
- **Routing**: what goes here and what does not
- **Status**: active / orphan / archive / submodule / gitignored / live-mount

---

## Top-Level Folders

### Production System

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `orchestrator/` | production | All Python app code: agents, crews, tools, handlers, engine, saver, skills. The only place new backend code goes. | active |
| `signal_works/` | production | Signal Works outreach pipeline code. Separate from orchestrator by design (different team/product). Future satellite once import boundaries are refactored. | active |
| `skills/` | production | Canonical skill library. New skills created here first, then copied to `~/.claude/skills/`. Never create skills only in the global folder. | active |
| `config/` | production | App configuration files (non-secret). | active / gitignored |
| `sql/` | production | SQL migration files. | active |
| `templates/` | production | Email and document templates used by agents. | active |
| `scripts/` | production | One-off operational scripts (skool harvester, pre-commit hooks, deploy scripts, ops helpers). Not imported by orchestrator. | active |
| `tests/` | production | Root-level test suite. Includes `tests/integration/` for end-to-end tests (graduated from `tmp/` 2026-05-02). | active |
| `docs/` | production | All documentation: roadmaps, handoffs, playbooks, reference, SOP. Source of truth for session context. | active |
| `migrations/` | production | DB migration files. | active |
| `n8n/` | production | n8n workflow imports (JSON). `n8n/imported/` holds synced workflows. Consolidated 2026-05-02 (formerly split across `workflows/`, `n8n-workflows/`). | active |

### Live Mount Points (DO NOT MOVE)

These paths are mounted by `docker-compose.yml` or referenced by skills/workflows. **Moving them breaks production.**

| Folder / file | Why | Reference |
|---|---|---|
| `setup-database.sql` (root) | Postgres init mount → `/docker-entrypoint-initdb.d/setup-database.sql` | `docker-compose.yml:32` |
| `agent_outputs/` | Container outputs mount → `/app/outputs` | `docker-compose.yml:204` + thepopebot ALLOWED_PATHS |
| `tmp_upload/` | Transcribe skill `WORK_DIR` | `skills/transcribe/transcribe.py:37` |
| `thepopebot/chat-ui/` | GitHub Actions deploy path filter | `.github/workflows/deploy-agentshq.yml:8` |
| `thepopebot/` (parent) | docker-compose.thepopebot.yml + thepopebot-event-handler container | `.github/workflows/rebuild-event-handler.yml`, `docker-compose.thepopebot.yml` |
| `codex_ssh/` | Active Codex tool (gitignored) | gitignored line 153 |

### Agent Output Sinks

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `outputs/` | production | **Primary agent output sink.** All live code writes here via `AGENTS_OUTPUT_DIR` env var (default `/app/outputs`). Gitignored. Do not move or rename. | active / gitignored |
| `agent_outputs/` | production | **LIVE container mount** (see Live Mount Points). Container writes `/app/outputs` here. Old contents archived 2026-05-02. | active / live-mount / gitignored |
| `logs/` | production | Application logs. Gitignored. | active / gitignored |

### Human Workspace

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `workspace/` | workspace | Boubacar's working area: demo sites, mocks, articles, media, AB tests. Not imported by any production code. Gitignored. | active / gitignored |
| `workspace/clients/[slug]/` | workspace | Per-client engagement folders (AGENTS.md + BRIEF.md + engagements/ + deliverables/). | active |
| `workspace/catalyst-works/` | workspace | CW brand work. | active |
| `workspace/internal/` | workspace | Platform dev scratch. | active |
| `data/` | workspace | Datasets, clusters, local DB snapshots, runtime state. Gitignored. | active / gitignored |
| `sandbox/` | workspace | **In-flight builds and experimental work. Tracked in git so laptop dying does not lose work.** No secrets. Monthly sweep: 30d untouched → graduate or archive. `sandbox/.tmp/` is gitignored throwaway corner. Full rule in `sandbox/README.md`. | active / tracked |
| `tmp_upload/` | workspace | **Transcribe skill WORK_DIR (live).** Old transcripts archived 2026-05-02. | active / live-mount / gitignored |

### External / Submodule

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `output/` | submodule | Git submodule pointing to `bokar83/attire-inspo-app` (Next.js). NOT an agent output folder: the name is coincidental. Do not write agent output here. | submodule / gitignored |
| `skills/community/` | submodule | Git submodule: `sickn33/antigravity-awesome-skills`. Community skill library. | submodule |
| `external/` | external | Third-party repos cloned for reference. Not imported by production. Gitignored. | active / gitignored |
| `tools/` | external | External CLI tools (autocli binary). Gitignored. | active / gitignored |
| `node_modules/` | tooling | JS dependencies. Gitignored. | active / gitignored |

### Satellites (own GitHub repos)

| Satellite | Type | Repo | Status |
| --- | --- | --- | --- |
| `Dashboards4Sale/` | product | `bokar83/dashboards4sale` (extraction pending) | submodule today, satellite target |
| `signal_works/` | productized AI presence | `bokar83/agentshq` (this repo) until imports refactored | future satellite |

Satellites are referenced in `docs/roadmap/` and the Ventures Registry (`docs/roadmap/README.md`). Their code never lives inside agentsHQ once extracted.

### Hidden / Dot Folders

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `.agents/` | tooling | Skills and workflows for non-Claude agents. | active |
| `.windsurf/` | tooling | Windsurf IDE skills. | active |
| `.claude/` | tooling | Claude Code worktrees + scheduled tasks. | active |
| `.superpowers/` | tooling | Brainstorm artifacts from superpowers skill. | active |
| `.worktrees/` | tooling | Git worktrees. Gitignored. | active / gitignored |
| `.venv/` | tooling | Python virtual environment. Gitignored. | active / gitignored |
| `.vscode/` | tooling | VSCode settings. | active |
| `.github/` | tooling | GitHub Actions workflows. | active |
| `.tmp/` | scratch | pytest cache + antivirus quarantine (regenerable). Gitignored. | active / gitignored |
| `.codex_ssh/` | scratch | Empty hidden duplicate of codex_ssh (permission-locked). Gitignored. | active / gitignored |
| `codex_ssh/` | active tool | Active Codex SSH working directory. Gitignored. | active / gitignored |

### Archive

| Folder | Owner | Routing | Status |
|--------|-------|---------|--------|
| `zzzArchive/` | archive | **Boubacar's signature graveyard. Gitignored. Batch-organized by date.** Each batch has a `MANIFEST.md` indexing every archived item with original path, archive path, reason, and reference-grep result. **`zzzArchive/` itself is never archived.** Latest batch: `_pre-cleanup-20260502/`. | active / gitignored |

---

## Top-Level Files (clean as of 2026-05-02)

| File | Status | Purpose |
|------|--------|---------|
| `AGENTS.md` | active | Soul file for all agents |
| `AGENT_INSTRUCTIONS.md` | active | Agent runtime instructions |
| `CLAUDE.md` | active | Claude Code session context |
| `CODEX.md` | active | Codex session context |
| `README.md` | active | Human-readable system overview |
| `CHANGELOG.md` | active | Release log |
| `LESSONS-LEARNED.md` | active | Engineering lessons archive |
| `review-gate.md` | active | PR review gate doc |
| `setup-database.sql` | active / live-mount | Postgres init script (mounted by docker-compose) |
| `system-status.sh` | active | Ops convenience |
| `deploy.sh` | active | Deploy convenience |
| `ignite.bat` | active | Windows launcher |
| `package.json`, `package-lock.json` | active | JS deps for mermaid-cli / Hyperframes |
| `pyrightconfig.json` | active | Python type checking |
| `vercel.json` | active | Vercel config |
| `skills-lock.json` | active / gitignored | Skill version lock |
| `docker-compose.yml`, `docker-compose.thepopebot.yml` | active | Container orchestration |
| `.gitignore`, `.gitmodules`, `.pre-commit-config.yaml`, `.env.example` | active | Repo hygiene |
| `.env`, `.secrets.baseline*` | active / gitignored | Secrets (never committed) |

**Cleaned up 2026-05-02 (archived to `zzzArchive/_pre-cleanup-20260502/`):**

- `schema_v2.sql` → archived (older than `docs/database/schema_v2.sql`)
- `ideas_full_list.txt`, `ideas_full_list_utf8.txt`, `search_output.txt` → archived (Notion is source of truth)
- `code_review_20260422.md` → moved to `docs/handoff/`
- `adversarial_report.md` → moved to `docs/reference/`
- `MakeShortcut.ps1`, `Run-Local-SecureWatch.bat`, `run_council_strat.py` → moved to `scripts/`
- `test_sankofa.py` → moved to `tests/`
- `a-b testing.xlsx`, `ninja.ico` → moved to `workspace/` (both gitignored)

---

## Platform With Satellites Rule (LOCKED 2026-04-27)

**agentsHQ is the AI operations platform. It is NOT a monorepo.**

> If the thing being built has its own URL, its own customer, or its own revenue stream: it gets its own GitHub repo (satellite).
> If it is infrastructure, tooling, or an AI capability that powers agentsHQ: it lives here.

**Client work lives in `workspace/clients/[slug]/`: never in orchestrator code.**

**Satellites are tracked in the Ventures Registry** (`docs/roadmap/README.md`).

---

## Folder Governance (LOCKED 2026-05-02)

See `docs/AGENT_SOP.md` "Folder Governance" section + `reference_folder_governance.md` in memory. Summary:

1. Every top-level folder has an `AGENTS.md` or `README.md` explaining its purpose.
2. No folder is created without a stated purpose.
3. **The word "delete" is retired.** Items not used → archived to `zzzArchive/<batch>/<path>/` with `MANIFEST.md` entry.
4. Live mounts never move. Reference-grep + `docker-compose.yml` check before any move.
5. Triple-verify before archive: grep, mount check, Codex review.
6. `zzzArchive/` is the graveyard. Gitignored. Batch-organized. Never archived itself.
7. Sandbox is for in-flight work (tracked). `sandbox/.tmp/` is gitignored throwaway.

---

## Move Day 2026-05-02 Summary (this session)

**Archived (in `zzzArchive/_pre-cleanup-20260502/`):**

- `remote-access-auditor/`: duplicate of `skills/remote-access-auditor/`
- `server-setup/`: one-time VPS bootstrap, superseded
- `workflows/`, `workflows/legacy/`: superseded by `n8n/imported/`
- `n8n-workflows/`: older duplicates of files now in `n8n/imported/`
- `scratch/`: old probes 2026-04-12 to 2026-04-20
- `tmp/` content (codex commit drafts + old apollo probes)
- `tmp_upload/` old transcripts (folder kept for transcribe skill)
- `agent_outputs/capital-allocation/` (folder kept as live mount)
- `.tmp/CLAUDE.md` (pytest cache regenerable, left in place)
- Root orphans: schema_v2.sql, ideas_full_list*.txt, search_output.txt

**Graduated:**

- `tmp/test_phase1_e2e.py` and `tmp/test_autonomy_e2e.py` → `tests/integration/`

**Consolidated:**

- 6 n8n workflow JSONs across 3 folders → `n8n/imported/n50-n52*.json`

**New:**

- `docs/roadmap/dashboards4sale.md` (satellite stub)
- `docs/roadmap/README.md` Ventures Registry table
- `sandbox/README.md` (in-flight work rules)
- `docs/AGENT_SOP.md` Folder Governance section
- `~/.claude/projects/.../memory/reference_folder_governance.md`

**Token efficiency fix (separate commit):**

- `orchestrator/handlers_chat.py` `limit=100` → `limit=20`

**5 production-mount footguns caught and prevented:** see "Live Mount Points" section above.
