"""Monday 12:00 MT newsletter drafting tick."""
from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime

import pytz

logger = logging.getLogger("agentsHQ.newsletter_anchor_tick")

TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")
CONTENT_BOARD_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
RICH_TEXT_CHUNK = 2000


def _now() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))


def _chat_id() -> str | None:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")


def send_message(chat_id: str, text: str) -> None:
    from notifier import send_message as _send_message

    _send_message(chat_id, text)


def send_message_with_buttons(chat_id: str, text: str, buttons: list[list[tuple[str, str]]]):
    from notifier import send_message_with_buttons as _send_message_with_buttons

    return _send_message_with_buttons(chat_id, text, buttons)


def _open_notion():
    from skills.forge_cli.notion_client import NotionClient

    secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
    return NotionClient(secret=secret)


def build_newsletter_crew(user_request: str, metadata: dict | None = None):
    from crews import build_newsletter_crew as _build_newsletter_crew

    return _build_newsletter_crew(user_request, metadata=metadata)


def start_task(crew_name: str, plan_summary: str):
    from episodic_memory import start_task as _start_task

    return _start_task(crew_name=crew_name, plan_summary=plan_summary)


def complete_task(outcome_id: int, result_summary: str | None = None, total_cost_usd: float = 0.0):
    from episodic_memory import complete_task as _complete_task

    return _complete_task(
        outcome_id=outcome_id,
        result_summary=result_summary,
        total_cost_usd=total_cost_usd,
        llm_calls_ids=[],
    )


def _anchor_filter(week_iso: str) -> dict:
    return {
        "and": [
            {"property": "Anchor Date", "date": {"equals": week_iso}},
            {"property": "Type", "select": {"equals": "Newsletter"}},
        ]
    }


def _plain_text(prop: dict) -> str:
    parts = (prop or {}).get("rich_text") or (prop or {}).get("title") or []
    out: list[str] = []
    for part in parts:
        text = part.get("plain_text")
        if text is None:
            text = ((part.get("text") or {}).get("content")) or ""
        out.append(text)
    return "".join(out).strip()


def _title_text(page: dict) -> str:
    props = (page or {}).get("properties", {}) or {}
    return _plain_text(props.get("Title", {}))


def _rich_text_items(text: str) -> list[dict]:
    if not text:
        return []
    return [{"text": {"content": text[i:i + RICH_TEXT_CHUNK]}} for i in range(0, len(text), RICH_TEXT_CHUNK)]


def _find_anchor_page(notion, week_iso: str) -> dict | None:
    rows = notion.query_database(CONTENT_BOARD_DB_ID, filter_obj=_anchor_filter(week_iso)) or []
    if len(rows) > 1:
        logger.warning(
            "newsletter_anchor_tick: multiple anchors matched for %s; using first record %s",
            week_iso,
            rows[0].get("id"),
        )
    return rows[0] if rows else None


def _build_request(title: str, source_note: str, week_iso: str) -> str:
    request = [
        "CONTEXT: This is a professional business and AI governance newsletter. "
        "Any allegorical or narrative elements used are strictly for business metaphor "
        "and do not constitute self-harm or medical advice.",
        f"Write the Catalyst Works newsletter for Monday {week_iso}.",
        f"Anchor title: {title or 'Weekly newsletter anchor'}.",
    ]
    if source_note:
        request.append(f"Anchor context: {source_note}")
    request.append(
        "Return the full final newsletter draft with subject line, preview text, body, CTA, and Sources if needed."
    )
    return "\n".join(request)


def _approval_buttons(page_id: str, once: bool) -> list[list[tuple[str, str]]]:
    suffix = ":test" if once else ""
    return [[
        ("Approve", f"newsletter_approve:{page_id}{suffix}"),
        ("Revise", f"newsletter_revise:{page_id}{suffix}"),
    ]]


def _review_subject(title: str, once: bool) -> str:
    subject = f"Newsletter review: {title or 'Weekly newsletter anchor'}"
    return f"[TEST] {subject}" if once else subject


def newsletter_anchor_tick(once: bool = False) -> None:
    now = _now()
    if not once and now.weekday() != 0:
        logger.debug("newsletter_anchor_tick: not Monday, skipping")
        return

    chat_id = _chat_id()
    if not chat_id:
        logger.warning("newsletter_anchor_tick: no chat id configured, skipping")
        return

    week_iso = now.date().isoformat()
    outcome_id = None
    try:
        outcome = start_task("newsletter", f"Newsletter anchor tick for {week_iso} once={once}")
        outcome_id = outcome.id
    except Exception as e:
        logger.warning("newsletter_anchor_tick: start_task failed: %s", e)

    result_summary = "newsletter anchor tick incomplete"
    try:
        notion = _open_notion()
        anchor_page = _find_anchor_page(notion, week_iso)
        if not anchor_page:
            result_summary = f"no anchor for {week_iso}"
            send_message(chat_id, f"Newsletter anchor tick: no anchor found for {week_iso}.")
            return

        page_id = anchor_page.get("id", "")
        title = _title_text(anchor_page)
        source_note = _plain_text(((anchor_page.get("properties", {}) or {}).get("Source Note", {})))
        request = _build_request(title, source_note, week_iso)
        crew = build_newsletter_crew(
            request,
            metadata={
                "anchor_page_id": page_id,
                "anchor_date": week_iso,
                "anchor_title": title,
            },
        )
        result = str(crew.kickoff() or "").strip()
        notion.update_page(
            page_id,
            properties={"Draft": {"rich_text": _rich_text_items(result)}},
        )

        send_message_with_buttons(
            chat_id,
            f"{_review_subject(title, once)}\nAnchor: {title}\nPage: {page_id}",
            _approval_buttons(page_id, once),
        )
        result_summary = f"drafted newsletter for {page_id}"
    except Exception as e:
        result_summary = f"newsletter anchor tick failed: {e}"
        logger.warning("newsletter_anchor_tick: execution failed: %s", e)
        send_message(chat_id, f"Newsletter anchor tick failed for {week_iso}: {e}")
    finally:
        if outcome_id is not None:
            try:
                complete_task(outcome_id, result_summary=result_summary, total_cost_usd=0.0)
            except Exception as e:
                logger.warning("newsletter_anchor_tick: complete_task failed: %s", e)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Monday newsletter anchor tick.")
    parser.add_argument("--once", action="store_true", help="Run immediately, bypass Monday gate, and mark outputs as test.")
    args = parser.parse_args(argv)
    newsletter_anchor_tick(once=args.once)


if __name__ == "__main__":
    main()
