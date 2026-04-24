"""
episodic_memory.py -- Phase 1 autonomy layer.

Writes and reads task_outcomes: one row per autonomous crew task. Captures
plan summary, result, cost, success flag, link to the approval_queue row
(if any), and Boubacar's feedback after approval or rejection.

Read path exposes:
  - find_similar(signature) for crews wanting past-case retrieval
  - crew_stats(crew_name, days) for Chairman / /outcomes command

Writes are autonomous-path only. User-initiated tasks still log to router_log
and llm_calls exactly as they did in Phase 0.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger("agentsHQ.episodic_memory")

# Strip these patterns from plan_summary before taking the signature prefix.
# Goal: make "Draft post for 2026-04-24" and "Draft post for 2026-04-25"
# collide on the same signature so find_similar actually returns past work.
_SIG_STRIP_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),                 # ISO dates
    re.compile(r"\b\d{2}:\d{2}(:\d{2})?\b"),              # HH:MM or HH:MM:SS
    re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),  # UUIDs
    re.compile(r"\b\d{5,}\b"),                            # long numeric IDs
    re.compile(r"\s+"),                                    # collapse whitespace (applied last)
]


@dataclass
class OutcomeRow:
    id: int
    ts_started: datetime
    ts_completed: Optional[datetime]
    crew_name: str
    task_signature: str
    plan_summary: Optional[str]
    result_summary: Optional[str]
    total_cost_usd: float
    success: Optional[bool]
    approval_queue_id: Optional[int]
    boubacar_feedback: Optional[str]
    llm_calls_ids: list


def build_signature(plan_summary: Optional[str]) -> str:
    """Normalize plan_summary and return first 50 chars as the signature.

    Deterministic; two calls on semantically-similar summaries yield the same
    signature. Phase 5 will replace this with an embedding-based approach.
    """
    if not plan_summary:
        return ""
    s = plan_summary.lower()
    for pat in _SIG_STRIP_PATTERNS[:-1]:
        s = pat.sub("", s)
    s = _SIG_STRIP_PATTERNS[-1].sub(" ", s).strip()
    return s[:50]


def _row_to_outcome(row) -> OutcomeRow:
    """Turn a psycopg2 row tuple into an OutcomeRow."""
    return OutcomeRow(
        id=row[0],
        ts_started=row[1],
        ts_completed=row[2],
        crew_name=row[3],
        task_signature=row[4],
        plan_summary=row[5],
        result_summary=row[6],
        total_cost_usd=float(row[7]) if row[7] is not None else 0.0,
        success=row[8],
        approval_queue_id=row[9],
        boubacar_feedback=row[10],
        llm_calls_ids=list(row[11] or []),
    )
