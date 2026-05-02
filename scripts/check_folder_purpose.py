"""Pre-commit hook: every top-level folder must have AGENTS.md or README.md.

Locked 2026-05-02 as part of Compass M0 governance scaffolding. Implements the
Folder Governance rule from docs/AGENT_SOP.md: no folder lives without a stated
purpose. Either AGENTS.md (rules-bearing folder) or README.md (workspace-style
folder) is required.

Behavior:
- Scans all top-level directories in the repo (depth 1 only).
- Skips gitignored directories, hidden directories, and known infrastructure
  directories that don't need governance docs (node_modules, .venv, .git, etc.).
- Skips submodules (their docs live in their own repo).
- For every remaining folder, checks for AGENTS.md or README.md.
- Reports every offender. Exits non-zero on any violation.
- Always runs (pass_filenames: false in pre-commit-config.yaml), so a fresh
  top-level folder gets caught before the commit lands.

Why this matters: Folder Governance was 32% enforced before this hook (8 of
25 top-level folders had AGENTS.md). Documents that govern without mechanism
decay. This hook converts the rule from aspirational to enforced.

See: docs/GOVERNANCE.md routing table; docs/AGENT_SOP.md Folder Governance
section; docs/roadmap/compass.md M0.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Folders that legitimately don't need a governance doc.
# Reasons documented inline so future agents don't re-add them blindly.
EXEMPT_DIRS = {
    ".git",                 # git internals
    ".github",              # standard GH location, conventions speak for themselves
    ".venv",                # Python virtualenv
    ".vscode",              # IDE
    ".windsurf",            # IDE
    ".claude",              # Claude Code worktrees + scheduled tasks
    ".agents",              # non-Claude agent skills
    ".superpowers",         # ephemeral brainstorm artifacts
    ".worktrees",           # git worktrees
    ".pytest_cache",        # pytest cache, regenerable
    ".pytest-tmp",          # pytest temp, regenerable
    ".pytest_tmp",          # pytest temp variant
    ".tmp",                 # pytest cache + antivirus quarantine
    "node_modules",         # JS deps
    "skills",               # has its own AGENTS.md and skills/_index.md (governance via _index)
    "pytest_tmp",           # pytest temp at root
    "pytest_tmp_work",      # pytest temp work
    "tools",                # external CLI binaries (autocli)
    "codex_ssh",            # Codex SSH working dir (gitignored, active tool)
    ".codex_ssh",           # hidden duplicate
    "secrets",              # gitignored, has README.md (good enough)
    "logs",                 # gitignored runtime logs
    "outputs",              # gitignored agent output sink (becoming agent_outputs)
    "agent_outputs",        # docker-compose live mount
    "tmp_upload",           # transcribe skill WORK_DIR (live mount)
    ".playwright-mcp",      # Playwright MCP runtime cache, regenerable
    "scratch",              # archived 2026-05-02; leftover empty folder, gitignored
    "Dashboards4Sale",      # extracts to satellite repo today; transient
    "zzzArchive",           # gitignored graveyard; AGENTS.md exists on disk but not tracked
    "output",               # submodule; AGENTS.md cannot live inside a submodule. Anatomy doc lives at docs/reference/output-folder-anatomy.md
}


def _is_submodule(path: Path, gitmodules_paths: set[str]) -> bool:
    """Return True if `path` is registered as a submodule in .gitmodules."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    return rel in gitmodules_paths


def _read_gitmodule_paths() -> set[str]:
    """Parse .gitmodules to find all registered submodule paths."""
    gitmodules = REPO_ROOT / ".gitmodules"
    if not gitmodules.exists():
        return set()
    paths: set[str] = set()
    for line in gitmodules.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("path") and "=" in line:
            paths.add(line.split("=", 1)[1].strip())
    return paths


def _force_utf8_stdout() -> None:
    """Avoid cp1252 crashes when printing offending lines."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def main() -> int:
    _force_utf8_stdout()
    submodule_paths = _read_gitmodule_paths()

    offenders: list[str] = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        if name in EXEMPT_DIRS:
            continue
        if _is_submodule(entry, submodule_paths):
            # Submodules govern themselves in their own repo.
            continue
        try:
            entries = {p.name for p in entry.iterdir()}
        except (PermissionError, OSError):
            # Skip permission-denied dirs (e.g. pytest_tmp variants on Windows).
            continue
        if "AGENTS.md" in entries or "README.md" in entries:
            continue
        offenders.append(name)

    if offenders:
        print("FAIL: top-level folders missing AGENTS.md or README.md:")
        for name in offenders:
            print(f"  - {name}/")
        print()
        print("Fix: add AGENTS.md (rules-bearing) or README.md (workspace) to each.")
        print("Reference: docs/GOVERNANCE.md + docs/AGENT_SOP.md Folder Governance.")
        print("Exempt list lives in scripts/check_folder_purpose.py if a folder genuinely doesn't need a doc.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
