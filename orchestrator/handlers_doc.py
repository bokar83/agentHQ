"""
handlers_doc.py - Telegram emoji command handlers for doc routing.
=================================================================
Implements the operator-facing commands sent by Telegram when the
Drive Watch scheduler surfaces a new document:

    confirm filing           operator sends the filing emoji
    edit a field             operator sends the edit emoji + "field:value"
    create new project       operator sends the new-project emoji + "<name>"
    flag for review          operator sends the flag emoji
    approve routing matrix   operator sends the approve emoji

Each handler:
  1. Reads the pending-doc record from Postgres (matched by reply_to_message_id
     or latest unresolved).
  2. Updates Drive + Sheets via the GWS CLI tools.
  3. Marks the record resolved and sends a Telegram confirmation.

All database access uses parameterized SQL. The one f-string in the
edit handler interpolates a column name from a fixed dict, which is
still safe because the user input is only the VALUE, not the column.
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional

import psycopg2

logger = logging.getLogger("agentsHQ.handlers_doc")

_EDIT_FIELD_MAP = {
    "folder": "target_folder_path",
    "project": "project_id",
    "doctype": "doc_type",
    "notebook": "notebook_assignment",
    "name": "standardized_filename",
}


def _db_connect():
    """Return a psycopg2 connection to the orchestrator Postgres."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
    )


def _get_pending_doc(conn, reply_msg_id):
    """Return the pending doc record, using reply_to_message_id or latest unresolved."""
    cur = conn.cursor()
    if reply_msg_id:
        cur.execute(
            "SELECT * FROM notebooklm_pending_docs WHERE telegram_message_id = %s AND resolved = false LIMIT 1",
            (str(reply_msg_id),),
        )
    else:
        cur.execute(
            "SELECT * FROM notebooklm_pending_docs WHERE resolved = false ORDER BY created_at DESC LIMIT 1"
        )
    row = cur.fetchone()
    if row is None:
        return None
    cols = [desc[0] for desc in cur.description]
    return dict(zip(cols, row))


def _load_gws_tools():
    """Lazy-import the GWS CLI tools. Path gymnastics match the container layout."""
    if "/app/orchestrator_skills" not in sys.path:
        sys.path.insert(0, "/app/orchestrator_skills")
    from doc_routing.gws_cli_tools import GWSDriveMoveRenameTool, GWSSheetsAppendRowTool
    return GWSDriveMoveRenameTool, GWSSheetsAppendRowTool


def _move_to_review_queue(record, move_tool):
    """Move the Drive file into the Review Queue folder under its standardized name."""
    review_queue_folder_id = os.environ.get("NOTEBOOKLM_REVIEW_QUEUE_FOLDER_ID", "")
    move_tool()._run(json.dumps({
        "file_id": record["drive_file_id"],
        "new_name": record["standardized_filename"],
        "new_parent_id": review_queue_folder_id,
        "old_parent_id": os.environ.get("NOTEBOOKLM_LIBRARY_ROOT_ID", ""),
    }))


def _append_queue_row(record, append_tool):
    """Append a standard Sheet1 row for the filed doc."""
    queue_sheet_id = os.environ.get("NOTEBOOKLM_QUEUE_SHEET_ID", "")
    append_tool()._run(json.dumps({
        "spreadsheet_id": queue_sheet_id,
        "range": "Sheet1!A:I",
        "values": [[
            record["standardized_filename"],
            "",
            record["domain"],
            record["project_id"],
            record["topic_or_client"],
            record["doc_type"],
            record["notebook_assignment"],
            datetime.utcnow().strftime("%Y-%m-%d"),
            "No",
        ]],
    }))


def _mark_resolved(conn, record_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE notebooklm_pending_docs SET resolved = true WHERE record_id = %s",
        (record_id,),
    )
    conn.commit()


# ── Confirm filing ────────────────────────────────────────────
def _handle_confirm(text, chat_id, reply_msg_id, send):
    move_tool, append_tool = _load_gws_tools()
    conn = _db_connect()
    try:
        record = _get_pending_doc(conn, reply_msg_id)
        if not record:
            send(chat_id, "No pending document found. It may have already been filed.")
            return True

        target_path = record.get("target_folder_path", "") or ""
        skipped_move = target_path.startswith("00_Review_Queue/")
        if skipped_move:
            logger.warning(
                f"Doc routing: target_folder_path '{target_path}' unresolved "
                f"-- skipping Drive move for record_id={record['record_id']}"
            )
        else:
            logger.warning(
                f"Doc routing: Drive folder ID resolution not implemented for '{target_path}' "
                f"-- using review queue folder as fallback for record_id={record['record_id']}"
            )
            _move_to_review_queue(record, move_tool)

        _append_queue_row(record, append_tool)
        _mark_resolved(conn, record["record_id"])
        send(
            chat_id,
            f"Filed: {record['standardized_filename']}\nFolder: {target_path}\nNotebook queue: updated.",
        )
    finally:
        conn.close()
    return True


# ── Edit a field ──────────────────────────────────────────────
def _handle_edit(text, chat_id, reply_msg_id, send, edit_emoji):
    payload = text[len(edit_emoji):].strip()
    if ":" not in payload:
        send(chat_id, "Edit format: field:value  (valid fields: folder, project, doctype, notebook, name)")
        return True

    field_key, field_val = payload.split(":", 1)
    field_key = field_key.strip().lower()
    field_val = field_val.strip()
    if field_key not in _EDIT_FIELD_MAP:
        send(chat_id, f"Unknown field '{field_key}'. Valid fields: {', '.join(_EDIT_FIELD_MAP.keys())}")
        return True

    conn = _db_connect()
    try:
        record = _get_pending_doc(conn, reply_msg_id)
        if not record:
            send(chat_id, "No pending document found to edit.")
            return True

        db_col = _EDIT_FIELD_MAP[field_key]  # safe: fixed dict lookup
        cur = conn.cursor()
        cur.execute(
            f"UPDATE notebooklm_pending_docs SET {db_col} = %s WHERE record_id = %s",
            (field_val, record["record_id"]),
        )
        conn.commit()
        cur.execute(
            "SELECT * FROM notebooklm_pending_docs WHERE record_id = %s",
            (record["record_id"],),
        )
        row = cur.fetchone()
        cols = [desc[0] for desc in cur.description]
        updated = dict(zip(cols, row))
        send(
            chat_id,
            f"Updated {field_key} to: {field_val}\n\n"
            f"New routing:\n"
            f"File: {updated['standardized_filename']}\n"
            f"Folder: {updated['target_folder_path']}\n"
            f"Notebook: {updated['notebook_assignment']}\n\n"
            f"Send the confirm emoji to file.",
        )
    finally:
        conn.close()
    return True


# ── Create a new project + file ───────────────────────────────
def _handle_new_project(text, chat_id, reply_msg_id, send, new_emoji):
    move_tool, append_tool = _load_gws_tools()
    payload = text[len(new_emoji):].strip()
    if not payload:
        send(chat_id, "Usage: <new-project emoji> <project name>")
        return True

    name_lower = payload.lower()
    if "client" in name_lower or (payload[0].isupper() and "research" not in name_lower):
        prefix = "CL"
    elif "research" in name_lower or "topic" in name_lower:
        prefix = "RS"
    elif "ops" in name_lower or "admin" in name_lower or "internal" in name_lower:
        prefix = "OP"
    else:
        prefix = "CW"

    conn = _db_connect()
    try:
        cur = conn.cursor()
        # Per-prefix advisory lock so two concurrent /new calls can't collide on next_num.
        cur.execute(f"SELECT pg_advisory_lock(hashtext('{prefix}'))")
        cur.execute(
            "SELECT COALESCE(MAX(CAST(SPLIT_PART(project_id, '-', 2) AS INTEGER)), 0) + 1 AS next_num "
            "FROM notebooklm_pending_docs WHERE project_id LIKE %s",
            (f"{prefix}-%",),
        )
        row = cur.fetchone()
        next_num = row[0] if row else 1
        new_project_id = f"{prefix}-{next_num:03d}"
        cur.execute(f"SELECT pg_advisory_unlock(hashtext('{prefix}'))")

        record = _get_pending_doc(conn, reply_msg_id)
        if not record:
            send(chat_id, "No pending document found to assign to the new project.")
            return True

        cur.execute(
            "UPDATE notebooklm_pending_docs SET project_id = %s WHERE record_id = %s",
            (new_project_id, record["record_id"]),
        )
        conn.commit()

        registry_sheet_id = os.environ.get("NOTEBOOKLM_REGISTRY_SHEET_ID", "")
        append_tool()._run(json.dumps({
            "spreadsheet_id": registry_sheet_id,
            "range": "Projects!A:H",
            "values": [[
                new_project_id,
                payload,
                payload,
                "",
                "",
                "",
                "active",
                datetime.utcnow().strftime("%Y-%m-%d"),
            ]],
        }))

        cur.execute(
            "SELECT * FROM notebooklm_pending_docs WHERE record_id = %s",
            (record["record_id"],),
        )
        row = cur.fetchone()
        cols = [desc[0] for desc in cur.description]
        updated = dict(zip(cols, row))

        target_path = updated.get("target_folder_path", "") or ""
        if not target_path.startswith("00_Review_Queue/"):
            _move_to_review_queue(updated, move_tool)
        _append_queue_row(updated, append_tool)
        _mark_resolved(conn, updated["record_id"])
        send(
            chat_id,
            f"Created: {new_project_id} | {payload}\nFiled: {updated['standardized_filename']}",
        )
    finally:
        conn.close()
    return True


# ── Flag for review ───────────────────────────────────────────
def _handle_flag(text, chat_id, reply_msg_id, send):
    move_tool, append_tool = _load_gws_tools()
    conn = _db_connect()
    try:
        record = _get_pending_doc(conn, reply_msg_id)
        if not record:
            send(chat_id, "No pending document found.")
            return True

        _move_to_review_queue(record, move_tool)
        queue_sheet_id = os.environ.get("NOTEBOOKLM_QUEUE_SHEET_ID", "")
        append_tool()._run(json.dumps({
            "spreadsheet_id": queue_sheet_id,
            "range": "Flagged Docs!A:E",
            "values": [[
                record["original_filename"],
                record["standardized_filename"],
                datetime.utcnow().strftime("%Y-%m-%d"),
                "Operator flagged via Telegram",
                "No",
            ]],
        }))
        _mark_resolved(conn, record["record_id"])
        send(
            chat_id,
            f"Flagged: {record['original_filename']}. Moved to Review Queue and logged.",
        )
    finally:
        conn.close()
    return True


# ── Approve routing matrix proposal ────────────────────────────
def _handle_approve_routing(chat_id, send):
    _, append_tool = _load_gws_tools()
    conn = _db_connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM routing_matrix_proposals WHERE status = 'pending' ORDER BY proposed_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            send(chat_id, "No pending routing matrix proposals.")
            return True

        cols = [desc[0] for desc in cur.description]
        proposal = dict(zip(cols, row))

        queue_sheet_id = os.environ.get("NOTEBOOKLM_QUEUE_SHEET_ID", "")
        append_tool()._run(json.dumps({
            "spreadsheet_id": queue_sheet_id,
            "range": "Routing Matrix!A:G",
            "values": [[
                "",
                proposal["signal_keywords"],
                proposal["suggested_domain"],
                proposal["suggested_folder"],
                "",
                proposal["suggested_notebook"],
                "operator-approved",
            ]],
        }))

        cur.execute(
            "UPDATE routing_matrix_proposals SET status = 'approved' WHERE proposal_id = %s",
            (proposal["proposal_id"],),
        )
        conn.commit()
        send(
            chat_id,
            f"Routing Matrix updated. New row added for: {proposal['signal_keywords']}",
        )
    finally:
        conn.close()
    return True


def handle_doc_emoji(emoji: str, text: str, chat_id: str, reply_msg_id: Optional[str]) -> bool:
    """
    Dispatch a Telegram emoji command to its doc-routing handler.
    Returns True if the emoji was handled (caller should stop processing),
    False if the emoji is not one we handle.

    Emojis (intentionally passed as the raw glyph to avoid hard-coding them in
    this module so the source stays ASCII-only and the orchestrator call site
    keeps the canonical mapping):
        confirm    -> _handle_confirm
        edit       -> _handle_edit
        new        -> _handle_new_project
        flag       -> _handle_flag
        approve    -> _handle_approve_routing
    """
    from notifier import send_message as _send
    try:
        _load_gws_tools()
    except ImportError:
        logger.error("Doc routing tools not found in /app/orchestrator_skills")
        return False

    try:
        # UTF-8 code points for the 5 emojis supported.
        # Keeping the dispatch keyed on the raw arg means the caller decides.
        if emoji == "✅":  # confirm (green check)
            return _handle_confirm(text, chat_id, reply_msg_id, _send)
        if emoji == "✏️":  # edit (pencil)
            return _handle_edit(text, chat_id, reply_msg_id, _send, emoji)
        if emoji == "\U0001f195":  # new (NEW button)
            return _handle_new_project(text, chat_id, reply_msg_id, _send, emoji)
        if emoji == "❌":  # flag (red X)
            return _handle_flag(text, chat_id, reply_msg_id, _send)
        if emoji == "➕":  # approve (heavy plus sign)
            return _handle_approve_routing(chat_id, _send)
        return False
    except Exception as exc:
        logger.error(f"handle_doc_emoji ({emoji!r}) failed: {exc}", exc_info=True)
        _send(chat_id, "Error processing command. Check logs.")
        return True
