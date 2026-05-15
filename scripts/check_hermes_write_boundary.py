#!/usr/bin/env python3
"""Pre-commit hook: enforce Hermes write-boundary against CLAUDE.md M6 + M7.

No-op for human-authored commits. Gates Hermes-authored commits against
the ALLOWED + FORBIDDEN tables defined in CLAUDE.md (Compass M6 + M7).

Logic:
  - Identify Hermes by author email or name (case-insensitive prefix)
  - FORBIDDEN matches first (highest precedence)
  - ALLOWED check second; every staged file must match exactly one allow glob
  - Wildcard "*" path-glob ban in commit message body
  - Rate limit 3 Hermes auto-wires per 24h America/Denver from
    data/hermes_auto_wire_state.json (read-only; absorb_auto_wire crew
    increments after a successful push)

Stdlib only. Exit 0 on pass, 1 on violation.
"""

from __future__ import annotations

import datetime as _dt
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

HERMES_EMAILS = {"hermes@agentshq.local", "hermes-fix@agentshq.local"}
HERMES_NAME_PREFIX = "hermes"

# FORBIDDEN patterns. Order doesn't matter; any match -> reject.
FORBIDDEN = [
    "CLAUDE.md",
    "AGENTS.md",
    "docs/AGENT_SOP.md",
    "docs/GOVERNANCE.md",
    "docs/governance.manifest.json",
    ".claude/settings.json",
    ".vscode/settings.json",
    "config/settings.json",
    ".pre-commit-config.yaml",
    "scripts/*.py",
    "secrets/**",
    "secrets/*",
    ".env",
    ".env.*",
    "orchestrator/*.py",
    "orchestrator/**/*.py",
    "skills/coordination.py",
    # SKILL.md files in any skill directory
    "skills/*/SKILL.md",
    "skills/**/SKILL.md",
    # *.py anywhere in skills/
    "skills/*.py",
    "skills/**/*.py",
    # Per-skill scripts/ + evals/ subdirs
    "skills/*/scripts/**",
    "skills/*/scripts/*",
    "skills/**/scripts/**",
    "skills/*/evals/**",
    "skills/*/evals/*",
    "skills/**/evals/**",
    # JSON anywhere in skills/ (Phase 5 deferred)
    "skills/*.json",
    "skills/**/*.json",
]

# ALLOWED patterns. Every staged file must match >=1.
ALLOWED = [
    "agent_outputs/**",
    "agent_outputs/*",
    "workspace/**",
    "workspace/*",
    "docs/audits/**",
    "docs/audits/*",
    "data/changelog.md",
    "docs/roadmap/*.md",
    # Per-skill M7 allowlist
    "skills/ctq-social/references/*.md",
    "skills/ctq-social/patterns/*.md",
    "skills/client-intake/references/*.md",
    "skills/client-intake/patterns/*.md",
    "skills/library/references/*.md",
    "skills/library/patterns/*.md",
    "skills/boubacar-prompts/references/*.md",
    "skills/boubacar-prompts/patterns/*.md",
]

RATE_LIMIT_PER_DAY = 3
RATE_LIMIT_STATE = Path("data/hermes_auto_wire_state.json")

# Wildcard-glob ban: catches a literal star path inside common shell write ops.
# We search the commit message + body for these patterns.
WILDCARD_PATTERNS = [
    re.compile(r"\b(rm|mv|cp|chmod|chown)\s+[^\n]*\*"),
    re.compile(r"git\s+(add|rm)\s+[^\n]*\*"),
    re.compile(r">\s*\S*\*"),   # redirect into a wildcard
]


def _run(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return (res.stdout or "").strip()


def _is_hermes_author(email: str, name: str) -> bool:
    if email.lower() in HERMES_EMAILS:
        return True
    if name.lower().startswith(HERMES_NAME_PREFIX):
        return True
    return False


def _match_any(path: str, patterns: list[str]) -> str | None:
    norm = path.replace("\\", "/")
    for pat in patterns:
        if fnmatch.fnmatchcase(norm, pat):
            return pat
    return None


def _denver_today() -> str:
    # America/Denver: UTC-7 in summer (MDT), UTC-7/-6 split. Use stdlib zoneinfo if available;
    # fall back to a fixed-offset that's correct most of the year.
    try:
        from zoneinfo import ZoneInfo
        now = _dt.datetime.now(ZoneInfo("America/Denver"))
    except Exception:
        now = _dt.datetime.utcnow() - _dt.timedelta(hours=7)
    return now.strftime("%Y-%m-%d")


def _rate_limit_count(repo_root: Path) -> int:
    state_path = repo_root / RATE_LIMIT_STATE
    if not state_path.exists():
        return 0
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    return int(data.get(_denver_today(), 0))


def _staged_files() -> list[str]:
    out = _run(["git", "diff", "--cached", "--name-only"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _commit_message_for_check() -> str:
    # During a pre-commit hook, the prepared message lives in .git/COMMIT_EDITMSG.
    for candidate in (".git/COMMIT_EDITMSG", ".git/MERGE_MSG"):
        p = Path(candidate)
        if p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
    return ""


def _author_identity() -> tuple[str, str]:
    # Fall back to env GIT_AUTHOR_* during pre-commit (commit hasn't landed yet).
    import os
    email = os.environ.get("GIT_AUTHOR_EMAIL") or _run(["git", "config", "user.email"])
    name = os.environ.get("GIT_AUTHOR_NAME") or _run(["git", "config", "user.name"])
    # If HEAD exists, also check last commit (covers --amend + post-commit invocations).
    head_email = _run(["git", "log", "-1", "--format=%ae"])
    head_name = _run(["git", "log", "-1", "--format=%an"])
    # Prefer the prepared-author identity over HEAD (HEAD is the previous commit).
    return (email or head_email, name or head_name)


def main() -> int:
    repo_root = Path(_run(["git", "rev-parse", "--show-toplevel"]) or ".")
    email, name = _author_identity()
    if not _is_hermes_author(email, name):
        # Human commits: pass through silently.
        return 0

    files = _staged_files()
    if not files:
        print("hermes-boundary: no staged files; nothing to check")
        return 0

    # FORBIDDEN first.
    for f in files:
        hit = _match_any(f, FORBIDDEN)
        if hit:
            print(f"hermes-boundary: FORBIDDEN {f!r} (matched {hit!r})", file=sys.stderr)
            return 1

    # ALLOWED next.
    for f in files:
        hit = _match_any(f, ALLOWED)
        if not hit:
            print(
                f"hermes-boundary: not in ALLOWED {f!r}\n"
                f"  hint: Hermes may only write under agent_outputs/, workspace/, "
                f"docs/audits/, docs/roadmap/*.md, data/changelog.md, or the four "
                f"per-skill references/patterns dirs (ctq-social, client-intake, "
                f"library, boubacar-prompts).",
                file=sys.stderr,
            )
            return 1

    # Wildcard-glob ban in commit message.
    msg = _commit_message_for_check()
    for pat in WILDCARD_PATTERNS:
        m = pat.search(msg)
        if m:
            print(
                f"hermes-boundary: wildcard-glob ban triggered ({m.group(0)!r})",
                file=sys.stderr,
            )
            return 1

    # Rate limit check (read-only).
    count = _rate_limit_count(repo_root)
    if count >= RATE_LIMIT_PER_DAY:
        print(
            f"hermes-boundary: rate limit exceeded ({count}/{RATE_LIMIT_PER_DAY} "
            f"today); commit parked for human review",
            file=sys.stderr,
        )
        return 1

    print(
        f"hermes-boundary OK ({len(files)} files, today count "
        f"{count}/{RATE_LIMIT_PER_DAY})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
