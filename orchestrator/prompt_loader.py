"""
prompt_loader.py - Load agent system prompts from disk at runtime.

Lookup order for agent_name "chat":
  1. /app/agents/chat/SYSTEM.md  (container path, editable without rebuild)
  2. AGENTS_DIR env var / {agent_name} / SYSTEM.md  (override path)
  3. fallback string passed by the caller

This lets Boubacar edit an agent's persona by editing a file on VPS
and reloading -- no code change, no container rebuild, no restart.

Usage:
    from prompt_loader import load_system_prompt

    prompt = load_system_prompt("chat", fallback=_SYSTEM_PROMPT)
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("agentsHQ.prompt_loader")

# Default base directory for agent SYSTEM.md files (inside the container)
_DEFAULT_AGENTS_DIR = "/app/agents"


def _agents_dir() -> str:
    return os.environ.get("AGENTS_DIR", _DEFAULT_AGENTS_DIR)


def get_system_md_path(agent_name: str) -> str:
    """Return the expected path for an agent's SYSTEM.md."""
    return os.path.join(_agents_dir(), agent_name, "SYSTEM.md")


def load_system_prompt(agent_name: str, fallback: Optional[str] = None) -> str:
    """
    Load the system prompt for agent_name.

    Checks DB config key SYSTEM_PROMPT_{AGENT_NAME} first (hot-swap via
    agent_config.set_config), then falls back to the SYSTEM.md file,
    then to the fallback string.

    Args:
        agent_name: Short identifier, e.g. "chat", "griot", "council".
        fallback: Hardcoded default prompt to use if no file or DB entry exists.

    Returns:
        The system prompt string (never empty if fallback is provided).
    """
    config_key = f"SYSTEM_PROMPT_{agent_name.upper()}"

    # Layer 1: DB config override (hot-swap without file edit)
    try:
        from agent_config import get_config
        db_val = get_config(config_key)
        if db_val:
            logger.debug(f"prompt_loader: loaded {agent_name} prompt from DB config")
            return db_val
    except Exception as e:
        logger.debug(f"prompt_loader: DB config lookup skipped: {e}")

    # Layer 2: SYSTEM.md file on disk
    path = get_system_md_path(agent_name)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
        if content:
            logger.info(f"prompt_loader: loaded {agent_name} prompt from {path}")
            return content
    except FileNotFoundError:
        logger.debug(f"prompt_loader: no SYSTEM.md at {path}, using fallback")
    except Exception as e:
        logger.warning(f"prompt_loader: error reading {path}: {e}")

    # Layer 3: hardcoded fallback
    return fallback or ""


def reload_prompt(agent_name: str, fallback: Optional[str] = None) -> str:
    """Alias for load_system_prompt -- signals intent to re-read from disk."""
    return load_system_prompt(agent_name, fallback=fallback)
