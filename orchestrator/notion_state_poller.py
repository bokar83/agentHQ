"""Notion State Poller.

Heartbeat-driven 5-minute tick. Queries Notion Tasks DB for rows changed in
last 6 minutes, diffs against cached state, writes one changelog line per
detected change. Single writer of docs/audits/changelog.md.

Spec: docs/superpowers/specs/2026-05-02-task-poller-and-add-design.md
"""
from __future__ import annotations

import httpx
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_PATH = REPO_ROOT / "data" / "notion_state_cache.json"
DEFAULT_CHANGELOG_PATH = REPO_ROOT / "docs" / "audits" / "changelog.md"
DEFAULT_NOTION_TASK_DB_ID = "249bcf1a302980739c26c61cad212477"

WINDOW_MIN = 6
HARD_ROW_CAP = 200
HARD_TICK_SECONDS = 10
MAX_CHANGELOG_BYTES = 5 * 1024 * 1024

NOTION_VERSION = "2022-06-28"
HEAVY_VBAR = "┃"
TITLE_MAX = 60

TRACKED_PROPS = (
    "task_id", "title", "status", "p0",
    "sprint", "owner", "due_date", "blocked_by",
    "notes", "outcome",
)


def load_cache(path: Path) -> dict:
    """Load the state cache. Returns {'_meta': ..., 'rows': {...}}.

    If the file is missing or corrupted, returns empty cache and renames
    the corrupted file out of the way for forensics.
    """
    if not path.exists():
        return {"_meta": {"version": 1}, "rows": {}}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict) or "rows" not in data:
            raise ValueError("cache missing 'rows' key")
        return data
    except (json.JSONDecodeError, ValueError) as e:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        broken = path.with_suffix(f".json.broken-{ts}")
        path.rename(broken)
        logger.warning(f"notion_state_poller: corrupted cache renamed to {broken.name}; reason: {e}")
        return {"_meta": {"version": 1}, "rows": {}}


def save_cache(path: Path, state: dict) -> None:
    """Atomically save cache: write tmp, fsync, rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = json.dumps(state, indent=2, ensure_ascii=False)
    tmp.write_text(raw, encoding="utf-8")
    try:
        with open(tmp, "rb") as f:
            os.fsync(f.fileno())
    except (OSError, AttributeError):
        pass
    tmp.replace(path)


def _rich_text_plain(rich_text_list: list) -> str:
    if not rich_text_list:
        return ""
    return rich_text_list[0].get("plain_text", "")


def _multi_select_names(items: list) -> list:
    return [item.get("name", "") for item in items]


def extract_tracked_props(row: dict) -> dict:
    """Extract just the properties we track from a Notion row payload.

    Returns a flat dict keyed by snake_case property name.
    Missing/null Notion values become empty string, empty list, or None.
    """
    props = row.get("properties", {})

    title_arr = props.get("Task", {}).get("title", []) or []
    task_id_arr = props.get("Task ID", {}).get("rich_text", []) or []
    notes_arr = props.get("Notes", {}).get("rich_text", []) or []
    outcome_arr = props.get("Outcome", {}).get("rich_text", []) or []

    status_sel = props.get("Status", {}).get("select")
    status = status_sel.get("name", "") if status_sel else ""

    p0 = bool(props.get("P0", {}).get("checkbox", False))

    sprint_items = props.get("Sprint", {}).get("multi_select", []) or []
    owner_items = props.get("Owner", {}).get("multi_select", []) or []

    due_obj = props.get("Due Date", {}).get("date")
    due_date = due_obj.get("start") if due_obj else None

    blocked_items = props.get("Blocked By", {}).get("relation", []) or []
    blocked_by = [r.get("id", "") for r in blocked_items if r.get("id")]

    return {
        "task_id": _rich_text_plain(task_id_arr),
        "title": _rich_text_plain(title_arr),
        "status": status,
        "p0": p0,
        "sprint": _multi_select_names(sprint_items),
        "owner": _multi_select_names(owner_items),
        "due_date": due_date,
        "blocked_by": blocked_by,
        "notes": _rich_text_plain(notes_arr),
        "outcome": _rich_text_plain(outcome_arr),
    }


def _csv(items: list) -> str:
    return ", ".join(items)


def diff_row(cache: dict, current: dict) -> list:
    """Compare cached state vs current state. Return list of verb events.

    Each event is a dict {"verb": <str>, "desc": <str>}. Empty list = no change.
    A single edit can produce multiple events (one per changed property).
    """
    events: list = []

    if cache.get("status") != current.get("status"):
        old = cache.get("status") or ""
        new = current.get("status") or ""
        events.append({"verb": "status", "desc": f"{old or '(empty)'} -> {new or '(empty)'}"})

    if cache.get("p0") != current.get("p0"):
        old = "true" if cache.get("p0") else "false"
        new = "true" if current.get("p0") else "false"
        events.append({"verb": "p0", "desc": f"{old} -> {new}"})

    cache_sprint = set(cache.get("sprint") or [])
    cur_sprint = set(current.get("sprint") or [])
    if cache_sprint != cur_sprint:
        old_csv = _csv(sorted(cache_sprint))
        new_csv = _csv(sorted(cur_sprint))
        events.append({"verb": "sprint", "desc": f"[{old_csv}] -> [{new_csv}]"})
        if "Archive" in cur_sprint and "Archive" not in cache_sprint:
            events.append({"verb": "archived", "desc": "Sprint moved to Archive"})

    cache_owner = set(cache.get("owner") or [])
    cur_owner = set(current.get("owner") or [])
    if cache_owner != cur_owner:
        old_csv = _csv(sorted(cache_owner))
        new_csv = _csv(sorted(cur_owner))
        events.append({"verb": "owner", "desc": f"[{old_csv}] -> [{new_csv}]"})

    if cache.get("due_date") != current.get("due_date"):
        old = cache.get("due_date") or "none"
        new = current.get("due_date") or "none"
        events.append({"verb": "due", "desc": f"{old} -> {new}"})

    cache_blocked = set(cache.get("blocked_by") or [])
    cur_blocked = set(current.get("blocked_by") or [])
    added = cur_blocked - cache_blocked
    removed = cache_blocked - cur_blocked
    if added:
        events.append({"verb": "blocked", "desc": f"added: {', '.join(sorted(added))}"})
    if removed:
        events.append({"verb": "unblocked", "desc": f"removed: {', '.join(sorted(removed))}"})

    if cache.get("title") != current.get("title"):
        old = cache.get("title") or ""
        new = current.get("title") or ""
        events.append({"verb": "renamed", "desc": f'"{old}" -> "{new}"'})

    if cache.get("notes", "") != current.get("notes", ""):
        new_notes = current.get("notes", "") or ""
        if ":" in new_notes[:60]:
            prefix = new_notes.split(":", 1)[0].strip()
            if 1 <= len(prefix) <= 30:
                events.append({"verb": "notes", "desc": f"prefix: {prefix}"})
            else:
                events.append({"verb": "notes", "desc": "notes changed (no detail)"})
        elif not new_notes:
            events.append({"verb": "notes", "desc": "notes cleared"})
        else:
            events.append({"verb": "notes", "desc": "notes changed (no detail)"})

    if cache.get("outcome", "") != current.get("outcome", ""):
        new_outcome = current.get("outcome", "") or ""
        truncated = new_outcome if len(new_outcome) <= 60 else new_outcome[:57] + "..."
        events.append({"verb": "outcome", "desc": f'set: "{truncated}"'})

    return events


def format_changelog_line(
    timestamp: str,
    task_id: str,
    verb: str,
    title: str,
    desc: str,
) -> str:
    """Format one changelog line per the spec contract.

    Pipe characters in title and desc are replaced with U+2503 to keep the
    field separator unambiguous. Title is truncated to TITLE_MAX chars + "..."
    if longer.
    """
    title_safe = (title or "").replace("|", HEAVY_VBAR)
    desc_safe = (desc or "").replace("|", HEAVY_VBAR)
    if len(title_safe) > TITLE_MAX:
        title_safe = title_safe[:TITLE_MAX] + "..."
    return f'{timestamp} | {task_id} | {verb} | "{title_safe}" | {desc_safe}'


def append_changelog(path: Path, line: str) -> None:
    """Append a single line to the changelog file. Creates parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _notion_headers() -> dict:
    token = os.environ.get("NOTION_SECRET")
    if not token:
        raise RuntimeError("NOTION_SECRET not in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_recently_changed(database_id: str, since_iso: str) -> list:
    """Query Notion DB for rows last_edited_time >= since_iso. Paginates.

    Returns list of raw row payloads (caller calls extract_tracked_props).
    """
    headers = _notion_headers()
    rows: list = []
    cursor = None
    while True:
        body = {
            "filter": {
                "timestamp": "last_edited_time",
                "last_edited_time": {"on_or_after": since_iso},
            },
            "page_size": 100,
        }
        if cursor:
            body["start_cursor"] = cursor
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if len(rows) > HARD_ROW_CAP:
            logger.warning(
                f"notion_state_poller: row count {len(rows)} exceeds HARD_ROW_CAP={HARD_ROW_CAP}; truncating"
            )
            rows = rows[:HARD_ROW_CAP]
            break
    return rows


def query_all_active(database_id: str) -> list:
    """Backfill helper: query ALL rows where Status != Done. Paginates.

    Returns list of raw row payloads.
    """
    headers = _notion_headers()
    rows: list = []
    cursor = None
    while True:
        body = {
            "filter": {"property": "Status", "select": {"does_not_equal": "Done"}},
            "page_size": 100,
        }
        if cursor:
            body["start_cursor"] = cursor
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return rows


def main():
    """CLI entry: run one tick. Used by heartbeat callback."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    result = tick()
    print(f"notion_state_poller: {result}")


def _now_utc_iso() -> str:
    """ISO 8601 UTC with Z suffix, no fractional seconds."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _with_lock(fn):
    """Run `fn` inside the coordination lock. Returns fn's value, or None on conflict.

    Made a module-level function so tests can monkeypatch it cleanly.
    """
    try:
        from skills.coordination import lock as coord_lock
    except ImportError:
        return fn()
    holder = "notion-state-poller"
    ttl = 60
    try:
        with coord_lock("task:notion-state-poller", holder=holder, ttl_seconds=ttl):
            return fn()
    except Exception as e:
        logger.warning(f"notion_state_poller: lock conflict or error ({e}); skipping tick")
        return {"mode": "skipped", "reason": "lock"}


def tick(database_id: str | None = None) -> dict:
    """Run one poller tick. Returns a dict summary.

    Modes:
      - "backfill" on first run (cache missing), populates cache from all
        active rows, emits one `system | backfill` line, no per-row events.
      - "normal" on subsequent runs, queries time-windowed changes, emits
        one event per (row, changed_property).
      - "skipped" if the coordination lock is held by another tick.
    """
    return _with_lock(lambda: _tick_inner(database_id))


def _tick_inner(database_id: str | None) -> dict:
    db_id = database_id or os.environ.get("NOTION_TASK_DB_ID", DEFAULT_NOTION_TASK_DB_ID)
    cache_path = DEFAULT_CACHE_PATH
    log_path = DEFAULT_CHANGELOG_PATH

    cache = load_cache(cache_path)
    rows_in_cache = bool(cache.get("rows"))

    now_iso = _now_utc_iso()

    if not cache_path.exists():
        all_rows = query_all_active(db_id)
        new_rows: dict = {}
        for r in all_rows:
            page_id = r["id"]
            new_rows[page_id] = extract_tracked_props(r)
        cache["rows"] = new_rows
        cache["_meta"] = {
            "version": 1,
            "last_tick": now_iso,
            "last_full_scan": now_iso,
        }
        save_cache(cache_path, cache)
        line = format_changelog_line(
            timestamp=now_iso,
            task_id="system",
            verb="backfill",
            title="",
            desc=f"n={len(new_rows)} active rows",
        )
        append_changelog(log_path, line)
        return {"mode": "backfill", "rows_indexed": len(new_rows)}

    last_tick = cache.get("_meta", {}).get("last_tick", _now_utc_iso())
    try:
        last_tick_dt = datetime.fromisoformat(last_tick.replace("Z", "+00:00"))
    except ValueError:
        last_tick_dt = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MIN)
    since_dt = max(last_tick_dt - timedelta(minutes=1), datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MIN))
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    rows = query_recently_changed(db_id, since_iso)

    events_emitted = 0
    for row in rows:
        page_id = row["id"]
        current = extract_tracked_props(row)
        cached = cache["rows"].get(page_id)
        if cached is None:
            owner_csv = ", ".join(current.get("owner") or [])
            sprint_csv = ", ".join(current.get("sprint") or [])
            src_arr = row.get("properties", {}).get("Source", {}).get("rich_text", []) or []
            src_text = src_arr[0].get("plain_text", "") if src_arr else ""
            line = format_changelog_line(
                timestamp=now_iso,
                task_id=current.get("task_id") or "T-?????",
                verb="created",
                title=current.get("title") or "",
                desc=f'Owner={owner_csv} Sprint={sprint_csv} Source="{src_text}"',
            )
            append_changelog(log_path, line)
            events_emitted += 1
        else:
            for evt in diff_row(cached, current):
                line = format_changelog_line(
                    timestamp=now_iso,
                    task_id=current.get("task_id") or "T-?????",
                    verb=evt["verb"],
                    title=current.get("title") or "",
                    desc=evt["desc"],
                )
                append_changelog(log_path, line)
                events_emitted += 1
        cache["rows"][page_id] = current

    cache["_meta"]["last_tick"] = now_iso
    save_cache(cache_path, cache)
    return {"mode": "normal", "events_emitted": events_emitted}


if __name__ == "__main__":
    main()
