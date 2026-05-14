# RCA: Gate merge-conflict spam loop on stale-base feature branches - 2026-05-14

**Root cause:** Gate's `_merge_branch` made no attempt at conflict resolution and returned `(False, "")` because git writes conflict markers to stdout (not stderr), leaving the Telegram alert content-free. Module-level dedup set (`_alerted_high_risk`, `_alerted_conflicts`) was reset on every systemd-timer process start, so the same MERGE FAILED alert re-fired every 60s tick. Triggered today by `feat/nate-tanner-audit-2026-05-14` [READY] tip `57a64ca` conflicting with main HEAD `255e9c3f` on `docs/roadmap/lighthouse.md` Session Log (both sides inserted Day 2 entry at the same newest-first anchor).

**Fix applied:**
- New module `orchestrator/gate_resolvers.py`: archive helpers + tiered deterministic resolvers (union for append-only logs, theirs-wins for everything else).
- `orchestrator/gate_agent.py::_merge_branch` (~155 lines new): on conflict, list conflicted files; archive both stages to `zzzArchive/gate-merges/<isotime>-<branch>/{main,branch}.<flattened-path>` BEFORE any resolution; HIGH_RISK conflicts halt with combined stdout+stderr in error; non-core conflicts auto-resolve per tier, archive resolved snapshot, commit merge with archive paths in commit message.
- `orchestrator/gate_agent.py` persistent dedup: `DEDUP_PATH = DATA_DIR / gate_alerted.json` with `_load_dedup`, `_save_dedup`, `_alerted_recently`, `_mark_alerted`, `_clear_alerted`, `_branch_tip_sha`. Keys: `high_risk[branch]=tip_sha`, `merge_fail[branch]=tip_sha`, `conflict[b1||b2||file]=tip_a|tip_b`. Wired into all three alert sites. Cleared on successful merge or explicit reject.
- `tests/test_gate_resolvers.py`: 12 unit tests covering is_append_only_log, union_entries dedup + ordering + empty sides, resolve_append_only_log round-trip, multi-block files. All green locally.

**Branch pushed:** `feat/gate-archive-merge-resolver` tip `37c9423` with `[READY]` tag. HIGH_RISK approval required (gate_agent.py edit).

**Success criterion (post-merge):**
1. Trigger a conflict on a non-HIGH_RISK append-only log path. Expected: gate merges cleanly; archive dir contains main/branch/resolved files; no Telegram alert.
2. Trigger a HIGH_RISK conflict. Expected: single Telegram alert with combined stdout+stderr text (not empty); re-tick on same branch tip = no second alert; tip moves = fresh alert.
3. `cat /var/lib/gate-agent/gate_alerted.json` shows persistent state keyed on branch->tip_sha.

**Never-again rule (HARD):** Gate cannot merge a non-HIGH_RISK conflict without first archiving both versions. Any new conflict resolver added to gate_resolvers.py must include archive-first behavior in its caller path. gate_agent.py changes go through Council premortem + Karpathy gate before code commit.

**Memory update:** YES - `feedback_gate_archive_merge_resolver.md` added.

---

## Sankofa Council premortem (Dead-Project mode, 6mo retrospective)

Pre-shipping, Council ran a retrospective on the original proposed fix (auto-rebase + stdout capture + module-level dedup).

- **Contrarian:** auto-rebase silently dropped one side's content on non-overlapping inserts at the same anchor. 3 silent data-loss incidents in 60 days. Unfixable when Boubacar quoted a corrupted entry in a client proposal.
- **First Principles:** wrong layer. Roadmap session log is a single shared mutable anchor; conflict is structural, not coincidental. Right fix: per-session JSON aggregator. Wrong fix: better merge mechanics on a broken architecture.
- **Outsider:** module-level dedup dict on a systemd-timer process = dead state on every tick. Insider knew the systemd-timer pattern (memory rule existed) and still wrote `_alerted_merge_fail: dict = {}`.
- **Expansionist:** per-session JSON entries, pre-commit hook on roadmap, separate `data/agent-session-logs/<branch>/` write path, or one-shot human-in-loop Telegram with the rebase command. Any would have saved the project.
- **Executor:** warning visible week of 2026-05-12 (Lighthouse Day 0, cadence flipped to multiple agents per day). Ignored for 2 days. Fired loud 2026-05-14.

**Verdict:** the auto-rebase part is wrong. The other two parts (better err text + dedup) are right BUT the dedup needs persistent state, not module-level.

## Karpathy audit (4 principles)

- **P1 Think Before Coding:** PASS — Council ran before any edit; intent stated; assumptions challenged.
- **P2 Simplicity First:** WARN — Council added a roadmap-specific Telegram handler beyond Parts 2+3; not minimum. Action: drop it; let improved err do the work.
- **P3 Surgical Changes:** WARN — per-session JSON aggregator architecture is multi-system; cannot bundle into a gate_agent.py PR. Action: file as separate roadmap milestone.
- **P4 Goal-Driven Execution:** PASS — success criterion stated + verifiable.

**Verdict:** HOLD until P2 + P3 actions applied. After dropping roadmap-specific handler + filing architecture fix separately + persisting dedup state to flat file: SHIP.

## Boubacar override (key reframe)

Boubacar: "I want this to be fixed in such a way that whenever merge needs to happen you figure out how it needs to happen. Gate knows how to make the merge happen and we don't lose data. We don't lose items and the merge just happens." Plus archive-not-delete rule.

Archive-not-delete unlocks safe auto-resolve. Council's data-loss veto on auto-rebase is downgraded because pre-resolve archive preserves every input version. Final design: archive-first + tiered deterministic resolvers + persistent dedup. Drops auto-rebase entirely (still risky even with archive because rebase rewrites SHAs unrelated to the conflict surface).

## Files changed this session

- `orchestrator/gate_resolvers.py` (new, 191 lines)
- `orchestrator/gate_agent.py` (modified, +159 / -9)
- `tests/test_gate_resolvers.py` (new, 12 tests)
- `docs/handoff/2026-05-14-gate-merge-conflict-archive-rca.md` (this file)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_gate_archive_merge_resolver.md` (memory)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md` (+1 index line under Gate section)

## Open follow-up (separate roadmap milestone)

Per-session JSON aggregator for roadmap session logs. Eliminates the conflict surface entirely. NOT blocking. File under compass or atlas with 2026-05-21 target. Schema sketch: `data/session-log/<isotime>-<codename>-<agent>.json` containing one entry per session. Aggregator script regenerates the human-readable roadmap as a derived artifact. Pre-commit hook rejects direct edits to `## Session Log` blocks in roadmap files.
