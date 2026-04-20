"""Log inbound lead: create Gmail draft via gws CLI, upsert Notion Pipeline row.

Design decisions (see docs/superpowers/specs/2026-04-20-inbound-lead-routine-addendum.md):
- Title property `Lead/Company` = person name (not company).
- `Contact Name` rich_text = company.
- `Next Action Date` = meeting_time.
- `Notes` rich_text = research summary (<=2000 chars).
- `Next Action` rich_text = draft review CTA.
- `URL (To link and rollup later)` rich_text = company website.
- `Source` select = "Other" (Calendly/Formspree options don't exist yet; warn).
- `Status` select = "Call Booked" on first enrichment.

Fields_skipped: gmail_draft (no URL property), booking_id_property (no property).
Both are still captured: gmail_draft URL goes into Next Action text; booking_id
goes into the appended page body block.
"""
from __future__ import annotations
import base64
import json
import logging
import os
import subprocess
from email.message import EmailMessage
from typing import Optional

from skills.forge_cli.notion_client import NotionClient
from skills.inbound_lead.schema import (
    DraftedEmail, InboundPayload, LogResult, ResearchBrief,
)

logger = logging.getLogger("agentsHQ.inbound_lead.logger")

NOTES_MAX_CHARS = 2000
GWS_BIN = os.environ.get("GWS_BIN", "gws")

_ALLOWED_SOURCES = {"LinkedIn", "X", "Referral", "Speaking", "Other"}
_ALLOWED_STATUSES = {"New", "Reached Out", "Call Booked", "Proposal Sent", "Won", "Lost"}
_BUMP_STATUSES = {"New", "Reached Out"}


def _rich_text(value: str) -> list[dict]:
    if not value:
        return []
    return [{"type": "text", "text": {"content": value[:NOTES_MAX_CHARS]}}]


def _build_research_summary(brief: ResearchBrief, booking_id: str) -> str:
    """Compact single-block summary. Full detail goes in page body blocks."""
    parts = [f"[booking:{booking_id}]", brief.what_they_do]
    if brief.likely_friction:
        parts.append("Likely friction: " + "; ".join(brief.likely_friction))
    if brief.conversation_hooks:
        parts.append("Hooks: " + "; ".join(brief.conversation_hooks))
    parts.append(f"Confidence: {brief.research_confidence}")
    if brief.notes:
        parts.append(f"Notes: {brief.notes}")
    return " | ".join(parts)[:NOTES_MAX_CHARS]


def _build_page_body_blocks(
    brief: ResearchBrief,
    draft: Optional[DraftedEmail],
    booking_id: str,
) -> list[dict]:
    """Full research + draft preview as page body blocks (no 2000-char cap)."""
    blocks: list[dict] = []

    def heading(text: str) -> dict:
        return {
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }

    def paragraph(text: str) -> dict:
        return {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def bullet(text: str) -> dict:
        return {
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    blocks.append(heading(f"Research brief ({brief.research_confidence})"))
    blocks.append(paragraph(f"Booking: {booking_id}"))
    blocks.append(paragraph(brief.what_they_do))

    if brief.industry_signals:
        blocks.append(heading("Industry signals"))
        blocks.extend(bullet(s) for s in brief.industry_signals)
    if brief.likely_friction:
        blocks.append(heading("Likely friction"))
        blocks.extend(bullet(f) for f in brief.likely_friction)
    if brief.conversation_hooks:
        blocks.append(heading("Conversation hooks"))
        blocks.extend(bullet(h) for h in brief.conversation_hooks)
    if brief.sources:
        blocks.append(heading("Sources"))
        blocks.extend(bullet(s) for s in brief.sources)

    if draft:
        blocks.append(heading("Draft preview"))
        blocks.append(paragraph(f"Subject: {draft.subject}"))
        blocks.append(paragraph(draft.body_markdown))
    return blocks


def create_gmail_draft(
    to_email: str,
    to_name: str,
    subject: str,
    body_markdown: str,
) -> Optional[str]:
    """Create a Gmail draft via gws CLI. Returns draft id or None on failure.

    gws path: `gmail users drafts create` with a raw base64url-encoded RFC822 message.
    """
    msg = EmailMessage()
    msg["To"] = f"{to_name} <{to_email}>"
    msg["Subject"] = subject
    msg.set_content(body_markdown)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii").rstrip("=")
    payload = {"message": {"raw": raw}}
    try:
        proc = subprocess.run(
            [GWS_BIN, "gmail", "users", "drafts", "create",
             "--params", '{"userId":"me"}',
             "--json", json.dumps(payload)],
            capture_output=True, text=True, timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.warning(f"gws invocation failed: {exc}")
        return None
    if proc.returncode != 0:
        logger.warning(f"gws returned {proc.returncode}: {proc.stderr[:200]}")
        return None
    try:
        out = json.loads(proc.stdout)
    except (ValueError, json.JSONDecodeError):
        logger.warning(f"gws stdout was not JSON: {proc.stdout[:200]}")
        return None
    return out.get("id")


def gmail_draft_url(draft_id: str) -> str:
    """Draft URL that opens the draft in the Gmail UI."""
    return f"https://mail.google.com/mail/u/0/#drafts?compose={draft_id}"


def _build_properties(
    payload: InboundPayload,
    brief: ResearchBrief,
    next_action_text: str,
    notes_text: str,
    status: Optional[str],
) -> dict:
    """Build the Notion properties dict. None-valued fields are omitted."""
    props: dict = {
        "Lead/Company": {"title": _rich_text(payload.name)},
        "Email": {"email": payload.email},
        "Contact Name": {"rich_text": _rich_text(payload.company or "")},
        "Next Action Date": (
            {"date": {"start": payload.meeting_time.isoformat()}}
            if payload.meeting_time else {"date": None}
        ),
        "Notes": {"rich_text": _rich_text(notes_text)},
        "Next Action": {"rich_text": _rich_text(next_action_text)},
        "URL (To link and rollup later)": {"rich_text": _rich_text(payload.raw_company_url or "")},
        "Source": {"select": {"name": "Other"}},
    }
    if status and status in _ALLOWED_STATUSES:
        props["Status"] = {"select": {"name": status}}
    return props


def _find_existing_row(
    client: NotionClient, database_id: str, email: str,
) -> Optional[dict]:
    """Look up an existing Pipeline row by Email property."""
    rows = client.query_database(
        database_id,
        filter_obj={"property": "Email", "email": {"equals": email}},
    )
    return rows[0] if rows else None


def _current_status(row: dict) -> Optional[str]:
    prop = row.get("properties", {}).get("Status", {})
    select = prop.get("select")
    return select.get("name") if select else None


def log_lead(
    payload: InboundPayload,
    brief: ResearchBrief,
    draft: Optional[DraftedEmail],
    database_id: str,
    notion_secret: str,
) -> LogResult:
    """Upsert the Pipeline row and (if draft present) create a Gmail draft.

    Returns a LogResult recording what was written, skipped, and any warnings.
    Never raises: failures are captured as warnings and fields_skipped entries
    so the orchestrator can degrade gracefully.
    """
    fields_written: list[str] = []
    fields_skipped: list[str] = []
    warnings: list[str] = []
    gmail_draft_id: Optional[str] = None
    gmail_url: Optional[str] = None
    notion_page_id: Optional[str] = None

    if draft:
        gmail_draft_id = create_gmail_draft(
            to_email=payload.email, to_name=payload.name,
            subject=draft.subject, body_markdown=draft.body_markdown,
        )
        if gmail_draft_id:
            gmail_url = gmail_draft_url(gmail_draft_id)
            fields_written.append("gmail_draft")
        else:
            warnings.append("Gmail draft creation failed; Notion row still written.")
            fields_skipped.append("gmail_draft")
    else:
        fields_skipped.append("gmail_draft")

    fields_skipped.append("booking_id_property")
    warnings.append(
        "Source set to Other; add Calendly + Formspree options to Source select to track channel."
    )

    next_action_text = (
        f"Review Gmail draft: {gmail_url}" if gmail_url else "Send welcome email"
    )
    notes_text = _build_research_summary(brief, payload.booking_id)

    client = NotionClient(secret=notion_secret)

    existing = None
    try:
        existing = _find_existing_row(client, database_id, payload.email)
    except Exception as exc:
        logger.warning(f"Pipeline query failed: {exc}")
        warnings.append(f"Could not query existing row: {exc}")

    if existing:
        notion_page_id = existing["id"]
        current = _current_status(existing)
        status_to_write = "Call Booked" if current in _BUMP_STATUSES or current is None else None
        props = _build_properties(payload, brief, next_action_text, notes_text, status_to_write)
        try:
            client.update_page(notion_page_id, props)
            fields_written.extend([
                "Lead/Company", "Email", "Contact Name", "Next Action Date",
                "Notes", "Next Action", "URL (To link and rollup later)",
            ])
            if status_to_write:
                fields_written.append("Status")
        except Exception as exc:
            logger.warning(f"Pipeline update failed for {payload.email}: {exc}")
            warnings.append(f"Notion update failed: {exc}")
    else:
        props = _build_properties(payload, brief, next_action_text, notes_text, "Call Booked")
        children = _build_page_body_blocks(brief, draft, payload.booking_id)
        try:
            page = client.create_page(database_id, props, children=children)
            notion_page_id = page.get("id")
            fields_written.extend([
                "Lead/Company", "Email", "Contact Name", "Next Action Date",
                "Notes", "Next Action", "URL (To link and rollup later)",
                "Source", "Status",
            ])
        except Exception as exc:
            logger.warning(f"Pipeline create failed for {payload.email}: {exc}")
            warnings.append(f"Notion create failed: {exc}")

    notion_row_url = (
        f"https://www.notion.so/{notion_page_id.replace('-', '')}"
        if notion_page_id else None
    )
    return LogResult(
        notion_page_id=notion_page_id,
        notion_row_url=notion_row_url,
        gmail_draft_id=gmail_draft_id,
        gmail_draft_url=gmail_url,
        fields_written=fields_written,
        fields_skipped=fields_skipped,
        warnings=warnings,
    )
