"""
startup_check.py - Hard-fail guard for required env vars.

Called once at server startup (inside the @app.on_event("startup") handler).
Exits the process with code 1 before any request is served if a required var
is absent or empty.

Vars with code-level defaults (CHAT_TEMPERATURE, CHAT_SANDBOX, ATLAS_CHAT_MODEL)
are intentionally excluded -- hard-failing on them would create new failures
where none exist.
"""
import os
import sys

REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "OPENROUTER_API_KEY",
    "NOTION_API_KEY",
    "FORGE_CONTENT_DB",
    "BLOTATO_API_KEY",
    "CHAT_MODEL",
]


def assert_required_env_vars() -> None:
    missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
    if missing:
        print(
            f"[startup_check] FATAL: missing or empty required env vars: {missing}",
            flush=True,
        )
        sys.exit(1)
