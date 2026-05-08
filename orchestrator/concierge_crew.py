"""
concierge_crew.py - M4 LLM-powered error triage.

Reads /var/log/error_monitor.log on VPS, groups errors by normalized
signature, proposes fixes via Claude Haiku, enqueues to approval_queue.
"""
from __future__ import annotations

import anthropic
import json
import logging
import os
import re
from typing import cast

import skills.coordination as coordination
import approval_queue

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


def fetch_recent_errors() -> list[str]:
    """Pull all error lines from error_monitor.log on VPS via SFTP.

    Reads the full log file. Caller uses group_by_signature + 7-day dedup
    in enqueue_proposals to avoid re-processing known errors.
    Returns empty list on SSH failure (non-fatal).
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
_PARAM_ID_RE = re.compile(r"\buuid=[a-f0-9A-F]+\b")


def _normalize(line: str) -> str:
    """Strip timestamps, UUIDs, line numbers, hex IDs for signature comparison."""
    s = _TIMESTAMP_RE.sub("", line)
    s = _UUID_RE.sub("<uuid>", s)
    s = _HEX_ID_RE.sub("<hexid>", s)
    s = _LINE_NUMBER_RE.sub(", line <N>", s)
    s = _PARAM_ID_RE.sub("uuid=<id>", s)
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


_HAIKU_MODEL = "claude-haiku-4-5-20251001"
_PROPOSE_PROMPT = """\
You are an ops engineer triaging a production error. Given this error signature and sample lines, return ONLY valid JSON with exactly these keys:
- "summary": one sentence describing the error (max 80 chars)
- "severity": one of "low", "med", "high"
- "triage_note": one concrete action to fix or investigate (max 120 chars)

Error signature:
{signature}

Sample lines (up to 3):
{samples}

Respond with JSON only. No explanation, no markdown.
"""


def propose_fix(group: dict) -> dict:
    """Call Claude Haiku to propose a fix for one error group.

    Returns {summary, severity, triage_note}. Falls back to safe defaults
    if the model returns unparseable output.
    """
    prompt = _PROPOSE_PROMPT.format(
        signature=group["signature"][:300],
        samples="\n".join(group["samples"])[:500],
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("concierge_crew: ANTHROPIC_API_KEY not set, skipping propose_fix")
        return {
            "summary": group["signature"][:80],
            "severity": "med",
            "triage_note": "Investigate logs manually.",
        }
    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=_HAIKU_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = cast(anthropic.types.TextBlock, response.content[0]).text.strip()
        if "```" in text:
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text).strip()
        result = json.loads(text)
        severity = result.get("severity", "med")
        if severity not in ("low", "med", "high"):
            severity = "med"
        return {
            "summary": str(result.get("summary", group["signature"][:80])),
            "severity": severity,
            "triage_note": str(result.get("triage_note", "Investigate logs manually.")),
        }
    except Exception as exc:
        logger.warning("concierge_crew: Haiku parse failed (%s), using fallback", exc)
        return {
            "summary": group["signature"][:80],
            "severity": "med",
            "triage_note": "Investigate logs manually.",
        }


_DEDUP_WINDOW_SECS = 7 * 24 * 3600  # 7 days


def enqueue_proposals(proposals: list[dict]) -> int:
    """Enqueue proposals not seen in the last 7 days.

    Uses coordination.recent_completed(kind='concierge-fix') for dedup.
    Returns count of newly enqueued proposals.
    """
    try:
        recent = coordination.recent_completed(
            kind="concierge-fix",
            since_seconds=_DEDUP_WINDOW_SECS,
            limit=500,
        )
    except Exception as exc:
        logger.warning("concierge_crew: coordination lookup failed: %s", exc)
        recent = []

    seen_sigs: set[str] = set()
    for task in recent:
        payload = task.get("payload") or {}
        sig = payload.get("signature")
        if sig:
            seen_sigs.add(sig)

    enqueued = 0
    for proposal in proposals:
        sig = proposal["signature"]
        if sig in seen_sigs:
            logger.info("concierge_crew: dedup skip sig=%s", sig[:60])
            continue

        payload = {
            "signature": sig,
            "count": proposal["count"],
            "samples": proposal["samples"],
            "summary": proposal["summary"],
            "severity": proposal["severity"],
            "triage_note": proposal["triage_note"],
        }

        try:
            row = approval_queue.enqueue(
                crew_name="concierge",
                proposal_type="concierge-fix",
                payload=payload,
            )
            logger.info(
                "concierge_crew: enqueued queue#%s sig=%s severity=%s",
                row.id,
                sig[:60],
                proposal["severity"],
            )
            enqueued += 1
        except Exception as exc:
            logger.error("concierge_crew: enqueue failed for sig=%s: %s", sig[:60], exc)

    return enqueued
