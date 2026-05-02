"""Surface rule-bearing files that have not been touched in N+ days.

Compass M2 enforcement layer. Complement to the M3 scheduled quarterly purge
agent. Where the M3 agent runs once a quarter and writes a full audit to
docs/audits/, this script is the on-demand version: any agent or human can
run it ad-hoc and get the same candidate list.

Scope: every file in the rule corpus.
- `docs/AGENT_SOP.md`
- `docs/GOVERNANCE.md`
- `docs/memory/*.md` (excluding MEMORY.md / MEMORY_ARCHIVE.md)
- every `AGENTS.md` at any depth (excluding zzzArchive/)

Behavior:
- For each corpus file, ask git when it was last touched: `git log -1 --format=%ct -- <file>`.
- If the last commit timestamp is older than `--days` (default 90), include it.
- Output a markdown table: file path, last touched (YYYY-MM-DD), days stale.
- Exit 0 always. This is a reporter, not a gatekeeper.

Pre-commit usage: wired as a manual-stage hook in .pre-commit-config.yaml so it
does NOT fire on every commit. Run with `pre-commit run --hook-stage manual
check-retirement-candidates --all-files`.

Direct usage: `python scripts/check_retirement_candidates.py [--days 60]`.

Why this matters: the retirement protocol in docs/GOVERNANCE.md is enforced
by the quarterly agent, but agents in flight still need a fast way to ask
"is this rule stale?" without waiting for the next quarterly fire.

See: docs/GOVERNANCE.md "Retirement protocol"; docs/roadmap/compass.md M2 + M3.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CORPUS_PATTERNS = (
    "docs/AGENT_SOP.md",
    "docs/GOVERNANCE.md",
)
CORPUS_GLOBS = (
    "docs/memory/*.md",
    "**/AGENTS.md",
)
SKIP_DIRS = ("zzzArchive", ".git", "node_modules", ".venv", "external", ".venv-")
SKIP_FILES = {"docs/memory/MEMORY.md", "docs/memory/MEMORY_ARCHIVE.md"}


def _force_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _is_corpus_file(rel: str) -> bool:
    if rel in SKIP_FILES:
        return False
    if any(part in SKIP_DIRS for part in Path(rel).parts):
        return False
    if rel in CORPUS_PATTERNS:
        return True
    posix = Path(rel).as_posix()
    if posix.startswith("docs/memory/") and posix.endswith(".md"):
        return True
    if Path(rel).name == "AGENTS.md":
        return True
    return False


def _iter_corpus_paths() -> list[Path]:
    out: list[Path] = []
    for pattern in CORPUS_PATTERNS:
        p = REPO_ROOT / pattern
        if p.exists():
            out.append(p)
    for glob in CORPUS_GLOBS:
        out.extend(REPO_ROOT.glob(glob))

    keep: list[Path] = []
    seen: set[Path] = set()
    for p in out:
        try:
            rel = p.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        if not _is_corpus_file(rel):
            continue
        if not p.is_file():
            continue
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        keep.append(p)
    return keep


def _last_touched_ct(path: Path) -> int | None:
    """Return committer-timestamp of last commit touching `path`, or None."""
    try:
        rel = path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return None
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    if not out:
        return None
    try:
        return int(out)
    except ValueError:
        return None


def _ymd(ct: int) -> str:
    return datetime.fromtimestamp(ct, tz=timezone.utc).strftime("%Y-%m-%d")


def main(argv: list[str]) -> int:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("--days", type=int, default=90, help="Threshold in days (default 90).")
    parser.add_argument(
        "--format",
        choices=("markdown", "plain"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    args = parser.parse_args(argv[1:])

    threshold_secs = args.days * 86400
    now = int(time.time())

    candidates: list[tuple[Path, int, int]] = []  # (path, last_ct, days_stale)
    for path in _iter_corpus_paths():
        ct = _last_touched_ct(path)
        if ct is None:
            continue
        age = now - ct
        if age >= threshold_secs:
            candidates.append((path, ct, age // 86400))

    if not candidates:
        print(f"No retirement candidates: every rule-corpus file touched in the last {args.days} days.")
        return 0

    candidates.sort(key=lambda t: t[1])  # oldest first

    if args.format == "markdown":
        print(f"# Retirement Candidates (>= {args.days} days untouched)\n")
        print(f"Audit run: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
        print("| File | Last touched | Days stale |")
        print("| --- | --- | --- |")
        for path, ct, days in candidates:
            try:
                rel = path.resolve().relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = str(path)
            print(f"| `{rel}` | {_ymd(ct)} | {days} |")
        print()
        print("Next step: for each candidate, decide retire vs keep. See docs/GOVERNANCE.md")
        print("Retirement protocol. Retired = archived to zzzArchive/_governance-retired-<date>/")
        print("with a manifest entry; never deleted.")
    else:
        for path, ct, days in candidates:
            try:
                rel = path.resolve().relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = str(path)
            print(f"{days:5d} days  {_ymd(ct)}  {rel}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
