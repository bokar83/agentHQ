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


def _conn():
    """Lazy import to avoid circular imports at module load."""
    from memory import _pg_conn
    return _pg_conn()


def start_task(crew_name: str, plan_summary: str) -> OutcomeRow:
    """Insert a new task_outcomes row with success=NULL and return the row."""
    signature = build_signature(plan_summary)
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO task_outcomes (crew_name, task_signature, plan_summary)
        VALUES (%s, %s, %s)
        RETURNING id, ts_started, ts_completed, crew_name, task_signature,
                  plan_summary, result_summary, total_cost_usd, success,
                  approval_queue_id, boubacar_feedback, llm_calls_ids
        """,
        (crew_name, signature, plan_summary),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return _row_to_outcome(row)


def complete_task(
    outcome_id: int,
    result_summary: Optional[str] = None,
    total_cost_usd: float = 0.0,
    llm_calls_ids: Optional[list] = None,
) -> OutcomeRow:
    """Fill ts_completed + result fields. Does not touch success (that's set
    by record_approval_result based on Boubacar's decision).
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE task_outcomes
           SET ts_completed   = now(),
               result_summary = %s,
               total_cost_usd = %s,
               llm_calls_ids  = %s
         WHERE id = %s
        RETURNING id, ts_started, ts_completed, crew_name, task_signature,
                  plan_summary, result_summary, total_cost_usd, success,
                  approval_queue_id, boubacar_feedback, llm_calls_ids
        """,
        (result_summary, total_cost_usd, llm_calls_ids or [], outcome_id),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    if row is None:
        raise ValueError(f"task_outcomes row {outcome_id} not found")
    return _row_to_outcome(row)


def link_approval(outcome_id: int, approval_queue_id: int) -> None:
    """Set approval_queue_id on the outcome row."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE task_outcomes SET approval_queue_id = %s WHERE id = %s",
        (approval_queue_id, outcome_id),
    )
    conn.commit()
    cur.close()


def record_approval_result(
    outcome_id: int,
    success: bool,
    feedback: Optional[str] = None,
) -> None:
    """Called when Boubacar approves, rejects, or edits a queued proposal.

    success=True: approved or edited-and-accepted.
    success=False: rejected.
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE task_outcomes
           SET success          = %s,
               boubacar_feedback = COALESCE(%s, boubacar_feedback)
         WHERE id = %s
        """,
        (success, feedback, outcome_id),
    )
    conn.commit()
    cur.close()


def find_similar(task_signature: str, limit: int = 5) -> list:
    """Return up to `limit` past outcomes whose signature shares the same prefix.

    Matches via LIKE <sig>% so shorter plan_summaries still hit longer ones
    that start with the same normalized stem.
    """
    if not task_signature:
        return []
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, ts_started, ts_completed, crew_name, task_signature,
               plan_summary, result_summary, total_cost_usd, success,
               approval_queue_id, boubacar_feedback, llm_calls_ids
          FROM task_outcomes
         WHERE task_signature LIKE %s
         ORDER BY ts_started DESC
         LIMIT %s
        """,
        (task_signature + "%", limit),
    )
    rows = cur.fetchall()
    cur.close()
    return [_row_to_outcome(r) for r in rows]


def crew_stats(crew_name: str, days: int = 7) -> dict:
    """Summary metrics for a crew in the last N days. Joins approval_queue for
    approval_status (we deliberately don't denormalize on task_outcomes).
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            COUNT(*)                                                 AS total,
            COUNT(*) FILTER (WHERE aq.status = 'approved')            AS approved,
            COUNT(*) FILTER (WHERE aq.status = 'rejected')            AS rejected,
            COUNT(*) FILTER (WHERE aq.status = 'edited')              AS edited,
            COALESCE(AVG(tout.total_cost_usd), 0)::float              AS avg_cost_usd
          FROM task_outcomes tout
          LEFT JOIN approval_queue aq ON aq.id = tout.approval_queue_id
         WHERE tout.crew_name = %s
           AND tout.ts_started > now() - (%s || ' days')::interval
        """,
        (crew_name, str(days)),
    )
    row = cur.fetchone()
    total, approved, rejected, edited, avg_cost = row
    cur.execute(
        """
        SELECT aq.boubacar_feedback_tag, COUNT(*) AS n
          FROM task_outcomes tout
          JOIN approval_queue aq ON aq.id = tout.approval_queue_id
         WHERE tout.crew_name = %s
           AND tout.ts_started > now() - (%s || ' days')::interval
           AND aq.boubacar_feedback_tag IS NOT NULL
         GROUP BY aq.boubacar_feedback_tag
         ORDER BY n DESC
         LIMIT 5
        """,
        (crew_name, str(days)),
    )
    top_tags = [(r[0], r[1]) for r in cur.fetchall()]
    cur.close()
    decided = approved + rejected + edited
    approval_rate = (approved + edited) / decided if decided > 0 else 0.0
    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "edited": edited,
        "approval_rate": round(approval_rate, 3),
        "avg_cost_usd": round(avg_cost, 6),
        "top_feedback_tags": top_tags,
    }
