"""
dream_handler.py - Telegram-integrated memory consolidation (Dreams loop).

Flow:
  1. scripts/dream.py runs locally, scans memory, sends proposal to Telegram
     with ✅ Approve / ❌ Reject inline buttons + chat_id written to PENDING file
  2. Button tap → handle_dream_callback() in handlers_approvals.handle_callback_query
  3. _apply_decision() implements or discards the proposal

PENDING file (dream-output/.pending): stores chat_id so the VPS can apply
the decision even after a container restart. No in-memory window needed.

Wired into:
  - handlers_approvals.handle_callback_query  (dream: prefix)
  - handlers_commands._cmd_dream              (/dream status/apply/reject)
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("agentsHQ.dream_handler")

MEMORY_DIR = Path(os.environ.get(
    "MEMORY_DIR",
    r"C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory"
))
OUTPUT_DIR = MEMORY_DIR / "dream-output"
ARCHIVE_DIR = MEMORY_DIR / "dream-archive"
PROPOSAL_FILE = OUTPUT_DIR / "PROPOSAL.md"
PENDING_FILE = OUTPUT_DIR / ".pending"   # chat_id — survives container restart


def _send(chat_id: str, text: str) -> int | None:
    """Send plain text, return message_id."""
    import requests
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("ORCHESTRATOR_TELEGRAM_BOT_TOKEN not set")
        return None
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    last_id = None
    for chunk in chunks:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=10,
            )
            if r.ok:
                last_id = r.json().get("result", {}).get("message_id")
        except Exception as e:
            logger.error(f"dream _send failed: {e}")
    return last_id


def _send_with_buttons(chat_id: str, text: str) -> None:
    """Send proposal summary with ✅ Approve / ❌ Reject buttons."""
    from notifier import send_message_with_buttons
    send_message_with_buttons(
        chat_id,
        text,
        buttons=[[("✅ Approve", "dream:approve"), ("❌ Reject", "dream:reject")]],
    )


def _get_chat_id() -> str:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")


def has_pending_proposal() -> bool:
    return PROPOSAL_FILE.exists() and PENDING_FILE.exists()


def run_dream_async(chat_id: str, n_sessions: int = 30) -> None:
    """Instruct Boubacar to run the scan locally."""
    _send(
        chat_id,
        f"Run locally to start dream scan:\n\n"
        f"  python scripts/dream.py --sessions {n_sessions}\n\n"
        f"Proposal will arrive here with Approve/Reject buttons."
    )


def handle_dream_reply(text: str, chat_id: str, _first_word: str, reply_to_msg_id: int | None) -> bool:
    """
    Fallback: catch approve/reject as naked text when a pending proposal exists.
    Buttons are the primary path; this catches text replies as backup.
    """
    if not has_pending_proposal():
        return False

    text_lower = text.strip().lower()

    if text_lower.startswith("approve except"):
        rest = text[len("approve except"):].strip()
        excluded = {f.strip() for f in rest.split(",") if f.strip()}
        _apply_decision("APPROVE", excluded, chat_id)
        return True

    if text_lower == "approve":
        _apply_decision("APPROVE", set(), chat_id)
        return True

    if text_lower == "reject":
        _apply_decision("REJECT", set(), chat_id)
        return True

    return False


def _apply_decision(decision: str, excluded: set, chat_id: str) -> None:
    """Implement or discard the dream proposal based on decision."""
    if decision == "REJECT":
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
        _send(chat_id, "Dream rejected. Memory store unchanged. dream-output/ cleared.")
        return

    if not OUTPUT_DIR.exists() or not list(OUTPUT_DIR.glob("*.md")):
        _send(chat_id, "No dream output found to apply. Run /dream again.")
        return

    # Archive originals
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_archive = ARCHIVE_DIR / f"pre_dream_{ts}"
    session_archive.mkdir()

    archived = 0
    for p in MEMORY_DIR.glob("*.md"):
        if p.name in ("MEMORY_ARCHIVE.md",):
            continue
        shutil.copy2(p, session_archive / p.name)
        archived += 1

    # Apply proposed files
    applied = []
    skipped = []
    for src in OUTPUT_DIR.glob("*.md"):
        if src.name in ("PROPOSAL.md",):
            continue
        if src.name in excluded:
            skipped.append(src.name)
            continue
        if src.name.startswith("ARCHIVE_"):
            dest = ARCHIVE_DIR / src.name
        else:
            dest = MEMORY_DIR / src.name
        shutil.copy2(src, dest)
        applied.append(src.name)

    shutil.rmtree(OUTPUT_DIR)

    msg = f"Dream applied.\n{len(applied)} files updated, {archived} originals archived."
    if skipped:
        msg += f"\nSkipped (excluded): {', '.join(skipped)}"
    msg += "\nMemory store updated. New sessions will use consolidated memory."
    _send(chat_id, msg)
    logger.info(f"Dream applied: {len(applied)} files, excluded={excluded}")


def handle_dream_callback(cb_data: str, cb_id: str, chat_id: str) -> bool:
    """
    Handle dream:approve / dream:reject button taps from handle_callback_query.
    Returns True if handled.
    """
    from notifier import answer_callback_query
    if not cb_data.startswith("dream:"):
        return False

    action = cb_data.split(":", 1)[1]

    if action == "approve":
        answer_callback_query(cb_id, "Approving dream...")
        _apply_decision("APPROVE", set(), chat_id)
        return True

    if action == "reject":
        answer_callback_query(cb_id, "Dream rejected.")
        _apply_decision("REJECT", set(), chat_id)
        return True

    return False
