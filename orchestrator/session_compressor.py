"""
session_compressor.py - Cross-session memory compressor (Atlas M9c).

Fires every 30 minutes via heartbeat. Finds sessions that went quiet
30-90 minutes ago and have not yet been summarized. Calls Haiku to produce
a 3-5 bullet summary and writes it to session_summaries. On the next
message, run_chat and run_atlas_chat silently inject the summary into the
system prompt.

Raw turns in agent_conversation_history are never deleted.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger("agentsHQ.session_compressor")

_SUMMARY_PROMPT = (
    "Summarize the following conversation in 3-5 concise bullet points. "
    "Focus on: decisions made, tasks completed, and any open items or next steps. "
    "Be specific -- include names, titles, or numbers where present. "
    "Do not include greetings or small talk. Output only the bullet list, nothing else."
)

_MIN_TURNS = 4


def find_sessions_to_compress() -> list[tuple[str, datetime]]:
    """
    Return sessions that are eligible for compression:
    - last_active_at between 30 and 90 minutes ago
    - no session_summaries row already covers this inactivity window
    """
    try:
        from db import get_local_connection
        conn = get_local_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.session_id, s.last_active_at
                FROM agent_sessions s
                WHERE s.last_active_at < NOW() - INTERVAL '30 minutes'
                  AND s.last_active_at > NOW() - INTERVAL '90 minutes'
                  AND NOT EXISTS (
                      SELECT 1 FROM session_summaries ss
                      WHERE ss.session_id = s.session_id
                        AND ss.created_at > s.last_active_at - INTERVAL '30 minutes'
                  )
            """)
            rows = cur.fetchall()
            cur.close()
            return [(row[0], row[1]) for row in (rows or [])]
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"find_sessions_to_compress failed: {e}")
        return []


def compress_session(session_id: str) -> bool:
    """
    Summarize the recent turns for session_id and write to session_summaries.
    Returns True if a summary was written, False if skipped or failed.
    """
    try:
        from memory import get_conversation_history
        turns = get_conversation_history(session_id, limit=100)
    except Exception as e:
        logger.warning(f"compress_session: history load failed for {session_id}: {e}")
        return False

    if not turns or len(turns) < _MIN_TURNS:
        logger.debug(f"compress_session: skipping {session_id} ({len(turns) if turns else 0} turns, min={_MIN_TURNS})")
        return False

    # Build conversation text for summarization
    lines = []
    last_ts = None
    for turn in reversed(turns):  # history comes back newest-first, reverse to chronological
        role = turn.get("role", "user")
        content = (turn.get("content") or "").strip()
        if content:
            lines.append(f"{role.upper()}: {content[:400]}")
        if turn.get("created_at"):
            last_ts = turn["created_at"]

    conversation_text = "\n\n".join(lines)
    window_end_at = last_ts or datetime.now(timezone.utc).isoformat()

    try:
        from llm_helpers import call_llm, HELPER_MODEL
        response = call_llm(
            messages=[
                {"role": "user", "content": f"{_SUMMARY_PROMPT}\n\n---\n\n{conversation_text}"}
            ],
            model=HELPER_MODEL,
            temperature=0.3,
        )
        summary = (response.choices[0].message.content or "").strip()
        if not summary:
            logger.warning(f"compress_session: empty summary returned for {session_id}")
            return False
    except Exception as e:
        logger.warning(f"compress_session: LLM call failed for {session_id}: {e}")
        return False

    try:
        from db import save_session_summary
        save_session_summary(
            session_id=session_id,
            summary=summary,
            turn_count=len(turns),
            window_end_at=str(window_end_at),
        )
        logger.info(f"session_compressor: compressed {len(turns)} turns for {session_id[:40]}")
        return True
    except Exception as e:
        logger.warning(f"compress_session: DB write failed for {session_id}: {e}")
        return False


def compressor_tick() -> None:
    """Heartbeat callback. Finds and compresses eligible sessions. Non-fatal per session."""
    logger.info("session_compressor: tick started")
    try:
        sessions = find_sessions_to_compress()
    except Exception as e:
        logger.error(f"session_compressor: find_sessions failed: {e}")
        return

    if not sessions:
        logger.debug("session_compressor: no sessions eligible for compression")
        return

    logger.info(f"session_compressor: {len(sessions)} session(s) to compress")
    compressed = 0
    for session_id, last_active_at in sessions:
        try:
            if compress_session(session_id):
                compressed += 1
        except Exception as e:
            logger.error(f"session_compressor: unexpected error on {session_id}: {e}")

    logger.info(f"session_compressor: tick done. {compressed}/{len(sessions)} compressed.")
