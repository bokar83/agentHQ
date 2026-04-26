"""
atlas_dashboard.py -- Pure data fetchers for the Atlas M8 dashboard.

One function per card. Returns plain dicts ready for json.dumps().
No FastAPI imports. No side effects. All I/O is read-only except
action helpers (added later) which are at the bottom of this file.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("agentsHQ.atlas_dashboard")


def get_state() -> dict:
    """Atlas State card: autonomy kill switch + per-crew flags."""
    from autonomy_guard import get_guard
    return get_guard().state_summary()


def get_queue() -> dict:
    """Approval Queue card: pending items, newest first."""
    import approval_queue
    rows = approval_queue.list_pending(limit=20)
    items = []
    for r in rows:
        preview = ""
        if isinstance(r.payload, dict):
            preview = str(r.payload.get("title") or r.payload.get("hook") or r.payload.get("content") or "")[:120]
        items.append({
            "id": r.id,
            "ts_created": r.ts_created.isoformat() if r.ts_created else None,
            "crew_name": r.crew_name,
            "proposal_type": r.proposal_type,
            "preview": preview,
            "status": r.status,
        })
    return {"items": items, "count": len(items)}
