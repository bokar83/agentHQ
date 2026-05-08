"""
concierge_crew.py - M4 LLM-powered error triage.

Reads /var/log/error_monitor.log on VPS, groups errors by normalized
signature, proposes fixes via Claude Haiku, enqueues to approval_queue.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("agentsHQ.concierge_crew")

_VPS_HOST = "72.60.209.109"
_VPS_USER = "root"
_LOG_PATH = "/var/log/error_monitor.log"
_ERROR_PATTERN = re.compile(
    r"Traceback \(most recent call last\)|\[ERROR\]|(?:^|\s)ERROR:|\bCRITICAL:"
)
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[\.,\d]*\s*")


def _ssh_client():
    """Return a connected paramiko SSHClient. Caller is responsible for close()."""
    import paramiko

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_key = os.environ.get("VPS_SSH_KEY_PATH", os.path.expanduser("~/.ssh/id_rsa"))
    client.connect(
        hostname=_VPS_HOST,
        username=_VPS_USER,
        key_filename=ssh_key,
        timeout=10,
    )
    return client


def fetch_recent_errors(hours: int = 24) -> list[str]:
    """Pull error lines from error_monitor.log on VPS via SFTP.

    Returns list of matching log lines. Empty list on SSH failure (non-fatal).
    """
    import paramiko

    try:
        client = _ssh_client()
    except (paramiko.SSHException, OSError) as exc:
        logger.warning("concierge_crew: SSH connect failed (skipping sweep): %s", exc)
        return []

    try:
        with client.open_sftp() as sftp:
            with sftp.open(_LOG_PATH) as fh:
                raw = fh.read().decode(errors="replace")
    except (IOError, OSError) as exc:
        logger.warning("concierge_crew: SFTP read failed: %s", exc)
        return []
    finally:
        client.close()

    lines = []
    for line in raw.splitlines():
        if _ERROR_PATTERN.search(line):
            lines.append(line)
    return lines
