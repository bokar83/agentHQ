"""
autonomy_guard.py -- Safety rails for autonomous crews.

Single source of truth for:
  - Daily autonomous LLM spend cap
  - Global kill switch (Telegram-driven)
  - Per-crew feature flags (off by default)
  - Per-crew dry-run mode (on by default)

Every autonomous LLM call MUST pass through guard() before the LLM is called.
User-initiated calls (from /run, Telegram chat, etc.) bypass this module.

State persists to data/autonomy_state.json so kill switch survives restarts.
Spend is read from the llm_calls ledger in real time (no duplicate counting).
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agentsHQ.autonomy_guard")


class ContractNotSatisfiedError(Exception):
    """Raised when set_crew_enabled(True) or set_crew_dry_run(False) is called
    without a valid signed contract file for the crew."""
    pass


DEFAULT_CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "contracts")

KNOWN_CREWS = ("griot", "hunter", "concierge", "chairman", "auto_publisher", "studio", "video_crew", "model_review_agent")

DEFAULT_STATE_FILE = os.environ.get(
    "AUTONOMY_STATE_FILE",
    "data/autonomy_state.json",
)

DEFAULT_CAP_USD = float(os.environ.get("AUTONOMY_DAILY_USD_CAP", "1.00"))


@dataclass
class GuardDecision:
    allowed: bool
    dry_run: bool
    reason: str
    decision_tag: str  # allowed | dry-run | blocked-killed | blocked-disabled | blocked-cap | blocked-unknown-crew
    spent_today_usd: float
    cap_usd: float


@dataclass
class SpendSnapshot:
    spent_today_usd: float
    cap_usd: float
    remaining_usd: float
    per_crew: dict  # {crew_name: usd}


class AutonomyGuard:
    """Thread-safe. One instance per process."""

    def __init__(
        self,
        state_file: str = DEFAULT_STATE_FILE,
        cap_usd: float = DEFAULT_CAP_USD,
        contracts_dir: str = DEFAULT_CONTRACTS_DIR,
    ):
        self._state_file = Path(state_file)
        self._cap_usd = cap_usd
        self._contracts_dir = Path(contracts_dir)
        self._lock = threading.RLock()
        self._state = self._load_state()

    # State persistence

    def _default_state(self) -> dict:
        return {
            "killed": False,
            "killed_at": None,
            "killed_reason": None,
            "crews": {
                c: {"enabled": False, "dry_run": True, "cost_ceiling_usd": None}
                for c in KNOWN_CREWS
            },
        }

    def _load_state(self) -> dict:
        try:
            if not self._state_file.exists():
                self._state_file.parent.mkdir(parents=True, exist_ok=True)
                state = self._default_state()
                self._state_file.write_text(json.dumps(state, indent=2))
                return state
            loaded = json.loads(self._state_file.read_text())
            return self._repair_state(loaded)
        except Exception as e:
            logger.warning(f"autonomy_guard: failed to load state, using defaults: {e}")
            return self._default_state()

    def _repair_state(self, loaded: dict) -> dict:
        """Merge a loaded (possibly partial) state file into the full default shape.

        Protects against partial writes (power cut mid-persist) or manual edits that
        drop a key. Missing fields fall back to safe defaults (killed=False, all
        crews off + dry-run).
        """
        base = self._default_state()
        if not isinstance(loaded, dict):
            return base
        base["killed"] = bool(loaded.get("killed", False))
        base["killed_at"] = loaded.get("killed_at")
        base["killed_reason"] = loaded.get("killed_reason")
        crews = loaded.get("crews")
        if isinstance(crews, dict):
            for crew_name, defaults in base["crews"].items():
                existing = crews.get(crew_name)
                if isinstance(existing, dict):
                    defaults["enabled"] = bool(existing.get("enabled", False))
                    defaults["dry_run"] = bool(existing.get("dry_run", True))
                    defaults["cost_ceiling_usd"] = existing.get("cost_ceiling_usd", None)
        return base

    def _assert_contract_satisfied(self, crew_name: str) -> None:
        """Raises ContractNotSatisfiedError if the crew has no valid signed contract.

        Checks:
          1. Contract file exists at contracts/<crew_name>.md
          2. File contains a SIGNED: line with a non-empty value
          3. COST_CEILING_USD line present and parseable as float
          4. C7: llm_calls queried for this crew over past 7 days (non-fatal if DB unreachable)
        """
        contract_path = self._contracts_dir / f"{crew_name}.md"
        if not contract_path.exists():
            raise ContractNotSatisfiedError(
                f"{crew_name}: contract file missing at {contract_path}. "
                f"Create and sign orchestrator/contracts/{crew_name}.md before enabling."
            )

        content = contract_path.read_text()

        signed_line = next(
            (line for line in content.splitlines() if line.startswith("SIGNED:")), None
        )
        if not signed_line or len(signed_line.split(":", 1)[-1].strip()) < 5:
            raise ContractNotSatisfiedError(
                f"{crew_name}: contract file exists but has no valid SIGNED: line. "
                f"Fill in: SIGNED: <approver> <YYYY-MM-DD>"
            )

        ceiling_line = next(
            (line for line in content.splitlines() if line.startswith("COST_CEILING_USD:")), None
        )
        if not ceiling_line:
            raise ContractNotSatisfiedError(
                f"{crew_name}: contract file missing COST_CEILING_USD: line."
            )
        try:
            ceiling = float(ceiling_line.split(":", 1)[-1].strip())
        except ValueError:
            raise ContractNotSatisfiedError(
                f"{crew_name}: COST_CEILING_USD must be a float (e.g. COST_CEILING_USD: 0.05)."
            )

        self._state["crews"][crew_name]["cost_ceiling_usd"] = ceiling
        self._persist()

        self._verify_seven_day_observation(crew_name, ceiling)

    def _verify_seven_day_observation(self, crew_name: str, ceiling_usd: float) -> None:
        """C7: query llm_calls for this crew over the past 7 days.

        Raises ContractNotSatisfiedError if no rows found or a tick exceeded ceiling.
        Non-fatal if DB unreachable.
        """
        try:
            from memory import _pg_conn
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*), MAX(cost_usd)
                FROM llm_calls
                WHERE crew_name = %s
                  AND autonomous = TRUE
                  AND ts >= NOW() - INTERVAL '7 days'
                """,
                (crew_name,),
            )
            row = cur.fetchone()
            cur.close()

            count, max_cost = row[0], row[1]

            if count == 0:
                raise ContractNotSatisfiedError(
                    f"{crew_name}: C7 failed: no autonomous llm_calls rows found in the "
                    f"past 7 days. Run the crew in dry_run=True for 7 days before enabling."
                )

            if max_cost is not None and float(max_cost) > ceiling_usd:
                raise ContractNotSatisfiedError(
                    f"{crew_name}: C7 failed: a tick exceeded the cost ceiling "
                    f"(max observed: ${max_cost:.4f}, ceiling: ${ceiling_usd:.4f}). "
                    f"Lower the ceiling or fix the runaway cost before enabling."
                )
        except ContractNotSatisfiedError:
            raise
        except Exception as e:
            logger.warning(
                f"autonomy_guard: C7 DB check for {crew_name} failed (non-fatal, "
                f"proceeding without 7-day verification): {e}"
            )

    def _persist(self) -> None:
        try:
            self._state_file.write_text(json.dumps(self._state, indent=2))
        except Exception as e:
            logger.warning(f"autonomy_guard: failed to persist state: {e}")

    # Spend tracking (reads live from llm_calls)

    def _spent_today_usd(self) -> float:
        try:
            from memory import _pg_conn
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COALESCE(SUM(cost_usd), 0)::float
                FROM llm_calls
                WHERE autonomous = TRUE
                  AND ts::date = (now() AT TIME ZONE 'America/Denver')::date
                """
            )
            spent = cur.fetchone()[0]
            cur.close()
            return float(spent or 0.0)
        except Exception as e:
            logger.warning(f"autonomy_guard: failed to read spend, treating as 0: {e}")
            return 0.0

    def _per_crew_spend_today(self) -> dict:
        try:
            from memory import _pg_conn
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT crew_name, COALESCE(SUM(cost_usd), 0)::float
                FROM llm_calls
                WHERE autonomous = TRUE
                  AND ts::date = (now() AT TIME ZONE 'America/Denver')::date
                GROUP BY crew_name
                """
            )
            result = {row[0] or "unknown": float(row[1]) for row in cur.fetchall()}
            cur.close()
            return result
        except Exception as e:
            logger.warning(f"autonomy_guard: per-crew spend read failed: {e}")
            return {}

    # Public API

    def guard(self, crew_name: str, estimated_usd: float = 0.0) -> GuardDecision:
        """Check if an autonomous LLM call for this crew is allowed."""
        with self._lock:
            spent = self._spent_today_usd()

            if self._state.get("killed"):
                return GuardDecision(
                    allowed=False, dry_run=False,
                    reason=f"killed: {self._state.get('killed_reason') or 'unknown'}",
                    decision_tag="blocked-killed",
                    spent_today_usd=spent, cap_usd=self._cap_usd,
                )

            crew = self._state["crews"].get(crew_name)
            if crew is None:
                return GuardDecision(
                    allowed=False, dry_run=False,
                    reason=f"unknown crew: {crew_name}",
                    decision_tag="blocked-unknown-crew",
                    spent_today_usd=spent, cap_usd=self._cap_usd,
                )

            if not crew.get("enabled", False):
                return GuardDecision(
                    allowed=False, dry_run=False,
                    reason=f"crew disabled: {crew_name}",
                    decision_tag="blocked-disabled",
                    spent_today_usd=spent, cap_usd=self._cap_usd,
                )

            if (spent + estimated_usd) > self._cap_usd:
                self._state["killed"] = True
                self._state["killed_at"] = datetime.now(timezone.utc).isoformat()
                self._state["killed_reason"] = f"daily cap reached (${spent:.4f} of ${self._cap_usd:.2f})"
                self._persist()
                return GuardDecision(
                    allowed=False, dry_run=False,
                    reason=self._state["killed_reason"],
                    decision_tag="blocked-cap",
                    spent_today_usd=spent, cap_usd=self._cap_usd,
                )

            # Per-crew cost ceiling (set at contract sign time, stored in state)
            crew_ceiling = crew.get("cost_ceiling_usd")
            if crew_ceiling is not None and estimated_usd > crew_ceiling:
                return GuardDecision(
                    allowed=False, dry_run=False,
                    reason=f"per-crew ceiling exceeded: estimated ${estimated_usd:.4f} > ceiling ${crew_ceiling:.4f} for {crew_name}",
                    decision_tag="blocked-crew-ceiling",
                    spent_today_usd=spent, cap_usd=self._cap_usd,
                )

            is_dry_run = bool(crew.get("dry_run", True))
            return GuardDecision(
                allowed=True, dry_run=is_dry_run,
                reason="ok",
                decision_tag="dry-run" if is_dry_run else "allowed",
                spent_today_usd=spent, cap_usd=self._cap_usd,
            )

    def kill(self, reason: str) -> None:
        with self._lock:
            self._state["killed"] = True
            self._state["killed_at"] = datetime.now(timezone.utc).isoformat()
            self._state["killed_reason"] = reason
            self._persist()
            logger.warning(f"autonomy_guard: KILL set ({reason})")

    def unkill(self) -> None:
        with self._lock:
            self._state["killed"] = False
            self._state["killed_at"] = None
            self._state["killed_reason"] = None
            self._persist()
            logger.info("autonomy_guard: kill switch cleared")

    def is_killed(self) -> bool:
        with self._lock:
            return bool(self._state.get("killed"))

    def set_crew_enabled(self, crew_name: str, enabled: bool) -> None:
        with self._lock:
            if crew_name not in self._state["crews"]:
                raise ValueError(f"unknown crew: {crew_name}")
            if enabled:
                self._assert_contract_satisfied(crew_name)
            self._state["crews"][crew_name]["enabled"] = bool(enabled)
            self._persist()

    def set_crew_dry_run(self, crew_name: str, dry_run: bool) -> None:
        with self._lock:
            if crew_name not in self._state["crews"]:
                raise ValueError(f"unknown crew: {crew_name}")
            if not dry_run:
                self._assert_contract_satisfied(crew_name)
            self._state["crews"][crew_name]["dry_run"] = bool(dry_run)
            self._persist()

    def snapshot(self) -> SpendSnapshot:
        spent = self._spent_today_usd()
        return SpendSnapshot(
            spent_today_usd=spent,
            cap_usd=self._cap_usd,
            remaining_usd=max(0.0, self._cap_usd - spent),
            per_crew=self._per_crew_spend_today(),
        )

    def state_summary(self) -> dict:
        with self._lock:
            return {
                "killed": bool(self._state.get("killed")),
                "killed_reason": self._state.get("killed_reason"),
                "crews": dict(self._state.get("crews", {})),
                "cap_usd": self._cap_usd,
            }


# Process-wide singleton (lazy init)
_singleton: Optional[AutonomyGuard] = None
_singleton_lock = threading.Lock()


def get_guard() -> AutonomyGuard:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = AutonomyGuard()
        return _singleton
