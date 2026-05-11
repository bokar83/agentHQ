"""
handlers_approvals.py - Phase 1 approval-queue handlers for Telegram.

Three public entry points, called in order by handlers.process_telegram_update:

  handle_callback_query(update)
    -> True if this was an inline-button feedback_tag tap (eats the update).

  handle_pending_feedback_tag(text, chat_id, first_word, reply_to_msg_id)
    -> True if this message was consumed as a free-text tag for the most
       recently rejected proposal within the 5-min window. Evicts stale
       windows as a side effect. Must run BEFORE normal approval logic.

  handle_approval_reply(text, chat_id, first_word, reply_to_msg_id, now_epoch)
    -> True if this was a reply-to-proposal approve/reject/edit.

  handle_naked_approval(text, chat_id, first_word, reply_to_msg_id)
    -> True if this was a naked 'yes confirm' / 'no confirm' matched against
       the latest pending proposal, OR a disambiguating 'did you mean'
       prompt after a bare approve/reject word. Respects doc-routing
       precedence (Codex PR #10 / PR #11 findings).

State shared via state._PENDING_FEEDBACK_WINDOWS. Approval-queue access via
approval_queue module. DB connections closed in try/finally in every path
per the PR #11 P2 connection-hygiene fix.
"""
import logging
import os
import time
from html import escape as _html_escape
from datetime import date, datetime, timedelta

from newsletter_editorial_input import upsert_reply
from state import _PENDING_FEEDBACK_WINDOWS, _PUBLISH_BRIEF_WINDOWS

# Atlas M1: imports at module level so tests can patch
# handlers_approvals.<name>. Keep handlers_approvals.send_message symbol
# even when send_message is unused elsewhere in this module.
from notifier import send_message
from episodic_memory import start_task, complete_task

logger = logging.getLogger("agentsHQ.handlers_approvals")

APPROVE_ALIASES = {"yes", "yep", "yeah", "approve", "approved", "confirm", "ok"}
REJECT_ALIASES = {"no", "nope", "reject", "rejected", "not approved", "discard"}
POSTED_ALIASES = {"posted", "published", "done"}
SKIP_ALIASES = {"skip", "skipped", "pass"}


def _maybe_apply_mutation(qrow) -> None:
    """If qrow is a chairman weight-mutation proposal, call apply_mutation() to persist it."""
    if qrow is None:
        return
    if qrow.crew_name != "chairman" or qrow.proposal_type != "weight-mutation":
        return
    try:
        from chairman_crew import apply_mutation
        apply_mutation(qrow.id, qrow.payload or {})
    except Exception as e:
        logger.error(f"_maybe_apply_mutation: failed for queue #{qrow.id}: {e}")


def _build_button(label: str, callback_data: str) -> dict:
    """Build a Telegram inline-keyboard button dict. Asserts 64-byte callback_data limit."""
    assert len(callback_data.encode()) <= 64, f"callback_data too long: {callback_data!r}"
    return {"text": label, "callback_data": callback_data}

# Emoji prefixes that belong to the doc-routing handler. Used to make sure
# the 5-min tag window does not swallow an emoji command.
_DOC_EMOJI_PREFIXES = ("✅", "✏️", "🆕", "❌", "➕")
_TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")
_EDITORIAL_MIN_LEN = 8
_EDITORIAL_BLOCKED_FIRST_WORDS = APPROVE_ALIASES | REJECT_ALIASES | {
    "posted",
    "skip",
    "edited",
    "yes",
    "no",
    "confirm",
    "approve",
    "reject",
    "edit",
    "flag",
    "discard",
}


def _handle_scout_newsletter(notion_page_id: str, cb_id: str, cb_chat_id: str) -> None:
    from notifier import answer_callback_query, send_message

    notion = _open_notion()
    page = notion.get_page(notion_page_id)
    page_props = page.get("properties", {}) or {}
    current_type = ((page_props.get("Type", {}) or {}).get("select") or {}).get("name")
    if current_type and current_type != "Newsletter":
        answer_callback_query(cb_id, f"Already typed as {current_type}.")
        send_message(
            cb_chat_id,
            f"Content Scout: cannot set Newsletter anchor because this pick is already typed as {current_type}.",
        )
        return

    today_iso = _now_local().date().isoformat()
    notion.update_page(
        notion_page_id,
        properties={
            "Type": {"select": {"name": "Newsletter"}},
            "Platform": {"multi_select": [{"name": "Beehiiv"}]},
            "Anchor Date": {"date": {"start": today_iso}},
        },
    )

    content_db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
    previous_anchors = notion.query_database(
        content_db_id,
        filter_obj={
            "and": [
                {"property": "Anchor Date", "date": {"equals": today_iso}},
                {"property": "Type", "select": {"equals": "Newsletter"}},
            ]
        },
    )

    displaced_ids = []
    clear_props = {
        "Type": {"select": None},
        "Platform": {"multi_select": []},
        "Anchor Date": {"date": None},
    }
    for prev in previous_anchors or []:
        prev_id = prev.get("id")
        if not prev_id or prev_id == notion_page_id:
            continue
        notion.update_page(prev_id, properties=clear_props)
        displaced_ids.append(prev_id)

    answer_callback_query(cb_id, "Newsletter anchor updated.")
    message = f"Content Scout: Newsletter anchor set on {notion_page_id[:8]}... for {today_iso}."
    if displaced_ids:
        displaced_list = ", ".join(displaced_ids)
        message += f" Cleared previous anchor(s): {displaced_list}."
    send_message(cb_chat_id, message)


def _escape(text: str) -> str:
    return _html_escape(text or "", quote=True)


def _render_beehiiv_html(draft_text: str) -> str:
    lines = [line.strip() for line in (draft_text or "").splitlines()]
    body_lines: list[str] = []
    for line in lines:
        lowered = line.lower()
        if lowered.startswith("subject:") or lowered.startswith("preview text:") or lowered.startswith("preview:"):
            continue
        body_lines.append(line)

    paragraphs: list[str] = []
    current: list[str] = []
    for line in body_lines:
        if not line:
            if current:
                paragraphs.append("<p>%s</p>" % "<br>".join(_escape(part) for part in current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append("<p>%s</p>" % "<br>".join(_escape(part) for part in current))

    return "<html><body>%s</body></html>" % "".join(paragraphs or [f"<p>{_escape(draft_text or '')}</p>"])


def _handle_newsletter_approve(notion_page_id: str, cb_id: str, cb_chat_id: str, once: bool = False) -> None:
    from notifier import answer_callback_query, send_message
    from signal_works.gmail_draft import create_draft

    notion = _open_notion()
    page = notion.get_page(notion_page_id)
    page_props = page.get("properties", {}) or {}
    title = "".join(
        seg.get("plain_text") or ((seg.get("text") or {}).get("content")) or ""
        for seg in (page_props.get("Title", {}) or {}).get("title", [])
    ).strip()
    draft_text = "".join(
        seg.get("plain_text") or ((seg.get("text") or {}).get("content")) or ""
        for seg in (page_props.get("Draft", {}) or {}).get("rich_text", [])
    ).strip()
    if not draft_text:
        answer_callback_query(cb_id, "No Draft field content found.")
        send_message(cb_chat_id, f"Newsletter approve failed for {notion_page_id[:8]}... because Draft is empty.")
        return

    subject = title or "Weekly newsletter draft"
    for line in draft_text.splitlines():
        lowered = line.strip().lower()
        if lowered.startswith("subject:"):
            candidate = line.split(":", 1)[1].strip()
            if candidate:
                subject = candidate
            break
    if once:
        subject = f"[TEST] {subject}"

    review_email = os.environ.get("NEWSLETTER_REVIEW_EMAIL", "boubacar@catalystworks.consulting")
    gmail_draft_id = create_draft(review_email, subject, _render_beehiiv_html(draft_text))

    existing_source_note = "".join(
        seg.get("plain_text") or ((seg.get("text") or {}).get("content")) or ""
        for seg in (page_props.get("Source Note", {}) or {}).get("rich_text", [])
    ).strip()
    stamp = _now_local().strftime("%Y-%m-%d %H:%M %Z")
    audit_line = f"Approved {stamp}; Gmail draft {gmail_draft_id}"
    source_note_text = f"{existing_source_note}\n\n{audit_line}".strip() if existing_source_note else audit_line
    notion.update_page(
        notion_page_id,
        properties={
            "Source Note": {
                "rich_text": [{"text": {"content": source_note_text[i:i + 2000]}} for i in range(0, len(source_note_text), 2000)]
            }
        },
    )

    answer_callback_query(cb_id, "Newsletter Gmail draft created.")
    send_message(
        cb_chat_id,
        f"Newsletter approved: Gmail draft {gmail_draft_id} created to {review_email} with subject '{subject}'.",
    )


def _handle_newsletter_revise(notion_page_id: str, cb_id: str, cb_chat_id: str, once: bool = False) -> None:
    from notifier import answer_callback_query, send_message

    notion = _open_notion()
    notion.update_page(
        notion_page_id,
        properties={"Status": {"select": {"name": "Needs rework"}}},
    )
    answer_callback_query(cb_id, "Marked Needs rework.")
    prefix = "[TEST] " if once else ""
    send_message(
        cb_chat_id,
        f"{prefix}Newsletter revision requested for {notion_page_id[:8]}... Edit the Draft in Notion, then rerun the tick.",
    )


# ══════════════════════════════════════════════════════════════
# callback_query (inline-button feedback tag tap)
# ══════════════════════════════════════════════════════════════

def handle_callback_query(update: dict) -> bool:
    """
    Phase 1: callback_query (inline-button taps for rejection-feedback).
    Returns True if the update was a callback_query (handled or not - either
    way the update should not be processed further as a regular message).
    """
    if not update.get("callback_query"):
        return False
    cb = update["callback_query"]
    cb_data = cb.get("data", "")
    cb_chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
    cb_id = cb.get("id")
    cb_sender_id = str(cb.get("from", {}).get("id", ""))
    allowed_raw = os.environ.get("ALLOWED_USER_IDS", "")
    allowed_ids = {uid.strip() for uid in allowed_raw.split(",") if uid.strip()}
    if allowed_ids and cb_sender_id not in allowed_ids:
        return True
    if cb_data.startswith("feedback_tag:"):
        try:
            _, qid_str, tag = cb_data.split(":", 2)
            qid = int(qid_str)
            from approval_queue import set_feedback_tag
            from notifier import answer_callback_query, send_message
            if tag == "skip":
                answer_callback_query(cb_id, "Feedback skipped.")
            else:
                set_feedback_tag(qid, tag)
                answer_callback_query(cb_id, f"Tagged: {tag}")
                send_message(cb_chat_id, f"Queue #{qid}: feedback tag '{tag}' saved.")
            _PENDING_FEEDBACK_WINDOWS.pop(qid, None)
        except Exception as e:
            logger.warning(f"callback_query feedback_tag handling error: {e}")

    elif cb_data.startswith("approve_queue_item:"):
        try:
            qid = int(cb_data.split(":", 1)[1])
            from approval_queue import approve as _aq_approve, get as _aq_get
            from notifier import answer_callback_query, send_message
            qrow = _aq_get(qid)
            if qrow and qrow.status == "pending":
                _aq_approve(qid, note=None)
                _maybe_apply_mutation(qrow)
                answer_callback_query(cb_id, f"Approved #{qid}")
                send_message(cb_chat_id, f"Queue #{qid}: approved.")
            elif qrow:
                answer_callback_query(cb_id, f"Already {qrow.status}.")
            else:
                answer_callback_query(cb_id, "Queue item not found.")
        except Exception as e:
            logger.warning(f"callback_query approve_queue_item handling error: {e}")

    elif cb_data.startswith("enhance_queue_item:"):
        try:
            qid = int(cb_data.split(":", 1)[1])
            from approval_queue import get as _aq_get, _conn as _aq_conn
            from notifier import answer_callback_query, send_message
            qrow = _aq_get(qid)
            if qrow and qrow.status == "pending":
                # Mark enhancing immediately so griot won't re-pick this candidate
                conn = _aq_conn()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE approval_queue SET status='enhancing', decision_note='enhance-button-tapped',"
                    " boubacar_feedback_tag='enhance', ts_decided=now() WHERE id=%s AND status='pending'",
                    (qid,),
                )
                conn.commit()
                cur.close()
                answer_callback_query(cb_id, f"Enhancing #{qid}...")
                title = (qrow.payload or {}).get("title", f"queue #{qid}")
                send_message(cb_chat_id, f"Enhancing: {title}\nLeGriot is rewriting now (~30s)...")
                import threading
                threading.Thread(
                    target=_run_enhance_crew,
                    args=(qid, qrow, cb_chat_id),
                    daemon=True,
                ).start()
            elif qrow:
                answer_callback_query(cb_id, f"Already {qrow.status}.")
            else:
                answer_callback_query(cb_id, "Queue item not found.")
        except Exception as e:
            logger.warning(f"callback_query enhance_queue_item handling error: {e}")

    elif cb_data.startswith("reject_queue_item:"):
        try:
            qid = int(cb_data.split(":", 1)[1])
            from approval_queue import reject as _aq_reject, get as _aq_get
            from notifier import answer_callback_query, send_message, send_message_with_buttons
            qrow = _aq_get(qid)
            if qrow and qrow.status == "pending":
                _aq_reject(qid, note=None)
                answer_callback_query(cb_id, f"Rejected #{qid}")
                send_message(cb_chat_id, f"Queue #{qid}: rejected. Pick a reason below (or just type one):")
                buttons = [
                    [(t, f"feedback_tag:{qid}:{t}") for t in ("off-voice", "wrong-hook", "stale")],
                    [(t, f"feedback_tag:{qid}:{t}") for t in ("too-salesy", "other", "skip")],
                ]
                send_message_with_buttons(cb_chat_id, f"Tag for queue #{qid}?", buttons)
                _PENDING_FEEDBACK_WINDOWS[qid] = (cb_chat_id, time.time())
            elif qrow:
                answer_callback_query(cb_id, f"Already {qrow.status}.")
            else:
                answer_callback_query(cb_id, "Queue item not found.")
        except Exception as e:
            logger.warning(f"callback_query reject_queue_item handling error: {e}")

    elif cb_data.startswith("approve_variation:"):
        # approve_variation:<queue_id>:<variation_index>
        try:
            parts = cb_data.split(":", 2)
            qid, var_idx = int(parts[1]), int(parts[2])
            from approval_queue import get as _aq_get, approve as _aq_approve
            from notifier import answer_callback_query, send_message
            qrow = _aq_get(qid)
            if qrow and qrow.status == "enhancing":
                variations = (qrow.payload or {}).get("variations", [])
                if 1 <= var_idx <= len(variations):
                    chosen = variations[var_idx - 1]
                    notion_id = (qrow.payload or {}).get("notion_id")
                    if notion_id:
                        try:
                            from notion_client import Client as NotionClient
                            nc = NotionClient(auth=os.environ.get("NOTION_SECRET", ""))
                            nc.pages.update(
                                page_id=notion_id,
                                properties={"Draft": {"rich_text": [{"text": {"content": chosen}}]}},
                            )
                        except Exception as ne:
                            logger.warning(f"approve_variation: Notion write failed: {ne}")
                    _aq_approve(qid, note=f"variation {var_idx} chosen")
                    answer_callback_query(cb_id, f"Approved variation {var_idx}!")
                    send_message(cb_chat_id, f"Queue #{qid}: variation {var_idx} written to Notion and scheduled.")
                else:
                    answer_callback_query(cb_id, "Invalid variation.")
            elif qrow:
                answer_callback_query(cb_id, f"Already {qrow.status}.")
            else:
                answer_callback_query(cb_id, "Queue item not found.")
        except Exception as e:
            logger.warning(f"callback_query approve_variation handling error: {e}")

    elif cb_data.startswith("reject_variation:"):
        # reject_variation:<queue_id>:<variation_index>
        # Removes that one variation from the list. Does NOT reject the queue row.
        # If it was the last variation, marks row rejected so griot can re-propose.
        try:
            parts = cb_data.split(":", 2)
            qid, var_idx = int(parts[1]), int(parts[2])
            from approval_queue import get as _aq_get, reject as _aq_reject, _conn as _aq_conn
            from notifier import answer_callback_query, send_message
            import json as _json
            qrow = _aq_get(qid)
            if qrow and qrow.status == "enhancing":
                variations = list((qrow.payload or {}).get("variations", []))
                if 1 <= var_idx <= len(variations):
                    variations.pop(var_idx - 1)
                    if variations:
                        # Still have other variations, so just update the list.
                        conn = _aq_conn()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE approval_queue SET payload = payload || %s::jsonb WHERE id = %s",
                            (_json.dumps({"variations": variations}), qid),
                        )
                        conn.commit()
                        cur.close()
                        answer_callback_query(cb_id, f"Variation {var_idx} removed.")
                        send_message(cb_chat_id, f"Variation {var_idx} removed. {len(variations)} remaining.")
                    else:
                        # No variations left, so reject the row so griot can try again.
                        _aq_reject(qid, note="all variations dismissed", feedback_tag="enhance")
                        answer_callback_query(cb_id, "All variations dismissed.")
                        send_message(cb_chat_id, f"Queue #{qid}: all variations dismissed. Griot will propose a new candidate tomorrow.")
                else:
                    answer_callback_query(cb_id, "Invalid variation.")
            elif qrow:
                answer_callback_query(cb_id, f"Already {qrow.status}.")
            else:
                answer_callback_query(cb_id, "Queue item not found.")
        except Exception as e:
            logger.warning(f"callback_query reject_variation handling error: {e}")

    elif cb_data.startswith("enhance_variation:"):
        # enhance_variation:<queue_id>:<variation_index> re-runs the crew on this variation.
        try:
            parts = cb_data.split(":", 2)
            qid, var_idx = int(parts[1]), int(parts[2])
            from approval_queue import get as _aq_get
            from notifier import answer_callback_query, send_message
            qrow = _aq_get(qid)
            if qrow and qrow.status == "enhancing":
                variations = (qrow.payload or {}).get("variations", [])
                if 1 <= var_idx <= len(variations):
                    chosen_draft = variations[var_idx - 1]
                    # Build a synthetic qrow with the chosen variation as the draft
                    import types
                    synthetic = types.SimpleNamespace(
                        id=qid,
                        payload={**( qrow.payload or {}), "text": chosen_draft},
                    )
                    answer_callback_query(cb_id, f"Enhancing variation {var_idx}...")
                    send_message(cb_chat_id, f"Queue #{qid}: enhancing variation {var_idx} further (~30s)...")
                    import threading
                    threading.Thread(
                        target=_run_enhance_crew,
                        args=(qid, synthetic, cb_chat_id),
                        daemon=True,
                    ).start()
                else:
                    answer_callback_query(cb_id, "Invalid variation.")
            elif qrow:
                answer_callback_query(cb_id, f"Already {qrow.status}.")
            else:
                answer_callback_query(cb_id, "Queue item not found.")
        except Exception as e:
            logger.warning(f"callback_query enhance_variation handling error: {e}")

    elif cb_data.startswith("scout_approve:"):
        # scout_approve:<notion_page_id> flips Content Board Status to Multiply and starts multiplier now.
        try:
            notion_page_id = cb_data.split(":", 1)[1]
            from notifier import answer_callback_query, send_message
            notion = _open_notion()
            notion.update_page(notion_page_id, properties={
                "Status": {"select": {"name": "Multiply"}}
            })
            try:
                from content_multiplier_crew import multiply_source
            except ImportError:
                from orchestrator.content_multiplier_crew import multiply_source
            import threading
            threading.Thread(target=multiply_source, args=(notion_page_id,), daemon=True).start()
            answer_callback_query(cb_id, "Approved. Status set to Multiply.")
            send_message(cb_chat_id, f"Content Scout: approved. Notion page {notion_page_id[:8]}... queued for multiplication.")
        except Exception as e:
            logger.warning(f"callback_query scout_approve handling error: {e}")
            try:
                from notifier import answer_callback_query
                answer_callback_query(cb_id, f"Error: {e}")
            except Exception:
                pass

    elif cb_data.startswith("scout_reject:"):
        # scout_reject:<notion_page_id> flips Content Board Status from Draft to Archived.
        try:
            notion_page_id = cb_data.split(":", 1)[1]
            from notifier import answer_callback_query, send_message
            notion = _open_notion()
            notion.update_page(notion_page_id, properties={
                "Status": {"select": {"name": "Archived"}}
            })
            answer_callback_query(cb_id, "Rejected. Status set to Archived.")
            send_message(cb_chat_id, f"Content Scout: rejected. Notion page {notion_page_id[:8]}... archived.")
        except Exception as e:
            logger.warning(f"callback_query scout_reject handling error: {e}")
            try:
                from notifier import answer_callback_query
                answer_callback_query(cb_id, f"Error: {e}")
            except Exception:
                pass

    elif cb_data.startswith("scout_newsletter:"):
        try:
            notion_page_id = cb_data.split(":", 1)[1]
            _handle_scout_newsletter(notion_page_id, cb_id, cb_chat_id)
        except Exception as e:
            logger.warning(f"callback_query scout_newsletter handling error: {e}")
            try:
                from notifier import answer_callback_query
                answer_callback_query(cb_id, f"Error: {e}")
            except Exception:
                pass

    elif cb_data.startswith("newsletter_approve:"):
        try:
            parts = cb_data.split(":", 2)
            notion_page_id = parts[1]
            once = len(parts) > 2 and parts[2] == "test"
            _handle_newsletter_approve(notion_page_id, cb_id, cb_chat_id, once=once)
        except Exception as e:
            logger.warning(f"callback_query newsletter_approve handling error: {e}")
            try:
                from notifier import answer_callback_query
                answer_callback_query(cb_id, f"Error: {e}")
            except Exception:
                pass

    elif cb_data.startswith("newsletter_revise:"):
        try:
            parts = cb_data.split(":", 2)
            notion_page_id = parts[1]
            once = len(parts) > 2 and parts[2] == "test"
            _handle_newsletter_revise(notion_page_id, cb_id, cb_chat_id, once=once)
        except Exception as e:
            logger.warning(f"callback_query newsletter_revise handling error: {e}")
            try:
                from notifier import answer_callback_query
                answer_callback_query(cb_id, f"Error: {e}")
            except Exception:
                pass

    elif cb_data.startswith("dream:"):
        try:
            from dream_handler import handle_dream_callback
            handle_dream_callback(cb_data, cb_id, cb_chat_id)
        except Exception as e:
            logger.warning(f"callback_query dream handling error: {e}")

    elif cb_data.startswith("gate_approve:") or cb_data.startswith("gate_reject:"):
        try:
            import json as _json
            import pathlib
            from datetime import datetime, timezone
            from notifier import answer_callback_query, send_message
            action, branch = cb_data.split(":", 1)
            decision = "approve" if action == "gate_approve" else "reject"
            repo_root = pathlib.Path(os.environ.get("REPO_ROOT", "/app"))
            marker_dir = pathlib.Path(os.environ.get("GATE_DATA_DIR", str(repo_root / "data"))) / "gate_approvals"
            marker_dir.mkdir(parents=True, exist_ok=True)
            marker_name = branch.replace("/", "__") + f".{decision}.json"
            marker_path = marker_dir / marker_name
            marker_path.write_text(_json.dumps({
                "branch": branch,
                "decision": decision,
                "approved_by": cb_sender_id,
                "ts": datetime.now(timezone.utc).isoformat(),
            }, indent=2), encoding="utf-8")
            label = "Approved" if decision == "approve" else "Rejected"
            answer_callback_query(cb_id, f"{label}: {branch}")
            send_message(cb_chat_id, f"Gate {decision} queued for `{branch}`. Processes on next tick (~60s).")
        except Exception as e:
            logger.warning(f"callback_query gate_approve/reject handling error: {e}")
            try:
                from notifier import answer_callback_query
                answer_callback_query(cb_id, f"Error: {e}")
            except Exception:
                pass


    elif cb_data.startswith("multiplier_approve_all:"):
        try:
            run_id = cb_data.split(":", 1)[1]
            from notifier import answer_callback_query, send_message
            notion = _open_notion()
            db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
            pages = notion.query_database(db_id, filter_obj={"and": [{"property": "Multiplier Run ID", "rich_text": {"equals": run_id}}, {"property": "Status", "select": {"equals": "Idea"}}]})
            count = 0
            for page in pages or []:
                notion.update_page(page["id"], properties={"Status": {"select": {"name": "Ready"}}})
                count += 1
            answer_callback_query(cb_id, f"Approved {count} pieces.")
            send_message(cb_chat_id, f"Multiplier: approved {count} pieces for run {run_id[:8]}.")
        except Exception as e:
            logger.warning(f"callback_query multiplier_approve_all handling error: {e}")

    elif cb_data.startswith("multiplier_reject_all:"):
        try:
            run_id = cb_data.split(":", 1)[1]
            from notifier import answer_callback_query, send_message
            notion = _open_notion()
            db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
            pages = notion.query_database(db_id, filter_obj={"and": [{"property": "Multiplier Run ID", "rich_text": {"equals": run_id}}, {"property": "Status", "select": {"equals": "Idea"}}]})
            count = 0
            for page in pages or []:
                notion.update_page(page["id"], properties={"Status": {"select": {"name": "Archived"}}})
                count += 1
            answer_callback_query(cb_id, f"Rejected {count} pieces.")
            send_message(cb_chat_id, f"Multiplier: rejected {count} pieces for run {run_id[:8]}.")
        except Exception as e:
            logger.warning(f"callback_query multiplier_reject_all handling error: {e}")

    elif cb_data.startswith("multiplier_per_piece:"):
        try:
            run_id = cb_data.split(":", 1)[1]
            from notifier import answer_callback_query, send_message_with_buttons
            notion = _open_notion()
            db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
            pages = notion.query_database(db_id, filter_obj={"and": [{"property": "Multiplier Run ID", "rich_text": {"equals": run_id}}, {"property": "Status", "select": {"equals": "Idea"}}]})
            count = len(pages or [])
            for page in pages or []:
                page_id = page.get("id", "")
                props = page.get("properties", {}) or {}
                title = "".join(
                    seg.get("plain_text") or ((seg.get("text") or {}).get("content")) or ""
                    for seg in (props.get("Title", {}) or {}).get("title", [])
                ).strip() or page_id[:8]
                draft = "".join(
                    seg.get("plain_text") or ((seg.get("text") or {}).get("content")) or ""
                    for seg in (props.get("Draft", {}) or {}).get("rich_text", [])
                ).strip()
                if not draft:
                    for prop in props.values():
                        rich = (prop or {}).get("rich_text")
                        if rich:
                            draft = "".join(
                                seg.get("plain_text") or ((seg.get("text") or {}).get("content")) or ""
                                for seg in rich
                            ).strip()
                            if draft:
                                break
                msg = f"{title}\n\n{draft[:200]}"
                buttons = [[
                    ("Approve", f"multiplier_piece_approve:{page_id}"),
                    ("Reject", f"multiplier_piece_reject:{page_id}"),
                ]]
                send_message_with_buttons(cb_chat_id, msg, buttons)
            answer_callback_query(cb_id, f"Sending {count} pieces for review.")
        except Exception as e:
            logger.warning(f"callback_query multiplier_per_piece handling error: {e}")

    elif cb_data.startswith("multiplier_piece_approve:"):
        try:
            page_id = cb_data.split(":", 1)[1]
            from notifier import answer_callback_query, send_message
            notion = _open_notion()
            notion.update_page(page_id, properties={"Status": {"select": {"name": "Ready"}}})
            answer_callback_query(cb_id, "Piece approved.")
            send_message(cb_chat_id, f"Multiplier: approved piece {page_id[:8]}.")
        except Exception as e:
            logger.warning(f"callback_query multiplier_piece_approve handling error: {e}")

    elif cb_data.startswith("multiplier_piece_reject:"):
        try:
            page_id = cb_data.split(":", 1)[1]
            from notifier import answer_callback_query, send_message
            notion = _open_notion()
            notion.update_page(page_id, properties={"Status": {"select": {"name": "Archived"}}})
            answer_callback_query(cb_id, "Piece rejected.")
            send_message(cb_chat_id, f"Multiplier: rejected piece {page_id[:8]}.")
        except Exception as e:
            logger.warning(f"callback_query multiplier_piece_reject handling error: {e}")
    return True


# ══════════════════════════════════════════════════════════════
# Enhance crew runner (background thread)
# ══════════════════════════════════════════════════════════════

def _run_enhance_crew(qid: int, qrow, chat_id: str) -> None:
    """Run social crew on the queued post. Sends each variation as a separate
    Telegram message with Approve / Enhance / Reject buttons.

    Called in a daemon thread so Telegram is not blocked (~30-45s).
    'qrow' may be a real QueueRow or a SimpleNamespace with .id and .payload
    (used when enhancing a specific variation for a second pass).
    """
    from notifier import send_message, send_message_with_buttons
    from approval_queue import reject as _aq_reject, _conn as _aq_conn
    import json as _json
    import re

    payload = qrow.payload or {}
    title = payload.get("title", "")
    existing_draft = payload.get("text", "")
    platform = payload.get("platform", "X")

    request = (
        f"Rewrite and enhance this {platform} post for Boubacar Barry. "
        f"Topic: {title}. "
        f"Existing draft: {existing_draft if existing_draft else '(none)'}. "
        f"Produce 2-3 distinct variations. Each must be complete and ready to post verbatim. "
        f"Label each one exactly as: VARIATION 1:, VARIATION 2:, VARIATION 3:"
    )

    try:
        from engine import run_orchestrator
        result = run_orchestrator(
            task_request=request,
            session_key=f"enhance-{qid}",
            task_type_override="social_content",
        )
        raw = (result or {}).get("result", "") if isinstance(result, dict) else str(result or "")

        # Parse labelled variations; fall back to whole response as single variation
        parts = re.split(r"VARIATION\s+\d+\s*:\s*", raw, flags=re.IGNORECASE)
        variations = [p.strip() for p in parts if p.strip()][:3]
        if not variations:
            variations = [raw.strip()] if raw.strip() else []
        if not variations:
            raise ValueError("social crew returned empty output")

        # Store variations in payload for Approve/Enhance callbacks to retrieve
        conn = _aq_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE approval_queue SET payload = payload || %s::jsonb WHERE id = %s",
            (_json.dumps({"variations": variations}), qid),
        )
        conn.commit()
        cur.close()

        # Send each variation as its own message with Approve / Enhance / No
        # "No" removes only that variation; it does not touch the other variations or the row.
        send_message(chat_id, f"Queue #{qid}: {len(variations)} variation(s) ready.")
        for i, v in enumerate(variations, 1):
            msg = f"Variation {i} of {len(variations)}:\n\n{v}"
            buttons = [[
                ("Approve", f"approve_variation:{qid}:{i}"),
                ("Enhance", f"enhance_variation:{qid}:{i}"),
                ("No", f"reject_variation:{qid}:{i}"),
            ]]
            send_message_with_buttons(chat_id, msg, buttons)

    except Exception as e:
        logger.error(f"_run_enhance_crew #{qid} failed: {e}")
        try:
            _aq_reject(qid, note=f"enhance-crew-failed: {e}", feedback_tag="enhance")
            send_message(
                chat_id,
                f"Queue #{qid}: enhancement failed ({e}). "
                f"Marked rejected. Fix the Draft in Notion and it will re-enter the pool.",
            )
        except Exception as ne:
            logger.warning(f"_run_enhance_crew cleanup failed: {ne}")


# ══════════════════════════════════════════════════════════════
# 5-minute free-text tag window
# ══════════════════════════════════════════════════════════════

def evict_expired_windows() -> None:
    """Drop any feedback window older than 5 minutes. Caller invokes before the tag check."""
    now = time.time()
    expired = [qid for qid, (_cid, t0) in _PENDING_FEEDBACK_WINDOWS.items() if now - t0 > 300]
    for qid in expired:
        _PENDING_FEEDBACK_WINDOWS.pop(qid, None)


def handle_pending_feedback_tag(text: str, chat_id: str, first_word: str, reply_to_msg_id) -> bool:
    """
    Consume a free-text tag for the most recent rejection if a window is open
    FOR THIS CHAT. Must run BEFORE normal approval logic so text like 'stale'
    is treated as a tag, not as a new command. Council-fix guards: no slash,
    no emoji prefix, not an approve/reject alias, <=40 chars, not a reply.

    Codex PR #14 P2: scoped to chat_id so a tag from chat A cannot be applied
    to a queue item rejected from chat B.
    """
    if not _PENDING_FEEDBACK_WINDOWS or reply_to_msg_id:
        return False
    emoji_prefix = any(text.startswith(e) for e in _DOC_EMOJI_PREFIXES)
    if not (
        len(text) <= 40
        and not text.startswith("/")
        and first_word not in APPROVE_ALIASES
        and first_word not in REJECT_ALIASES
        and not emoji_prefix
    ):
        return False
    # Filter windows to those opened by THIS chat (Codex P2).
    chat_windows = {
        qid: ts for qid, (cid, ts) in _PENDING_FEEDBACK_WINDOWS.items() if cid == chat_id
    }
    if not chat_windows:
        return False
    # Most recently opened window for this chat.
    qid_target = max(chat_windows, key=lambda q: chat_windows[q])
    from approval_queue import normalize_feedback_tag, set_feedback_tag
    from notifier import send_message as _send
    tag = normalize_feedback_tag(text)
    set_feedback_tag(qid_target, tag)
    _send(chat_id, f"Queue #{qid_target}: feedback tag '{tag}' saved.")
    _PENDING_FEEDBACK_WINDOWS.pop(qid_target, None)
    return True


# ══════════════════════════════════════════════════════════════
# Reply-to-message approval path
# ══════════════════════════════════════════════════════════════

def handle_approval_reply(text: str, chat_id: str, first_word: str, reply_to_msg_id, now_epoch: float) -> bool:
    """
    Reply-to-message approve/reject/edit. Opens a 5-minute feedback window
    on reject. Returns True if the message was consumed by an approval action
    (or by an 'already decided' response).
    """
    is_edit = text.lower().startswith("edit:") or text.lower().startswith("edit ")
    if not reply_to_msg_id:
        return False
    if not (first_word in APPROVE_ALIASES or first_word in REJECT_ALIASES or is_edit):
        return False

    from approval_queue import (
        find_by_telegram_msg_id,
        approve as _aq_approve,
        reject as _aq_reject,
        edit as _aq_edit,
    )
    from notifier import send_message as _send, send_message_with_buttons

    qrow = find_by_telegram_msg_id(reply_to_msg_id)
    if qrow and qrow.status == "pending":
        if is_edit:
            new_body = text.split(":", 1)[1].strip() if ":" in text else text[5:].strip()
            new_payload = dict(qrow.payload) if qrow.payload else {}
            new_payload["body"] = new_body
            _aq_edit(qrow.id, new_payload, note=None)
            _send(chat_id, f"Queue #{qrow.id}: edited.")
            return True
        if first_word in APPROVE_ALIASES:
            _aq_approve(qrow.id, note=None)
            _maybe_apply_mutation(qrow)
            _send(chat_id, f"Queue #{qrow.id}: approved.")
            return True
        if first_word in REJECT_ALIASES:
            _aq_reject(qrow.id, note=None)
            _send(chat_id, f"Queue #{qrow.id}: rejected. Pick a reason below (or just type one):")
            buttons = [
                [(t, f"feedback_tag:{qrow.id}:{t}") for t in ("off-voice", "wrong-hook", "stale")],
                [(t, f"feedback_tag:{qrow.id}:{t}") for t in ("too-salesy", "other", "skip")],
            ]
            send_message_with_buttons(chat_id, f"Tag for queue #{qrow.id}?", buttons)
            _PENDING_FEEDBACK_WINDOWS[qrow.id] = (chat_id, now_epoch)
            return True
    elif qrow and qrow.status != "pending":
        _send(chat_id, f"Queue #{qrow.id}: already {qrow.status}.")
        return True
    return False


# ══════════════════════════════════════════════════════════════
# Naked approval fallback (no reply target)
# ══════════════════════════════════════════════════════════════

def _doc_routing_pending() -> bool:
    """
    Check whether a doc is pending operator attention. Close the connection
    in all paths per Codex PR #11 P2. Fail-open on any error (assume not
    pending; let queue fallback handle it).
    """
    try:
        from memory import _pg_conn
        c = _pg_conn()
        try:
            cur = c.cursor()
            try:
                cur.execute("SELECT 1 FROM notebooklm_pending_docs WHERE resolved = false LIMIT 1")
                return cur.fetchone() is not None
            finally:
                cur.close()
        finally:
            try:
                c.close()
            except Exception:
                pass
    except Exception:
        return False


def handle_naked_approval(text: str, chat_id: str, first_word: str, reply_to_msg_id) -> bool:
    """
    Bare 'yes confirm' / 'no confirm' against the latest pending proposal,
    OR a 'did you mean' disambiguation after a bare approve/reject word.

    Doc-routing precedence (Codex PR #10 / PR #11):
      Defer to the doc-routing emoji handler only when the user's first word
      is an approve-like word AND a doc is pending. Reject words always hit
      the queue fallback because doc-routing does not handle them.
    """
    if reply_to_msg_id:
        return False
    if not (first_word in APPROVE_ALIASES or first_word in REJECT_ALIASES):
        return False

    is_approve_word = first_word in APPROVE_ALIASES
    skip_fallback = is_approve_word and _doc_routing_pending()
    if skip_fallback:
        # Defer to the emoji/doc-routing path. Return False so caller can try it.
        return False

    from approval_queue import find_latest_pending, approve as _aq_approve, reject as _aq_reject
    from notifier import send_message as _send

    pending = find_latest_pending(max_age_hours=2)
    if pending is None:
        # Silent when nothing is pending; let normal chat flow continue.
        return False

    text_lower_full = text.strip().lower()
    if text_lower_full == "yes confirm":
        _aq_approve(pending.id, note=None)
        _maybe_apply_mutation(pending)
        _send(chat_id, f"Queue #{pending.id}: approved.")
        return True
    if text_lower_full == "no confirm":
        _aq_reject(pending.id, note=None)
        _send(chat_id, f"Queue #{pending.id}: rejected. Use /reject {pending.id} <tag> to add a reason.")
        return True
    if first_word in APPROVE_ALIASES:
        _send(chat_id, f"Did you mean queue #{pending.id} ({pending.crew_name} {pending.proposal_type})? Reply 'yes confirm' to approve.")
        return True
    if first_word in REJECT_ALIASES:
        _send(chat_id, f"Did you mean queue #{pending.id} ({pending.crew_name} {pending.proposal_type})? Reply 'no confirm' to reject.")
        return True
    return False


# ══════════════════════════════════════════════════════════════
# Atlas M1: publish-brief reply (Notion Status reconcile)
# ══════════════════════════════════════════════════════════════

def _open_notion():
    """Open a NotionClient using the orchestrator's NOTION_SECRET. Lazy
    import so test-time patching of handlers_approvals._open_notion can
    swap in a mock without loading the real client at module-import time.
    """
    from skills.forge_cli.notion_client import NotionClient
    secret = os.environ.get("NOTION_SECRET") or os.environ.get("NOTION_API_KEY")
    return NotionClient(secret=secret)


def handle_publish_reply(text: str, chat_id: str, first_word: str,
                         reply_to_msg_id) -> bool:
    """
    Reply 'posted' or 'skip' to a publish-brief per-post Telegram message.

    Reads _PUBLISH_BRIEF_WINDOWS for the dict entry keyed by reply_to_msg_id.
    Flips Notion Status to Posted or Skipped (read-before-write so an
    out-of-band flip is a no-op). Writes one task_outcomes row. Evicts the
    dict entry on success.

    Returns True if the update was consumed by this handler, False if it
    falls through to other handlers.

    Atlas M1; see docs/roadmap/atlas.md and
    docs/superpowers/specs/2026-04-25-atlas-m1-publish-reply-design.md.
    """
    if not reply_to_msg_id:
        return False

    fw = (first_word or "").lower()
    if fw not in POSTED_ALIASES and fw not in SKIP_ALIASES:
        return False

    entry = _PUBLISH_BRIEF_WINDOWS.get(reply_to_msg_id)
    if entry is None:
        return False

    page_id = entry["notion_page_id"]
    title = entry.get("title", "")
    target_status = "Posted" if fw in POSTED_ALIASES else "Skipped"
    action = "posted" if target_status == "Posted" else "skipped"

    # Layer 2 idempotency: read Notion first.
    try:
        notion = _open_notion()
        page = notion.get_page(page_id)
        current = (
            (page.get("properties", {}).get("Status", {}) or {})
            .get("select") or {}
        ).get("name")
    except Exception as e:
        logger.warning(f"handle_publish_reply: Notion read failed for {page_id}: {e}")
        send_message(chat_id, "Could not read Notion for this post. Try again or flip manually.")
        return True

    if current in ("Posted", "Skipped"):
        # Out-of-band flip already happened. Capture the no-op outcome and evict.
        try:
            out = start_task(crew_name="griot",
                             plan_summary=f"publish:{page_id}:noop_{action}")
            complete_task(out.id,
                          result_summary=f"Already {current} in Notion when reply arrived",
                          total_cost_usd=0.0,
                          llm_calls_ids=[])
        except Exception as e:
            logger.warning(f"handle_publish_reply: task_outcomes write failed: {e}")
        _PUBLISH_BRIEF_WINDOWS.pop(reply_to_msg_id, None)
        send_message(chat_id, f"Already marked {current} in Notion.")
        return True

    # Happy path: flip Notion, write outcome, evict.
    try:
        notion.update_page(page_id, properties={
            "Status": {"select": {"name": target_status}}
        })
    except Exception as e:
        logger.warning(f"handle_publish_reply: Notion update failed for {page_id}: {e}")
        send_message(chat_id, "Notion write failed. Flip manually for now.")
        return True

    try:
        out = start_task(crew_name="griot",
                         plan_summary=f"publish:{page_id}:{action}")
        complete_task(out.id,
                      result_summary=f"{action} via Telegram reply to msg {reply_to_msg_id}",
                      total_cost_usd=0.0,
                      llm_calls_ids=[])
    except Exception as e:
        logger.warning(f"handle_publish_reply: task_outcomes write failed: {e}")

    _PUBLISH_BRIEF_WINDOWS.pop(reply_to_msg_id, None)

    short_title = (title[:60] + "...") if len(title) > 60 else title
    send_message(chat_id, f"Marked {target_status}: {short_title}")
    return True


# ══════════════════════════════════════════════════════════════
# Newsletter editorial input capture
# ══════════════════════════════════════════════════════════════

def _now_local() -> datetime:
    import pytz

    return datetime.now(pytz.timezone(_TIMEZONE))


def _operator_chat_id() -> str | None:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")


def _editorial_window_active(now: datetime) -> bool:
    """True when the Sunday evening editorial capture window is open."""
    weekday = now.weekday()
    if weekday == 6 and now.hour >= 18:
        return True
    if weekday == 0 and now.hour < 6:
        return True
    return False


def _next_monday_date(now: datetime) -> date:
    """Return the Monday date this editorial reply should attach to."""
    if now.weekday() == 0:
        return now.date()
    return (now + timedelta(days=1)).date()


def handle_newsletter_editorial_reply(
    text: str, chat_id: str, first_word: str, reply_to_msg_id
) -> bool:
    """Capture free-text editorial input during the Sunday evening window."""
    if reply_to_msg_id:
        return False

    operator_chat_id = _operator_chat_id()
    if not operator_chat_id or chat_id != operator_chat_id:
        return False

    if first_word in _EDITORIAL_BLOCKED_FIRST_WORDS:
        return False

    if text.startswith("/"):
        return False

    cleaned_text = text.strip()
    if len(cleaned_text) < _EDITORIAL_MIN_LEN:
        return False

    now = _now_local()
    if not _editorial_window_active(now):
        return False

    target_monday = _next_monday_date(now)
    try:
        upsert_reply(target_monday, cleaned_text, chat_id)
    except Exception as e:
        logger.warning(f"handle_newsletter_editorial_reply: upsert failed: {e}")
        return False

    send_message(
        chat_id,
        f"Newsletter input captured for Monday {target_monday.isoformat()}. "
        f"Drafting Mon 12:00 MT.",
    )
    return True
