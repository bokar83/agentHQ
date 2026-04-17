import os
import re
import logging
import threading
from typing import Optional

logger = logging.getLogger("agentsHQ.handlers_chat")

def _is_praise(text: str) -> bool:
    """Detect if the user is praising the output."""
    praise_patterns = [
        r"\b(great|awesome|excellent|perfect|good|nice|wow|amazing|thanks|thank you)\b",
        r"\b(good job|well done|love it|spot on|exactly what i needed)\b",
        r"👍|🚀|🔥|🙌"
    ]
    text_low = text.lower()
    return any(re.search(p, text_low) for p in praise_patterns)

def _is_feedback_on_prior_job(text: str, chat_id: str) -> bool:
    """Detect if the user is providing corrective feedback on the last job."""
    from state import _last_completed_job
    
    if chat_id not in _last_completed_job:
        return False
    
    negative_patterns = [
        r"\b(incorrect|wrong|not quite|error|mistake|fix|change|don't like|failure|broken)\b",
        r"\b(too long|too short|missing|wrong format)\b",
        r"👎|❌|⚠️"
    ]
    text_low = text.lower()
    return any(re.search(p, text_low) for p in negative_patterns)

def handle_feedback(text: str, chat_id: str):
    """Process user feedback and save to memory."""
    if os.environ.get("MEMORY_LEARNING_ENABLED", "false").lower() != "true":
        return
        
    from state import _last_completed_job
    from notifier import send_message
    
    if _is_praise(text) and chat_id in _last_completed_job:
        prior = _last_completed_job[chat_id]
        logger.info(f"Praise detected for job {prior['job_id']}")
        from memory import extract_and_save_learnings
        threading.Thread(
            target=extract_and_save_learnings,
            args=(prior["task_request"], prior["task_type"], prior["result_summary"], "preference"),
            daemon=True
        ).start()
        send_message(chat_id, "Got it — noted as a good pattern.")
        return True

    elif _is_feedback_on_prior_job(text, chat_id):
        prior = _last_completed_job[chat_id]
        logger.info(f"Critique detected for job {prior['job_id']}")
        from memory import extract_negative_lesson
        threading.Thread(
            target=extract_negative_lesson,
            args=(text, prior["task_type"], prior["result_summary"], chat_id),
            daemon=True
        ).start()
        send_message(chat_id, "Got it — I'll avoid that next time.")
        return True
    
    return False
