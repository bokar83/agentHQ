"""Pre-commit hook: roadmap edits must update the Session Log.

Compass M2 enforcement layer. The roadmap discipline rule (in AGENT_SOP.md
Session End section) requires that any roadmap touched in a session gets a
dated session-log entry. This hook converts that rule from aspirational to
enforced at commit time.

Behavior:
- Receives changed file paths from pre-commit (default invocation).
- Filters to `docs/roadmap/*.md` files (the codename roadmaps).
- Skips `docs/roadmap/README.md` (registry, not a project roadmap).
- For each staged roadmap, reads the staged diff.
- If the diff contains any meaningful line additions (anything other than the
  session-log entry itself), require at least one NEW line matching a dated
  session-log header pattern.
- Dated patterns recognized:
    `## Session Log: YYYY-MM-DD ...`
    `### YYYY-MM-DD ...`
    `### Session Log: YYYY-MM-DD ...`
- A "Last updated:" timestamp bump alone does NOT count.

Bypass:
- The commit message can include `[skip roadmap]` to opt out (e.g. fixing a
  typo in a milestone heading). Pre-commit hooks fire before the message
  exists; users who need the bypass should run `git commit --no-verify` for
  that one commit, or set `SKIP=check-session-log` per the pre-commit env var.
  The hook honors `SKIP_SESSION_LOG=1` as an explicit env override.

Why this matters: roadmaps without session logs become stale registries that
nobody trusts. The discipline only holds if the mechanism enforces it.

See: docs/AGENT_SOP.md Session End section; docs/roadmap/compass.md M2;
memory/feedback_roadmap_discipline.md.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP_DIR = "docs/roadmap"
SKIP_FILES = {"README.md", "future-enhancements.md"}

# Match a NEW dated session-log entry. Anchored to start so we only count
# header lines, not random ISO dates inside body text.
DATED_ENTRY_RE = re.compile(
    r"^\+(?:#{2,3}\s+)(?:Session Log\s*[:\-]\s*)?(\d{4}-\d{2}-\d{2})\b",
)
# Trivial additions that don't count as "real edits requiring a log entry".
TRIVIAL_LINE_RE = re.compile(
    r"^\+\s*(?:\*?Last updated[:\*]|<!--|$)",
    re.IGNORECASE,
)
# Detect milestone status changes in added lines (SHIPPED/IN PROGRESS/QUEUED/BLOCKED).
MILESTONE_STATUS_RE = re.compile(
    r"^\+###\s+M\d+\w*[:\s].*"
    r"(?:SHIPPED|IN PROGRESS|QUEUED|BLOCKED|TRIGGER-GATED|NOT STARTED)",
    re.IGNORECASE,
)


def _force_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _is_roadmap_file(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return False
    if not rel.startswith(f"{ROADMAP_DIR}/"):
        return False
    if path.name in SKIP_FILES:
        return False
    if path.suffix != ".md":
        return False
    # Subfolder roadmaps (e.g. docs/roadmap/atlas/m7a-decision-spike.md) are
    # working notes for a milestone, not the roadmap itself; skip them.
    parts = Path(rel).parts
    if len(parts) > 3:
        return False
    return True


def _staged_diff(path: Path) -> str | None:
    """Return the staged diff for `path`, or None if git is unavailable."""
    try:
        rel = path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel = str(path)
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=0", "--", rel],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            cwd=str(REPO_ROOT),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _has_meaningful_additions(diff: str) -> bool:
    """True if the diff adds any non-trivial line (excludes blank/timestamp/comment)."""
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if TRIVIAL_LINE_RE.match(line):
            continue
        return True
    return False


def _has_new_dated_entry(diff: str) -> bool:
    for line in diff.splitlines():
        if line.startswith("+++"):
            continue
        if DATED_ENTRY_RE.match(line):
            return True
    return False


def _check_stale_milestone_status(path: Path, diff: str) -> list[str]:
    """Warn if a milestone header in the file still shows old status after changes.

    Specifically: if the diff adds lines containing 'SHIPPED' in a session-log
    entry but the file still has that milestone header marked as QUEUED or
    IN PROGRESS, flag it.

    Returns list of warning strings (empty = clean).
    """
    warnings: list[str] = []
    # Find milestone names mentioned as SHIPPED in added session-log lines
    shipped_in_log: set[str] = set()
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        # Look for "M9", "M10" etc. mentioned alongside SHIPPED in log additions
        m = re.search(r"\b(M\d+\w*)\b.*\bSHIPPED\b", line, re.IGNORECASE)
        if m:
            shipped_in_log.add(m.group(1).upper())

    if not shipped_in_log:
        return []

    # Read current file content and check milestone headers
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    for milestone in shipped_in_log:
        # Find the milestone header line
        header_re = re.compile(
            rf"^###\s+{re.escape(milestone)}[:\s].*$", re.MULTILINE | re.IGNORECASE
        )
        for match in header_re.finditer(content):
            header_line = match.group(0)
            # If header doesn't contain SHIPPED, flag it
            if "SHIPPED" not in header_line.upper():
                try:
                    rel = path.resolve().relative_to(REPO_ROOT).as_posix()
                except ValueError:
                    rel = str(path)
                warnings.append(
                    f"  {rel}: {milestone} logged as SHIPPED in session log "
                    f"but header still shows: '{header_line.strip()}'"
                )
    return warnings


def main(argv: list[str]) -> int:
    _force_utf8_stdout()

    if os.environ.get("SKIP_SESSION_LOG") == "1":
        return 0

    offenders: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        if not _is_roadmap_file(path):
            continue
        diff = _staged_diff(path)
        if diff is None or not diff.strip():
            continue
        if not _has_meaningful_additions(diff):
            continue
        if _has_new_dated_entry(diff):
            continue
        try:
            rel = path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = str(path)
        offenders.append(rel)

    if offenders:
        print("FAIL: roadmap files modified without a new dated Session Log entry:")
        for rel in offenders:
            print(f"  - {rel}")
        print()
        print("Fix: append a `### YYYY-MM-DD: <one-line>` entry under '## Session Log'.")
        print("Bypass for cosmetic fixes: SKIP_SESSION_LOG=1 git commit ...")
        print("Reference: docs/AGENT_SOP.md Session End; docs/roadmap/compass.md M2.")
        return 1

    # Secondary check: warn (non-blocking) if milestone headers are stale
    stale_warnings: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        if not _is_roadmap_file(path):
            continue
        diff = _staged_diff(path)
        if not diff:
            continue
        stale_warnings.extend(_check_stale_milestone_status(path, diff))

    if stale_warnings:
        print("WARN: session log mentions SHIPPED milestones whose headers may be stale:")
        for w in stale_warnings:
            print(w)
        print()
        print("Fix: update the ### MXX header status to '✅ SHIPPED YYYY-MM-DD'.")
        print("This is a warning only — commit is not blocked.")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
