"""
session_logger.py — Claude Code Stop hook: cost logger + Telegram notification

Called by the Stop hook in ~/.claude/settings.json.

Environment variables provided by Claude Code Stop hook:
  CLAUDE_CODE_SESSION_ID  — session UUID
  CLAUDE_CODE_PROJECT_DIR — working directory for the session
  stdin                   — JSON blob with token counts and cost

Telegram credentials loaded from d:/Ai_Sandbox/agentsHQ/.env:
  ORCHESTRATOR_TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

LOG_FILE = Path("d:/Ai_Sandbox/agentsHQ/output/session_log.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

ENV_FILE = Path("d:/Ai_Sandbox/agentsHQ/.env")


def _load_env_file():
    """Load key=value pairs from .env into os.environ if not already set."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    try:
        import urllib.request
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass  # silent — hook must never block session close


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return

    try:
        usage = json.loads(raw)
    except json.JSONDecodeError:
        return

    _load_env_file()

    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "unknown")
    project_dir = os.environ.get("CLAUDE_CODE_PROJECT_DIR", "unknown")
    project_label = Path(project_dir).name if project_dir != "unknown" else "unknown"

    record = {
        "ts": datetime.now(UTC).isoformat(),
        "session_id": session_id[:8],
        "project": project_label,
        "cost_usd": usage.get("total_cost_usd", 0),
        "turns": usage.get("num_turns", 0),
        "duration_s": round(usage.get("duration_ms", 0) / 1000, 1),
        "input_tokens": usage.get("usage", {}).get("input_tokens", 0),
        "output_tokens": usage.get("usage", {}).get("output_tokens", 0),
        "cache_read": usage.get("usage", {}).get("cache_read_input_tokens", 0),
        "cache_create": usage.get("usage", {}).get("cache_creation_input_tokens", 0),
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    bot_token = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        cost = record["cost_usd"]
        turns = record["turns"]
        dur = record["duration_s"]
        msg = (
            f"🔴 Session ended\n"
            f"Project: {project_label}\n"
            f"ID: {session_id[:8]}\n"
            f"Cost: ${cost:.4f} | Turns: {turns} | {dur}s"
        )
        _send_telegram(bot_token, chat_id, msg)


if __name__ == "__main__":
    main()
