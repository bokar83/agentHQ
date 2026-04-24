"""
approval_queue.py -- Phase 1 autonomy layer.

Every autonomous proposal flows through here. enqueue() writes a row and
sends a Telegram message for Boubacar's review. approve / reject / edit
transition the row and notify episodic_memory so the outcome row is updated.

Reply-to-message is the primary approval UX. find_latest_pending() backs the
fallback when Boubacar types 'yes' without replying.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger("agentsHQ.approval_queue")

# Controlled rejection-feedback vocabulary. Extend in code, not DB.
KNOWN_FEEDBACK_TAGS = ("off-voice", "wrong-hook", "stale", "too-salesy", "other")


@dataclass
class QueueRow:
    id: int
    ts_created: datetime
    ts_decided: Optional[datetime]
    crew_name: str
    proposal_type: str
    payload: dict
    telegram_msg_id: Optional[int]
    status: str
    decision_note: Optional[str]
    boubacar_feedback_tag: Optional[str]
    edited_payload: Optional[dict]
    task_outcome_id: Optional[int]


def _conn():
    from memory import _pg_conn
    return _pg_conn()


def _row_to_queue(row) -> QueueRow:
    return QueueRow(
        id=row[0],
        ts_created=row[1],
        ts_decided=row[2],
        crew_name=row[3],
        proposal_type=row[4],
        payload=row[5] if isinstance(row[5], dict) else json.loads(row[5]),
        telegram_msg_id=row[6],
        status=row[7],
        decision_note=row[8],
        boubacar_feedback_tag=row[9],
        edited_payload=row[10] if row[10] is None or isinstance(row[10], dict) else json.loads(row[10]),
        task_outcome_id=row[11],
    )


_SELECT_COLS = """
    id, ts_created, ts_decided, crew_name, proposal_type, payload,
    telegram_msg_id, status, decision_note, boubacar_feedback_tag,
    edited_payload, task_outcome_id
"""


def normalize_feedback_tag(raw: Optional[str]) -> Optional[str]:
    """Pattern-match free text against KNOWN_FEEDBACK_TAGS. Unmatched text is
    returned verbatim (Phase 5 Chairman classifies later).
    """
    if not raw:
        return None
    s = raw.strip().lower().replace(" ", "-")
    for tag in KNOWN_FEEDBACK_TAGS:
        if tag in s:
            return tag
    return raw.strip()
