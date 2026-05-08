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
    except Exception as exc:
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


_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_HEX_ID_RE = re.compile(r"\b[0-9a-f]{16,}\b", re.IGNORECASE)
_LINE_NUMBER_RE = re.compile(r", line \d+")


def _normalize(line: str) -> str:
    """Strip timestamps, UUIDs, line numbers, hex IDs for signature comparison."""
    s = _TIMESTAMP_RE.sub("", line)
    s = _UUID_RE.sub("<uuid>", s)
    s = _HEX_ID_RE.sub("<hexid>", s)
    s = _LINE_NUMBER_RE.sub(", line <N>", s)
    s = re.sub(r"\buuid=[a-f0-9A-F]+\b", "uuid=<id>", s)
    return s.strip()


def group_by_signature(lines: list[str]) -> list[dict]:
    """Deduplicate error lines by normalized signature.

    Returns list of dicts: {signature, count, samples: [str, ...]}.
    Ordered by descending count.
    """
    from collections import defaultdict

    buckets: dict[str, list[str]] = defaultdict(list)
    for line in lines:
        sig = _normalize(line)
        buckets[sig].append(line)

    groups = [
        {"signature": sig, "count": len(samples), "samples": samples[:3]}
        for sig, samples in buckets.items()
    ]
    groups.sort(key=lambda g: g["count"], reverse=True)
    return groups
