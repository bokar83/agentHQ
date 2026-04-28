# Session Handoff - Repo Architecture + Platform-With-Satellites - 2026-04-27

## TL;DR

Full architecture planning session. Started as a routine structure cleanup, grew into a deep analysis covering token efficiency, LLM navigability, client scalability, and saleability. Three tools ran: Sankofa Council (3 passes), Karpathy Principles audit, deep code impact analysis via subagent. Permanent architecture rule locked: agentsHQ is the AI operations platform, not a monorepo. All Priority 1 work (additive only: no file moves) shipped and pushed to GitHub as commit `2343b59`. Weekend cleanup routine scheduled for Saturday May 3 at 9 AM MT.

## What was built / changed

**New skills:**
- `skills/karpathy/SKILL.md`: 4-principle code audit skill, available as `/karpathy`
- `~/.claude/skills/karpathy/SKILL.md`: global copy

**Updated skills:**
- `skills/superpowers/skills/verification-before-completion/SKILL.md`: Karpathy check added as Step 5 (auto-fires before every ship)

**New AGENTS.md files (LLM context injection per folder):**
- `orchestrator/AGENTS.md`: context scoping table: which files to load per task type
- `skills/AGENTS.md`: skill creation rules + category taxonomy
- `docs/AGENTS.md`: SOP navigation
- `n8n/AGENTS.md`: n8n rules (no docker touch)
- `signal_works/AGENTS.md`: pipeline context + future satellite note
- `scripts/AGENTS.md`: pre-commit hook path warning

**New reference docs:**
- `skills/_index.md`: 71-skill machine-readable routing table (replaces reading 71 SKILL.md files)
- `docs/reference/repo-structure.md`: full folder taxonomy with owner/routing/status
- `docs/reference/client-template/AGENTS.md`: template for new client folders
- `docs/reference/client-template/BRIEF.md`: template for new client briefs

**Updated root files:**
- `AGENTS.md`: platform-with-satellites rule, workspace structure, client governance added

**Workspace structure (gitignored, local only):**
- `workspace/internal/`: platform dev scratch
- `workspace/clients/`: client engagement folders
- `workspace/catalyst-works/`: CW brand work

**Session log:**
- `docs/roadmap/atlas.md`: 2026-04-27 entry appended

**Scheduled routine:**
- `trig_0162ZSF53Rd5dEugztbSy3Nf`: Saturday 2026-05-03 09:00 MT, weekend cleanup checklist
- View: https://claude.ai/code/routines/trig_0162ZSF53Rd5dEugztbSy3Nf

## Decisions made

1. **Platform-with-satellites (permanent):** agentsHQ is the AI operations platform. Anything with its own URL, customer, or revenue stream gets its own GitHub repo. Written into AGENTS.md and repo-structure.md.

2. **Dashboards4Sale is a satellite:** Create `bokar83/dashboards4sale` repo, remove submodule from agentsHQ. Not yet done: separate task.

3. **signal_works/ stays at root:** Has active Python imports in orchestrator. Future satellite once import boundaries are refactored.

4. **Client governance:** New clients go in `workspace/clients/[slug]/` with AGENTS.md + BRIEF.md from `docs/reference/client-template/`. No orchestrator code changes for a new client.

5. **Token efficiency findings (not yet fixed):**
   - `handlers_chat.py` line ~321: `limit=100` - change to 20 for ~5x token reduction on chat calls
   - `design_context.py`: reads styleguide files from disk per crew build (~5-7K tokens): cache on startup
   - `engine.py` lines 22-35: 6-turn history duplicated across ALL agents in crew: inject once

6. **Karpathy auto-fires:** Step 5 in verification-before-completion. Standalone `/karpathy` available on demand.

7. **thepopebot/chat-ui/ move deferred:** Requires 3 coordinated steps (GitHub Actions path filter + docker-compose.thepopebot.yml + VPS restart). Must be done as its own window with a savepoint first.

## What is NOT done (explicit)

- Archive moves (remote-access-auditor/, codex_ssh/, sandbox/, scratch/, tmp/, etc.): weekend task, savepoint first
- thepopebot/chat-ui/ -> ui/atlas/: needs coordinated 3-step window
- n8n-workflows/ merge into n8n/: weekend
- zzzArchive/ rename to archive/: weekend
- Dashboards4Sale separate repo: separate task
- Token efficiency Python fixes: separate task
- workspace/ AGENTS.md files are local only (gitignored): not pushed to GitHub

## Open questions

- None blocking. All decisions made.

## Next session must start here

1. Read `docs/roadmap/atlas.md` for current atlas state (M5 gate opens 2026-05-08, VPS orphan archive due for deletion)
2. If it is Saturday May 3 or later: the cleanup routine fired at 9 AM MT: check it
3. For archive cleanup: tag savepoint FIRST (`git tag savepoint-pre-archive-cleanup-YYYYMMDD`), then execute safe moves from `docs/reference/repo-structure.md` Weekend Cleanup Sequence
4. For thepopebot move: do NOT start without reading the coordinated window steps in `docs/reference/repo-structure.md`
5. Token fix is one line: `handlers_chat.py` `limit=100` -> `limit=20`, then `python -m py_compile`, then VPS deploy

## Files changed this session

```text
AGENTS.md                                          (modified)
orchestrator/AGENTS.md                             (created)
skills/AGENTS.md                                   (created)
skills/_index.md                                   (created)
skills/karpathy/SKILL.md                           (created)
skills/superpowers/skills/verification-before-completion/SKILL.md  (modified)
docs/AGENTS.md                                     (created)
docs/reference/repo-structure.md                   (created)
docs/reference/client-template/AGENTS.md           (created)
docs/reference/client-template/BRIEF.md            (created)
docs/roadmap/atlas.md                              (modified: session log appended)
docs/handoff/2026-04-28-atlas-chat-routing-fix.md  (pre-existing, em-dash fix only)
n8n/AGENTS.md                                      (created)
signal_works/AGENTS.md                             (created)
scripts/AGENTS.md                                  (created)
~/.claude/skills/karpathy/SKILL.md                 (created: global copy)
~/.claude/projects/.../memory/project_repo_architecture_2026_04_27.md  (created)
~/.claude/projects/.../memory/MEMORY.md            (updated: index entry added)
workspace/AGENTS.md                                (created, gitignored)
workspace/internal/AGENTS.md                       (created, gitignored)
workspace/clients/AGENTS.md                        (created, gitignored)
workspace/catalyst-works/AGENTS.md                 (created, gitignored)

Commit: 2343b59 on main, pushed to origin.
VPS: no pull needed: no runtime code changed.
```
