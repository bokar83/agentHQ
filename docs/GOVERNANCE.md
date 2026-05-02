# agentsHQ Governance

**Codename for the multi-session work building this out:** `compass` ([roadmap](roadmap/compass.md))

**The question this doc answers in <30 seconds:** *Where does each kind of rule live, who enforces it, and how does it get retired?*

## Success criteria for this doc

This doc passes if:

1. Any rule in agentsHQ is reachable in under 30 seconds from the routing table below.
2. This file never exceeds 80 lines. Beyond 80 lines means the underlying rules need consolidation, not more routing.
3. Every rule that exists in the codebase has a routing entry below.

When (1), (2), or (3) fails, that triggers a Compass review pass.

## Explicit gap statement

**Today (2026-05-02) ships scaffolding only.** The 8 underlying rule surfaces are not yet consolidated. Compass M1 audits and consolidates them. Compass M2 builds the enforcement hooks. **The structure is forward-proof only after Compass M2.** Reading this doc and thinking "governance is done" would be wrong; governance is set up, not finished.

## Routing table

| Rule type | Source of truth | Enforcement | Review cadence |
|---|---|---|---|
| Behavior of every coding-agent session (Hard Rules, session protocols, Karpathy principles, Codex-First) | [`docs/AGENT_SOP.md`](AGENT_SOP.md) | Read at session start; Sankofa + Karpathy on plans | Per-session; quarterly purge |
| Folder purpose + structure | [`docs/AGENT_SOP.md`](AGENT_SOP.md) Folder Governance section + [`docs/reference/repo-structure.md`](reference/repo-structure.md) | `scripts/check_folder_purpose.py` pre-commit hook + `<folder>/AGENTS.md` per folder | Monthly sandbox sweep; per-PR via hook |
| Cross-session knowledge (case law) | `MEMORY.md` at `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/` | Frontmatter discipline; grep-before-asking rule | Per-session writes; quarterly purge |
| Multi-session projects (atlas, harvest, studio, echo, dashboards4sale, compass) | [`docs/roadmap/<codename>.md`](roadmap/) | Roadmap skill; session-start + session-end protocol | Per-session log entry |
| Atomic execution tasks | Notion ⏳ Tasks DB (T-YYxxxx) + `data/changelog.md` | Notion poller (5-min heartbeat); `/task add` Telegram verb | Per-task; per-day standup digest |
| Code-level invariants (em-dashes, secrets, future folder-purpose) | `.pre-commit-config.yaml` + `scripts/*.py` hooks | Pre-commit (every commit) | Per-commit |
| Local LLM context per folder | `<folder>/AGENTS.md` (or `README.md` for non-rules folders like `sandbox/`) | Folder-purpose hook + Sankofa audit (Compass M1) | Per-folder-add; Compass M1 audit |
| Platform vs satellite boundary | Root [`AGENTS.md`](../AGENTS.md) Platform-with-Satellites Rule + Ventures Registry in [`docs/roadmap/README.md`](roadmap/README.md) | Manual review when a venture has its own URL/customer/revenue | Per-venture-add |

## Conflict resolution (when rule sources disagree)

1. **Hooks beat docs.** If a pre-commit hook fails, the commit fails, regardless of what any markdown file says. Mechanism wins.
2. **AGENT_SOP beats memory.** If `AGENT_SOP.md` and a memory file contradict, AGENT_SOP wins. Memory is case law; AGENT_SOP is constitutional.
3. **AGENT_SOP beats folder-local AGENTS.md.** Local context can extend or specialize; it cannot contradict.
4. **The user beats everything.** Boubacar's explicit instruction in the current conversation overrides every doc and hook. (See AGENT_SOP "Instruction Priority" if added; until then this is the de facto rule.)

## Retirement protocol

Every rule that exists must justify itself today, not three years ago.

- **Quarterly purge:** every 90 days, run `git log --since="90 days ago"` against each governance surface. Any rule untouched 90+ days AND not referenced by any commit, hook, or memory entry in that window is a candidate for retirement.
- **Retirement = archive, not delete.** Per the no-delete hard rule, retired rules move to `zzzArchive/_governance-retired-<date>/<source-file>/<rule>.md` with a manifest entry stating why and when it stopped applying.
- **Resurrection:** any retired rule can be unarchived by adding it back to its source surface and citing the manifest entry that explains the prior retirement.

## Adding a new rule

1. Decide which surface owns the rule (use the routing table above).
2. Write it in that surface, with a `*Why:*` line citing the incident or decision that motivated it.
3. If the rule is enforceable by mechanism, add a hook in the same commit. Documents that govern without mechanism decay in 14 days.
4. If the rule conflicts with an existing rule, retire the older one or reconcile explicitly. Two contradictory rules in two surfaces is the sprawl pattern.

## Where to read first when joining a session

1. This file (`docs/GOVERNANCE.md`) for the map.
2. `docs/AGENT_SOP.md` for the rules.
3. `MEMORY.md` for cross-session context.
4. The active roadmap for the current project.
5. The folder's local `AGENTS.md` only if the work is scoped to one folder.

Five surfaces, in this order, and you have full context.
