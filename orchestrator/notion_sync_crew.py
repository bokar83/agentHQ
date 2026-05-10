"""
notion_sync_crew.py - Atlas M9d Step 3: Nightly Notion sync

Pulls modified pages from Notion databases and UPSERTs them into the
memory table so /query can find them.

Designed to run via VPS cron: 02:00 daily
  0 2 * * * root cd /root/agentsHQ && docker exec orc-crewai python3 orchestrator/notion_sync_crew.py >> /var/log/notion_sync.log 2>&1

Databases synced:
  IDEAS_DB_ID     → category=idea rows
  NOTION_TASK_DB_ID → category=project_state rows (active tasks only)
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

ORCH_DIR = Path(__file__).resolve().parent
ROOT_DIR = ORCH_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger("agentsHQ.notion_sync")

IDEAS_DB_ID = os.environ.get("IDEAS_DB_ID", "")
TASK_DB_ID = os.environ.get("NOTION_TASK_DB_ID", "249bcf1a302980739c26c61cad212477")


def _extract_title(page: dict) -> str:
    props = page.get("properties", {})
    for key in ("Name", "Title", "Task"):
        prop = props.get(key, {})
        title_list = prop.get("title", [])
        if title_list:
            return title_list[0].get("text", {}).get("content", "")
    return ""


def _extract_select(page: dict, field: str) -> str:
    prop = page.get("properties", {}).get(field, {})
    sel = prop.get("select")
    return sel.get("name", "") if sel else ""


def _fetch_notion_pages(nc, db_id: str) -> list[dict]:
    return nc.query_database(db_id, filter_obj=None) or []


def _write_memory(model) -> int | None:
    from orchestrator.memory_store import write
    return write(model)


def sync_ideas(nc, db_id: str) -> int:
    """Sync Ideas DB pages → memory rows (category=idea). Returns count written."""
    count = 0
    try:
        pages = _fetch_notion_pages(nc, db_id)
        for page in pages:
            title = _extract_title(page)
            if not title:
                continue
            status = _extract_select(page, "Status")
            if status in ("Done", "Killed", "Archived"):
                continue
            pipeline = _extract_select(page, "Category") or "general"
            pipeline = pipeline.lower().replace(" ", "-")[:20]

            from orchestrator.memory_models import Idea
            model = Idea(
                title=title[:100],
                context=f"Synced from Notion Ideas DB. Status: {status or 'unknown'}",
                pipeline="general",
                priority="soon",
                source="notion",
                external_id=f"notion-idea-{page['id']}",
            )
            row_id = _write_memory(model)
            if row_id:
                count += 1
        logger.info(f"notion_sync: synced {count} ideas from Ideas DB")
    except Exception as e:
        logger.warning(f"notion_sync.sync_ideas failed (non-fatal): {e}")
    return count


def sync_tasks(nc, db_id: str) -> int:
    """Sync active Notion tasks → memory rows (category=project_state). Returns count written."""
    count = 0
    try:
        pages = _fetch_notion_pages(nc, db_id)
        for page in pages:
            title = _extract_title(page)
            if not title:
                continue
            status = _extract_select(page, "Status")
            if status in ("Done", "Cancelled", "Archived"):
                continue

            from orchestrator.memory_models import ProjectState
            try:
                model = ProjectState(
                    codename="general",
                    milestone="",
                    status="on-track",
                    last_action=f"Notion task: {title[:80]}",
                    next_action=f"Complete: {title[:80]}",
                    blockers="",
                    source="notion",
                    external_id=f"notion-task-{page['id']}",
                )
                row_id = _write_memory(model)
                if row_id:
                    count += 1
            except Exception:
                continue
        logger.info(f"notion_sync: synced {count} tasks from Task DB")
    except Exception as e:
        logger.warning(f"notion_sync.sync_tasks failed (non-fatal): {e}")
    return count


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    notion_secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
    if not notion_secret:
        logger.error("notion_sync: NOTION_SECRET not set, aborting")
        return

    from skills.forge_cli.notion_client import NotionClient
    nc = NotionClient(secret=notion_secret)

    total = 0
    if IDEAS_DB_ID:
        total += sync_ideas(nc, IDEAS_DB_ID)
    else:
        logger.warning("notion_sync: IDEAS_DB_ID not set, skipping ideas sync")

    total += sync_tasks(nc, TASK_DB_ID)

    logger.info(f"notion_sync: total {total} rows upserted")

    try:
        from notifier import send_message
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if chat_id and total > 0:
            send_message(chat_id, f"Notion sync complete: {total} memory rows updated.")
    except Exception as e:
        logger.debug(f"Telegram notify skipped: {e}")


if __name__ == "__main__":
    run()
