# RCA: cold-outreach pipeline — 2026-05-12

**Subsystem:** Signal Works + Catalyst Works morning_runner / harvest / sequence_engine
**Trigger:** Boubacar reported SW=13 / CW=0 drafts today vs expected 50 NEW + T2-T4 follow-ups
**Severity:** P1 — primary outbound motion at ~26% of target
**Owner:** Boubacar (resolution), agentsHQ (diagnosis + fix)

---

## Root cause

`signal-works-morning.service` systemd `TimeoutStartSec=120min` killed `morning_runner` at 15:00:01 UTC mid-Step-2 SW topup, before Steps 3 (SW sequence drafts), 4 (CW Apollo), 4.5 (voice personalize), and 5 (CW sequence) could run. Step 2 hung because `topup_leads.topup(minimum=35)` loops until 35 email-bearing leads exist, and SMB trades have <5% Apollo coverage so leads saved as phone-only never count toward the target, looping until SIGKILL.

The 13 SW T2 drafts that DID land today were created post-orchestrator-restart at 16:19 UTC, processing a residual queue at 1.7s/draft — not from today's morning run.

## Eight contributing failures (ranked)

| # | Failure | File:line | Severity |
|---|---------|-----------|----------|
| 1 | Systemd 120min budget too tight | `scripts/systemd/signal-works-morning.service:14` | 🔴 Critical |
| 2 | Per-process Hunter cap 200/day — hit at 13:18 UTC | `signal_works/hunter_client.py:41` | 🔴 Critical |
| 3 | Step 2 bypassed 400-cap path | `signal_works/morning_runner.py:124` | 🟠 High |
| 4 | Apollo SMB coverage gap | network behavior | 🟠 High |
| 5 | Recycle-CW-fallback never coded | `signal_works/morning_runner.py:206-209` | 🔴 Critical |
| 6 | `pipeline_metrics` table missing | auto-create vs migration absence | 🟡 Medium |
| 7 | No CW-specific timer | systemd unit files | 🟠 High |
| 8 | Health-check alerts unreachable | `signal_works/morning_runner.py:281` | 🟠 High |

## Fix applied

**PR #36** (Agent 3) — Hunter cap 200→400, Apollo→Hunter→Prospeo cascade, 45-min wall-clock cap, new `prospeo_client.py`, 9 tests.

**PR #35** (Agent 2) — systemd 120→240min, atexit partial-state alert, new `recycle_cw.py` with T-advance via `last_contacted_at` ageing, migration 008 (pipeline_metrics + sw_email_log.recycle BOOLEAN).

**Follow-up `0c1ba12`** — Codex P1: try/except around `int(env_cap)` so bad config logs warning + falls back to 400 instead of crashing harvest.

## Success criterion verified

Live manual run 2026-05-12 17:54-18:48 UTC (`systemctl start signal-works-morning.service`):

```
Run complete:
  Bounces cleared:        1
  SW leads harvested:     28
  SW drafts created:      34
  CW outreach drafts:     67
  TOTAL drafts in inbox:  101
```

**Threshold check:** SW=34 ≥ 30 ✓, CW=67 ≥ 10 ✓, total=101 ≥ 50 ✓.

**Each fix observed in production:**
- 240min budget used 54min — 23% utilization ✓
- 45-min wall-clock cap fired at 25/35 in Step 2, runner advanced cleanly ✓
- Hunter cap caught at 28min (400 calls) ✓
- Steps 3/4/4.5/5 all completed (previously killed mid-Step-2) ✓
- Recycle gate didn't fire (CW=67 >> threshold=10) ✓

## Known issues parked

- 🟡 **Prospeo schema bug** — 100% INVALID_DATAPOINTS today, 0% contribution. Sub-agent fix in flight.
- 🟡 **Hunter Starter quota** — 100/2000 used. At 400/day cap = 5-day burn. Growth tier or partial-fallback days.
- 🟡 **Apollo SMB coverage gap** — structural. CW pivot (Antigravity agent shipping now) removes this constraint.

## Never-again rule

**Every long-running pipeline step must have an internal wall-clock cap shorter than the orchestrator's outer timeout.** SIGKILL from outer timeout bypasses cleanup, telemetry, downstream-step logic. Internal cap must trigger first so step exits gracefully.

`morning_runner`: 240min systemd outer, 45min Step 2 inner, 195min remaining for Steps 3-5. Any new step declares its own cap, sum < outer.

## Memory update

`feedback_long_running_step_wall_clock_cap.md`:
- Rule: every long pipeline step caps its own runtime below orchestrator timeout
- Why: 2026-05-12 morning_runner SIGKILL incident
- How to apply: set `WALL_CLOCK_SECONDS` constant in module, exit gracefully with partial-state log on timeout

`feedback_sw_pipeline_bottleneck.md` ("bottleneck = calls not infra") still applies — today proved it again.

---

**Phase 6 closure:** RCA complete, fixes shipped, live verification passed.

**Cross-ref:**
- `docs/handoff/2026-05-12-master.md` — full day roll-up
- PR #35 + #36 (merged)
- Council verdict on CW pivot: `/outputs/council/2026-05-12-18-37-24.html` (VPS)
