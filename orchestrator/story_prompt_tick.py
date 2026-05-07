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
from datetime import datetime

import pytz

logger = logging.getLogger("agentsHQ.story_prompt_tick")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")
STORY_QUEUE_MIN = int(os.environ.get("STORY_QUEUE_MIN", "5"))
CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")

# Each prompt is (question, channels) where channels is a list of tags.
# BB=Boubacar Personal, 1stGen=First Gen Money, UTB=Under the Baobab, AIC=AI Catalyst
STORY_PROMPTS = [
    # MOMENTS OF FRICTION
    ("What happened this week that annoyed you but also confirmed something you already believed?",
     ["BB", "AIC"]),
    ("Name a conversation you had recently where you said something you had not planned to say. What was it?",
     ["BB", "UTB"]),
    ("When was the last time you were the only person in the room who saw something clearly but said nothing?",
     ["BB", "AIC"]),
    # ORIGIN WOUNDS
    ("What is one thing you watched your parents do with money that you swore you would never do — and then did anyway?",
     ["1stGen", "UTB"]),
    ("What is something you believed about success before you left West Africa that America quietly dismantled?",
     ["UTB", "1stGen", "BB"]),
    ("There is a version of you from five years ago that would not recognize your current life. What would surprise him most?",
     ["BB", "UTB"]),
    # THE GAP BETWEEN PUBLIC AND PRIVATE
    ("What are you telling clients to do right now that you have not fully done yourself?",
     ["BB", "AIC"]),
    ("What does your calendar say about you that you would not want a client to see?",
     ["BB"]),
    ("What business decision are you sitting on right now that you already know the answer to but have not made yet?",
     ["BB", "1stGen"]),
    # THE UTAH REALITY
    ("Describe a moment in Utah where you felt completely out of place. What did you do with that feeling?",
     ["UTB", "BB"]),
    ("What assumption did someone make about you in a professional setting recently that they would never have made in Dakar or Dubai?",
     ["UTB", "BB"]),
    ("What does it cost you — practically, emotionally — to be building this firm here, in this place, right now?",
     ["BB", "UTB", "1stGen"]),
    # BUILDER HONESTY
    ("What part of Catalyst Works is not working yet that you have not told anyone?",
     ["BB"]),
    ("What would you build differently if you were starting today with the same money but everything you know now?",
     ["BB", "1stGen", "AIC"]),
    ("What is a service you offer that you secretly know is undersold — and one that you quietly know is not ready?",
     ["BB"]),
    # THE LONG GAME
    ("What are you building this for? Not the pitch answer. The 2am answer.",
     ["BB", "UTB", "1stGen"]),
    ("Who are you trying to prove something to? Have you admitted that to yourself?",
     ["BB", "UTB"]),
    ("What would it mean to you if Catalyst Works did not exist in three years? Be specific.",
     ["BB", "1stGen"]),
    # SMALL MOMENTS, BIG SIGNAL
    ("What is something small that happened this week that no one would write an article about, but that you have not stopped thinking about?",
     ["BB", "UTB", "AIC", "1stGen"]),
    ("Finish this sentence without editing yourself: Nobody talks about how hard it is to...",
     ["BB", "UTB", "1stGen"]),
]

CHANNEL_LABELS = {
    "BB":  "Boubacar Personal (LinkedIn + X)",
    "1stGen": "First Gen Money (X + IG + TikTok + YouTube)",
    "UTB": "Under the Baobab (X + IG + TikTok + YouTube)",
    "AIC": "AI Catalyst (X + IG + TikTok + YouTube)",
}

_last_prompt: str | None = None


def _count_story_ideas(notion) -> int:  # type: ignore[no-untyped-def]
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


def _pick_prompt() -> tuple:
    global _last_prompt
    candidates = [(q, c) for q, c in STORY_PROMPTS if q != _last_prompt]
    chosen_q, chosen_c = random.choice(candidates)
    _last_prompt = chosen_q
    return chosen_q, chosen_c


def _send_prompt(prompt: str, channels: list, reason: str) -> None:
    try:
        from notifier import send_message  # type: ignore[import]
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
        if not chat_id:
            logger.warning("story_prompt: no Telegram chat_id configured")
            return
        channel_hint = " | ".join(CHANNEL_LABELS[c] for c in channels if c in CHANNEL_LABELS)
        msg = (
            f"Story prompt:\n\n"
            f"{prompt}\n\n"
            f"Could feed: {channel_hint}\n\n"
            f"Reply with whatever comes to mind. Raw is better. "
            f"LéGroit saves it and suggests channel routing when you are ready to post."
        )
        send_message(str(chat_id), msg)
        logger.info(f"story_prompt: sent prompt [{prompt[:60]}...] reason={reason}")
    except Exception as e:
        logger.warning(f"story_prompt: Telegram send failed: {e}")


def story_prompt_scheduled_tick() -> None:
    """Fires daily at 17:00 MT but only sends on Tuesday (weekday=1) and Thursday (weekday=3)."""
    if os.environ.get("STORY_PROMPTS_ENABLED", "1") == "0":
        return
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    if now.weekday() not in (1, 3):  # 1=Tuesday, 3=Thursday
        logger.debug(f"story_prompt: skipping scheduled prompt on {now.strftime('%A')}")
        return
    prompt, channels = _pick_prompt()
    _send_prompt(prompt, channels, reason=f"scheduled {now.strftime('%A')}")


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
            prompt, channels = _pick_prompt()
            _send_prompt(prompt, channels, reason=f"queue sparse ({count} ideas)")
        else:
            logger.debug(f"story_prompt: Story queue healthy ({count} ideas), skipping")
    except Exception as e:
        logger.warning(f"story_prompt: sparse check failed: {e}")
