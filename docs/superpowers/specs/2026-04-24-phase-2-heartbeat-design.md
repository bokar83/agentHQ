# Phase 2: Heartbeat Scheduler

**Date:** 2026-04-24
**Owner:** Boubacar Barry
**Branch:** `feat/heartbeat`
**Save point tag:** `savepoint-pre-phase-2-20260424`
**Status:** Draft (Council-reviewed, 8 fixes applied, owner-approved)

## Context

Phase 0 shipped safety rails. Phase 1 shipped episodic memory + approval queue. Phase 2 ships the timing layer: a simple wake-on-schedule runner that lets crews register callbacks and fire them at specific times with full autonomy-guard integration.

Phase 2 is explicitly plumbing. **Zero LLM spend from Phase 2 code paths.** The only callback that runs in Phase 2 is a built-in self-test that writes a `task_outcomes` row and returns. Phase 3 is when Griot registers a real callback that produces real work.

| Phase | Status |
|---|---|
| 0. Safety rails | SHIPPED 2026-04-23 |
| 1. Episodic memory + approval queue | SHIPPED 2026-04-24 |
| **2. Heartbeat (this spec)** | DRAFT |
| 2.5. Event-triggered wakes (webhooks, Supabase realtime) | queued |
| 3. Griot pilot | queued |
| 4. Concierge (self-healing) | queued |
| 5. Chairman learning loop | queued |
| 6. Hunter pilot | queued |

## Goals

1. Provide a `register_wake(name, at=..., every=..., callback=fn)` API so crews can schedule themselves
2. Run three default daily wakes (07:00, 13:00, 19:00 MT) that call any registered callbacks
3. Integrate with autonomy_guard: if killed, crew callbacks skip; self-test still runs so we know the loop is alive
4. Integrate with episodic_memory: every fire writes one `task_outcomes` row for observability
5. Be DST-safe and idempotent (one fire per scheduled time per day, even across DST transitions)
6. Be smoke-testable without waiting for Phase 3

## Non-goals

- Any crew running real logic (Phase 3+)
- Event-triggered wakes / webhooks / Supabase realtime (Phase 2.5)
- Weekly cadence for Chairman (`at="Sun 19:00"`): Phase 5
- Dynamic re-registration from Telegram (Phase 3+)
- Any LLM call from Phase 2 code paths (explicitly forbidden)
- Per-crew cadence overrides via config file (Phase 3 when crews exist)

## Parameters locked with owner

| Parameter | Value | Source |
|---|---|---|
| Public API | `register_wake(name, at="HH:MM America/Denver", every="Nh", callback=fn)` | Council (Expansionist + First Principles), owner approval |
| Default wakes | 07:00, 13:00, 19:00 MT (registered at orc boot) | Owner design assumption |
| LLM spend | Zero from Phase 2 paths (tests enforce) | Council (Contrarian), owner approval |
| Manual trigger | `/trigger_heartbeat <wake>` is dry-run read-only | Council (Contrarian), owner approval |
| Kill-switch behavior | Self-test runs always; crew callbacks skip when killed | Council (Executor) |
| Timezone | `America/Denver` with explicit `pytz.localize()` | Council (Contrarian) |
| Event triggers | Phase 2.5, not Phase 2 | Owner 2026-04-24 |

## Council-surfaced fixes applied

1. DST-safe timezone-aware time arithmetic + explicit DST-boundary unit tests
2. Phase 2 fires zero LLM calls; spec + test enforce this
3. Built-in `heartbeat-self-test` callback so Phase 2 is testable without Phase 3
4. `register_wake` API accepts `at=` (daily time) and `every=` (interval)
5. `/trigger_heartbeat` is read-only dry-run in Phase 2
6. Kill-switch integration: self-test always runs, crew callbacks skip
7. "Smart" marketing label dropped; it's a `heartbeat` scheduler, no adjective
8. Weekly cadence deferred to Phase 5

## Architecture

One new module. One extension to `scheduler.py`. One or two new Telegram commands. No changes to Phase 0 or Phase 1 modules.

```
orchestrator/
├── heartbeat.py              NEW, ~200 lines
├── scheduler.py              EXTEND: call heartbeat.start() in start_scheduler()
├── orchestrator.py           EXTEND: /heartbeat_status + /trigger_heartbeat commands
└── tests/
    └── test_heartbeat.py     NEW, unit tests including DST boundary
```

Do NOT touch: `autonomy_guard.py`, `approval_queue.py`, `episodic_memory.py`, `notifier.py`, router, crews, council.

## `heartbeat.py` public API

```python
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WakeRegistration:
    name: str                        # unique wake name
    crew_name: str                   # 'griot', 'hunter', 'concierge', 'chairman', 'heartbeat-self-test'
    at: Optional[str]                # 'HH:MM' in TIMEZONE; mutually exclusive with every
    every_seconds: Optional[int]     # for interval-based wakes; mutually exclusive with at
    callback: Callable[[], None]     # fn to call on fire; takes no args, returns None
    last_fired_date: Optional[datetime]   # for daily wakes: last calendar date fired in TIMEZONE
    last_fired_epoch: Optional[float]     # for interval wakes: epoch seconds of last fire

def register_wake(name, *, crew_name, at=None, every=None, callback):
    """Register a wake. Exactly one of at / every must be provided.
    at: 'HH:MM' string interpreted in TIMEZONE (America/Denver).
    every: '1h' | '30m' | '2h' etc; minimum 60 seconds.
    callback: zero-arg callable that does the work.
    Raises ValueError on invalid shape or duplicate name.
    """

def unregister_wake(name): ...

def list_wakes() -> list[WakeRegistration]: ...

def start():
    """Start the heartbeat thread. Idempotent (safe to call twice).
    Called from scheduler.start_scheduler()."""

def dry_run_next(wake_name: str) -> dict:
    """Return what /trigger_heartbeat would show. No side effects.
    {
        'name': str,
        'crew_name': str,
        'next_fire_local': str,
        'seconds_until_fire': int,
        'guard_would_allow': bool,
        'guard_reason': str | None,
    }
    """

def _self_test_callback():
    """Built-in. Writes one task_outcomes row with crew_name='heartbeat-self-test',
    plan_summary='wake: <wake_name>', total_cost_usd=0. Zero LLM calls."""
```

### Default wakes registered at boot

```python
# Called from heartbeat.start(), runs once
register_wake(
    name="heartbeat-morning",
    crew_name="heartbeat-self-test",
    at="07:00",
    callback=_self_test_callback,
)
register_wake(
    name="heartbeat-midday",
    crew_name="heartbeat-self-test",
    at="13:00",
    callback=_self_test_callback,
)
register_wake(
    name="heartbeat-evening",
    crew_name="heartbeat-self-test",
    at="19:00",
    callback=_self_test_callback,
)
```

Phase 3 will add crew-specific wakes alongside these defaults; they remain as the system's heartbeat baseline (prove-it's-alive signal).

## Run loop

Single daemon thread. Polls every 30 seconds.

```python
def _heartbeat_loop():
    tz = pytz.timezone(TIMEZONE)
    while True:
        try:
            now = datetime.now(tz)
            for w in list(_wakes.values()):
                if _should_fire(w, now):
                    _fire(w, now)
        except Exception as e:
            logger.error(f"HEARTBEAT: loop error: {e}", exc_info=True)
        time.sleep(30)
```

### `_should_fire(wake, now)` logic

- For `at=` wakes: returns True iff `now.hour == parsed_hour` AND `now.minute >= parsed_minute` AND `last_fired_date != now.date()`. Self-debouncing; any sample in the target-hour window fires once per day.
- For `every=` wakes: returns True iff `now.timestamp() - last_fired_epoch >= every_seconds`.

### `_fire(wake, now)` logic

```python
def _fire(wake, now):
    # Record fire intent before callback (so we know even if callback crashes)
    fire_id = str(uuid.uuid4())
    logger.info(f"HEARTBEAT: fire {fire_id} {wake.name} at {now.isoformat()}")

    # Kill-switch integration
    from autonomy_guard import get_guard
    killed = get_guard().is_killed()

    # Self-test always runs (even when killed) so we know the loop is alive
    is_self_test = wake.crew_name == "heartbeat-self-test"

    if killed and not is_self_test:
        logger.info(f"HEARTBEAT: skipping {wake.name} (guard killed)")
        _update_last_fired(wake, now)
        return

    try:
        wake.callback()
    except Exception as e:
        logger.error(f"HEARTBEAT: callback {wake.name} raised: {e}", exc_info=True)

    _update_last_fired(wake, now)
```

`_update_last_fired` writes `last_fired_date = now.date()` for daily wakes or `last_fired_epoch = now.timestamp()` for interval wakes. This is in-memory only in Phase 2 (restart re-fires today's wake at most once more, which is acceptable since self-test is idempotent).

## `_self_test_callback` implementation

```python
def _self_test_callback():
    """Phase 2 built-in callback. Writes one observability row. Zero LLM calls."""
    from episodic_memory import start_task, complete_task
    outcome = start_task(
        crew_name="heartbeat-self-test",
        plan_summary=f"Heartbeat self-test fire at {datetime.now().isoformat()}",
    )
    complete_task(outcome.id, result_summary="self-test ok", total_cost_usd=0.0)
```

This gives us a forever-growing ledger of heartbeat fires. Queryable via `/outcomes heartbeat-self-test` to prove the loop is alive.

## Telegram commands

Added to the Phase 0/1 command block in `orchestrator.py`:

- `/heartbeat_status`: shows registered wakes, next fire time for each, kill state, last-fire timestamps. Read-only.
- `/trigger_heartbeat <wake_name>`: **dry-run only in Phase 2.** Returns `dry_run_next(wake_name)` formatted as Telegram text. No actual fire. Example output:
  ```
  Wake: heartbeat-morning
  Crew: heartbeat-self-test
  Next fire: 07:00 America/Denver (in 4h 23m)
  Guard: allow (self-test exempt from kill)
  ```

## Data flow (heartbeat fire)

```
30s poll tick in _heartbeat_loop
    |
    v
for each registered wake:
    _should_fire(wake, now)?
        |
        v
    yes:  _fire(wake, now)
              |
              +--> autonomy_guard.is_killed()?
              |       yes + not self-test  -> skip (log only)
              |       no, or self-test     -> proceed
              |
              +--> wake.callback()
              |       self-test: episodic_memory.start_task + complete_task
              |       Phase 3+: crew-specific logic that may call approval_queue.enqueue
              |
              +--> _update_last_fired(wake, now)
```

## Error handling

| Failure | Behavior |
|---|---|
| Callback raises an exception | Logged at ERROR with full traceback; `last_fired` still updated so we don't retry-loop; other wakes proceed |
| `_should_fire` raises (e.g., parse error on cadence string) | Logged at ERROR; wake skipped this tick; next tick re-tries |
| Heartbeat thread crashes | Outermost `while True` catches `Exception`; 30s sleep and resume |
| autonomy_guard import fails | Logged at ERROR; wake treated as killed (skip crew callbacks) but self-test still runs |
| episodic_memory.start_task fails (DB down) | Self-test callback logs warning; no row written; next fire tries again |
| DST spring-forward (07:00 doesn't exist) | `pytz.localize(..., is_dst=None)` raises `NonExistentTimeError`; we catch it and fire at the first valid time after (08:00) |
| DST fall-back (07:00 exists twice) | `is_dst=False` (pick the second occurrence so we fire once); documented in test |

## Testing plan

**Unit tests** (`orchestrator/tests/test_heartbeat.py`):

1. `register_wake` happy path (at=, every=, duplicate-name rejection, invalid-cadence rejection)
2. `_should_fire` for daily wake: fires inside the target hour when `last_fired_date != today`, skips when already fired today
3. `_should_fire` for interval wake: fires when elapsed >= every_seconds, skips otherwise
4. `_fire` calls the callback when allowed; catches callback exceptions; still updates last_fired
5. `_fire` skips crew callback when `autonomy_guard.is_killed()`; still runs self-test
6. `_self_test_callback` writes a `task_outcomes` row with cost=0 and no LLM call (mock the model)
7. `dry_run_next` returns correct "seconds_until_fire" for a wake registered today
8. **DST spring-forward**: wake registered at "02:30 America/Denver" on 2026-03-08 (spring-forward day); `_should_fire` handles the non-existent hour by falling through to the next valid time
9. **DST fall-back**: wake registered at "01:30 America/Denver" on 2026-11-01 (fall-back day); fires exactly once despite 01:30 existing twice
10. **Zero-LLM invariant**: patch `usage_logger.log_call` and `litellm.completion` to raise; fire a self-test; assert it succeeds (proves no LLM path touched)

**Integration test** (extend `tmp/test_phase1_e2e.py` or add `tmp/test_phase2_e2e.py`):

- Register a daily wake "at 12:34" (five minutes from now in fake time)
- Advance fake time to 12:35
- Assert callback fired, `last_fired_date` updated, `task_outcomes` row appeared

**Regression:** 49/49 existing tests must still pass.

**Live sanity on VPS after deploy:**

- `docker logs orc-crewai | grep HEARTBEAT` shows three registration lines at boot + the `HEARTBEAT: thread started` line
- `/heartbeat_status` from Telegram returns the three default wakes
- `/trigger_heartbeat heartbeat-morning` returns the dry-run output
- Wait until 13:00 MT (or whichever wake is next); verify a new `heartbeat-self-test` row in `task_outcomes` and a `HEARTBEAT: fire ...` log line
- `autonomy_guard /pause_autonomy` then wait for next wake; self-test still writes a row; no crew callbacks (there are none in Phase 2 anyway) fire

## Deploy plan

Same flow as Phase 0/1:

1. Save point `savepoint-pre-phase-2-20260424` (done)
2. Branch `feat/heartbeat` (done)
3. Merge to main after local tests + E2E pass
4. VPS pull main
5. No migration (Phase 2 uses Phase 1's tables unchanged)
6. `docker compose up -d --build orchestrator`
7. Tail logs for `HEARTBEAT: thread started` + 3 registration lines
8. `/heartbeat_status` from Telegram
9. Save-point tag `savepoint-phase-2-shipped-20260424`
10. Memory update: `project_autonomy_layer.md` status row for Phase 2 = SHIPPED

## Rollback

```
git reset --hard savepoint-pre-phase-2-20260424
docker compose up -d --build orchestrator
```

No migration to reverse. No state file to clean up (heartbeat state is in-memory).

## Success criteria

- `/heartbeat_status` returns the three default wakes with future next-fire times
- At least one `heartbeat-self-test` row appears in `task_outcomes` within 24 hours of deploy
- Container logs show `HEARTBEAT: thread started` and `HEARTBEAT: fire <id>` lines on each scheduled time
- Unit suite green (49 existing + ~10 new = ~59 tests)
- Zero-LLM invariant test passes (proves no model call in Phase 2 paths)
- DST boundary tests pass
- No regressions in Phase 0 or Phase 1 Telegram commands

## What ships AFTER Phase 2

Phase 2.5 adds event-triggered wakes: `register_event_wake(event_name, callback)` + webhook/Supabase-realtime wiring. Phase 3 registers Griot's first real callbacks. Phase 4 registers Concierge. Phase 5 adds the weekly Chairman cadence.

Phase 2 ships the timing bus. Phase 3 puts cargo on it.
