# agentsHQ: Shared Agent SOP

> **This is the agentsHQ rules library.** The constitution that routes between rule sources is at [`docs/GOVERNANCE.md`](GOVERNANCE.md). When in doubt about where a rule belongs or which rule wins in a conflict, read GOVERNANCE.md first. This file is the rules themselves.

Applies to every coding-agent session (Claude Code, Codex, any future agent). Agent-specific addenda live in `CLAUDE.md` and `CODEX.md` at the repo root.

## Session Start

1. Read `D:\Ai_Sandbox\agentsHQ\docs\memory\MEMORY.md` and every linked file.
2. **Read all active roadmaps every session, regardless of what Boubacar asks for:**
   - `docs/roadmap/atlas.md` (THE ENGINE ROOM): Autonomy infrastructure: content pipeline, heartbeats, approval queues, publish loops, learning crews, VPS hardening. If it makes agentsHQ operate without Boubacar, it lives here.
   - `docs/roadmap/harvest.md` (THE SALES FLOOR): Revenue work: offers, outreach, contracts, client milestones, Signal Works pipeline. If it puts money in the door, it lives here.
   - `docs/roadmap/studio.md` (THE CONTENT FACTORY): Faceless agency - branded channels producing revenue independent of client work. Trend scout, production crew, publish pipeline, monetization.
   - `docs/roadmap/compass.md` (THE RULEBOOK): Governance model - where rules live, how they enforce, how they retire, anti-sprawl. Milestone-gated evolution of AGENT_SOP + GOVERNANCE.
   - `docs/roadmap/echo.md` (THE ASYNC LAYER): Partnership substrate - agent proposes commits, human acks asynchronously. Neither blocks on the other.
   - Read the latest session-log entry in each. Surface any milestone that has gone stale (trigger date passed, blocker removed, or action overdue) and flag it before starting work.
3. Check `docs/superpowers/plans/` for a handoff. Legacy: roadmaps supersede handoff docs for any roadmapped project.
4. **Load second brain context at session start.** Run this snippet to inject hard rules + recent lessons before starting work:

  ```python
  # cd d:/Ai_Sandbox/agentsHQ && python -c "..."
  import sys; sys.path.insert(0, '.')
  from orchestrator.memory_store import load_hard_rules, query_text
  from datetime import date

  rules = load_hard_rules()
  print(f"=== {len(rules)} HARD RULES ===")
  for r in rules:
      print(f"• {r['content'][:120]}")

  recent = query_text("", limit=10, category="agent_lesson")
  print(f"\n=== RECENT LESSONS (last 7 days) ===")
  for r in recent[:5]:
      print(f"• {r['content'][:150]}")
  ```

  If Postgres is unreachable (laptop offline, VPS down), skip silently — flat-file MEMORY.md is the fallback.

1. **Read `docs/CADENCE_CALENDAR.md`** if work touches scheduling, heartbeats, or anything that pulls Boubacar into a window. The calendar is the single source of truth for what runs when and where humans are required. Update it when a schedule changes; never schedule new human-in-loop work without first checking the daily attention budget there.

## Session End

1. If a roadmap was touched this session, **before** appending the session log:
   - Find the `### MXX:` header for every milestone that shipped. Change `⏳ QUEUED` or `🔄 IN PROGRESS` to `✅ SHIPPED YYYY-MM-DD`. This edit goes in the header line itself, not just the session log body.
   - Update the sub-milestone status table rows inside the milestone body to match.
   - Create or update the Notion task entry (`NOTION_TASK_DB_ID = 249bcf1a302980739c26c61cad212477`) — set Status: Done for shipped milestones, In Progress for partial.
2. Append a session-log entry to that roadmap. Date, what changed, what's next.
3. Push (local + VPS, per hard rule below).

## Who Boubacar Is

Diagnostic problem-solver. Eight lenses, equally weighted: Theory of Constraints, Jobs to Be Done, Lean, Behavioral Economics, Systems Thinking, Design Thinking, Org Development, AI Strategy. TOC is one tool, not his identity. Never name a framework in any output Boubacar might show a client (emails, site copy, proposals, posts). Defaulting to TOC costs him clients.

## Hard Rules

- **Final human-facing deliverables default to HTML, opened in browser automatically.** When the output is intended for a human to read (client reports, audit summaries, briefings, engagement memos shared externally, research summaries for leadership): produce HTML AND immediately spin up a localhost preview (`python -m http.server` or `npx serve`) so Boubacar can view it without manual steps. When the output is internal agent context, planning, version-controlled specs, or agent-to-agent handoff: use `.md`. Exception: receiving system requires `.md` (GitHub PRs, Notion page imports). Interactive use case available on demand: ask Claude to build a single-file throwaway HTML tool (draggable triage, config editor, prompt tuner) with a copy-as-JSON export button — always served locally for immediate viewing. *Why: agents write docs, humans read them. HTML is optimized for reading; .md is optimized for writing. 2026-05-08 community validation via @trq212 (2400+ likes). Existing skills (seo-strategy, website-teardown) already default to HTML; rule codifies the principle across all agents.*

- **Capability check before asking.** Before saying "I cannot do X," "please run X for me," or asking Boubacar for VPS / SSH / DB / Drive / Gmail / Vercel / Notion credentials or commands, you MUST first grep `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/` (Claude Code) or the equivalent memory location (Codex, other agents) for the capability. If a `reference_*.md` or `feedback_*.md` describes the action, attempt it. Surface a blocker only after one attempt fails. Always-true capability shortlist lives at the top of `MEMORY.md` (lines 1-25). *Why: capability amnesia (asking how to SSH, send Gmail, upload to Drive) was diagnosed 2026-04-29 as a placement bug, fixed by adding the rule to the always-loaded zone of MEMORY.md. The fix only generalizes if every agent surface enforces it. See `feedback_placement_before_architecture.md` for the diagnostic principle.*
- Files live in `D:\Ai_Sandbox\agentsHQ` or `D:\Ai_Sandbox\`. Never C:. *Why: past sessions scattered files on C: and lost them.*
- Never create directories without confirming location.
- End every session with git push (local + VPS).
- No em dashes anywhere. Not `--`, not `: `. Rewrite the sentence. *Why: Boubacar edits every one out by hand when they slip through. A pre-commit hook also blocks them.*
- WebFetch: blanket permission. Never ask before fetching a URL.
- **`orchestrator.py` no longer exists.** Sunset 2026-04-25 in commit `4d1aeb3`. The 2800-line monolith was split into modular files (`engine.py`, `constants.py`, `handlers_chat.py`, `state.py`, `handlers.py`, etc.) and `app.py` is the canonical entrypoint. **Never recreate `orchestrator.py`.** All imports use the modular stack. See `project_orchestrator_sunset.md` in memory for the full import map. *Why: agents kept "fixing" missing-orchestrator.py errors by recreating the file, undoing the refactor.*
- **Google Drive uploads: always use gws CLI. Never ask Boubacar to upload manually. Never.** Command: `gws drive files create --params "{\"fields\":\"id,webViewLink\"}" --json "{\"name\":\"FILENAME\",\"parents\":[\"FOLDER_ID\"]}" --upload "d:/path/to/file" --upload-content-type "mime/type"`. CW OAuth credentials = Gmail scope only, not Drive. Service account = no storage quota. gws CLI is the only local path that works. If gws fails, route through agentsHQ orchestrator. Only surface a blocker to Boubacar after both paths fail. *Why: Boubacar has been explicit. Stop telling him to do things the system can do.*
- **Any Drive file linked from outgoing email or external-facing message MUST be `anyone with link` reader.** Use `orchestrator.drive_publish.publish_public_file()` for new uploads and `update_public_file(file_id, ...)` for content swaps -- both call `ensure_public()` so the public-link permission is set in the same operation. After uploading by hand via gws CLI, immediately run `gws drive permissions create --params '{"fileId":"<ID>","fields":"id,type,role"}' --json '{"role":"reader","type":"anyone","allowFileDiscovery":false}'`. To audit the active email-template PDFs at any time: `python -m orchestrator.drive_publish audit` (exits 2 if any private). *Why: 2026-05-08 we shipped the SaaS-Audit PDF link in cw_t2 outreach, then discovered the file was owner-only -- recipients clicking the link saw a permission-denied screen. Caught before the morning send. Per Boubacar: every Drive URL in an email must be openable by the recipient, every time, with no manual perm-fix step.*
- **Listmonk newsletter service (2026-05-06): self-hosted at `mail.srv1040886.hstgr.cloud`, deployed via `/root/listmonk-compose.yml` on VPS. Replaces Beehiiv send API (Enterprise-only gating). Orchestrator reaches it at `http://listmonk:9000` on `orc-net`. Env vars: `LISTMONK_URL`, `LISTMONK_USERNAME`, `LISTMONK_PASSWORD`, `LISTMONK_LIST_ID` -- all in `.env` and wired into `docker-compose.yml` orchestrator environment block. Admin: `bokar83@gmail.com` / `bokar83` username. Gmail SMTP wired. Beehiiv kept for subscriber growth tools only.**
- **Container deploy: code is now VOLUME-MOUNTED. NO REBUILD NEEDED for code changes (2026-05-05).** As of 2026-05-05, `docker-compose.yml` volume-mounts `signal_works/`, `skills/`, `templates/`, `orchestrator/` from VPS host into `/app/` in the container. Code changes are LIVE in the container immediately on disk. Correct deploy for code-only changes: `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"` -- takes ~10 seconds. **DO NOT run `docker compose build` or `scripts/orc_rebuild.sh` for code changes** -- it wastes 15-25 minutes and has no benefit. **NEW env vars must ALSO be added to `docker-compose.yml` `orchestrator:` service `environment:` block** or they silently don't reach the container even though they are in `.env`. *Why: stale-container problem (2026-05-05): Apollo morning run fired with 12-hour-old code because `docker compose build` was the deploy path. Volume mount eliminates the failure mode entirely. Code changes deploy in seconds, not minutes.*
- **Rebuild ONLY when `requirements.txt` changes.** If you edited Python deps (added/removed/upgraded a package in `orchestrator/requirements.txt`), then and ONLY then run `bash scripts/orc_rebuild.sh` on VPS. The wrapper checks the `task:morning-runner` coordination lock and refuses to rebuild while a runner is in flight (`--force` flag for emergencies). For everything else (code changes, env var changes, config changes): use `docker compose up -d orchestrator` -- never `--build`. *Why: rebuilds take 15-25 min (pip resolver iterates dep versions) and historically failed silently with `ResolutionTooDeep: 200000`. Code-only changes don't need any of that pain.*
- **Gate runs on VPS host cron only. Never register gate_tick in the container.** `/etc/cron.d/gate-agent` fires every 5 minutes, 24/7. No cost (pure Python + git, no LLM calls). Container has no `.git` dir so gate must run on host. In-container registration removed 2026-05-08 from `scheduler.py`. Gate is fully autonomous — merges, deploys, cleans up branches silently. Only sends Telegram for: tests failed, merge failed, push/deploy failed, conflict between branches, high-risk file review (buttons). Success = silent. High-risk files (buttons required): `gate_agent.py`, `orc_rebuild.sh`, `.env`, `docker-compose`. Everything else auto-merges if tests pass. To operate: toggle `crews.gate.enabled` in `data/autonomy_state.json`. Logs: `tail -f /var/log/gate-agent.log` on VPS. Manual trigger: `GATE_DATA_DIR=/root/agentsHQ/data REPO_ROOT=/root/agentsHQ python3 /root/agentsHQ/orchestrator/gate_agent.py`. *Why: 2026-05-08 gate was wired in container AND host cron simultaneously — container logged `fatal: not a git repository` every 60s. Removed container registration. Cron reduced from 15-min to 5-min 2026-05-08 — no LLM spend, no rate-limit risk, just faster pipeline.*
- **Hero section is the close. Video over still by default.** The hero closes the client AND the client's clients, every time, every site (CW + SW + their clients). Use video whenever possible (drone, time-lapse, walk-through, founder-to-camera, before/after). Static is fallback only. **Once a hero is approved by Boubacar, asset-level changes (image, video, copy, fonts) need explicit sign-off: even when an automated signal (Lighthouse, accessibility audit, contrast checker) says they should change.** Code-level fixes (focus rings, ARIA, schema, contrast tokens that don't change the look) are silent. **If file size is the problem, compress the approved asset; do NOT substitute a smaller-but-different image.** Use WebP + JPG fallback via CSS `image-set()` for backgrounds, `<picture>` for `<img>` tags. **Lead with hero changes in any user-facing report: top of the message, not buried in a list.** *Why: 2026-05-01 Elevate hero substitution incident. The wrong hero was swapped to fix LCP without sign-off; Boubacar caught it before the cover note went to Rod. Trust got dinged but not broken. Full protocol in `feedback_hero_is_the_close.md` and the `frontend-design` skill's hard rule. Trends source: `reference_web_design_trends.md`: read at start of every website session.*
- **Asset-level changes to any approved deliverable need explicit sign-off.** This generalizes the hero rule above. After a design / copy / artifact is approved, agent-side changes to anything visible to the prospect (hero images, copy, photos, fonts, color values, logos, screenshots, CTA buttons, social cards) require Boubacar's confirmation, even when a score number or audit says they should change. Code-level changes (semantic markup, focus styles, schema, ARIA, build tooling, dev dependencies) remain silent. The bar: **if it changes what the prospect sees on the artifact, ask first.** *Why: same Elevate hero incident; the principle is that brand integrity supersedes optimization metrics, and once approved, the prospect's expectations are anchored on what they last saw.*
- **The word "delete" is retired from agentsHQ vocabulary.** No file or folder is ever deleted. Items not used → archived to `zzzArchive/<batch-name>/<original/path/preserved>/` with a `MANIFEST.md` line documenting: original path, archive path, reason (14d-untouched / duplicate-of-X / superseded-by-Y), and the reference-grep result that proved zero callers. If we ever need it back, the manifest is the index. *Why: every "delete" call eventually becomes a "where is that file I had?" question. Archives are reversible, deletions are not. Boubacar locked this rule 2026-05-02 during Move Day. Full rule + workflow in `reference_folder_governance.md` memory entry.*
- **Make educated decisions on routine triage. Don't paginate three-way verdicts.** For file diffs, keep-vs-archive calls, version reconciliation, and reference-checked moves: execute, document the decision in the archive manifest, surface only what genuinely needs Boubacar's eyes (irreversible operations, business-strategy choices, genuinely ambiguous semantics). Boubacar trusts you when you have the context and the verification tools. *Why: Boubacar's exact words 2026-05-02: "you know the whole codebase better than I do. You have the information needed and the context needed to do this better than I can." See `feedback_make_educated_decisions.md`.*
- **Auto-update roadmap and Notion task after EVERY shipped task. No prompting.** When you finish a task that maps to a roadmap milestone (M0, M1, etc.) OR a Notion task (T-XXXXXX), update BOTH in the same turn before the user-facing summary: (a) flip milestone status in `docs/roadmap/<codename>.md` and append a dated `### YYYY-MM-DD:` Session Log entry; (b) flip Notion task status to Done via the Notion MCP. The session-log pre-commit hook (`scripts/check_session_log_updated.py`, Compass M2) enforces (a) at commit time; (b) is on the agent. *Why: Boubacar said 2026-05-02 "whenever you finish a task, update the roadmap and task list automatically. I shouldn't have to tell you this." Manual reminders are friction. See `feedback_auto_update_roadmap_and_tasks.md`.*
- **New hooks, skills, and heartbeats that make LLM calls must pass a canary checklist before registration.** Before wiring any `UserPromptSubmit`, `PreToolUse`, `SessionStart`, or scheduled heartbeat that calls an LLM or rewrites global config, answer all four questions in writing: (a) which model and what is the max context size it will see at realistic session length, (b) what is the cost per firing at that context (prompt tokens x model rate), (c) what is the worst-case firing rate (calls/min if it loops or hooks on every message), (d) does a kill switch exist that stops it without restarting the process. If (b) x (c) exceeds $0.10/min, the thing is not safe to register. For VPS crews, verify at least one call appears in `llm_calls` with expected model and token range before enabling autonomous mode. See `orchestrator/contracts/TEMPLATE.md` Gate 2 for the crew-specific version of this rule. *Why: The 2026-05-02 incident ($57 in 3 hours) and the general class of "new thing fires on every message with growing context" were both preventable by asking question (b) x (c) before wiring. The switch-provider hook answered (b) = ~$0.08/call at 200k tokens and (c) = every message, which computes to financial ruin. See docs/notes/switch-provider-paused-2026-05-02.md.*
- **Global config writes require an isolated, scope-limited test before any hook or automation.** Before any code writes to `~/.claude/settings.json`, `~/.codex/config.toml`, or any file that affects ALL sessions globally: (a) confirm the write has the intended effect with a manual single-run test in a fresh session, (b) measure the size of the hook stdin payload at real session length (not toy-session length), and (c) do NOT register a `UserPromptSubmit` or any per-message hook that triggers that write until both tests pass. *Why: The 2026-05-02 provider-switching hook rewrote settings.json on every prompt without verifying that mid-session config rewrites take effect, and without checking that the accumulated session context (potentially 200k+ tokens) would not exceed OpenRouter's per-request token cap. The result was an "810k token limit" error on every subsequent message, making the session unusable within 4.5 hours. A global config write multiplied by a per-message hook is the highest blast-radius change in the codebase. Karpathy score: 1/10 for surgical changes. See docs/notes/switch-provider-paused-2026-05-02.md.*
- **Propose codification when patterns repeat (two-strikes rule).** If Boubacar gives the same correction or instruction twice, OR you find yourself running the same multi-step ritual across sessions, pause and ask once whether to capture it as (a) a memory feedback file, (b) a new skill, (c) a pre-commit hook, or (d) a hookify rule. Don't pre-build; ask first with options framed by weight (memory < skill < hook). *Why: Boubacar said 2026-05-02 "if there are things i repeatedly tell you or that we do over and over, you should ask me if it is a new skill or action that you should rememeber or create." Documents that govern without mechanism decay; the same applies to verbal corrections. See `feedback_propose_skill_for_repeated_patterns.md`.*
- **No iteration artifacts at repo root. Use `workspace/scratch/<topic>/` or `deliverables/<scope>/iterations/` instead.** When generating screenshots, draft HTML, intermediate renders, or other iteration outputs: never save them to repo root. Screenshots from page work go in `deliverables/<scope>/iterations/`. Throwaway scratch (debugging, one-shots) goes in `workspace/scratch/<date>-<topic>/`. The repo root is reserved for canonical files only. The pre-commit `.gitignore` patterns auto-skip `/sw-*.png`, `/screenshot-*.png`, `/scratch-*`, `/temp-*`, `/test-*`, `/iteration-*` at root, but the rule is to save to the right place from the start, not rely on gitignore as a safety net. *Why: 2026-05-05 cleanup of 11 orphaned `sw-997-*.png` iteration screenshots in repo root. Trail of clutter compounds across sessions and obscures real changes in source-control panel. The SessionStart audit (`scripts/session_start_audit.sh`) warns when root has stray PNGs/HTMLs.*
- **Before archiving any `skills/<name>/` directory, grep for active Python imports.** A stub `SKILL.md` (few lines, no procedures) does NOT mean the directory is safe to remove. Run: `grep -rn "from skills.<name>\|skills/<name>" orchestrator/ signal_works/ --include="*.py" | grep -v __pycache__`. Any active import found = do NOT archive. Update `SKILL.md` to say "Agent-internal only. DO NOT archive." instead. *Why: 2026-05-06 skill consolidation nearly deleted `skills/outreach/`, `skills/forge_cli/`, `skills/email_enrichment/`, `skills/github_skill/`, `skills/local_crm/`, `skills/notion_skill/` -- all contained production Python imported by orchestrator. Caught by import grep before commit. See `feedback_skill_directory_has_active_code.md`.*
- **Agent completion reports must include outcome, changes, validation, and blockers — never just "done".** Every Atlas agent (studio, griot, hunter, chairman, gate, any spawned subagent) MUST close each prompted work turn with a structured completion report: (a) outcome/status — what was accomplished or why it stopped, (b) changes — files modified, records written, messages sent, (c) validation performed — what was checked to confirm correctness, (d) blockers or follow-ups — what cannot proceed and why. A completion report of "done", a bare status change, or a tool transcript alone is INVALID. If a worker fails before producing a final response, the coordinator still receives the lifecycle failure notification — that is not a substitute for a completion report when work succeeds. *Why: jcode architecture review 2026-05-08 identified this as a structural gap in Atlas. Silent "done" stubs cause coordinators to miss partial failures, skipped validation, and unresolved blockers. Completion report contract borrowed from jcode SWARM_ARCHITECTURE.md Completion Report Policy.*
- **When deploy / infrastructure changes, grep all docs for stale claims in the same commit.** When you modify `docker-compose.yml`, `orchestrator/Dockerfile`, deploy scripts, or any infra config: grep `CLAUDE.md`, `docs/AGENT_SOP.md`, `skills/*/SKILL.md` for old phrasing that the change has invalidated. The pre-commit hook (`.git/hooks/pre-commit` check #6) enforces this for the deploy-model drift class (stale baked-image or volume-mount claims). Add new patterns to that hook when shipping new infrastructure rules. *Why: 2026-05-05: shipped volume-mount fix in `docker-compose.yml` but the previous AGENT_SOP rule "Container deploy: rebuild, do not docker-cp" remained in the same file for 6 hours, contradicting the deployed reality. Stale infra docs cause future agents to revert correct behavior or run obsolete commands. The hook turns this into a commit-time block instead of a discovery-by-incident.*
- **Every `claim()` call must be wrapped in `try/finally: complete()`.** A session that crashes or exits without calling `complete()` leaves a phantom `running` row. `gate_poll.py` reaps these every 5 min via `_reap_stale_leases()`, but clean shutdown is the contract -- the reaper is a safety net, not the plan. Pattern: `task = claim(...); if task is None: return; try: do_work() finally: complete(task["id"])`. The `lock()` context manager already enforces this. Direct `claim()` callers must do it manually. *Why: 2026-05-04 `claude-main` session died mid-run, leaving `studio_blotato_publisher.py` and `studio_production_crew.py` locked as `running` for 6 days. Any agent needing those files saw them as held and could not proceed. Phantom locks caused the multi-session conflict backlog diagnosed 2026-05-10.*

- **Never run `git filter-repo` while live remote branches exist.** If a secret lands in a commit: (a) rotate the token immediately, (b) use GitHub's secret bypass URL to push, (c) add the token pattern to `scripts/check_vendor_tokens.py`. History rewrite while branches are live forces mass SHA divergence across all active work — 2026-05-10 filter-repo run with 23 live branches caused mass SHA divergence, 2000+ spurious gate alerts, 4-hour rebase session. Only run filter-repo during a full branch freeze (all agents stopped, all non-main branches merged or deleted). *Why: 2026-05-10 root cause analysis.*

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

## Agent Role Authority

Every session has exactly ONE role. Determine it at session start using this table. Do not perform the other roles' actions.

| Role | Authority | Hard limits |
|------|-----------|-------------|
| **Gate** | Merge to main, push to VPS, approve/reject [READY] branches | Refuses all other work until queue is clear |
| **Coding agent** (spawned, autonomous) | Edit files, commit to feature branch, push feature branch | Never push to main, never deploy, never merge |
| **Direct session** (Boubacar present) | Edit files, claim tasks, coordinate | Never push without explicit "push it" instruction from Boubacar |

If unsure which role: check whether Boubacar explicitly assigned Gate duty this session. If not, treat as direct session. Full role detail in `CLAUDE.md` Agent Role Authority section.

## Concurrency Rule

**1 message = all related operations.** Batch all independent tool calls in a single response turn.

- Batch ALL file reads in one message
- Spawn ALL subagents in one message with `run_in_background: true`
- Batch ALL file edits that do not depend on each other in one message
- After spawning subagents: do NOT poll for status. Wait for completion notifications.

**Never continuously check status after spawning agents. Wait for results.**

Non-Claude agents (Codex, other): same rule applies. Call coordination tools and immediately continue working. Never stop and wait for an orchestrator to "do work" after a registration call.

## Extension Ownership Boundary

Fix owner-specific behavior in the owner module only. Core gets generic seams, not bundled extension logic. Concrete rules:

- `gate_agent.py` owns Gate behavior. Skills own their own `SKILL.md` + tests. No cross-module patches.
- If a bug is in skill X, fix skill X — do not add a workaround in `engine.py` or `coordination.py`.
- If a capability is needed by two skills, the correct fix is a shared helper in `skills/coordination/` or `orchestrator/`, not copy-paste into both skill dirs.
- Before touching any file outside the module you are fixing, ask: is this a seam (generic interface) or a bundled extension (owner-specific logic)? Seams belong in core. Logic belongs in the owner.

*Pattern source: openclaw/openclaw AGENTS.md — "Extension-specific behavior stays extension-owned. Core provides generic seams only." Absorbed 2026-05-09.*

## Coding Principles (Karpathy)

1. **Think before coding**: state assumptions; ask when ambiguous.
2. **Simplicity first**: minimum code that solves the problem.
3. **Surgical changes**: touch only what must change.
4. **Goal-driven execution**: verifiable success criteria, checkpoints, loop back.

**Multi-agent work:** apply `skills/boubacar-skill-creator/references/context-budget-discipline.md` - four-tier degradation model (PEAK/GOOD/DEGRADING/POOR), read-depth-by-window table, early warning signs. Apply `skills/boubacar-skill-creator/references/gates-taxonomy.md` for any workflow with subagents or review loops.

## Context-Mode Rule

**Use `/ctx` before any multi-file exploration.** context-mode saves ~40% context vs manual file reads by running commands in a sandbox and returning only summaries.

- Any `git log`, `git diff`, log reads, test runs, docker inspect → `ctx_execute` not Bash
- Any large file read for analysis (not editing) → `ctx_execute_file` not Read
- Any Playwright snapshot → `browser_snapshot(filename)` → `ctx_index(path)` → `ctx_search`

MCP server registered in `settings.json` mcpServers. If tools unavailable, restart Claude Code.

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

If you need to discover available capabilities, read `docs/SKILLS_INDEX.md`.

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
test
