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
KNOWN_FEEDBACK_TAGS = ("off-voice", "wrong-hook", "stale", "too-salesy", "enhance", "other")


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


def enqueue(
    crew_name: str,
    proposal_type: str,
    payload: dict,
    outcome_id: Optional[int] = None,
    chat_id: Optional[str] = None,
) -> QueueRow:
    """Insert a pending row, send a Telegram preview with Approve/Reject buttons, store the msg_id back.

    If chat_id is None, reads OWNER_TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID env.
    If Telegram send fails, row persists with telegram_msg_id=NULL and shows on /queue.
    """
    import os as _os
    from notifier import send_message_with_buttons

    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        f"""
        INSERT INTO approval_queue (crew_name, proposal_type, payload, task_outcome_id)
        VALUES (%s, %s, %s::jsonb, %s)
        RETURNING {_SELECT_COLS}
        """,
        (crew_name, proposal_type, json.dumps(payload), outcome_id),
    )
    row = _row_to_queue(cur.fetchone())
    conn.commit()

    if chat_id is None:
        chat_id = _os.environ.get("OWNER_TELEGRAM_CHAT_ID") or _os.environ.get("TELEGRAM_CHAT_ID")

    preview = _format_proposal_preview(row)
    msg_id = None
    if chat_id:
        buttons = [
            [
                (f"Approve #{row.id}", f"approve_queue_item:{row.id}"),
                (f"Enhance #{row.id}", f"enhance_queue_item:{row.id}"),
                (f"Reject #{row.id}", f"reject_queue_item:{row.id}"),
            ],
        ]
        msg_id = send_message_with_buttons(str(chat_id), preview, buttons)
    if msg_id:
        cur.execute(
            f"UPDATE approval_queue SET telegram_msg_id = %s WHERE id = %s RETURNING {_SELECT_COLS}",
            (msg_id, row.id),
        )
        row = _row_to_queue(cur.fetchone())
        conn.commit()
    else:
        logger.warning(f"enqueue: Telegram send failed for queue #{row.id}; row persists without msg_id")

    cur.close()
    return row


def _format_proposal_preview(row: QueueRow) -> str:
    """One-message preview sent to Boubacar when a proposal is queued."""
    p = row.payload or {}
    title = p.get("title", "")
    platform = p.get("platform", "")
    hook = (p.get("hook_preview") or p.get("hook") or "").strip()
    post_text = (p.get("text") or p.get("body") or p.get("content") or p.get("draft") or "").strip()

    platform_label = f" [{platform}]" if platform else ""

    # Show hook as the lead line — enough to judge the post at a glance.
    # Full body follows so Boubacar can read the whole thing if he wants.
    lines = [f"Queue #{row.id}{platform_label}: {title}", "---"]
    if hook:
        lines.append(f"Hook: {hook[:200]}")
        lines.append("")
    if post_text:
        lines.append(post_text)
    else:
        lines.append("(no body)")
    lines.append("---")
    lines.append("Approve to schedule. Enhance to queue for rewrite. Edit: reply 'edit: <new text>'.")

    return "\n".join(lines)


def get(queue_id: int) -> Optional[QueueRow]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(f"SELECT {_SELECT_COLS} FROM approval_queue WHERE id = %s", (queue_id,))
    row = cur.fetchone()
    cur.close()
    return _row_to_queue(row) if row else None


def find_by_telegram_msg_id(msg_id: int) -> Optional[QueueRow]:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT {_SELECT_COLS} FROM approval_queue WHERE telegram_msg_id = %s ORDER BY id DESC LIMIT 1",
        (msg_id,),
    )
    row = cur.fetchone()
    cur.close()
    return _row_to_queue(row) if row else None


def find_latest_pending(max_age_hours: int = 2) -> Optional[QueueRow]:
    """Fallback for naked 'yes' when no reply target was supplied."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT {_SELECT_COLS}
          FROM approval_queue
         WHERE status = 'pending'
           AND ts_created > now() - (%s || ' hours')::interval
         ORDER BY ts_created DESC
         LIMIT 1
        """,
        (str(max_age_hours),),
    )
    row = cur.fetchone()
    cur.close()
    return _row_to_queue(row) if row else None


def list_pending(limit: int = 10) -> list:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT {_SELECT_COLS} FROM approval_queue WHERE status = 'pending' ORDER BY ts_created DESC LIMIT %s",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    return [_row_to_queue(r) for r in rows]


def count_pending() -> int:
    """Return the total number of pending rows (no LIMIT).

    Used by the morning digest so we don't under-report backlog when more
    than the preview-limit are pending. See Codex review on PR #10.
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM approval_queue WHERE status = 'pending'")
    n = cur.fetchone()[0]
    cur.close()
    return int(n or 0)


def _transition(
    queue_id: int,
    new_status: str,
    note: Optional[str],
    feedback_tag: Optional[str],
    edited_payload: Optional[dict],
) -> Optional[QueueRow]:
    """Atomically move a pending row to approved / rejected / edited. Returns
    None if the row doesn't exist or is already decided.
    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        f"""
        UPDATE approval_queue
           SET status = %s,
               ts_decided = now(),
               decision_note = COALESCE(%s, decision_note),
               boubacar_feedback_tag = COALESCE(%s, boubacar_feedback_tag),
               edited_payload = COALESCE(%s::jsonb, edited_payload)
         WHERE id = %s AND status = 'pending'
        RETURNING {_SELECT_COLS}
        """,
        (
            new_status, note, feedback_tag,
            json.dumps(edited_payload) if edited_payload is not None else None,
            queue_id,
        ),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    if row is None:
        return None
    out = _row_to_queue(row)
    # Notify episodic_memory so the outcome row's success flag updates.
    if out.task_outcome_id is not None:
        try:
            from episodic_memory import record_approval_result
            success = new_status in ("approved", "edited")
            record_approval_result(out.task_outcome_id, success=success, feedback=note)
        except Exception as e:
            logger.warning(f"_transition: episodic_memory update failed for outcome {out.task_outcome_id}: {e}")
    return out


def approve(queue_id: int, note: Optional[str] = None) -> Optional[QueueRow]:
    return _transition(queue_id, "approved", note, None, None)


def reject(queue_id: int, note: Optional[str] = None, feedback_tag: Optional[str] = None) -> Optional[QueueRow]:
    return _transition(queue_id, "rejected", note, feedback_tag, None)


def edit(queue_id: int, new_payload: dict, note: Optional[str] = None) -> Optional[QueueRow]:
    return _transition(queue_id, "edited", note, None, new_payload)


def set_feedback_tag(queue_id: int, feedback_tag: str) -> Optional[QueueRow]:
    """Used by the post-rejection feedback window (button tap or text reply)."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        f"""
        UPDATE approval_queue
           SET boubacar_feedback_tag = %s
         WHERE id = %s AND status = 'rejected'
        RETURNING {_SELECT_COLS}
        """,
        (feedback_tag, queue_id),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return _row_to_queue(row) if row else None
