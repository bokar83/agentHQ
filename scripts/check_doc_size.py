"""Pre-commit hook: warn when rule documents grow past their consolidation threshold.

Compass M2 enforcement layer. Documents that grow without a hard ceiling
silently become impossible to read, which makes them silently impossible to
enforce. This hook surfaces growth before it crosses the point of no return.

Per-file thresholds (lines):

    File                              Warn      Hard fail
    docs/GOVERNANCE.md                  70           85       (success-criteria cap is 80)
    docs/AGENT_SOP.md                  400          600
    docs/memory/MEMORY.md              195          220       (only first 200 lines load)
    docs/memory/*.md (other entries)   400          600
    **/AGENTS.md                       200          400

Roadmaps (`docs/roadmap/<codename>.md`) are intentionally NOT capped: a long
session log is a feature, not a bug.

Behavior:
- Receives changed file paths from pre-commit (default invocation).
- For each file, look up the matching threshold; emit a WARN for soft limits
  and FAIL for hard limits.
- Exit 1 only if any hard limit is crossed. Soft warnings exit 0.

Why this matters: GOVERNANCE.md was scoped at 64 lines; AGENT_SOP at 108;
MEMORY.md is at 205 today (5 over the loader cap). Without the hook, the
slow-creep pattern returns the moment a session forgets to consolidate.

See: docs/GOVERNANCE.md success criteria; docs/roadmap/compass.md M2
(doc-size hook); MEMORY.md WARNING note about 200-line truncation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (relative_path_or_glob, warn_lines, hard_lines).
# More-specific entries should appear earlier; the first match wins.
THRESHOLDS: list[tuple[str, int, int]] = [
    ("docs/GOVERNANCE.md",        70,   85),
    ("docs/AGENT_SOP.md",        400,  600),
    ("docs/memory/MEMORY.md",    195,  220),
    ("docs/memory/MEMORY_ARCHIVE.md", 600, 1200),
    ("docs/memory/*.md",         400,  600),
    ("**/AGENTS.md",             200,  400),
]

SKIP_DIRS = ("zzzArchive", ".git", "node_modules", ".venv", "external")

# AGENTS.md inside skill bundles is skill content, not folder governance.
# Skill payloads can legitimately be thousands of lines (Vercel react-best-practices,
# postgres-best-practices, etc.). The Folder Governance threshold only applies to
# folder-purpose AGENTS.md, not to skill-content AGENTS.md.
SKILL_PATH_PARTS = ("skills",)


def _force_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _match_threshold(rel: str) -> tuple[int, int] | None:
    rel_path = Path(rel)
    for pattern, warn, hard in THRESHOLDS:
        # Exact-path match.
        if pattern == rel:
            return warn, hard
        # Glob match (Path.match handles "**/AGENTS.md" and "docs/memory/*.md").
        if rel_path.match(pattern):
            return warn, hard
    return None


def _line_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def main(argv: list[str]) -> int:
    _force_utf8_stdout()
    strict = os.environ.get("DOC_SIZE_STRICT") == "1"

    warns: list[str] = []
    fails: list[str] = []

    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            continue
        try:
            rel = path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in Path(rel).parts):
            continue
        # Skip skill-content AGENTS.md (skills/<name>/AGENTS.md and skills/community/...)
        if Path(rel).name == "AGENTS.md" and Path(rel).parts and Path(rel).parts[0] in SKILL_PATH_PARTS:
            # Only skip when the AGENTS.md is at depth >= 3 (e.g. skills/<name>/AGENTS.md is depth 3).
            # The top-level skills/AGENTS.md (depth 2) IS folder governance; keep it under the cap.
            if len(Path(rel).parts) >= 3:
                continue
        thresh = _match_threshold(rel)
        if thresh is None:
            continue
        warn_lim, hard_lim = thresh
        n = _line_count(path)
        if n >= hard_lim:
            fails.append(f"{rel}: {n} lines >= hard limit {hard_lim}. Consolidate now.")
        elif n >= warn_lim:
            warns.append(f"{rel}: {n} lines >= soft limit {warn_lim} (hard {hard_lim}). Plan a consolidation pass.")

    if warns:
        print("\nWARN: doc-size hook flagged growth past soft limits:")
        for w in warns:
            print(f"  - {w}")

    if fails:
        print("\nFAIL: doc-size hook flagged hard-limit violations:")
        for f in fails:
            print(f"  - {f}")
        print()
        print("Fix: split the file, archive sections to zzzArchive/_consolidation-<date>/,")
        print("or move long-tail content into a topic-specific file. Roadmaps are exempt;")
        print("rule docs are not. See docs/GOVERNANCE.md success criteria.")
        return 1

    if warns and strict:
        # Strict mode upgrades warns to fails too.
        print("\nDOC_SIZE_STRICT=1 set; treating soft warnings as failures.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
