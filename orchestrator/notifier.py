"""
notifier.py — All Telegram Bot API calls for agentsHQ.
No other file sends Telegram messages.

Env vars required:
  TELEGRAM_BOT_TOKEN  — bot token from BotFather
  TELEGRAM_CHAT_ID    — your personal chat ID with the bot
"""
import os
import random
import logging
import requests

logger = logging.getLogger("agentsHQ.notifier")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

TASK_TYPE_LABELS = {
    "research_report":        "Research Agent is on the case 🔍",
    "consulting_deliverable": "Consulting Agent is building your deliverable 📋",
    "website_build":          "Web Builder Agent is coding your site 🌐",
    "app_build":              "App Builder Agent is on it 🛠️",
    "code_task":              "Code Agent is writing your solution 💻",
    "general_writing":        "Writing Agent is crafting your document ✍️",
    "social_content":         "Social Agent is creating your content 📱",
    "agent_team":             "The full team is on it 🚀",
    "chat":                   "...",
    "unknown":                "Agents are on it ⚙️",
}

SIMPSONS_QUOTES = [
    "It's taking forever... or is it just me? — Homer",
    "I am so smart! S-M-R-T. The agents are proving it right now. — Homer",
    "Mmm... deep research... — Homer",
    "Trying is the first step towards failure. Good thing your agents don't try — they DO. — Homer",
    "Don't have a cow — still chewing on it. — Bart",
    "Excellent... the plan is proceeding. — Mr. Burns",
    "In this house, we obey the laws of thermodynamics. Processing takes time. — Homer",
    "This is the greatest thing I've ever been asked to do. — Homer",
    "Why do they call it a shortcut when it never is? — Homer",
    "This better be worth it... it will be. — Homer",
    "I'm not normally a praying man, but if you're up there... speed up the agents. — Homer",
    "The key to happiness is not to ask questions. Also: wait for the ping. — Homer",
    "Remember: an idiot is anyone slower than me. These agents are not idiots. — Homer",
    "I've learned that life is one crushing defeat after another — until the deliverable arrives. — Homer",
    "Every time I try to leave, something pulls me back. Just like this research task. — Homer",
    "Ahhh, the agents are thinking. There's nothing more satisfying... except nachos. — Homer",
    "I can't promise I'll try, but I'll try to try. The agents promised more. — Homer",
    "Facts are meaningless. You can use facts to prove anything that's even remotely true. Like: your task is almost done. — Homer",
    "To alcohol! The cause of, and solution to, all of life's problems. To agents! — Homer",
    "The problem with being right is that nobody believes you until it's too late. Check back in 5 minutes. — Homer",
]

_last_quote_index: int = -1


def send_message(chat_id: str, text: str) -> None:
    """Send a plain text message to a Telegram chat. Truncates at 4096 chars."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping send_message")
        return
    if len(text) > 4096:
        text = text[:4090] + "\n[...]"
    try:
        resp = requests.post(
            f"{TELEGRAM_API_BASE}/sendMessage",
            json={"chat_id": str(chat_id), "text": text},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(f"Telegram sendMessage returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Telegram sendMessage failed: {e}")


def send_ack(chat_id: str, task_type: str) -> None:
    """Send immediate acknowledgement — fires within ~1s of receiving the task."""
    label = TASK_TYPE_LABELS.get(task_type, TASK_TYPE_LABELS["unknown"])
    send_message(chat_id, f"On it — {label}")


def send_progress_ping(chat_id: str) -> None:
    """Send a random Simpsons quote. Never repeats the same one consecutively."""
    global _last_quote_index
    available = [i for i in range(len(SIMPSONS_QUOTES)) if i != _last_quote_index]
    idx = random.choice(available)
    _last_quote_index = idx
    send_message(chat_id, SIMPSONS_QUOTES[idx])


def send_result(chat_id: str, summary: str, drive_url: str, github_url: str) -> None:
    """Send the final result with Drive and GitHub links."""
    parts = [summary]
    if drive_url:
        parts.append(f"\n📁 Drive: {drive_url}")
    if github_url:
        parts.append(f"📂 GitHub: {github_url}")
    send_message(chat_id, "\n".join(parts))
