"""
startup_check.py - Hard-fail guard for required env vars.

Called once at server startup (inside the @app.on_event("startup") handler).
Exits the process with code 1 before any request is served if a required var
is absent or empty.

CHAT_MODEL and ATLAS_CHAT_MODEL are NOT in REQUIRED_VARS. They have
code-level defaults in llm_helpers (`os.environ.get(KEY) or _DEFAULT_MODEL`).
The post-import check below verifies that the resolved model slugs are
non-empty after default-coalescing, catching the failure mode where
docker-compose injects KEY="" and silently defeats the default.
"""
import os
import sys

REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "OPENROUTER_API_KEY",
    "NOTION_SECRET",
    "FORGE_CONTENT_DB",
    "BLOTATO_API_KEY",
]


def assert_required_env_vars() -> None:
    missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
    if missing:
        print(
            f"[startup_check] FATAL: missing or empty required env vars: {missing}",
            flush=True,
        )
        sys.exit(1)

    # Verify resolved chat-model slugs are non-empty after default-coalescing.
    # Catches the failure where compose substitutes ${CHAT_MODEL} to "" and
    # the OpenRouter call later returns 400 "No models provided".
    try:
        from llm_helpers import CHAT_MODEL, ATLAS_CHAT_MODEL, HELPER_MODEL
    except Exception:
        from orchestrator.llm_helpers import CHAT_MODEL, ATLAS_CHAT_MODEL, HELPER_MODEL  # type: ignore[no-redef]

    empty_models = [
        name for name, val in (
            ("CHAT_MODEL", CHAT_MODEL),
            ("ATLAS_CHAT_MODEL", ATLAS_CHAT_MODEL),
            ("HELPER_MODEL", HELPER_MODEL),
        ) if not val
    ]
    if empty_models:
        print(
            f"[startup_check] FATAL: resolved model slug is empty: {empty_models}. "
            f"Check llm_helpers default and docker-compose env passthrough.",
            flush=True,
        )
        sys.exit(1)
