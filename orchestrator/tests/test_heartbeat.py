"""Unit tests for heartbeat (Phase 2)."""
from __future__ import annotations

import os
import sys
from datetime import date, datetime
from unittest.mock import patch, MagicMock

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

import pytest
import pytz

import heartbeat as hb

TZ = pytz.timezone("America/Denver")


def _dt(y, m, d, h, mi, s=0):
    return TZ.localize(datetime(y, m, d, h, mi, s))


def _noop():
    pass


def setup_function(_fn):
    """Reset registry before each test."""
    with hb._wakes_lock:
        hb._wakes.clear()
    hb._thread_started = False


# ---------- cadence parsers ----------

def test_parse_at_valid():
    assert hb._parse_at("07:00") == (7, 0)
    assert hb._parse_at("23:59") == (23, 59)
    assert hb._parse_at("00:00") == (0, 0)


def test_parse_at_rejects_bad_shape():
    for bad in ("7am", "07-00", ""):
        with pytest.raises(ValueError):
            hb._parse_at(bad)


def test_parse_at_rejects_out_of_range():
    for bad in ("24:00", "07:60"):
        with pytest.raises(ValueError):
            hb._parse_at(bad)


def test_parse_every_units():
    assert hb._parse_every("1h") == 3600
    assert hb._parse_every("30m") == 1800
    assert hb._parse_every("120s") == 120


def test_parse_every_minimum_60s():
    with pytest.raises(ValueError):
        hb._parse_every("30s")


def test_parse_every_rejects_bad_shape():
    for bad in ("1 hour", "h1"):
        with pytest.raises(ValueError):
            hb._parse_every(bad)


# ---------- register_wake ----------

def test_register_wake_at_happy():
    reg = hb.register_wake("w1", crew_name="griot", at="07:00", callback=_noop)
    assert reg.at_hour == 7 and reg.at_minute == 0
    assert reg.every_seconds is None


def test_register_wake_every_happy():
    reg = hb.register_wake("w2", crew_name="concierge", every="2h", callback=_noop)
    assert reg.every_seconds == 7200
    assert reg.at_hour is None


def test_register_wake_requires_exactly_one_cadence():
    with pytest.raises(ValueError):
        hb.register_wake("w3", crew_name="x", callback=_noop)
    with pytest.raises(ValueError):
        hb.register_wake("w4", crew_name="x", at="07:00", every="1h", callback=_noop)


def test_register_wake_duplicate_raises():
    hb.register_wake("dup", crew_name="x", at="07:00", callback=_noop)
    with pytest.raises(ValueError):
        hb.register_wake("dup", crew_name="x", at="08:00", callback=_noop)


def test_list_wakes_returns_all():
    hb.register_wake("a", crew_name="x", at="07:00", callback=_noop)
    hb.register_wake("b", crew_name="x", every="1h", callback=_noop)
    names = {w.name for w in hb.list_wakes()}
    assert names == {"a", "b"}


def test_unregister_wake_idempotent():
    hb.register_wake("gone", crew_name="x", at="07:00", callback=_noop)
    hb.unregister_wake("gone")
    assert "gone" not in hb._wakes
    hb.unregister_wake("gone")  # no raise on second call


# ---------- _should_fire ----------

def test_should_fire_daily_before_window():
    reg = hb.register_wake("d1", crew_name="x", at="07:00", callback=_noop)
    assert hb._should_fire(reg, _dt(2026, 4, 24, 6, 59)) is False


def test_should_fire_daily_at_window():
    reg = hb.register_wake("d2", crew_name="x", at="07:00", callback=_noop)
    assert hb._should_fire(reg, _dt(2026, 4, 24, 7, 0)) is True


def test_should_fire_daily_after_window_but_not_yet_fired():
    reg = hb.register_wake("d3", crew_name="x", at="07:00", callback=_noop)
    assert hb._should_fire(reg, _dt(2026, 4, 24, 7, 30)) is True


def test_should_fire_daily_already_fired_today():
    reg = hb.register_wake("d4", crew_name="x", at="07:00", callback=_noop)
    reg.last_fired_date = date(2026, 4, 24)
    assert hb._should_fire(reg, _dt(2026, 4, 24, 8, 0)) is False


def test_should_fire_daily_fires_again_next_day():
    reg = hb.register_wake("d5", crew_name="x", at="07:00", callback=_noop)
    reg.last_fired_date = date(2026, 4, 24)
    assert hb._should_fire(reg, _dt(2026, 4, 25, 7, 0)) is True


def test_should_fire_interval_first_ever():
    reg = hb.register_wake("i1", crew_name="x", every="2h", callback=_noop)
    assert hb._should_fire(reg, _dt(2026, 4, 24, 7, 0)) is True


def test_should_fire_interval_too_soon():
    reg = hb.register_wake("i2", crew_name="x", every="2h", callback=_noop)
    now = _dt(2026, 4, 24, 7, 0)
    reg.last_fired_epoch = now.timestamp() - 3599
    assert hb._should_fire(reg, now) is False


def test_should_fire_interval_elapsed():
    reg = hb.register_wake("i3", crew_name="x", every="2h", callback=_noop)
    now = _dt(2026, 4, 24, 7, 0)
    reg.last_fired_epoch = now.timestamp() - 7200
    assert hb._should_fire(reg, now) is True


# ---------- _fire ----------

def test_fire_calls_callback_when_allowed():
    called = []
    reg = hb.register_wake("f1", crew_name="griot", at="07:00",
                           callback=lambda: called.append(1))
    with patch.object(hb, "_is_guard_killed", return_value=False):
        hb._fire(reg, _dt(2026, 4, 24, 7, 0))
    assert called == [1]
    assert reg.last_fired_date == date(2026, 4, 24)


def test_fire_skips_crew_callback_when_killed():
    called = []
    reg = hb.register_wake("f2", crew_name="griot", at="07:00",
                           callback=lambda: called.append(1))
    with patch.object(hb, "_is_guard_killed", return_value=True):
        hb._fire(reg, _dt(2026, 4, 24, 7, 0))
    assert called == []
    # last_fired still updates so we don't busy-loop retrying
    assert reg.last_fired_date == date(2026, 4, 24)


def test_fire_runs_self_test_even_when_killed():
    called = []
    reg = hb.register_wake("st", crew_name=hb.SELF_TEST_CREW, at="07:00",
                           callback=lambda: called.append(1))
    with patch.object(hb, "_is_guard_killed", return_value=True):
        hb._fire(reg, _dt(2026, 4, 24, 7, 0))
    assert called == [1]


def test_fire_catches_callback_exception():
    def boom():
        raise RuntimeError("planned failure")
    reg = hb.register_wake("f3", crew_name="griot", at="07:00", callback=boom)
    with patch.object(hb, "_is_guard_killed", return_value=False):
        hb._fire(reg, _dt(2026, 4, 24, 7, 0))
    assert reg.last_fired_date == date(2026, 4, 24)


# ---------- DST boundary ----------

def test_dst_spring_forward_fires_after_skipped_hour():
    """2026-03-08 US spring-forward (02:00 -> 03:00).
    A wake registered at 02:30 should still fire at 03:00 of the new wall time
    since the calendar day has not yet fired.
    """
    reg = hb.register_wake("dst_sf", crew_name="x", at="02:30", callback=_noop)
    assert hb._should_fire(reg, _dt(2026, 3, 8, 3, 0)) is True


def test_dst_fall_back_fires_once():
    """2026-11-01 US fall-back (02:00 -> 01:00); 01:30 exists twice.
    last_fired_date prevents a second fire on the same calendar date.
    """
    reg = hb.register_wake("dst_fb", crew_name="x", at="01:30", callback=_noop)
    first_pass = _dt(2026, 11, 1, 1, 30)
    assert hb._should_fire(reg, first_pass) is True
    reg.last_fired_date = first_pass.date()
    second_pass = _dt(2026, 11, 1, 2, 30)
    assert hb._should_fire(reg, second_pass) is False


def test_dst_fall_back_fires_next_day():
    reg = hb.register_wake("dst_fb2", crew_name="x", at="01:30", callback=_noop)
    reg.last_fired_date = date(2026, 11, 1)
    assert hb._should_fire(reg, _dt(2026, 11, 2, 1, 30)) is True


# ---------- Zero-LLM invariant ----------

def test_self_test_callback_writes_zero_cost_row():
    """_self_test_callback must not touch any LLM client. We block litellm
    imports during the call and assert it still succeeds.
    """
    fake_ep = MagicMock()
    fake_ep.start_task.return_value = MagicMock(id=42)
    fake_ep.complete_task.return_value = None

    saved_ep = sys.modules.get("episodic_memory")
    sys.modules["episodic_memory"] = fake_ep

    import builtins
    original_import = builtins.__import__

    def _no_llm_import(name, *a, **k):
        if name == "litellm":
            raise ImportError("litellm must not be imported from heartbeat")
        return original_import(name, *a, **k)

    builtins.__import__ = _no_llm_import
    try:
        hb._self_test_callback()
    finally:
        builtins.__import__ = original_import
        if saved_ep is not None:
            sys.modules["episodic_memory"] = saved_ep
        else:
            sys.modules.pop("episodic_memory", None)

    assert fake_ep.start_task.called
    assert fake_ep.complete_task.called
    cost_arg = fake_ep.complete_task.call_args.kwargs.get("total_cost_usd")
    assert cost_arg == 0.0


# ---------- dry_run_next ----------

def test_dry_run_next_unknown_wake():
    assert "error" in hb.dry_run_next("ghost")


def test_dry_run_next_returns_future_time_for_daily_wake():
    hb.register_wake("dn1", crew_name=hb.SELF_TEST_CREW, at="07:00", callback=_noop)
    with patch.object(hb, "_is_guard_killed", return_value=False):
        result = hb.dry_run_next("dn1")
    assert result["name"] == "dn1"
    assert result["crew_name"] == hb.SELF_TEST_CREW
    assert result["seconds_until_fire"] >= 0
    assert result["guard_would_allow"] is True


def test_dry_run_next_interval_first_fire_is_immediate():
    hb.register_wake("dn2", crew_name="griot", every="1h", callback=_noop)
    with patch.object(hb, "_is_guard_killed", return_value=False):
        result = hb.dry_run_next("dn2")
    assert result["seconds_until_fire"] == 0


def test_dry_run_next_self_test_allowed_even_when_killed():
    hb.register_wake("dn3", crew_name=hb.SELF_TEST_CREW, at="07:00", callback=_noop)
    with patch.object(hb, "_is_guard_killed", return_value=True):
        result = hb.dry_run_next("dn3")
    assert result["guard_would_allow"] is True


def test_dry_run_next_crew_blocked_when_killed():
    hb.register_wake("dn4", crew_name="griot", at="07:00", callback=_noop)
    with patch.object(hb, "_is_guard_killed", return_value=True):
        result = hb.dry_run_next("dn4")
    assert result["guard_would_allow"] is False
    assert "killed" in result["guard_reason"]


# ---------- start() + defaults ----------

def test_start_registers_default_wakes():
    # Prevent the real thread from starting during tests
    with patch.object(hb, "threading") as _tm:
        _tm.Thread = MagicMock()
        _tm.RLock = threading_RLock = hb.threading.RLock  # keep the real lock
        hb.start()
    names = {w.name for w in hb.list_wakes()}
    assert {"heartbeat-morning", "heartbeat-midday", "heartbeat-evening"} <= names
    for n in ("heartbeat-morning", "heartbeat-midday", "heartbeat-evening"):
        assert hb._wakes[n].crew_name == hb.SELF_TEST_CREW


def test_start_idempotent():
    with patch.object(hb, "threading") as _tm:
        _tm.Thread = MagicMock()
        hb.start()
        first_count = len(hb._wakes)
        hb.start()
    assert len(hb._wakes) == first_count


def test_start_sets_thread_started_flag():
    assert hb._thread_started is False
    with patch.object(hb, "threading") as _tm:
        _tm.Thread = MagicMock()
        hb.start()
    assert hb._thread_started is True
