# Phase 0: Autonomy Safety Rails

**Date:** 2026-04-23
**Owner:** Boubacar Barry
**Branch:** `feat/autonomy-safety-rails`
**Save point:** `savepoint-pre-autonomy-20260423`
**Status:** Draft (awaiting approval)

## Context

agentsHQ is moving from L0 (reactive tool, executes on command) to L1 (proposes work, queues for human approval). Before any crew runs on its own cadence, the system needs rails that prevent runaway spend, allow instant kill, and let each crew be turned on independently.

This is Phase 0 of a phased rollout:

| Phase | What it delivers | Branch |
|---|---|---|
| **0. Safety rails (this doc)** | Spend cap, kill switch, feature flags, ledger split | `feat/autonomy-safety-rails` |
| 1. Episodic memory + approval queue | Substrate for learning + human-in-the-loop | `feat/episodic-memory-and-queue` |
| 2. Smart heartbeat | Scheduler that wakes 3x/day + event-driven | `feat/heartbeat` |
| 3. Griot pilot | First autonomous crew (content) | `feat/griot-autonomous` |
| 4. Concierge (self-healing) | Error investigation, auto-fix proposals | `feat/concierge-autonomous` |
| 5. Chairman learning loop | Weekly review, prompt/skill mutation proposals | `feat/chairman-learning-loop` |
| 6. Hunter pilot | Leads + sales crew | `feat/hunter-autonomous` |

Phase 0 ships nothing autonomous on its own. It ships the guardrails that make everything after it safe.

## Goals

1. Hard cap on daily autonomous LLM spend. Hit the cap → system pauses itself, not Boubacar's wallet.
2. One-command kill switch via Telegram. No SSH, no deploy, no code change required.
3. Per-crew feature flags so crews can be enabled one at a time during rollout.
4. Dry-run mode per crew so each new crew can be observed for 48h before going live.
5. Token ledger split: autonomous spend tracked separately from user-initiated spend, so ROI is measurable.
6. No changes to existing behavior. Every rail is additive and off by default.

## Non-goals

- Autonomous task origination (Phase 2)
- Any crew acting on its own (Phase 3+)
- Learning loop or self-healing (Phase 4-5)
- Changes to router, crew assembly, Sankofa Council, or existing 6am Hunter cron
- A web dashboard (Telegram only for now)

## Parameters locked with owner

| Parameter | Value | Source |
|---|---|---|
| Daily autonomous spend cap | `$1.00 USD` | Owner decision 2026-04-23 |
| Morning digest time | `07:00 MT` | Owner decision 2026-04-23 |
| Autonomy level at launch | `L1 for all crews` (propose + queue, no external action without approval) | Owner decision 2026-04-23 |
| Pilot crew | Griot (content/marketing) first, 30 days minimum | Owner decision 2026-04-23 |
| Heartbeat cadence | 07:00 / 13:00 / 19:00 MT + event-triggered | Owner decision 2026-04-23 |

## Architecture

Phase 0 adds one new orchestrator module and extends one existing one. No changes to router, crews, agents, or Sankofa Council.

```
orchestrator/
├── autonomy_guard.py       ← NEW: spend cap + kill switch + feature flags
├── usage_logger.py         ← EXTEND: add autonomous=bool column
└── notifier.py             ← EXTEND: new Telegram command handlers (/pause_autonomy, /resume_autonomy, /spend)
```

### Component 1: `autonomy_guard.py` (new)

Single source of truth for autonomy state. Every autonomous LLM call goes through this module.

**Responsibilities:**
- Load autonomy state from env + a JSON state file on disk
- Provide `is_crew_enabled(crew_name) -> bool`
- Provide `is_dry_run(crew_name) -> bool`
- Provide `check_budget() -> (ok: bool, spent_today_usd: float, cap_usd: float)`
- Provide `is_killed() -> bool` (global kill switch)
- Provide `record_spend(usd: float)` (writes through to the ledger via usage_logger)
- Persist kill switch state to disk so it survives restarts

**Public API:**

```python
class AutonomyGuard:
    def guard(self, crew_name: str, estimated_usd: float = 0.0) -> GuardDecision:
        """Returns GuardDecision with .allowed (bool), .reason (str), .dry_run (bool)"""

    def kill(self, reason: str) -> None:
        """Activate kill switch. All subsequent guard() calls return allowed=False."""

    def unkill(self) -> None:
        """Deactivate kill switch."""

    def spend_today(self) -> SpendSnapshot:
        """Returns spend_usd, cap_usd, remaining_usd, per_crew_breakdown."""
```

**State file:** `data/autonomy_state.json` (gitignored)

```json
{
  "killed": false,
  "killed_at": null,
  "killed_reason": null,
  "crews": {
    "griot":     {"enabled": false, "dry_run": true},
    "hunter":    {"enabled": false, "dry_run": true},
    "concierge": {"enabled": false, "dry_run": true},
    "chairman":  {"enabled": false, "dry_run": true}
  }
}
```

Default state at launch: **all crews disabled, all in dry-run**. Pilot rollout flips Griot's flags after Phase 3 ships.

**Env vars (`.env`):**

```
AUTONOMY_ENABLED=true
AUTONOMY_DAILY_USD_CAP=1.00
AUTONOMY_STATE_FILE=data/autonomy_state.json
AUTONOMY_ALERT_THRESHOLDS=0.50,0.80,1.00
```

`AUTONOMY_ALERT_THRESHOLDS` fires Telegram alerts at 50%, 80%, and 100% of daily cap.

### Component 2: `usage_logger.py` extension

Today's ledger logs every LLM call with cost and task_type. Phase 0 adds:

- `autonomous BOOLEAN NOT NULL DEFAULT FALSE`: was this call initiated by the autonomy layer?
- `crew_name TEXT`: which autonomous crew made the call (nullable, only set when autonomous=true)

Migration lives in `orchestrator/migrations/` following the existing pattern (see [router_log migration](../../orchestrator/migrations/)).

**No breaking changes.** Existing ledger queries ignore the new columns; new queries can filter on them.

### Component 3: `notifier.py` extension

Four new Telegram commands routed in [handlers_chat.py](../../orchestrator/handlers_chat.py):

| Command | What it does |
|---|---|
| `/pause_autonomy` | Calls `AutonomyGuard.kill(reason="telegram command")`. All autonomous LLM calls blocked until resumed. Replies with confirmation. |
| `/resume_autonomy` | Calls `AutonomyGuard.unkill()`. Replies with confirmation + current state summary. |
| `/spend` | Replies with today's autonomous spend, cap, remaining, and per-crew breakdown. |
| `/autonomy_status` | Replies with full state: killed or live, enabled crews, dry-run crews, today's spend. |

These commands are **owner-only** (checked against `TELEGRAM_CHAT_ID` env var, following existing pattern in handlers_chat.py).

## Data flow

```
Autonomous crew wants to call LLM
        ↓
AutonomyGuard.guard(crew_name, estimated_usd)
        ↓
┌────────────────────────────────────┐
│ killed? → allowed=False, reason=kill│
│ crew not enabled? → allowed=False   │
│ cap exceeded? → allowed=False + pause│
│ dry_run? → allowed=True, dry_run=True│
│ else → allowed=True                 │
└────────────────────────────────────┘
        ↓
If allowed and not dry_run:
    - make LLM call
    - record_spend(actual_usd)
    - if cumulative spend crossed threshold:
        → Telegram alert
    - if cumulative spend reached cap:
        → auto-kill + Telegram alert
If dry_run:
    - log what would have been called
    - no LLM call
    - no spend
```

## Telegram digest at 07:00 MT

Phase 0 ships a minimal morning digest cron (this is not the smart heartbeat, that's Phase 2). For Phase 0 it just reports on:

- Autonomous spend yesterday (should be $0 until Griot pilot starts)
- Current autonomy state (killed or live, which crews are enabled)
- Any kill events in the last 24h

This proves the digest plumbing works before Phase 2 adds real content to it.

Implementation: extends existing [scheduler.py](../../orchestrator/scheduler.py), new `_morning_digest_thread()` alongside the existing hunter thread. Runs at 07:00 MT, sends via notifier.py.

## Testing

- Unit tests for `AutonomyGuard` covering: enabled crew, disabled crew, dry-run, cap exceeded, killed state, state persistence across restart
- Integration test: simulated autonomous call flows through guard + logger; verify ledger row has `autonomous=true`
- Manual test: `/pause_autonomy` from Telegram → verify subsequent guard calls return allowed=False
- Manual test: `/spend` returns formatted snapshot

Tests go in `orchestrator/tests/test_autonomy_guard.py`.

## Deployment

1. Create migration `orchestrator/migrations/004_autonomy_columns.sql` following the existing numbered pattern (001/002/003).
2. Deploy to VPS: `git push` → SSH → `docker compose up -d --build orc`
3. Apply migration the same way existing migrations are applied (psql against Supabase, matching how `003_router_log.sql` was applied).
4. Verify on Telegram: `/autonomy_status` should return "autonomy live, 0 crews enabled, $0.00/$1.00 spent today"
5. Verify kill switch: `/pause_autonomy` then `/autonomy_status` should show killed state; `/resume_autonomy` restores

## Rollback

If anything breaks:

```
git reset --hard savepoint-pre-autonomy-20260423
docker compose up -d --build orc
```

Migration is additive (nullable columns with defaults), so no migration rollback needed.

## Success criteria

- `/pause_autonomy` and `/resume_autonomy` work from Boubacar's phone within 10 seconds
- `/spend` returns accurate spend for the day
- Autonomy state survives `docker compose restart`
- No regression in existing flows (user tasks still work identically)
- Ledger shows `autonomous=false` for every user-initiated task and `autonomous=true` for any autonomous test call
- Morning digest arrives at 07:00 MT

## What ships AFTER Phase 0

Phase 1 will use the guard on every autonomous call. Phase 2 will use the digest plumbing for the smart heartbeat. Phase 3 onwards turns crews on one at a time via the feature flags built here.

Phase 0 is the floor. It doesn't deliver visible autonomy on its own. It makes autonomy safe to deliver.
