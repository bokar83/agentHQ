"""Unit tests for autonomy_guard. DB spend reads are mocked."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from autonomy_guard import AutonomyGuard, KNOWN_CREWS


def _make_guard(tmp_path: Path, cap: float = 1.00) -> AutonomyGuard:
    state_file = tmp_path / "autonomy_state.json"
    return AutonomyGuard(state_file=str(state_file), cap_usd=cap)


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_default_state_blocks_all_crews(_m, tmp_path: Path):
    g = _make_guard(tmp_path)
    for crew in KNOWN_CREWS:
        d = g.guard(crew)
        assert d.allowed is False
        assert d.decision_tag == "blocked-disabled"


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_enabled_crew_with_dry_run_allows_and_flags_dry_run(_m, tmp_path: Path):
    g = _make_guard(tmp_path)
    g.set_crew_enabled("griot", True)
    d = g.guard("griot")
    assert d.allowed is True
    assert d.dry_run is True
    assert d.decision_tag == "dry-run"


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_enabled_live_crew_allows_and_not_dry_run(_m, tmp_path: Path):
    g = _make_guard(tmp_path)
    g.set_crew_enabled("griot", True)
    g.set_crew_dry_run("griot", False)
    d = g.guard("griot")
    assert d.allowed is True
    assert d.dry_run is False
    assert d.decision_tag == "allowed"


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.95)
def test_near_cap_with_small_estimate_still_allowed(_m, tmp_path: Path):
    g = _make_guard(tmp_path, cap=1.00)
    g.set_crew_enabled("griot", True)
    d = g.guard("griot", estimated_usd=0.01)
    assert d.allowed is True


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.99)
def test_cap_exceeded_blocks_and_auto_kills(_m, tmp_path: Path):
    g = _make_guard(tmp_path, cap=1.00)
    g.set_crew_enabled("griot", True)
    d = g.guard("griot", estimated_usd=0.05)
    assert d.allowed is False
    assert d.decision_tag == "blocked-cap"
    assert g.is_killed() is True


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_kill_blocks_all_crews(_m, tmp_path: Path):
    g = _make_guard(tmp_path)
    g.set_crew_enabled("griot", True)
    g.kill("manual test")
    d = g.guard("griot")
    assert d.allowed is False
    assert d.decision_tag == "blocked-killed"


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_unkill_restores(_m, tmp_path: Path):
    g = _make_guard(tmp_path)
    g.set_crew_enabled("griot", True)
    g.kill("test")
    g.unkill()
    d = g.guard("griot")
    assert d.allowed is True


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_unknown_crew_blocked(_m, tmp_path: Path):
    g = _make_guard(tmp_path)
    d = g.guard("nonexistent_crew")
    assert d.allowed is False
    assert d.decision_tag == "blocked-unknown-crew"


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_state_persists_across_instances(_m, tmp_path: Path):
    state_file = tmp_path / "autonomy_state.json"
    g1 = AutonomyGuard(state_file=str(state_file), cap_usd=1.00)
    g1.set_crew_enabled("griot", True)
    g1.kill("persist test")

    g2 = AutonomyGuard(state_file=str(state_file), cap_usd=1.00)
    assert g2.is_killed() is True
    summary = g2.state_summary()
    assert summary["crews"]["griot"]["enabled"] is True


def test_set_crew_enabled_rejects_unknown_crew(tmp_path: Path):
    g = _make_guard(tmp_path)
    with pytest.raises(ValueError):
        g.set_crew_enabled("not_a_real_crew", True)


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
@patch("autonomy_guard.AutonomyGuard._per_crew_spend_today", return_value={})
def test_snapshot_returns_remaining(_mpc, _ms, tmp_path: Path):
    g = _make_guard(tmp_path, cap=1.00)
    snap = g.snapshot()
    assert snap.spent_today_usd == 0.0
    assert snap.cap_usd == 1.00
    assert snap.remaining_usd == 1.00


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=1.50)
@patch("autonomy_guard.AutonomyGuard._per_crew_spend_today", return_value={"griot": 1.50})
def test_snapshot_remaining_floored_at_zero(_mpc, _ms, tmp_path: Path):
    g = _make_guard(tmp_path, cap=1.00)
    snap = g.snapshot()
    assert snap.remaining_usd == 0.0


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_partial_state_missing_crews_key_falls_back_to_defaults(_m, tmp_path: Path):
    """If the state file is partially written (missing 'crews'), guard() must not crash."""
    import json
    sf = tmp_path / "state.json"
    sf.write_text(json.dumps({"killed": False}))
    g = AutonomyGuard(state_file=str(sf), cap_usd=1.0)
    d = g.guard("griot")
    assert d.allowed is False
    assert d.decision_tag == "blocked-disabled"


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_partial_state_missing_one_crew_reads_other_crews(_m, tmp_path: Path):
    """If 'crews' dict is partial (missing griot), other crews still read correctly."""
    import json
    sf = tmp_path / "state.json"
    sf.write_text(json.dumps({
        "killed": False,
        "crews": {"hunter": {"enabled": True, "dry_run": False}},
    }))
    g = AutonomyGuard(state_file=str(sf), cap_usd=1.0)
    d_griot = g.guard("griot")
    assert d_griot.allowed is False
    d_hunter = g.guard("hunter")
    assert d_hunter.allowed is True
    assert d_hunter.dry_run is False


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
def test_garbage_state_file_falls_back_to_defaults(_m, tmp_path: Path):
    """Non-dict / garbage shape must not crash guard()."""
    sf = tmp_path / "state.json"
    sf.write_text('["not", "a", "dict"]')
    g = AutonomyGuard(state_file=str(sf), cap_usd=1.0)
    d = g.guard("griot")
    assert d.allowed is False
    assert d.decision_tag == "blocked-disabled"
