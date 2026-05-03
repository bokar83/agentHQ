"""
classify_task.py - Classify incoming Claude Code message and switch provider.

Called as a UserPromptSubmit hook. Reads JSON from stdin, classifies the
prompt by task type, then calls switch_provider.py --quiet to switch.

Exit codes:
  0 - success (always; hook failures should not block Claude Code)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# Keywords that map to anthropic-official (design/creative/frontend)
ANTHROPIC_KEYWORDS = {
    "design", "creative", "writing", "brand", "copy", "logo", "font",
    "color", "colour", "palette", "landing page", "ui", "frontend",
    "visual", "layout", "style", "wireframe", "mockup", "hero", "banner",
    "email template", "illustration", "typography", "aesthetic", "branding",
    "figma", "canva", "graphic",
}

# Manual override phrases -> provider key
# "codex-suggest" is a special value: keep openrouter but log a suggestion
OVERRIDE_PATTERNS = [
    (["switch to anthropic", "use anthropic", "change to anthropic"], "anthropic-official"),
    (["switch to openrouter", "use openrouter", "change to openrouter"], "openrouter"),
    (["switch to therouter", "use therouter", "change to therouter"], "therouter"),
    (["switch to gemini", "use gemini", "change to gemini"], "openrouter"),
    (["switch to codex", "use codex", "change to codex"], "codex-suggest"),
]


def parse_prompt(stdin_text: str) -> str:
    """Extract prompt text from UserPromptSubmit hook JSON payload."""
    try:
        data = json.loads(stdin_text)
        return data.get("prompt", "")
    except (json.JSONDecodeError, AttributeError):
        return ""


def detect_override(text: str) -> str | None:
    """Return provider key if text contains a manual override phrase, else None."""
    lower = text.lower()
    for phrases, provider in OVERRIDE_PATTERNS:
        for phrase in phrases:
            if phrase in lower:
                return provider
    return None


def classify(text: str) -> str:
    """
    Classify text by task type. Override phrases take priority over keyword matching.
    Returns a provider key: 'anthropic-official', 'openrouter', or 'codex-suggest'.
    """
    override = detect_override(text)
    if override is not None:
        return override

    lower = text.lower()
    words = set(lower.replace(",", " ").replace(".", " ").split())
    for kw in ANTHROPIC_KEYWORDS:
        if " " in kw:
            if kw in lower:
                return "anthropic-official"
        elif kw in words:
            return "anthropic-official"

    return "openrouter"


def switch(provider_key: str) -> None:
    """Call switch_provider.py --quiet to apply the provider switch."""
    if provider_key == "codex-suggest":
        print(
            "[smart-router] Coding task detected. Consider opening Codex for this.",
            file=sys.stderr,
        )
        return

    script = SCRIPT_DIR / "switch_provider.py"
    try:
        subprocess.run(
            [sys.executable, str(script), provider_key, "--quiet"],
            check=False,
            timeout=5,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as e:
        print(f"[smart-router] switch failed (non-fatal): {e}", file=sys.stderr)


def main() -> None:
    stdin_text = sys.stdin.read()
    prompt = parse_prompt(stdin_text)
    if not prompt:
        sys.exit(0)

    provider = classify(prompt)
    switch(provider)
    sys.exit(0)


if __name__ == "__main__":
    main()
