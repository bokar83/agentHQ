"""
atlas_dashboard.py -- Pure data fetchers for the Atlas M8 dashboard.

One function per card. Returns plain dicts ready for json.dumps().
No FastAPI imports. No side effects. All I/O is read-only except
action helpers (added later) which are at the bottom of this file.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("agentsHQ.atlas_dashboard")

from autonomy_guard import get_guard


def get_state() -> dict:
    """Atlas State card: autonomy kill switch + per-crew flags."""
    return get_guard().state_summary()
