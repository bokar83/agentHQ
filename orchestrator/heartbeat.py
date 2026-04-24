"""
heartbeat.py -- Phase 2 autonomy layer.

Time-based wake-on-schedule runner with a register_wake() API. Every wake
registers a zero-arg callback; the heartbeat loop fires each wake at its
scheduled time and calls the callback.

Phase 2 ships three default wakes that call a built-in _self_test_callback
which writes one task_outcomes row and returns. Phase 3+ registers real
crew callbacks alongside the defaults.

Design rules (enforced by tests):
  - Zero LLM spend from this module's code paths
  - DST-safe: wake_at times are localized via pytz explicitly
  - Kill-switch integration: self-test always runs; crew callbacks skip when killed
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Dict, List, Optional

import pytz

logger = logging.getLogger("agentsHQ.heartbeat")

TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")

# Self-test crew name. Reserved; callers cannot register non-self-test callbacks under this.
SELF_TEST_CREW = "heartbeat-self-test"


@dataclass
class WakeRegistration:
    name: str
    crew_name: str
    callback: Callable[[], None]
    at_hour: Optional[int] = None          # 0-23, for daily at= wakes
    at_minute: Optional[int] = None        # 0-59, for daily at= wakes
    every_seconds: Optional[int] = None    # for interval every= wakes
    last_fired_date: Optional[date] = None
    last_fired_epoch: Optional[float] = None


# Thread-safe registry. Process-wide singleton.
_wakes: Dict[str, WakeRegistration] = {}
_wakes_lock = threading.RLock()
_thread_started = False


def _parse_at(at: str) -> tuple:
    """Parse 'HH:MM' to (hour, minute). Raises ValueError on bad input."""
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", at.strip())
    if not m:
        raise ValueError(f"at= must be 'HH:MM', got {at!r}")
    h, mm = int(m.group(1)), int(m.group(2))
    if not (0 <= h <= 23 and 0 <= mm <= 59):
        raise ValueError(f"at= out of range: {at!r}")
    return h, mm


def _parse_every(every: str) -> int:
    """Parse '1h' / '30m' / '90s' to seconds. Minimum 60. Raises ValueError."""
    m = re.fullmatch(r"(\d+)\s*([smh])", every.strip().lower())
    if not m:
        raise ValueError(f"every= must be 'Nh'|'Nm'|'Ns', got {every!r}")
    n, unit = int(m.group(1)), m.group(2)
    seconds = {"s": n, "m": n * 60, "h": n * 3600}[unit]
    if seconds < 60:
        raise ValueError(f"every= must be >= 60 seconds, got {seconds}")
    return seconds


def register_wake(
    name: str,
    *,
    crew_name: str,
    callback: Callable[[], None],
    at: Optional[str] = None,
    every: Optional[str] = None,
) -> WakeRegistration:
    """Register a wake. Exactly one of at / every must be provided.

    - at: 'HH:MM' in TIMEZONE (America/Denver)
    - every: '1h' | '30m' | '2h' (minimum 60 seconds)

    The crew_name is used for kill-switch exemption (SELF_TEST_CREW always runs).
    Duplicate names raise ValueError.
    """
    if (at is None) == (every is None):
        raise ValueError("register_wake requires exactly one of at= or every=")
    with _wakes_lock:
        if name in _wakes:
            raise ValueError(f"wake already registered: {name}")
        reg = WakeRegistration(name=name, crew_name=crew_name, callback=callback)
        if at is not None:
            reg.at_hour, reg.at_minute = _parse_at(at)
        else:
            reg.every_seconds = _parse_every(every)
        _wakes[name] = reg
        logger.info(
            f"HEARTBEAT: registered wake {name} ({crew_name}) "
            f"at={at} every={every}"
        )
        return reg


def unregister_wake(name: str) -> None:
    with _wakes_lock:
        _wakes.pop(name, None)


def list_wakes() -> List[WakeRegistration]:
    with _wakes_lock:
        return list(_wakes.values())


def _should_fire(wake: WakeRegistration, now: datetime) -> bool:
    """Return True iff this wake is due at `now`.

    Daily (at=) wakes fire once per calendar date in TIMEZONE when the
    current local time is at or past HH:MM and we haven't already fired today.

    Interval (every=) wakes fire when elapsed since last fire >= every_seconds.
    First fire happens on the first poll after registration.
    """
    if wake.at_hour is not None:
        today_local = now.date()
        if wake.last_fired_date == today_local:
            return False
        return (
            now.hour > wake.at_hour
            or (now.hour == wake.at_hour and now.minute >= (wake.at_minute or 0))
        )
    if wake.every_seconds is None:
        return False
    if wake.last_fired_epoch is None:
        return True
    return (now.timestamp() - wake.last_fired_epoch) >= wake.every_seconds


def _update_last_fired(wake: WakeRegistration, now: datetime) -> None:
    with _wakes_lock:
        if wake.at_hour is not None:
            wake.last_fired_date = now.date()
        else:
            wake.last_fired_epoch = now.timestamp()


def _is_guard_killed() -> bool:
    """Lazy import; returns True (safe default) if autonomy_guard is unreachable."""
    try:
        from autonomy_guard import get_guard
        return get_guard().is_killed()
    except Exception as e:
        logger.warning(f"HEARTBEAT: autonomy_guard check failed ({e}); treating as killed for safety")
        return True


def _fire(wake: WakeRegistration, now: datetime) -> None:
    """Run the callback unless the guard is killed and this is not a self-test."""
    fire_id = str(uuid.uuid4())[:8]
    logger.info(f"HEARTBEAT: fire {fire_id} {wake.name} at {now.isoformat()}")

    is_self_test = wake.crew_name == SELF_TEST_CREW
    killed = _is_guard_killed()

    if killed and not is_self_test:
        logger.info(f"HEARTBEAT: {fire_id} skip (guard killed, crew={wake.crew_name})")
        _update_last_fired(wake, now)
        return

    try:
        wake.callback()
    except Exception as e:
        logger.error(f"HEARTBEAT: callback {wake.name} raised: {e}", exc_info=True)
    finally:
        _update_last_fired(wake, now)


def _self_test_callback() -> None:
    """Phase 2 built-in callback. Writes one observability row with zero LLM spend.

    Fails gracefully if episodic_memory is unreachable (container still proves
    the wake loop ran via the log line from _fire).
    """
    try:
        from episodic_memory import start_task, complete_task
        outcome = start_task(
            crew_name=SELF_TEST_CREW,
            plan_summary=f"Heartbeat self-test fire at {datetime.now(pytz.timezone(TIMEZONE)).isoformat()}",
        )
        complete_task(outcome.id, result_summary="self-test ok", total_cost_usd=0.0)
    except Exception as e:
        logger.warning(f"HEARTBEAT: self_test episodic_memory write failed: {e}")


def dry_run_next(wake_name: str) -> dict:
    """Return what /trigger_heartbeat would show. No side effects.

    Computes the next fire time based on cadence + last_fired state.
    """
    with _wakes_lock:
        wake = _wakes.get(wake_name)
    if wake is None:
        return {"error": f"unknown wake: {wake_name}"}

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    if wake.at_hour is not None:
        target_today = tz.localize(datetime(now.year, now.month, now.day,
                                             wake.at_hour, wake.at_minute or 0))
        if wake.last_fired_date == now.date() or target_today <= now:
            from datetime import timedelta
            tmr = now + timedelta(days=1)
            target = tz.localize(datetime(tmr.year, tmr.month, tmr.day,
                                           wake.at_hour, wake.at_minute or 0))
        else:
            target = target_today
    else:
        if wake.last_fired_epoch is None:
            target = now
        else:
            from datetime import timedelta
            target = now + timedelta(seconds=max(0, wake.every_seconds - (now.timestamp() - wake.last_fired_epoch)))

    guard_killed = _is_guard_killed()
    is_self_test = wake.crew_name == SELF_TEST_CREW
    would_allow = (not guard_killed) or is_self_test

    return {
        "name": wake.name,
        "crew_name": wake.crew_name,
        "next_fire_local": target.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "seconds_until_fire": max(0, int((target - now).total_seconds())),
        "guard_would_allow": would_allow,
        "guard_reason": None if would_allow else "guard killed (non-self-test crew)",
    }


def _heartbeat_loop() -> None:
    """Poll every 30s. For each wake, if _should_fire then _fire."""
    tz = pytz.timezone(TIMEZONE)
    logger.info(f"HEARTBEAT: thread started (tz={TIMEZONE})")
    while True:
        try:
            now = datetime.now(tz)
            with _wakes_lock:
                snapshot = list(_wakes.values())
            for wake in snapshot:
                if _should_fire(wake, now):
                    _fire(wake, now)
        except Exception as e:
            logger.error(f"HEARTBEAT: loop error: {e}", exc_info=True)
        time.sleep(30)


def _register_defaults() -> None:
    """Phase 2 ships three default wakes that run the self-test callback."""
    defaults = [
        ("heartbeat-morning", "07:00"),
        ("heartbeat-midday", "13:00"),
        ("heartbeat-evening", "19:00"),
    ]
    for name, at in defaults:
        if name not in _wakes:
            try:
                register_wake(
                    name=name,
                    crew_name=SELF_TEST_CREW,
                    at=at,
                    callback=_self_test_callback,
                )
            except Exception as e:
                logger.warning(f"HEARTBEAT: default {name} registration failed: {e}")


def start() -> None:
    """Start the heartbeat thread. Idempotent; called from scheduler.start_scheduler()."""
    global _thread_started
    with _wakes_lock:
        if _thread_started:
            return
        _register_defaults()
        t = threading.Thread(target=_heartbeat_loop, daemon=True, name="heartbeat")
        t.start()
        _thread_started = True
        logger.info(f"HEARTBEAT: start() complete; {len(_wakes)} wake(s) registered")
