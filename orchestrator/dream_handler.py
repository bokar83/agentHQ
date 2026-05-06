"""
dream_handler.py - Telegram-integrated memory consolidation (Dreams loop).

Flow:
  1. /dream command triggers run_dream_async() in a background thread
  2. Claude scans memory + git, produces PROPOSAL.md + dream-output/ files
  3. Proposal summary sent to Telegram with approve/reject instructions
  4. handle_dream_reply() intercepts Boubacar's reply (approve/reject/approve except X)
  5. apply_dream_decision() implements or discards the proposal

Wired into:
  - handlers_commands._cmd_dream  (step 1)
  - handlers.process_telegram_update step 4.6 (step 4)
"""

import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from state import _DREAM_WINDOWS

logger = logging.getLogger("agentsHQ.dream_handler")

MEMORY_DIR = Path(os.environ.get(
    "MEMORY_DIR",
    r"C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory"
))
OUTPUT_DIR = MEMORY_DIR / "dream-output"
ARCHIVE_DIR = MEMORY_DIR / "dream-archive"
PROPOSAL_FILE = OUTPUT_DIR / "PROPOSAL.md"
DREAM_WINDOW_TTL = 24 * 3600  # 24h


def _send(chat_id: str, text: str) -> int | None:
    """Send message, return telegram message_id (needed to register reply window)."""
    import requests
    token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("ORCHESTRATOR_TELEGRAM_BOT_TOKEN not set")
        return None
    # Truncate at 4096, split into chunks if needed
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    last_msg_id = None
    for chunk in chunks:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=10,
            )
            if resp.ok:
                last_msg_id = resp.json().get("result", {}).get("message_id")
        except Exception as e:
            logger.error(f"send failed: {e}")
    return last_msg_id


def _get_chat_id() -> str:
    return os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")


def run_dream_async(chat_id: str, n_sessions: int = 30) -> None:
    """
    Memory files live on the local machine, not the VPS container.
    Instruct Boubacar to run the scan locally — dream.py sends the
    proposal to Telegram directly once it completes.
    """
    _send(
        chat_id,
        f"To start a dream scan, run locally:\n\n"
        f"  python scripts/dream.py --sessions {n_sessions}\n\n"
        f"Claude will scan your memory store and send the proposal here.\n"
        f"You'll then reply approve / reject / approve except X, Y to this chat."
    )


def evict_expired_dream_windows() -> None:
    now = time.time()
    expired = [mid for mid, w in _DREAM_WINDOWS.items() if now - w["ts_sent"] > DREAM_WINDOW_TTL]
    for mid in expired:
        del _DREAM_WINDOWS[mid]


def handle_dream_reply(text: str, chat_id: str, _first_word: str, reply_to_msg_id: int | None) -> bool:
    """
    Check if this message is a reply to a pending dream proposal.
    Returns True if handled (caller should return early).
    """
    evict_expired_dream_windows()

    # Must be a reply to a registered dream message
    if reply_to_msg_id not in _DREAM_WINDOWS:
        return False

    window = _DREAM_WINDOWS[reply_to_msg_id]
    if window["chat_id"] != chat_id:
        return False

    # Parse decision
    text_lower = text.strip().lower()

    if text_lower.startswith("reject"):
        del _DREAM_WINDOWS[reply_to_msg_id]
        _apply_decision("REJECT", set(), chat_id)
        return True

    if text_lower.startswith("approve except"):
        rest = text[len("approve except"):].strip()
        excluded = {f.strip() for f in rest.split(",") if f.strip()}
        del _DREAM_WINDOWS[reply_to_msg_id]
        _apply_decision("APPROVE EXCEPT", excluded, chat_id)
        return True

    if text_lower.startswith("approve"):
        del _DREAM_WINDOWS[reply_to_msg_id]
        _apply_decision("APPROVE", set(), chat_id)
        return True

    # Not a dream decision word — ignore (don't consume the message)
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
