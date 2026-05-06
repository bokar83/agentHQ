"""
story_prompt_tick.py -- LéGroit storytelling prompt engine.

Fires on two triggers:
  1. Scheduled: Tuesday and Thursday at 08:00 MT (morning, before the day gets loud).
  2. Sparse queue: any heartbeat tick where Story-tagged Idea count < STORY_QUEUE_MIN.

Picks a random prompt from STORY_PROMPTS, sends via Telegram.
Never sends the same prompt twice in a row (tracks last_sent in memory).
Respects STORY_PROMPTS_ENABLED env var kill-switch.
"""
from __future__ import annotations

import logging
import os
import random
from datetime import datetime, date

import pytz

logger = logging.getLogger("agentsHQ.story_prompt_tick")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
STORY_QUEUE_MIN = int(os.environ.get("STORY_QUEUE_MIN", "5"))
CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")

STORY_PROMPTS = [
    # MOMENTS OF FRICTION
    "What happened this week that annoyed you but also confirmed something you already believed?",
    "Name a conversation you had recently where you said something you had not planned to say. What was it?",
    "When was the last time you were the only person in the room who saw something clearly but said nothing?",
    # ORIGIN WOUNDS
    "What is one thing you watched your parents do with money that you swore you would never do — and then did anyway?",
    "What is something you believed about success before you left West Africa that America quietly dismantled?",
    "There is a version of you from five years ago that would not recognize your current life. What would surprise him most?",
    # THE GAP BETWEEN PUBLIC AND PRIVATE
    "What are you telling clients to do right now that you have not fully done yourself?",
    "What does your calendar say about you that you would not want a client to see?",
    "What business decision are you sitting on right now that you already know the answer to but have not made yet?",
    # THE UTAH REALITY
    "Describe a moment in Utah where you felt completely out of place. What did you do with that feeling?",
    "What assumption did someone make about you in a professional setting recently that they would never have made in Dakar or Dubai?",
    "What does it cost you — practically, emotionally — to be building this firm here, in this place, right now?",
    # BUILDER HONESTY
    "What part of Catalyst Works is not working yet that you have not told anyone?",
    "What would you build differently if you were starting today with the same money but everything you know now?",
    "What is a service you offer that you secretly know is undersold — and one that you quietly know is not ready?",
    # THE LONG GAME
    "What are you building this for? Not the pitch answer. The 2am answer.",
    "Who are you trying to prove something to? Have you admitted that to yourself?",
    "What would it mean to you if Catalyst Works did not exist in three years? Be specific.",
    # SMALL MOMENTS, BIG SIGNAL
    "What is something small that happened this week that no one would write an article about, but that you have not stopped thinking about?",
    "Finish this sentence without editing yourself: Nobody talks about how hard it is to...",
]

_last_prompt: str | None = None


def _count_story_ideas(notion) -> int:
    """Count Content Board records with Status=Idea and Content Type=Story."""
    try:
        posts = notion.query_database(
            CONTENT_DB_ID,
            filter_obj={
                "and": [
                    {"property": "Status", "select": {"equals": "Idea"}},
                    {"property": "Content Type", "select": {"equals": "Story"}},
                ]
            },
        )
        return len(posts)
    except Exception as e:
        logger.warning(f"story_prompt: story idea count failed: {e}")
        return STORY_QUEUE_MIN  # fail-safe: assume queue is fine, don't spam


def _pick_prompt() -> str:
    global _last_prompt
    candidates = [p for p in STORY_PROMPTS if p != _last_prompt]
    chosen = random.choice(candidates)
    _last_prompt = chosen
    return chosen


def _send_prompt(prompt: str, reason: str) -> None:
    try:
        from notifier import send_message
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
        if not chat_id:
            logger.warning("story_prompt: no Telegram chat_id configured")
            return
        msg = (
            f"Story prompt ({reason}):\n\n"
            f"{prompt}\n\n"
            f"Reply with whatever comes to mind. Raw is better. "
            f"LéGroit will shape it into a post when you are ready."
        )
        send_message(str(chat_id), msg)
        logger.info(f"story_prompt: sent prompt [{prompt[:60]}...] reason={reason}")
    except Exception as e:
        logger.warning(f"story_prompt: Telegram send failed: {e}")


def story_prompt_scheduled_tick() -> None:
    """Fires on Tue/Thu schedule. Always sends a prompt."""
    if os.environ.get("STORY_PROMPTS_ENABLED", "1") == "0":
        return
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).strftime("%A")
    _send_prompt(_pick_prompt(), reason=f"scheduled {today}")


def story_prompt_sparse_tick() -> None:
    """Fires every heartbeat tick. Sends only if Story queue < STORY_QUEUE_MIN."""
    if os.environ.get("STORY_PROMPTS_ENABLED", "1") == "0":
        return
    try:
        from skills.forge_cli.notion_client import NotionClient
        notion = NotionClient(
            secret=(
                os.environ.get("NOTION_SECRET")
                or os.environ.get("NOTION_API_KEY")
                or os.environ.get("NOTION_TOKEN")
            )
        )
        count = _count_story_ideas(notion)
        if count < STORY_QUEUE_MIN:
            logger.info(f"story_prompt: Story queue sparse ({count} < {STORY_QUEUE_MIN}), sending prompt")
            _send_prompt(_pick_prompt(), reason=f"queue sparse ({count} ideas)")
        else:
            logger.debug(f"story_prompt: Story queue healthy ({count} ideas), skipping")
    except Exception as e:
        logger.warning(f"story_prompt: sparse check failed: {e}")
