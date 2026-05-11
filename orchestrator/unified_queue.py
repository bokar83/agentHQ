"""
unified_queue.py -- Echo M3: single display + routing layer for all pending approvals.

Two backing stores:
  approval_queue (Postgres table) -- content proposals, outreach drafts, concierge fixes.
  tasks (Postgres table, kind='commit-proposal') -- async commit proposals from Echo M1.

Public API:
  list_all_pending()        -> list[dict]   merged, sorted by created_at desc
  list_all_recent(hours)    -> list[dict]   merged, all statuses, last N hours
  approve_any(id_str, note) -> dict         routes to correct store by id format
  reject_any(id_str, note)  -> dict         routes to correct store by id format

ID disambiguation:
  approval_queue rows use integer ids  (e.g. "42")
  tasks rows use uuid hex ids          (e.g. "3f9a1b2c" or full 32-char uuid)
"""

from __future__ import annotations

from typing import Optional


def _is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def _aq_row_to_dict(r) -> dict:
    """Convert a QueueRow from approval_queue into the unified shape."""
    p = r.payload or {}
    summary = str(
        p.get("title") or p.get("hook_preview") or p.get("hook") or
        p.get("summary") or p.get("content") or p.get("draft") or ""
    )[:120]
    return {
        "source": "approval_queue",
        "id": str(r.id),
        "label": f"Q{r.id}",
        "crew_name": r.crew_name,
        "proposal_type": r.proposal_type,
        "summary": summary,
        "status": r.status,
        "created_at": r.ts_created.isoformat() if r.ts_created else None,
        "decided_at": r.ts_decided.isoformat() if r.ts_decided else None,
        "decision_note": r.decision_note,
    }


def _task_row_to_dict(r: dict) -> dict:
    """Convert a tasks row (from proposal.list_pending) into the unified shape."""
    p = r.get("payload") or {}
    msg = p.get("suggested_message") or ""
    summary = msg.splitlines()[0][:120] if msg else ""
    created_at = r.get("created_at")
    return {
        "source": "tasks",
        "id": r["id"],
        "label": f"P{r['id'][:8]}",
        "crew_name": p.get("proposed_by", "agent"),
        "proposal_type": "commit-proposal",
        "summary": summary,
        "status": r.get("status", "queued"),
        "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at or ""),
        "decided_at": None,
        "decision_note": r.get("error"),
    }


def list_all_pending(limit: int = 20) -> list[dict]:
    """All pending items from both stores, sorted newest-first."""
    import approval_queue
    from skills.coordination import proposal as _proposal

    aq_rows = approval_queue.list_pending(limit=limit)
    task_rows = _proposal.list_pending(limit=limit)

    items = [_aq_row_to_dict(r) for r in aq_rows]
    items += [_task_row_to_dict(r) for r in task_rows]
    items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return items[:limit]


def list_all_recent(hours: int = 48, limit: int = 50) -> list[dict]:
    """All items (any status) from both stores in last N hours, sorted newest-first."""
    import approval_queue
    from skills.coordination import proposal as _proposal

    aq_rows = approval_queue.list_recent(hours=hours, limit=limit)
    # tasks table: no list_recent yet -- fall back to list_pending for commit-proposals
    task_rows = _proposal.list_pending(limit=limit)

    items = [_aq_row_to_dict(r) for r in aq_rows]
    items += [_task_row_to_dict(r) for r in task_rows]
    items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return items[:limit]


def approve_any(id_str: str, note: Optional[str] = None) -> dict:
    """Approve an item from either store. Routes by id format.

    approval_queue ids are integers (e.g. "42").
    tasks ids are uuid hex strings (e.g. "3f9a1b2c").
    """
    id_str = id_str.strip()
    if _is_int(id_str):
        import approval_queue
        row = approval_queue.approve(int(id_str), note=note)
        if row is None:
            return {"ok": False, "error": f"Queue #{id_str}: not found or already decided"}
        return {"ok": True, "source": "approval_queue", "id": id_str, "status": row.status}
    else:
        from skills.coordination.proposal import ack
        result = ack(id_str, message_override=note)
        return {**result, "source": "tasks", "id": id_str}


def reject_any(id_str: str, note: Optional[str] = None, feedback_tag: Optional[str] = None) -> dict:
    """Reject an item from either store. Routes by id format."""
    id_str = id_str.strip()
    if _is_int(id_str):
        import approval_queue
        row = approval_queue.reject(int(id_str), note=note, feedback_tag=feedback_tag)
        if row is None:
            return {"ok": False, "error": f"Queue #{id_str}: not found or already decided"}
        return {"ok": True, "source": "approval_queue", "id": id_str, "status": row.status}
    else:
        from skills.coordination.proposal import reject
        result = reject(id_str, reason=note)
        return {**result, "source": "tasks", "id": id_str}
