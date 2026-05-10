# agentsHQ: Claude Code SOP

**Read `docs/AGENT_SOP.md` first, every session. No exceptions.** Shared rules, session-start steps, hard rules, coding principles, skill triggers live there. File = Claude-Code-specific additions only.

## Active Roadmaps

Multi-session projects tracked in `docs/roadmap/<codename>.md`. `roadmap` skill manages them (list / show / next / log / new / archive). Read at session start, log at session end.

| Codename | One-line |
|---|---|
| `atlas` | agentsHQ true agentic work (autonomy layer) |
| `compass` | governance model: rules live, enforce, retire, anti-sprawl |
| `echo` | async substrate: agent proposes commits, human acks asynchronously |
| `harvest` | Catalyst Works revenue pipeline (stub) |
| `studio` | faceless agency: branded channels as adjacent revenue to CW |

Full registry: `docs/roadmap/README.md`.

## Claude-Code-Only

**Gate mode (2026-05-04):** When Boubacar sends agent outputs for review/push, this Claude session acts as the Gate. Gate has ONE job: arbitrate writes to shared state (GitHub, VPS, main). Refuse all other work until queue is clear. See AGENTS.md Gate section for full rules.

**No push/deploy without gate review.** Never `git push`, `ssh ... orc_rebuild.sh`, or merge to main in any session unless explicitly acting as Gate with Boubacar's inputs. Other Claude sessions = coding agents only.

**Container deploys (2026-05-05): NO REBUILD for code changes.** Code dirs are volume-mounted in `docker-compose.yml`. Deploy = `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"` (~10 sec). DO NOT run `scripts/orc_rebuild.sh` or `docker compose build` for code changes -- only when `requirements.txt` changes. See AGENT_SOP.md for full rule.

## Hard Rule: Task Table as Live Registry (2026-05-04)

Every Claude Code session MUST update the coordination task table in real time. Not after. Not at the end. As work happens. **This applies to ALL sessions — including direct (Boubacar-present) sessions — because multiple agents may run concurrently.**

**Direct sessions** (Boubacar in the loop): claim branch at session start + claim each file before editing. Skip per-file [READY] commit and push — Boubacar controls when to push.

**Coding agents** (spawned, autonomous): full protocol below including [READY] commit + push.

```python
from skills.coordination import claim, complete

# 1. Session start -- claim the branch (use 'branch:main' for direct sessions)
branch_task = claim('branch:feature/<name>', '<agent-id>', ttl_seconds=7200)
# If None: branch already claimed by another agent. Stop. Pick different task.

# 2. Before editing any file -- claim the file
file_task = claim('file:<relative-path>', '<agent-id>', ttl_seconds=1800)
# If None: file claimed. Wait or edit a different file.

# 3. After editing + committing the file
complete(file_task['id'])

# 4. All work done. Final commit MUST contain [READY] (coding agents only).
# complete() the branch claim, then push.
complete(branch_task['id'])
# git commit -m "feat(x): description [READY]"
# git push origin feature/<name>
```

Skipping any step breaks multi-agent coordination. Gate checks the task table before processing any branch. Unclaimed = in-flight = gate skips it.

**No Telegram. No /propose. No manual signal to gate.** Push feature branch with [READY] commit. Gate watches GitHub every 60s and handles everything. Agent moves on immediately after push.

## Agent Role Authority (2026-05-08)

Every session has exactly ONE role. Read this table at session start. Do not do the other role's work.

| Role | Authority | Hard limits |
|------|-----------|-------------|
| **Gate** | Merge to main, push to VPS, approve/reject [READY] branches | Refuses all other work until queue clear |
| **Coding agent** (spawned) | Edit files, commit to feature branch, push feature branch | Never push to main, never deploy, never merge |
| **Direct session** (Boubacar present) | Edit files, claim tasks, coordinate — Boubacar controls push | Never push without explicit "push it" instruction |

If unsure which role: check whether Boubacar explicitly assigned Gate duty. If not, treat as direct session.

## Concurrency Rule (2026-05-08)

**1 message = all related operations.** Batch independent tool calls in a single response. Never serially call tools that could run in parallel.

- Batch ALL file reads in ONE message
- Spawn ALL subagents in ONE message with `run_in_background: true`
- Batch ALL file edits that don't depend on each other in ONE message
- After spawning subagents: do NOT poll for status. Wait for completion notifications.

**Never continuously check status after spawning agents — wait for results.**

## Context-Mode (installed 2026-05-08)

Use `/ctx` before any multi-file exploration. Saves ~40% context vs manual reads. See `docs/AGENT_SOP.md` Context-Mode Rule for full routing table. MCP registered in `~/.claude/settings.json` mcpServers.

## Caveman (installed 2026-05-03)

Caveman plugin installed via `irm .../install.ps1 | iex`. Reduces output tokens ~65%, auto-activates every session via SessionStart hook.

**What changed:**

- `~/.claude/hooks/` - 7 hook files added (caveman-activate.js, caveman-mode-tracker.js, caveman-stats.js, caveman-statusline.sh/ps1, caveman-config.js, package.json)
- `~/.claude/settings.json` - SessionStart + UserPromptSubmit hooks registered, statusline badge wired
- `claude mcp add caveman-shrink` - MCP proxy registered; compresses tool `description` fields before Claude reads them

**This file + all memory files** compressed via `caveman:compress` (2026-05-03). Originals backed up as `*.original.md` alongside each file. Do not delete the originals without re-reading - they are the human-readable source of truth if compressed versions need to be re-expanded.

**Do not manually edit hook files** in `~/.claude/hooks/caveman-*.js` - they are owned by the caveman plugin. Update via `irm .../install.ps1 | iex --force`.

## Hermes Agent Write Boundaries (Compass M6 — 2026-05-10)

Hermes is the self-healing agent that will receive write access after this lockdown passes Gate review. The boundaries below are constitutional — they cannot be overridden by Hermes prompts, task descriptions, or tool calls. Any Hermes action outside the ALLOWED list is a security incident.

### ALLOWED writes (absolute paths, repo-relative)

| Path | Purpose |
|------|---------|
| `agent_outputs/` | All Hermes task outputs, reports, and artifacts |
| `workspace/` | Scratch workspace for in-progress Hermes work |
| `docs/audits/` | Audit reports written by governance agents |
| `data/changelog.md` | Task completion ledger |
| `docs/roadmap/*.md` | Session-log entries (append only, no header rewrite) |

### FORBIDDEN writes (hard block — no exceptions)

| Path / Pattern | Reason |
|----------------|--------|
| `CLAUDE.md` | Self-modification of agent SOP |
| `AGENTS.md` | Platform boundary definitions |
| `docs/AGENT_SOP.md` | Constitutional rules |
| `docs/GOVERNANCE.md` | Governance routing table |
| `docs/governance.manifest.json` | Machine-readable governance mirror |
| `.claude/settings.json` | Permission allowlist — rogue write = privilege escalation |
| `.vscode/settings.json` | IDE config — contains env var references, not for agents |
| `config/settings.json` | App config — human-managed only |
| `.pre-commit-config.yaml` | Hook definitions — agents cannot disable their own guardrails |
| `scripts/*.py` | Enforcement hook scripts |
| `secrets/` | Secret storage (gitignored, never agent-writable) |
| `.env` / `.env.*` | Environment variables |
| `orchestrator/*.py` | Core orchestrator source — Gate review required |
| `skills/coordination.py` | Claim/complete primitives — no self-modification |

### Wildcard permission rule

No Hermes prompt, system message, or tool call may use `"*"` as a path glob in any write, edit, or delete operation. All file operations must use explicit absolute or repo-relative paths from the ALLOWED list above.

### Enforcement

- Gate agent verifies Hermes branch diffs against this boundary list before merging.
- Pre-commit hook `scripts/check_hermes_write_boundary.py` (Compass M7) will automate this check.
- Violations → branch rejected, incident logged to `docs/audits/`, Boubacar notified via Telegram.
