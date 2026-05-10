"""
content_connection_crew.py - Atlas M9d-C: Content Connection Finder

Reads last 30 days of content board, calls LLM to surface non-obvious
thematic connections, writes Connection Insight records to content board.

VPS cron: Monday 07:00 MT (13:00 UTC)
  0 13 * * 1 root cd /root/agentsHQ && docker exec orc-crewai python3 orchestrator/content_connection_crew.py >> /var/log/content_connection.log 2>&1

Success criterion: Boubacar acts on 1 suggestion within 7 days of first run.
"""
from __future__ import annotations

import logging
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ORCH_DIR = Path(__file__).resolve().parent
ROOT_DIR = ORCH_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger("agentsHQ.content_connection")

CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
CONNECTION_MODEL = "anthropic/claude-sonnet-4-6"
LOOKBACK_DAYS = 30
PUBLISHED_STATUSES = {"Published", "Scheduled", "Ready"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _title(prop: dict) -> str:
    """Extract plain text from a Notion title or rich_text property."""
    arr = prop.get("title") or prop.get("rich_text")
    if isinstance(arr, list) and arr:
        item = arr[0]
        return item.get("plain_text") or item.get("text", {}).get("content", "")
    return ""


def _select(prop: dict) -> str:
    """Extract name from a Notion select property."""
    sel = prop.get("select") if prop else None
    return sel.get("name", "") if sel else ""


# ---------------------------------------------------------------------------
# Core functions (testable, no I/O side effects)
# ---------------------------------------------------------------------------

def fetch_recent_content(notion, db_id: str, days: int = LOOKBACK_DAYS) -> list[dict]:
    """Fetch published/scheduled/ready content from last `days` days.

    Skips:
    - Records with Status not in PUBLISHED_STATUSES
    - Records with Type == "Connection Insight" (our own output)
    - Records whose Scheduled Date is older than `days` ago
    """
    posts = notion.query_database(db_id, filter_obj=None) or []
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    results = []
    for p in posts:
        props = p.get("properties", {})

        # Filter by status
        status = _select(props.get("Status", {}))
        if status not in PUBLISHED_STATUSES:
            continue

        # Skip our own Connection Insight records to avoid feedback loops
        type_val = _select(props.get("Type", {}))
        if type_val == "Connection Insight":
            continue

        # Date filter — only skip if a date exists AND it's before cutoff
        sched_prop = props.get("Scheduled Date", {})
        sched_date_obj = sched_prop.get("date") if sched_prop else None
        if isinstance(sched_date_obj, dict):
            sched_start = sched_date_obj.get("start", "")
            if sched_start and sched_start < cutoff:
                continue

        title = _title(props.get("Name", {}))
        if not title:
            continue

        results.append({
            "title": title,
            "platform": _select(props.get("Platform", {})),
            "status": status,
            "notion_id": p["id"],
        })
    return results


def build_connection_prompt(posts: list[dict], today: str) -> str:
    """Build the LLM prompt to surface non-obvious thematic connections."""
    post_lines = "\n".join(
        f"- [{p.get('platform', '')}] {p['title']}" for p in posts if p.get("title")
    )
    return f"""You are the agentsHQ content connection agent. Today is {today}.

Below are {len(posts)} recent content pieces (published, scheduled, or ready):

{post_lines}

Surface 3-5 non-obvious connections between these pieces that Boubacar could act on.

A non-obvious connection is one where:
- Two pieces address the same underlying problem from different angles
- Two pieces contain a productive contradiction worth exploring
- One piece provides evidence for or against a claim made in another
- A cross-platform angle exists that has not been written yet

Do NOT surface obvious connections (same topic, same platform, clearly related titles).

For each connection, write:

### Connection [N]: [short title]
**Pieces:** [piece A title] + [piece B title]
**Type:** [same problem | contradiction | cross-domain | evidence | cross-platform angle]
**Why it matters:** [one sentence]
**Content angle this creates:** [one sentence — what Boubacar could write next]

Only include connections that create a clear content opportunity."""


def parse_connections(llm_output: str) -> list[dict]:
    """Parse LLM output into list of connection dicts with title + body."""
    connections = []
    # Split on "### Connection N:" headers (N = any digit sequence)
    blocks = re.split(r"\n###\s+Connection\s+\d+:", "\n" + llm_output)
    for block in blocks[1:]:
        lines = block.strip().split("\n")
        title = lines[0].strip().lstrip(":").strip() if lines else "Connection"
        connections.append({"title": title, "body": block.strip()})
    return connections


def write_connections_to_notion(notion, connections: list[dict], today: str) -> None:
    """Write each connection as a new record in the content board.

    Creates records with:
    - Type = "Connection Insight"
    - Scheduled Date = today
    - Body in page content blocks
    """
    for conn in connections:
        properties = {
            "Name": {"title": [{"text": {"content": conn["title"][:100]}}]},
            "Type": {"select": {"name": "Connection Insight"}},
            "Scheduled Date": {"date": {"start": today}},
        }
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": conn["body"][:2000]},
                        }
                    ]
                },
            }
        ]
        notion.create_page(CONTENT_DB_ID, properties, children)
        logger.info("content_connection: created record: %s", conn["title"])


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(dry_run: bool = False) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    today = date.today().isoformat()

    notion_secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
    if not notion_secret:
        raise RuntimeError("NOTION_SECRET env var not set")

    from skills.forge_cli.notion_client import NotionClient
    notion = NotionClient(secret=notion_secret)

    logger.info("content_connection: fetching recent content (last %d days)", LOOKBACK_DAYS)
    posts = fetch_recent_content(notion, CONTENT_DB_ID)
    logger.info("content_connection: %d posts fetched", len(posts))

    if len(posts) < 3:
        logger.info("content_connection: fewer than 3 posts — skipping (need ≥3 to find connections)")
        return

    from llm_helpers import call_llm
    prompt = build_connection_prompt(posts, today)
    logger.info("content_connection: calling LLM (%s)", CONNECTION_MODEL)
    response = call_llm(
        messages=[{"role": "user", "content": prompt}],
        model=CONNECTION_MODEL,
        max_tokens=1200,
        temperature=0.5,
    )
    llm_output = response.choices[0].message.content.strip()
    connections = parse_connections(llm_output)
    logger.info("content_connection: %d connections parsed", len(connections))

    if dry_run:
        sys.stdout.buffer.write((llm_output + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
        return

    write_connections_to_notion(notion, connections, today)
    logger.info("content_connection: done — %d records written", len(connections))

    # Telegram notification (best-effort)
    try:
        from notifier import send_message
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if chat_id:
            send_message(
                chat_id,
                f"Content connections ready ({today}): {len(connections)} found. "
                "Check content board (Type=Connection Insight).",
            )
    except Exception as e:
        logger.debug("Telegram notify skipped: %s", e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Content Connection Finder — Atlas M9d-C")
    parser.add_argument("--dry-run", action="store_true", help="Print LLM output, skip Notion writes")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
