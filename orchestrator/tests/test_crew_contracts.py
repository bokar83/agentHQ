"""Tests for contract file parsing and guard() per-crew ceiling enforcement."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from autonomy_guard import AutonomyGuard, ContractNotSatisfiedError, KNOWN_CREWS


def _make_guard(tmp_path: Path, cap: float = 1.00) -> AutonomyGuard:
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    return AutonomyGuard(
        state_file=str(tmp_path / "state.json"),
        cap_usd=cap,
        contracts_dir=str(contracts_dir),
    )


def _write_contract(contracts_dir: Path, crew: str, signed: bool = True,
                    ceiling: float = 0.05, extra: str = "") -> None:
    lines = [
        f"# {crew} contract",
        "## C1: Output schema",
        "All writes documented.",
        "",
        extra,
        "",
    ]
    if ceiling is not None:
        lines.append(f"COST_CEILING_USD: {ceiling}")
    if signed:
        lines.append("SIGNED: boubacar 2026-04-26")
    (contracts_dir / f"{crew}.md").write_text("\n".join(lines))


@patch("autonomy_guard.AutonomyGuard._verify_seven_day_observation")
def test_valid_contract_allows_enable(_mock_c7, tmp_path):
    g = _make_guard(tmp_path)
    _write_contract(tmp_path / "contracts", "griot")
    g.set_crew_enabled("griot", True)  # must not raise
    assert g._state["crews"]["griot"]["enabled"] is True


@patch("autonomy_guard.AutonomyGuard._verify_seven_day_observation")
def test_unsigned_contract_raises(_mock_c7, tmp_path):
    g = _make_guard(tmp_path)
    _write_contract(tmp_path / "contracts", "griot", signed=False)
    with pytest.raises(ContractNotSatisfiedError, match="SIGNED"):
        g.set_crew_enabled("griot", True)


@patch("autonomy_guard.AutonomyGuard._verify_seven_day_observation")
def test_missing_ceiling_raises(_mock_c7, tmp_path):
    g = _make_guard(tmp_path)
    _write_contract(tmp_path / "contracts", "griot", ceiling=None)
    with pytest.raises(ContractNotSatisfiedError, match="COST_CEILING_USD"):
        g.set_crew_enabled("griot", True)


@patch("autonomy_guard.AutonomyGuard._verify_seven_day_observation")
def test_ceiling_persisted_to_state(_mock_c7, tmp_path):
    g = _make_guard(tmp_path)
    _write_contract(tmp_path / "contracts", "griot", ceiling=0.03)
    g.set_crew_enabled("griot", True)
    assert g._state["crews"]["griot"]["cost_ceiling_usd"] == pytest.approx(0.03)


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
@patch("autonomy_guard.AutonomyGuard._verify_seven_day_observation")
def test_guard_enforces_per_crew_ceiling(_mock_c7, _mock_spend, tmp_path):
    """guard() must block if estimated_usd exceeds crew cost_ceiling_usd."""
    g = _make_guard(tmp_path, cap=10.00)  # global cap is high
    _write_contract(tmp_path / "contracts", "griot", ceiling=0.02)
    g.set_crew_enabled("griot", True)
    g.set_crew_dry_run("griot", False)
    decision = g.guard("griot", estimated_usd=0.05)
    assert decision.allowed is False
    assert "ceiling" in decision.reason.lower()


@patch("autonomy_guard.AutonomyGuard._spent_today_usd", return_value=0.0)
@patch("autonomy_guard.AutonomyGuard._verify_seven_day_observation")
def test_guard_allows_under_per_crew_ceiling(_mock_c7, _mock_spend, tmp_path):
    g = _make_guard(tmp_path, cap=10.00)
    _write_contract(tmp_path / "contracts", "griot", ceiling=0.10)
    g.set_crew_enabled("griot", True)
    g.set_crew_dry_run("griot", False)
    decision = g.guard("griot", estimated_usd=0.02)
    assert decision.allowed is True
