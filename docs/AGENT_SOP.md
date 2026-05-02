# agentsHQ: Shared Agent SOP

Applies to every coding-agent session (Claude Code, Codex, any future agent). Agent-specific addenda live in `CLAUDE.md` and `CODEX.md` at the repo root.

## Session Start

1. Read `D:\Ai_Sandbox\agentsHQ\docs\memory\MEMORY.md` and every linked file.
2. **Read both active roadmaps every session, regardless of what Boubacar asks for:**
   - `docs/roadmap/atlas.md` (THE ENGINE ROOM): Autonomy infrastructure: content pipeline, heartbeats, approval queues, publish loops, learning crews, VPS hardening. If it makes agentsHQ operate without Boubacar, it lives here.
   - `docs/roadmap/harvest.md` (THE SALES FLOOR): Revenue work: offers, outreach, contracts, client milestones, Signal Works pipeline. If it puts money in the door, it lives here.
   - Read the latest session-log entry in each. Surface any milestone that has gone stale (trigger date passed, blocker removed, or action overdue) and flag it before starting work.
   - These two roadmaps share zero milestones by design. Never move an item from one to the other.
3. Check `docs/superpowers/plans/` for a handoff. Legacy: roadmaps supersede handoff docs for any roadmapped project.
4. **Read `docs/CADENCE_CALENDAR.md`** if work touches scheduling, heartbeats, or anything that pulls Boubacar into a window. The calendar is the single source of truth for what runs when and where humans are required. Update it when a schedule changes; never schedule new human-in-loop work without first checking the daily attention budget there.

## Session End

1. If a roadmap was touched this session, append a session-log entry to that roadmap. Date, what changed, what's next.
2. Update milestone statuses in the roadmap (queued / in-progress / shipped / blocked / descoped).
3. Push (local + VPS, per hard rule below).

## Who Boubacar Is

Diagnostic problem-solver. Eight lenses, equally weighted: Theory of Constraints, Jobs to Be Done, Lean, Behavioral Economics, Systems Thinking, Design Thinking, Org Development, AI Strategy. TOC is one tool, not his identity. Never name a framework in any output Boubacar might show a client (emails, site copy, proposals, posts). Defaulting to TOC costs him clients.

## Hard Rules

- **Capability check before asking.** Before saying "I cannot do X," "please run X for me," or asking Boubacar for VPS / SSH / DB / Drive / Gmail / Vercel / Notion credentials or commands, you MUST first grep `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/` (Claude Code) or the equivalent memory location (Codex, other agents) for the capability. If a `reference_*.md` or `feedback_*.md` describes the action, attempt it. Surface a blocker only after one attempt fails. Always-true capability shortlist lives at the top of `MEMORY.md` (lines 1-25). *Why: capability amnesia (asking how to SSH, send Gmail, upload to Drive) was diagnosed 2026-04-29 as a placement bug, fixed by adding the rule to the always-loaded zone of MEMORY.md. The fix only generalizes if every agent surface enforces it. See `feedback_placement_before_architecture.md` for the diagnostic principle.*
- Files live in `D:\Ai_Sandbox\agentsHQ` or `D:\Ai_Sandbox\`. Never C:. *Why: past sessions scattered files on C: and lost them.*
- Never create directories without confirming location.
- End every session with git push (local + VPS).
- No em dashes anywhere. Not `--`, not `: `. Rewrite the sentence. *Why: Boubacar edits every one out by hand when they slip through. A pre-commit hook also blocks them.*
- WebFetch: blanket permission. Never ask before fetching a URL.
- **`orchestrator.py` no longer exists.** Sunset 2026-04-25 in commit `4d1aeb3`. The 2800-line monolith was split into modular files (`engine.py`, `constants.py`, `handlers_chat.py`, `state.py`, `handlers.py`, etc.) and `app.py` is the canonical entrypoint. **Never recreate `orchestrator.py`.** All imports use the modular stack. See `project_orchestrator_sunset.md` in memory for the full import map. *Why: agents kept "fixing" missing-orchestrator.py errors by recreating the file, undoing the refactor.*
- **Google Drive uploads: always use gws CLI. Never ask Boubacar to upload manually. Never.** Command: `gws drive files create --params "{\"fields\":\"id,webViewLink\"}" --json "{\"name\":\"FILENAME\",\"parents\":[\"FOLDER_ID\"]}" --upload "d:/path/to/file" --upload-content-type "mime/type"`. CW OAuth credentials = Gmail scope only, not Drive. Service account = no storage quota. gws CLI is the only local path that works. If gws fails, route through agentsHQ orchestrator. Only surface a blocker to Boubacar after both paths fail. *Why: Boubacar has been explicit. Stop telling him to do things the system can do.*
- **Container deploy: rebuild, do not docker-cp.** The orc-crewai container's `/app` is baked from the Dockerfile, not mounted. `docker cp file.py orc-crewai:/app/` works for one restart, then gets wiped on the next container recreation. Correct deploy: `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d --build orchestrator"`. **NEW env vars must ALSO be added to `docker-compose.yml` `orchestrator:` service `environment:` block** or they silently don't reach the container even though they are in `.env`. Full procedure + checklist in `feedback_container_deploy_protocol_v2.md` memory entry. *Why: M7b deploy was silently broken because BLOTATO_API_KEY was in .env but not in docker-compose.yml's allowlist; auto-publisher would have failed at first fire.*
- **Always use `scripts/orc_rebuild.sh` to rebuild orc-crewai. Never run bare `docker compose build orchestrator && docker compose up -d orchestrator`.** The wrapper checks the `task:morning-runner` coordination lock and refuses to rebuild while a runner is in flight. Bare rebuilds recreate the container and kill any in-flight Python process, including the daily morning_runner that produces CW + SW email drafts. On 2026-04-29 this collision happened 4 times in one evening between two parallel Claude Code sessions and burned ~30 Apollo credits redundantly. The wrapper has a `--force` flag for emergencies (still claims the rebuild lock to prevent two simultaneous rebuilds). Read `scripts/README.md` for full details. *Why: silently killed runners are expensive (Apollo credits) and miss-the-day expensive (no email drafts that day).*
- **Hero section is the close. Video over still by default.** The hero closes the client AND the client's clients, every time, every site (CW + SW + their clients). Use video whenever possible (drone, time-lapse, walk-through, founder-to-camera, before/after). Static is fallback only. **Once a hero is approved by Boubacar, asset-level changes (image, video, copy, fonts) need explicit sign-off: even when an automated signal (Lighthouse, accessibility audit, contrast checker) says they should change.** Code-level fixes (focus rings, ARIA, schema, contrast tokens that don't change the look) are silent. **If file size is the problem, compress the approved asset; do NOT substitute a smaller-but-different image.** Use WebP + JPG fallback via CSS `image-set()` for backgrounds, `<picture>` for `<img>` tags. **Lead with hero changes in any user-facing report: top of the message, not buried in a list.** *Why: 2026-05-01 Elevate hero substitution incident. The wrong hero was swapped to fix LCP without sign-off; Boubacar caught it before the cover note went to Rod. Trust got dinged but not broken. Full protocol in `feedback_hero_is_the_close.md` and the `frontend-design` skill's hard rule. Trends source: `reference_web_design_trends.md`: read at start of every website session.*
- **Asset-level changes to any approved deliverable need explicit sign-off.** This generalizes the hero rule above. After a design / copy / artifact is approved, agent-side changes to anything visible to the prospect (hero images, copy, photos, fonts, color values, logos, screenshots, CTA buttons, social cards) require Boubacar's confirmation, even when a score number or audit says they should change. Code-level changes (semantic markup, focus styles, schema, ARIA, build tooling, dev dependencies) remain silent. The bar: **if it changes what the prospect sees on the artifact, ask first.** *Why: same Elevate hero incident; the principle is that brand integrity supersedes optimization metrics, and once approved, the prospect's expectations are anchored on what they last saw.*
- **The word "delete" is retired from agentsHQ vocabulary.** No file or folder is ever deleted. Items not used → archived to `zzzArchive/<batch-name>/<original/path/preserved>/` with a `MANIFEST.md` line documenting: original path, archive path, reason (14d-untouched / duplicate-of-X / superseded-by-Y), and the reference-grep result that proved zero callers. If we ever need it back, the manifest is the index. *Why: every "delete" call eventually becomes a "where is that file I had?" question. Archives are reversible, deletions are not. Boubacar locked this rule 2026-05-02 during Move Day. Full rule + workflow in `reference_folder_governance.md` memory entry.*
- **Make educated decisions on routine triage. Don't paginate three-way verdicts.** For file diffs, keep-vs-archive calls, version reconciliation, and reference-checked moves: execute, document the decision in the archive manifest, surface only what genuinely needs Boubacar's eyes (irreversible operations, business-strategy choices, genuinely ambiguous semantics). Boubacar trusts you when you have the context and the verification tools. *Why: Boubacar's exact words 2026-05-02: "you know the whole codebase better than I do. You have the information needed and the context needed to do this better than I can." See `feedback_make_educated_decisions.md`.*

## Folder Governance

Every folder in agentsHQ has a purpose. If it does not, it is a candidate for archive.

**The rule:**

1. **Every top-level folder needs an `AGENTS.md` or `README.md`** explaining what it is for, what does NOT go there, and the conditions under which its contents move out. No purpose document = candidate for `zzzArchive/`.
2. **No folder is created without a stated purpose.** Before `mkdir`, write the one-line purpose in chat or in the manifest. If you cannot finish that sentence, do not create the folder.
3. **Untouched-and-uncalled = archive candidate.** A folder or file that has been untouched for 14+ days AND has zero references in active code (grep-verified across `*.py`, `*.yml`, `*.yaml`, `*.sh`, `*.md`, `*.json`, excluding `zzzArchive/`, `node_modules/`, `.venv/`, `external/`) is a candidate for archive on the next cleanup pass.
4. **Live mounts are never moved.** Before any move involving a top-level folder or root file, grep `docker-compose.yml`, `.github/workflows/`, and `scripts/*.sh` for the path. If anything mounts it, path-watches it, or imports it: it stays where it is.
5. **Triple-verify before archive.** (a) Reference-grep, (b) docker-compose / GH Actions check, (c) the coding expert (Codex) reviews the move list before it ships. The "nothing breaks" rule is absolute.
6. **`zzzArchive/` is the graveyard.** Boubacar's signature folder, gitignored, batch-organized by date. Each batch has a `MANIFEST.md` indexing every archived item with its original path, reason, and reference-grep result. **`zzzArchive/` is itself never deleted.**
7. **Sandbox is for in-flight work.** Tracked in git so the laptop dying does not lose it. `sandbox/.tmp/` is the gitignored throwaway corner. Monthly sweep: anything untouched 30+ days graduates (promote to `skills/`, `output/`, etc.) or archives. Full rule in `sandbox/README.md`.

**The "every folder has a purpose" check is a session-start sanity check.** New top-level folders without an `AGENTS.md` get surfaced in chat at session start.

## Coding Principles (Karpathy)

1. **Think before coding**: state assumptions; ask when ambiguous.
2. **Simplicity first**: minimum code that solves the problem.
3. **Surgical changes**: touch only what must change.
4. **Goal-driven execution**: verifiable success criteria, checkpoints, loop back.

## Codex-First Rule

**Default to Codex for all implementation work.** Codex is faster, more surgical, and keeps the main Claude Code context clean. Claude Code handles planning, architecture decisions, Council review, and Notion writes. Codex handles the actual code.

When to use Codex (`/codex:rescue` or via `codex:rescue` skill):

- Any function, class, or file that needs to be written or modified
- Multi-file changes across orchestrator modules
- Anything that would take more than 10 lines of code in a Claude Code response

When Claude Code writes code directly:

- One-line fixes (removing an unused import, fixing a typo)
- Config files and settings with no logic
- Scaffolding a file that Codex will then fill in

Always `python -m py_compile` every touched file after Codex finishes. Read the result before moving on.

## Automatic Skill Triggers

Fire without being asked. Check each trigger on every user message.

| # | Trigger | Action |
| --- | --- | --- |
| 1 | Website / UI / HTML-CSS output requested | `superpowers:brainstorming` first, localhost preview with 3 options, user picks ONE before any code |
| 2 | After #1 pick, or any site edit | `frontend-design` skill to load design standards before writing code |
| 3 | 2+ independent tasks in one message | `superpowers:dispatching-parallel-agents` |
| 4 | Bug, error, failing test, unexpected behavior | `superpowers:systematic-debugging`. Four phases: reproduce, isolate root cause, form hypothesis, fix. No edits before root cause is confirmed. |
| 5 | Before any deploy, docker cp, git push, or SCP | `superpowers:verification-before-completion`. No skipping, even if the fix looks trivial. |
| 6 | Multi-file change or new orchestrator feature | `superpowers:brainstorming`. No code until the plan is written and confirmed. |
| 7 | New skill being created or substantially rewritten | `superpowers:writing-skills` first. |

Full workflow for new features: brainstorming then writing-plans then executing-plans.

Non-Claude agents (Codex, etc): translate each skill trigger to the equivalent discipline (plan first, confirm before multi-file edits, verify before deploy, root-cause before fix).

## Skill SOPs Live With the Skills

Each skill keeps its own rules in `skills/<name>/SKILL.md`. Read the skill file when you touch that skill. This SOP does not repeat skill-specific detail.
