# Session Handoff - Notion Task Audit + Poller + /task add Shipped - 2026-05-02

## TL;DR

Friday cleanup that became a 12+ hour focused build. Three major arcs:

1. **Full Notion Task DB audit** (Round 1 of 2): walked 4 roadmaps + 56 plans + 45 specs + 70 handoffs, harvested 638 atomic tasks via Haiku LLM extraction, normalized Source field, ran 4-pass dependency filter (Haiku → Sankofa Council → strict real-blocker → meta-work) down to 48 real Blocked By edges across 38 active tasks, surfaced 8 Golden Gems from archived material. Schema v2 dropped 7 unused fields, added Task ID (T-YYxxxx year-prefixed), Blocked By self-relation, rebuilt Owner (Boubacar/Coding/agentsHQ/Decision) and Sprint (Backlog/Week 1-12/Archive). One P0 dictator at top of Notion: T-260393 "Follow up on inbox replies within 24 hours".
2. **VPS-edits-override merge** (Round 2): parallel session had been editing email templates + sequence_engine + AGENT_SOP directly on VPS for the no-greeting-when-first-name-unknown rule. Pulled VPS edits down, merged with VPS-priority, committed in 2 logical commits, pushed. Plus 60+ deliverables from the Catalyst Works internal teardown.
3. **Notion State Poller + /task add** (M15, Round 3): Sankofa Council reframe killed the original /task done/p0/sprint command surface in favor of a passive 5-min Notion poller writing to data/changelog.md. /task add is the only Telegram verb. C1-C4 all verified live on VPS via PR chain (#25, #26, #27, #28, #29). 4-PR fix chain after initial merge addressed: heartbeat crew gate, REPO_ROOT path under flattened container, changelog mount path, atlas roadmap M15 SHIPPED entry.

Session ended with all 3 (local + GitHub + VPS) in sync at `093a64e`.

## What was built / changed

### Round 1: Audit harvester (PR #24)

- `scripts/notion_task_audit.py` (~600 lines) - walks markdown feeders, Haiku-extracts atomic tasks, classifies, dedupes, upserts to Notion. Re-runnable via `--mode=sweep --window=14d`.
- `tests/test_notion_task_audit.py` - 26 unit tests
- `docs/superpowers/specs/2026-05-01-notion-task-audit-design.md`
- `docs/superpowers/plans/2026-05-01-notion-task-audit.md`
- Notion schema v2 (live via API): added Source, Completion Criteria, Task ID, Blocked By, rebuilt Owner + Sprint
- 564 Source fields normalized from raw paths to "Roadmap: Atlas" etc.
- 8 Golden Gems written to Notion as T-26610..T-26617 with `🔍 GOLDEN GEM:` Notes prefix
- 48 Blocked By relations written across 38 tasks (after 4-pass filter)
- Audit files committed to `docs/audits/`: archived (1424 items), summary, needs-review, dependencies, dependencies-council-reviewed, golden-gems

### Round 2: VPS edits + handoffs (part of PR #24 merge + earlier commits)

- `templates/email/{cold_outreach, cw_t2, cw_t3, cw_t4, cw_t5, sw_t1, sw_t2, sw_t3, sw_t4}.py` - all 9 templates refactored to `build_body(lead)` callable with confidence-aware greeting
- `skills/outreach/sequence_engine.py` - source-aware first-name extraction with HIGH/LOW confidence
- `signal_works/topup_leads.py` - `_resolve_email` returns owner_name in addition to email + source
- `docs/AGENT_SOP.md` - hero-is-the-close hard rule + no-greeting hard rule
- `skills/apollo_skill/SKILL.md`, `skills/frontend-design/SKILL.md`, `skills/website-intelligence/SKILL.md` - HARD RULES blocks (em-dashes scrubbed)
- `deliverables/teardowns/catalystworks-consulting/` - 60+ files (research, mockups, previews, palette swatches)
- 2 new handoff docs: 2026-05-01-no-greeting-rule, 2026-05-01-constraints-ai-live
- `.gitignore` - added pytest tmp dirs + `.codex-task-progress.txt`

### Round 3: Poller + /task add (PRs #25-#29)

- `orchestrator/notion_state_poller.py` (~400 lines) - 5-min heartbeat tick, queries Notion for rows changed in last 6 min, diffs against `data/notion_state_cache.json`, appends to `data/changelog.md`. Backfill mode on first run. Coordination lock via `skills.coordination.lock("task:notion-state-poller")`.
- `tests/test_notion_state_poller.py` - 22 unit tests (cache I/O, property extraction, diff, format, query pagination, tick orchestration)
- `orchestrator/handlers_commands.py` - `handle_task_add()` parser + Notion writer + `_cmd_task_add` dispatch hook
- `tests/test_handle_task_add.py` - 11 unit tests
- `orchestrator/scheduler.py` - registered `notion-state-poller` wake every 5m under `_heartbeat.SELF_TEST_CREW`
- `docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md`
- `docs/superpowers/plans/2026-05-02-task-poller-and-add.md`
- `docs/roadmap/atlas.md` - M15 SHIPPED entry

### Fix chain (4 PRs after initial merge)

- **PR #26** `fix/poller-crew-gate`: changed `crew_name="atlas"` to `_heartbeat.SELF_TEST_CREW`. Heartbeat had been silently skipping every fire because no atlas crew exists in autonomy_state.json.
- **PR #27** `fix/poller-container-paths`: REPO_ROOT under flattened orc-crewai container resolved to `/` instead of `/app`. Pinned to `/app` when `__file__` parent is `/app`.
- **PR #28** `fix/changelog-into-mounted-data`: moved changelog from `/app/docs/audits/` (NOT mounted) to `/app/data/` (mounted to `/root/agentsHQ/data/`). Original spec said `docs/audits/changelog.md` but pragmatic fix is `data/changelog.md`.
- **PR #29** `docs/atlas-m15-shipped`: roadmap update with M15 SHIPPED entry.

## Decisions made

1. **Sankofa Council reframe killed the /task command surface for state mutations.** Original spec had `/task done`, `/task p0`, `/task sprint`, etc. Council verdict: command surface forces operator discipline that fails in practice. Replaced with passive Notion poller + only `/task add` for fast capture. Spec section 5.2 preserves the rationale.
2. **Year-prefix Task ID format `T-YYxxxx` (4-digit suffix).** Auto-rolls 2027-01-01 to T-27001. Avoids collisions, makes creation year visible.
3. **Owner taxonomy: Boubacar / Coding / agentsHQ / Decision.** Replaces single-option Owner. Daily view filters to `Owner contains Boubacar` to cut cardinality from 299 active rows down to 198 truly-actionable.
4. **Dependencies must have REAL teeth** (Boubacar's rule). 4-pass filter brought 128 raw Haiku candidates -> 119 Sankofa survivors -> 63 strict real-blocker -> 48 final after meta-work removal. Final ~19% of active rows have a Blocked By edge.
5. **Notion = state truth + editing surface, NOT read-only-for-edits.** Earlier session said "Notion read-only", Sankofa flipped this: Notion stays the editing surface (where it's actually fast on mobile), agentsHQ catches up via poller.
6. **Changelog format is a public contract.** Format locked: `<ISO_UTC> | <task_id> | <verb> | "<title>" | <change_desc>`. Closed verb list. Future consumers (3-day past-due, daily standup, gem nudge) read it.
7. **Bundled commits when Codex sandbox blocks `.git`.** Codex executes 10-task plan, parent commits as one bundle with all 10 tasks named in commit message. Audit trail = plan + handoff + commit message.
8. **VPS-priority on parallel-session merges except for website work.** Boubacar's standing rule. Website edits go local -> GitHub direct -> Hostinger pulls.

## What is NOT done (explicit)

- **`/task done`, `/task p0`, `/task sprint`, `/task block`, `/task archive`, `/task reopen`, `/task reassign`** - all state-mutation verbs. Build only when a specific friction is named. Sankofa reframe kept the surface minimal.
- **3-day past-due Telegram digest** - reads the changelog. Heartbeat job, ~30 lines Python. Spec section 4.2.
- **Daily standup digest** - groups last-24h changelog by verb. Trivial.
- **Bi-weekly Golden Gem nudge** - surfaces Gems unchanged for 14+ days.
- **Roadmap markdown auto-edit** when Status flips Done. Sankofa: too fragile across 4 roadmaps + 56 plans + 70 handoffs.
- **`--due` flag on `/task add`** - YAGNI until phone-friction-felt.
- **Automated changelog rotation when file >5 MB** - manual when needed.
- **`thepopebot-runner` cleanup** - GitHub Actions self-hosted runner stuck in restart loop since 2026-04-27 (`Cannot configure the runner because it is already configured`). Not blocking anything operational. Either remove via `./config.sh remove --token <token>` then restart, or drop the service from `docker-compose.yml`.
- **Estimated Hours field on Notion** - extracted by harvester, only embedded in Completion Criteria text. Make a sortable column if you want filter-by-time.

## Open questions

1. **Will the `--mode=sweep` re-run produce duplicates?** Harvester does title-match dedupe. With Task IDs now stable, future runs should match-by-Task-ID not title (deferred follow-up).
2. **Should the changelog include `system | tick` lines for empty ticks?** Currently only writes on real events. Discussion of "did the poller fire or not" is answered by container logs. Acceptable as-is.
3. **What's the right cadence for the bi-weekly Golden Gem review?** Spec says "every other Friday." Boubacar should set a reminder OR build the read-only digest job that surfaces stale Gems automatically.

## Next session must start here

1. **Read this handoff doc** at `docs/handoff/2026-05-02-notion-task-audit-and-poller-shipped.md`.
2. **Read `project_notion_task_system_state.md` in memory** for the current Notion DB state + open follow-ups.
3. **Open Notion at https://app.notion.com/p/249bcf1a302980739c26c61cad212477** and use it like a normal task DB. Click Status changes, set P0 by hand, drag rows into sprints. The poller catches up within 5 min.
4. **Test `/task add` from your phone** when you have a thought you want captured fast: `/task add "Reply to <name>"` → reply within 30s with new T-26xxx + top 3 next tasks.
5. **Confirm changelog is being populated:** `ssh root@72.60.209.109 "cat /root/agentsHQ/data/changelog.md | tail -10"` should show recent events.
6. **Container cleanup follow-up (low priority):** `thepopebot-runner` restart loop. Decide: remove service, or fix `./config.sh` registration.

## Files changed this session

```
docs/audits/
  2026-05-01-archived.md (NEW)
  2026-05-01-dependencies-council-reviewed.md (NEW)
  2026-05-01-dependencies.md (NEW)
  2026-05-01-golden-gems.md (NEW)
  2026-05-01-needs-review.md (NEW)
  2026-05-01-summary.md (NEW)
docs/handoff/
  2026-05-01-no-greeting-rule-and-cw-personalizer-fixes.md (committed)
  2026-05-01-constraints-ai-live-and-revenue-moves.md (committed)
  2026-05-02-notion-task-audit-and-poller-shipped.md (NEW, this file)
docs/roadmap/atlas.md - added M15 entry
docs/superpowers/specs/
  2026-05-01-notion-task-audit-design.md (NEW)
  2026-05-02-task-poller-and-add-design.md (NEW)
docs/superpowers/plans/
  2026-05-01-notion-task-audit.md (NEW)
  2026-05-02-task-poller-and-add.md (NEW)
scripts/notion_task_audit.py (NEW)
tests/test_notion_task_audit.py (NEW)
orchestrator/notion_state_poller.py (NEW)
tests/test_notion_state_poller.py (NEW)
tests/test_handle_task_add.py (NEW)
orchestrator/scheduler.py - 1 wake registration added
orchestrator/handlers_commands.py - handle_task_add + parser + dispatch
docs/AGENT_SOP.md - hero rule + no-greeting rule
skills/{apollo_skill,frontend-design,website-intelligence}/SKILL.md - HARD RULES blocks
templates/email/* - 9 templates with build_body(lead)
skills/outreach/sequence_engine.py - source-aware first-name extraction
signal_works/topup_leads.py - owner_name return
deliverables/teardowns/catalystworks-consulting/ (NEW dir, 60+ files)
.gitignore - pytest tmp + codex progress + task_progress
```

**Memory files added/updated this session:**
- `feedback_flattened_container_imports.md` - extended with `__file__` path resolution lesson + mount inventory
- `feedback_heartbeat_crew_gating.md` (NEW)
- `feedback_notion_last_edited_time_quirk.md` (NEW)
- `feedback_codex_sandbox_commit_pattern.md` (NEW)
- `project_notion_task_system_state.md` (NEW)
- `MEMORY.md` line 84 - 4 pointers compressed into one line
- `MEMORY_ARCHIVE.md` - new "Active project state" section header

**PRs merged this session:** #24, #25, #26, #27, #28, #29.

**Final 3-way sync:** local + GitHub + VPS all at `093a64e`.
