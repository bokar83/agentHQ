# RCA: cold-outreach pipeline — 2026-05-12

**Subsystem:** Signal Works + Catalyst Works morning_runner / harvest / sequence_engine
**Trigger:** Boubacar reported SW=13 / CW=0 drafts today vs expected 50 NEW + T2-T4 follow-ups
**Severity:** P1 — primary outbound motion at ~26% of target
**Owner:** Boubacar (resolution), agentsHQ (diagnosis + fix)

---

## Root cause

`signal-works-morning.service` systemd `TimeoutStartSec=120min` killed `morning_runner` at 15:00:01 UTC mid-Step-2 SW topup, before Steps 3 (SW sequence drafts), 4 (CW Apollo), 4.5 (voice personalize), and 5 (CW sequence) could run. Step 2 hung because `topup_leads.topup(minimum=35)` loops until 35 email-bearing leads exist, and SMB trades (roofers/plumbers/electricians/chiros/dentists) have <5% Apollo coverage so leads saved as phone-only never count toward the target, looping until SIGKILL.

The 13 SW T2 drafts that DID land today were created post-orchestrator-restart at 16:19 UTC, processing a residual queue at 1.7s/draft — not from today's morning run.

## Eight contributing failures (full ranked table)

| # | Failure | File:line | Severity |
|---|---------|-----------|----------|
| 1 | Systemd 120min budget too tight for the work being done | `scripts/systemd/signal-works-morning.service:14` | 🔴 Critical |
| 2 | Per-process Hunter cap 200/day — hit at 13:18 UTC, then circuit breaker tripped 13:23 UTC | `signal_works/hunter_client.py:41` | 🔴 Critical |
| 3 | Step 2 bypassed `harvest_until_target.py` (400 cap path), called bare `topup_leads.topup()` (200 cap) | `signal_works/morning_runner.py:124` | 🟠 High |
| 4 | Apollo coverage gap for SMB trades — `no Apollo org match` / `no owner-tier people` for the majority of calls | network behavior | 🟠 High |
| 5 | Recycle-original-CW-queue fallback **never coded** — step 5b removed 2026-05-11, no replacement | `signal_works/morning_runner.py:206-209` | 🔴 Critical |
| 6 | `pipeline_metrics` table missing in orc-postgres — `log_step()` calls silently swallowed | `signal_works/pipeline_metrics.py` auto-create vs migration absence | 🟡 Medium |
| 7 | No CW-specific timer — CW depends 100% on shared SW service that already times out | systemd unit files | 🟠 High |
| 8 | Health-check Telegram alerts at runner end unreachable when runner killed mid-Step 2 | `signal_works/morning_runner.py:281` | 🟠 High |

## Fix applied

Shipped via 2 PRs + 1 follow-up patch + 1 migration, all merged to main 2026-05-12:

**PR #36 — `fix/harvest-hunter-cap-apollo-fallback-prospeo-chain`** (Agent 3)
- `signal_works/hunter_client.py:41` — default cap 200 → 400 (env-overridable)
- `signal_works/topup_leads.py` — Apollo → Hunter → Prospeo cascading fallback chain (5-layer `_resolve_email`)
- `signal_works/topup_leads.py` — 45-min wall-clock cap inside `topup()`, exits gracefully on timeout instead of hanging
- `signal_works/prospeo_client.py` — NEW harvest-path wrapper (was only in `enrichment_tool` before)
- `tests/test_topup_leads_prospeo_fallback.py` — 9 tests covering cascade + cap + wall-clock

**PR #35 — `fix/sw-cw-orchestration-240min-recycle`** (Agent 2)
- `scripts/systemd/signal-works-morning.service:14` — `TimeoutStartSec` 120min → 240min
- `signal_works/morning_runner.py` — `atexit` partial-state Telegram alert, fires on SIGKILL/SIGTERM with whatever counts exist at exit
- `signal_works/recycle_cw.py` — NEW: scans last-7-day CW sends, ages `last_contacted_at` to clear next-touch gap, lets existing `run_sequence("cw")` advance them
- `signal_works/morning_runner.py` Step 5b — calls `recycle_cw` when `cw_drafted < CW_THRESHOLD (=10)`, feeds advanced cohort back through sequence_engine
- `migrations/008_pipeline_metrics.sql` — canonical schema for pipeline_metrics + adds `recycle BOOLEAN` column to `sw_email_log` with partial index

**Follow-up commit `0c1ba12` — codex review P1**
- `signal_works/topup_leads.py:210-225` — try/except around `int(env_cap)` so bad `HUNTER_MAX_SEARCHES_PER_DAY` config logs warning + falls back to 400 instead of crashing entire harvest

## Success criterion verified

**Live manual run 2026-05-12 17:54-18:48 UTC (systemctl start signal-works-morning.service):**

```
ssh root@72.60.209.109 "tail -50 /var/log/signal_works_morning.log | grep -E 'Run complete|TOTAL drafts'"
```

```
2026-05-12 18:48:36 INFO Run complete:
2026-05-12 18:48:36 INFO   Bounces cleared:        1
2026-05-12 18:48:36 INFO   SW leads harvested:     28
2026-05-12 18:48:36 INFO   SW drafts created:      34
2026-05-12 18:48:36 INFO   CW outreach drafts:     67
2026-05-12 18:48:36 INFO   TOTAL drafts in inbox:  101
```

**Threshold check:** SW=34 ≥ 30 ✓, CW=67 ≥ 10 ✓, total=101 ≥ 50 ✓.

**Each fix observed in production:**
- 240min budget used 54min — 23% utilization ✓
- 45-min wall-clock cap fired at 25/35 in Step 2, runner advanced to Step 3 cleanly ✓
- Hunter cap caught at 28min (400 calls) ✓
- Steps 3/4/4.5/5 all completed (previously killed mid-Step-2) ✓
- Recycle gate logic correct — didn't fire (CW=67 >> threshold=10) ✓

## Known issues parked

- 🟡 **Prospeo schema bug** — 100% INVALID_DATAPOINTS on all calls today, contributing 0% to the chain. Apollo + Hunter alone carried the harvest. Sub-agent (`aa250328257c81e5e`) currently working on fix in isolated worktree.
- 🟡 **Hunter Starter quota** — 100/2000 used. At 400/day cap, burns through quota in 5 days. Either raise Hunter to Growth tier or accept partial-fallback days.
- 🟡 **Apollo SMB coverage gap** — structural. No code fix solves it. Strategic decision pending (Council recommended pivoting CW off automated harvest; Boubacar reviewing with separate Antigravity agent).

## Never-again rule

**Every long-running pipeline step must have an internal wall-clock cap shorter than the orchestrator's outer timeout.** When the outer timeout (systemd / docker / cron) fires, it sends SIGKILL — bypassing any cleanup, telemetry, or downstream-step logic. The internal cap must trigger first so the step can exit gracefully and let downstream steps run.

Concretely: `morning_runner` has 240min systemd budget; Step 2 has 45min internal cap; Steps 3-5 share the remaining 195min. Any future Step X added to morning_runner must declare its own wall-clock cap upfront, summing to < outer budget.

## Memory update

**Yes** — adding `feedback_long_running_step_wall_clock_cap.md`:
- Rule: "Every long pipeline step caps its own runtime below the orchestrator's timeout"
- Why: 2026-05-12 morning_runner SIGKILL incident — systemd 120min budget exhausted by Step 2 SW topup, Steps 3-5 never ran. Telemetry + health alerts at end-of-runner unreachable.
- How to apply: when adding a step to morning_runner or any long pipeline, set `WALL_CLOCK_SECONDS` constant in module + exit gracefully with partial-state log when reached.

Existing rule `feedback_sw_pipeline_bottleneck.md` ("bottleneck = calls not infra") still applies — today proved it again. Apollo SMB coverage + Hunter quota structural ceilings dominate over any code fix.

---

**Phase 6 closure:** RCA complete, fixes shipped, live verification passed. Open thread = Prospeo schema fix + CW strategy pivot (both delegated to other agents).

**Cross-ref:**
- `docs/handoff/2026-05-12-master.md` — full day roll-up
- PR #35: https://github.com/bokar83/agentHQ/pull/35
- PR #36: https://github.com/bokar83/agentHQ/pull/36
- Council verdict on CW strategy: `/outputs/council/2026-05-12-18-37-24.html` (on VPS)
