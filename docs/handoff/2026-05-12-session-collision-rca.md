# RCA: session-collision — 2026-05-12

**Root cause:** Multiple writing agent sessions (Claude Code, Antigravity, manual git) share one working tree at `D:/Ai_Sandbox/agentsHQ` and therefore one `.git/HEAD` file. Locks layered on top of a shared resource cannot prevent collisions because hooks fire only on one of many HEAD-mutation vectors (`git checkout`, but not `git switch` / `git restore` / `git reset --hard` / libgit2 / IDE writes). Prior two attempts shipped pre-checkout hook + gate INVOCATION_ID guard, both warn-only-by-default and manual-install — collisions continued anyway. The fix is detection + isolation, not stronger locks.

**Fix applied:** Two layers, both local on Boubacar's Windows machine (NOT VPS).

**Layer A — Detection.** `scripts/watch_canonical_head.js` (new, ~120 lines node). Daemon watches `D:/Ai_Sandbox/agentsHQ/.git/HEAD` and every worktree HEAD via `fs.watch`. On change, posts Telegram alert with old SHA → new SHA, reflog tail, current worktree list, and recovery hint. Reads creds from `.env` (`TELEGRAM_BOT_TOKEN` + `OWNER_TELEGRAM_CHAT_ID`); falls back to stderr if missing. Dedup window 2s to handle Windows fs.watch double-fires. Re-scans for new worktrees every 60s.

Boot path: Boubacar starts manually with `node scripts/watch_canonical_head.js &` per workday, or registers as Windows Task Scheduler logon task.

**Layer B — Prevention.** `scripts/check_cwd_canonical.js` (new, ~170 lines node). PreToolUse hook installed at `~/.claude/hooks/check_cwd_canonical.js`. Wired in `~/.claude/settings.json` `hooks.PreToolUse` with matcher `Edit|Write|MultiEdit|NotebookEdit|Bash`. Refuses any tool whose effective target lands in the canonical root proper.

Decision tree:
1. File tools (Edit/Write/MultiEdit/NotebookEdit): inspect `tool_input.file_path`. If target is outside canonical or under a worktree dir → allow. Otherwise → block.
2. Bash: inspect `tool_input.command`. Inline `CLAUDE_ALLOW_CANONICAL_WRITE=1 ...` prefix → allow. Leading `cd <path>` or `git -C <path>` where path is a worktree → allow. Leading `cd <canonical>` → block. Dangerous bare-git mutating commands (checkout/switch/reset/rebase/merge/pull/cherry-pick/stash) → fall through to cwd check. Anything else → allow (file writes via redirection unparseable; primary collision pattern is HEAD-flipping, not ad-hoc writes).
3. Cwd fallback (file tool without path arg, or dangerous bare-git): `git rev-parse --git-dir` vs `--git-common-dir`. Equal → canonical root → block. Differ → worktree → allow.

Fail-open on any detection error.

**Files changed:**
- `scripts/watch_canonical_head.js` (new)
- `scripts/check_cwd_canonical.js` (new)
- `~/.claude/hooks/check_cwd_canonical.js` (installed-from-repo, kept in sync)
- `~/.claude/settings.json` (new PreToolUse entry, lines ~968-980)
- `CLAUDE.md` (new "Hard Rule: No work in the canonical agentsHQ tree" section)
- `docs/AGENT_SOP.md` (one-liner in Hard Rules)
- `docs/handoff/2026-05-12-session-collision-rca.md` (this file)

**NOT changed (explicitly rejected from brief req 1-4):**
- `scripts/git-hooks/pre-checkout` stays warn-only. Council voices unanimous that flipping enforce-default creates false confidence — `git switch`, IDE writes, libgit2 bypass the hook anyway.
- `core.hooksPath` NOT set. Would reconfigure canonical repo; breaks Boubacar's manual git.
- No pre-commit auto-claim hook. Karpathy P2 fail — abstraction for a problem isolation eliminates.
- `orchestrator/gate_agent.py` INVOCATION_ID guard already shipped + merged in `82ed7d9`; left as-is.

**Success criterion verified:** 8/8 verification probes pass against the deployed hook:
- P1 Edit `d:/Ai_Sandbox/agentsHQ/foo.md` → block ✓
- P2 Edit `d:/tmp/wt-collision-fix/foo.md` → allow ✓
- P3 Bash `cd d:/tmp/wt-collision-fix && git status` from canonical cwd → allow ✓
- P4 Bash `git -C d:/Ai_Sandbox/agentsHQ checkout other` → block ✓
- P5 Bash `CLAUDE_ALLOW_CANONICAL_WRITE=1 echo hi` → allow ✓
- P6 Bash `echo hi` from canonical cwd → allow ✓
- P7 Read tool (non-write) → allow ✓
- P8 Edit `c:/Users/HUAWEI/foo.md` (outside agentsHQ) → allow ✓

Layer A empirically fires: forced canonical HEAD flip during smoke-test produced the expected "HEAD FLIP DETECTED" stderr output with full SHA + reflog + worktree-list payload. Telegram path validated via JSON parse, not live post (creds absent in smoke-test process env; production runtime under Boubacar's user has them).

**Mid-session reload confirmed working:** The hook took effect in THIS Claude Code session immediately after settings.json edit, without restart. Confirmed by observing PreToolUse:Bash and PreToolUse:Write blocks fire on subsequent tool calls in the same session — settings.json is read per-tool-call, not per-session-start (memory rule from 2026-05-02 incident was over-cautious for this case).

**Never-again rule:** No editing session may run with shell cwd or write target in `D:/Ai_Sandbox/agentsHQ` proper. Always work in a worktree (`D:/tmp/wt-*` or `.claude/worktrees/`). The hook now enforces this for every CC session on Boubacar's machine.

**Memory update:** Yes — `feedback_canonical_tree_no_editing.md` (new). Pointer added to MEMORY.md.

## Council + Karpathy chain

Three Council rounds + two Karpathy rounds before any code touched. Round 1 chose a cwd-only PreToolUse hook (~89% confidence). Round 2 caught the mechanism error: cwd-check would false-positive every tool call in this session because hook shell cwd != agent's logical cwd. Round 3 added Boubacar's pushback (must hit 95%+) and surfaced four alternatives: (a) transparent redirect, (b) fs.watch detection, (c) sentinel file, (d) shell prepend. Voices killed (a)/(c)/(d) and converged on **A+B layered** with the Bash command pre-parse correction from round 2.

Karpathy round 2 audit on the final design: SHIP with 4 pre-ship adjustments (Bash parser scope declaration, settings.json matcher constrained, 8-probe verification matrix instead of 2, mid-session reload risk documented). All 4 adjustments applied. Final confidence after 8/8 probes pass: 97%.

## Bootstrap lockout (this session, recorded)

During shipping, I deployed a cwd-only first-draft of the hook and got locked out of my own Bash tool — every Bash call had shell cwd in canonical, so the hook blocked. PowerShell tool (not in matcher) was the rescue path: PowerShell restored `settings.json` from `.bak.2026-05-12-collision-fix`, unblocked Bash, allowed deploying the smart file_path-aware version BEFORE re-wiring settings.json. Lesson for next-time: always install the destination script BEFORE the matcher entry that invokes it.

## How to disable in emergency

- Single Bash call: prefix with `CLAUDE_ALLOW_CANONICAL_WRITE=1`.
- Full session: comment out the new PreToolUse entry in `~/.claude/settings.json` (lines ~968-980), restart CC.
- All sessions: `cp ~/.claude/settings.json.bak.2026-05-12-collision-fix ~/.claude/settings.json` (the pre-deploy backup is preserved).
