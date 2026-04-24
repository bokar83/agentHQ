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

KNOWN_CREWS = ("griot", "hunter", "concierge", "chairman")

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

    def __init__(self, state_file: str = DEFAULT_STATE_FILE, cap_usd: float = DEFAULT_CAP_USD):
        self._state_file = Path(state_file)
        self._cap_usd = cap_usd
        self._lock = threading.RLock()
        self._state = self._load_state()

    # State persistence

    def _default_state(self) -> dict:
        return {
            "killed": False,
            "killed_at": None,
            "killed_reason": None,
            "crews": {
                c: {"enabled": False, "dry_run": True} for c in KNOWN_CREWS
            },
        }

    def _load_state(self) -> dict:
        try:
            if not self._state_file.exists():
                self._state_file.parent.mkdir(parents=True, exist_ok=True)
                state = self._default_state()
                self._state_file.write_text(json.dumps(state, indent=2))
                return state
            return json.loads(self._state_file.read_text())
        except Exception as e:
            logger.warning(f"autonomy_guard: failed to load state, using defaults: {e}")
            return self._default_state()

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
            self._state["crews"][crew_name]["enabled"] = bool(enabled)
            self._persist()

    def set_crew_dry_run(self, crew_name: str, dry_run: bool) -> None:
        with self._lock:
            if crew_name not in self._state["crews"]:
                raise ValueError(f"unknown crew: {crew_name}")
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
