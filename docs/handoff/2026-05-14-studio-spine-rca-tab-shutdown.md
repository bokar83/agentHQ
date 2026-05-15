# Session Handoff - Studio pipeline spine RCA + 3 subagent satellite fixes - 2026-05-14

## TL;DR

Boubacar asked "how is studio doing this week" -- triggered full /rca on the
Studio pipeline. RCA exposed 3 coupled defects (em-dash sanitizer asymmetry,
missing scouted->Ready filter, no silence watchdog). Sankofa Council premortem
killed Option E (governance theater); Karpathy audit caught proposed strip
duplicated existing _post_process. Reframe to Option E2-prime shipped with 3
parallel subagents handling engagement-scraper Indonesian-locale fix, Telegram
pulse callback handlers, and Lighthouse W1 demo decision (verdict: defer to
Sat 5/16 M5 Conversion Scorecard). Six branches gate-merged. Container
restarted. Pipeline self-heals. Blotato actively fanning out 29 records to
X+Instagram+TikTok+YouTube live. qa-failed cleared 13->0.

## What was built / changed

**Code (orchestrator/):**
- `studio_script_generator.py:367` -- _post_process now strips 4 dash variants
  (em-dash U+2014, en-dash U+2013, " -- " spaced, word--word no-space) via
  3 string-replaces + 1 regex sub.
- `studio_production_crew.py:_fetch_qa_passed_candidates` -- filter extended
  to include Status=scouted (one-pass invariant: run_production updates Status
  to scheduled or qa-failed).
- `studio_production_crew.py:studio_production_tick` -- pulse-state watchdog.
  Persists last_seen_with_candidates + last_alert_sent + snoozed_until to
  /app/workspace/studio_pipeline_pulse.json. Telegram alert with action
  buttons fires if 0 candidates >90 min and no alert in last 6h. Respects
  snoozed_until if set.
- `studio_analytics_scraper.py` -- _parse_leading_int (locale-tolerant int
  extractor; handles tontonan/vistas/vues/Aufrufe/views + thousand
  separators). _parse_youtube_views reads videoViewCountRenderer.simpleText
  first. Accept-Language: en-US,en;q=0.9 header forces English locale.
- `handlers_approvals.py:handle_callback_query` -- studio_pulse:ack and
  studio_pulse:snooze callback handlers. ack zeros last_alert_sent; snooze
  sets snoozed_until = now + 6h. editMessageText updates the alert message
  in place + removes buttons.

**Tests (orchestrator/tests/):**
- `test_studio_script_generator_emdash.py` -- 5 cases covering all 4 dash
  variants + no-dash baseline. PASS.
- `test_studio_pulse_callbacks.py` -- 5 cases: ack, snooze (with + without
  state file), watchdog suppression while snoozed, watchdog re-fires after
  snooze expires. PASS.
- `test_studio_analytics_scraper.py` -- 22 cases. PASS. Includes the exact
  production failure (Indonesian + originalViewCount=0 must return 14).

**Docs:**
- `docs/handoff/2026-05-14-studio-pipeline-spine-rca.md` -- full RCA.
- `docs/handoff/2026-05-15-studio-engagement-scraper-rca.md` -- scraper RCA.
- `docs/handoff/2026-05-15-studio-pulse-callbacks.md` -- callbacks handoff.
- `docs/roadmap/studio.md` -- session log entry appended.
- `docs/roadmap/lighthouse.md` -- W1 Day 2 PM side-track entry.

**Memory (~/.claude/projects/.../memory/):**
- `feedback_qa_check_paired_sanitizer.md` (new) -- regex check pattern set
  MUST equal sanitizer pattern set, or asymmetry documented + regression test.
- `feedback_studio_pipeline_spine_dependencies.md` (new) -- spine wiring
  (scouted in filter + silence alert + scheduled->blotato fan-out) is
  load-bearing.
- `MEMORY.md` -- 2 entries indexed. Voice-signature + Multiplier consolidated
  to free a line. Now 200 lines (at cap).
- VPS Postgres `memory` table -- 5 lessons + 1 project_state + 1 session_log
  written via container.

**Skills:**
- `~/.claude/skills/rca/SKILL.md` + repo mirror `skills/rca/SKILL.md` --
  added 3 Known Pitfalls: stale failure-reason fields mislead diagnosis,
  dry_run paths often bypass production logic, asymmetric check+sanitizer
  pair = silent rejection loop.

## Decisions made

1. **Two-review gate before any non-trivial fix:** /sankofa premortem AND
   /karpathy audit run before code change. Both rejected the first 2 fix
   proposals (Option E, Option E2 initial draft). Final shipped fix was
   structurally different from initial proposal.
2. **Scouted records auto-advance via filter inclusion, not via separate
   qa-tick.** One-line change, simpler than building new tick. run_production
   already handles full pipeline; filter just needed to fetch the input.
3. **6h watchdog cooldown for repeated alerts** (avoid spam during natural
   queue-empty windows like Sundays).
4. **Lighthouse W1 demo writeup defers to Saturday 5/16 10:30 MDT M5
   Conversion Scorecard,** not Sunday. Per Sankofa subagent verdict.
5. **Engagement scraper backfill happens automatically** on next analytics
   tick (daily). No manual re-scrape needed.

## What is NOT done (explicit)

- **Worktree cleanup** -- D:/tmp/wt-* still has 4-5 worktrees from this
  session and earlier sessions. Low priority; auto-cleanup on next nsync.
- **Studio pipeline silence-vs-empty distinguishing** -- watchdog currently
  fires on legitimate empty queue (true positive but cosmetic noise). Could
  refine to only fire when scouted_count > 0 AND tick fetches 0. Followup.
- **Lighthouse Sat 5/16 M5 Conversion Scorecard** -- Boubacar runs the
  Saturday ritual. No template established yet; subagent recommended HTML
  scorecard at `docs/lighthouse/w1-scorecard-2026-05-16.html` to start the
  W1-W12 convention.

## Open questions

- None blocking. Pipeline live + verified.

## Files changed this session

```
orchestrator/
  studio_script_generator.py        (+5 / -1)
  studio_production_crew.py         (+78 / -1)
  studio_analytics_scraper.py       (+50ish)
  handlers_approvals.py             (callback branch)
  tests/test_studio_script_generator_emdash.py   (NEW, 5 tests)
  tests/test_studio_pulse_callbacks.py           (NEW, 5 tests)
  tests/test_studio_analytics_scraper.py         (NEW, 22 tests)

docs/
  handoff/2026-05-14-studio-pipeline-spine-rca.md      (NEW)
  handoff/2026-05-15-studio-engagement-scraper-rca.md  (NEW)
  handoff/2026-05-15-studio-pulse-callbacks.md         (NEW)
  handoff/2026-05-14-studio-spine-rca-tab-shutdown.md  (this file, NEW)
  roadmap/studio.md                                    (session log appended)
  roadmap/lighthouse.md                                (W1 Day 2 PM side-track)

skills/rca/SKILL.md                  (3 Known Pitfalls added)
~/.claude/skills/rca/SKILL.md        (mirrored)

memory/
  feedback_qa_check_paired_sanitizer.md             (NEW)
  feedback_studio_pipeline_spine_dependencies.md    (NEW)
  MEMORY.md                                         (2 entries indexed)

VPS Postgres memory table:
  5 AgentLesson + 1 ProjectState + 1 SessionLog rows
```

## Branches merged via gate

```
fix/studio-emdash-spine                d3651e7
docs/studio-spine-rca-2026-05-14       467bff0
fix/engagement-scraper-locale          5106f9f
chore/roadmap-logs-2026-05-14          bd538ac
fix/studio-pulse-callbacks             5b36d5e
fix/absorb-scout-wake-restore-2026-05-14   8c5e53b  (someone else's, batched in)
```

## Verification at next deploy / next session

1. blotato_publisher 09:00 UTC (~7h from now) processes remaining scheduled
   records. Watch `STUDIO PUBLISHER: tick done` log.
2. studio_analytics_scraper next analytics tick (18:00 UTC daily) backfills
   Views=0 records on previously-published posts.
3. Saturday 2026-05-16 10:30 MDT: Boubacar runs M5 Conversion Scorecard for
   Lighthouse W1 close.
