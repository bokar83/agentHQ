"""
switch_provider.py - Switch Claude Code / Codex CLI provider.

Usage:
    python switch_provider.py <provider> [--cli claude|codex|all] [--list]

providers.json lives alongside this script. $VAR values are resolved from env.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DEFAULT_PROVIDERS_PATH = SCRIPT_DIR / "providers.json"
DEFAULT_CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
DEFAULT_CODEX_CONFIG = Path.home() / ".codex" / "config.toml"


def _load_providers(providers_path: str) -> dict:
    with open(providers_path) as f:
        return json.load(f)


def _resolve_env_vars(d: dict) -> dict:
    """Recursively resolve $VAR strings in dict values from os.environ."""
    out = {}
    for k, v in d.items():
        if isinstance(v, str) and v.startswith("$"):
            var_name = v[1:]
            out[k] = os.environ.get(var_name, v)
        elif isinstance(v, dict):
            out[k] = _resolve_env_vars(v)
        else:
            out[k] = v
    return out


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically via temp file + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def switch_claude(
    provider_key: str,
    providers_path: str = str(DEFAULT_PROVIDERS_PATH),
    settings_path: str = str(DEFAULT_CLAUDE_SETTINGS),
) -> None:
    """Write provider config into ~/.claude/settings.json env block."""
    providers = _load_providers(providers_path)
    if provider_key not in providers:
        print(f"ERROR: unknown provider '{provider_key}'. Run --list to see options.", file=sys.stderr)
        sys.exit(1)

    provider = providers[provider_key]
    if "claude" not in provider:
        print(f"Provider '{provider_key}' has no claude config. Skipping.", file=sys.stderr)
        return

    claude_config = _resolve_env_vars(provider["claude"])

    p = Path(settings_path)
    existing: dict = {}
    if p.exists():
        try:
            existing = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    if "env" not in existing:
        existing["env"] = {}

    if not claude_config:
        existing["env"].pop("ANTHROPIC_BASE_URL", None)
        existing["env"].pop("ANTHROPIC_AUTH_TOKEN", None)
    else:
        existing["env"].update(claude_config)

    _atomic_write(p, json.dumps(existing, indent=2))
    label = provider.get("label", provider_key)
    base_url = claude_config.get("ANTHROPIC_BASE_URL", "official Anthropic")
    print(f"Switched Claude Code to {label} ({base_url})")
    if not claude_config:
        print("  ANTHROPIC_BASE_URL removed. Claude Code will use official Anthropic auth.")
    print("  Takes effect on next tool call (no restart needed).")


def switch_codex(
    provider_key: str,
    providers_path: str = str(DEFAULT_PROVIDERS_PATH),
    config_path: str = str(DEFAULT_CODEX_CONFIG),
) -> None:
    """Update model in ~/.codex/config.toml."""
    providers = _load_providers(providers_path)
    if provider_key not in providers:
        print(f"ERROR: unknown provider '{provider_key}'. Run --list to see options.", file=sys.stderr)
        sys.exit(1)

    provider = providers[provider_key]
    if "codex" not in provider:
        print(f"Provider '{provider_key}' has no codex config. Skipping Codex.", file=sys.stderr)
        return

    codex_config = _resolve_env_vars(provider["codex"])
    new_model = codex_config.get("model")
    if not new_model:
        print(f"Provider '{provider_key}' codex config has no 'model' key. Skipping.", file=sys.stderr)
        return

    p = Path(config_path)
    if p.exists():
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
    else:
        lines = []

    new_lines = []
    model_written = False
    for line in lines:
        if line.strip().startswith("model") and "=" in line:
            new_lines.append(f'model = "{new_model}"')
            model_written = True
        else:
            new_lines.append(line)
    if not model_written:
        new_lines.insert(0, f'model = "{new_model}"')

    _atomic_write(p, "\n".join(new_lines) + "\n")
    label = provider.get("label", provider_key)
    print(f"Switched Codex to {label} (model={new_model})")
    print("  Restart your terminal or Codex session for the change to take effect.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Switch Claude Code / Codex CLI provider."
    )
    parser.add_argument(
        "provider", nargs="?",
        help="Provider key from providers.json (e.g. openrouter, anthropic-official)"
    )
    parser.add_argument(
        "--cli", default="claude", choices=["claude", "codex", "all"],
        help="Which CLI to switch (default: claude)"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available providers and exit"
    )
    parser.add_argument(
        "--providers", default=str(DEFAULT_PROVIDERS_PATH),
        help="Path to providers.json (default: alongside this script)"
    )
    args = parser.parse_args()

    if args.list:
        providers = _load_providers(args.providers)
        print("Available providers:")
        for key, val in providers.items():
            print(f"  {key:25s}  {val.get('label', '')}")
        return

    if not args.provider:
        parser.error("provider argument required unless --list is used")

    if args.cli in ("claude", "all"):
        switch_claude(args.provider, args.providers)
    if args.cli in ("codex", "all"):
        switch_codex(args.provider, args.providers)


if __name__ == "__main__":
    main()
