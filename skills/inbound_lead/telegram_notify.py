"""Format Telegram notification for inbound lead completion.

The actual send is performed by orchestrator.notifier.send_message (Python
urllib, not curl -- curl fails SSL on this network per feedback memory).
This module only produces the message text so it can be unit-tested without
touching the network.
"""
from __future__ import annotations

from skills.inbound_lead.schema import InboundRoutineResult


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "\u2026"


def _status_emoji(status: str) -> str:
    return {
        "enriched": "\U00002705",        # green check
        "rebook_update": "\U0001F504",   # counterclockwise arrows
        "partial": "\U000026A0\uFE0F",   # warning
        "failed": "\U0000274C",          # red x
    }.get(status, "\U00002753")          # question mark


def format_inbound_telegram_message(result: InboundRoutineResult) -> str:
    """Return a short Telegram message summarizing a routine run.

    Telegram parses HTML when parse_mode=HTML; we avoid relying on that so the
    message also reads fine in plain text. Keep under ~1000 chars.
    """
    emoji = _status_emoji(result.status)
    lines: list[str] = [
        f"{emoji} Inbound lead: {result.status}",
        f"{result.payload.name} <{result.payload.email}>",
    ]

    if result.payload.company:
        lines.append(f"Company: {result.payload.company}")

    if result.payload.meeting_time:
        lines.append(f"Meeting: {result.payload.meeting_time.isoformat()}")

    if result.brief:
        lines.append(f"Research: {result.brief.research_confidence}")
        if result.brief.likely_friction:
            frictions = "; ".join(result.brief.likely_friction[:2])
            lines.append(f"Friction: {_truncate(frictions, 200)}")

    if result.log:
        if result.log.notion_row_url:
            lines.append(f"Notion: {result.log.notion_row_url}")
        if result.log.gmail_draft_url:
            lines.append(f"Gmail draft: {result.log.gmail_draft_url}")
        if result.log.fields_skipped:
            lines.append(f"Skipped: {', '.join(result.log.fields_skipped)}")
        for warning in result.log.warnings[:2]:
            lines.append(f"Warn: {_truncate(warning, 200)}")

    if result.email:
        subject = _truncate(result.email.subject, 80)
        lines.append(f"Draft subject: {subject}")

    if result.error:
        lines.append(f"Error: {_truncate(result.error, 300)}")

    message = "\n".join(lines)
    return _truncate(message, 1500)
