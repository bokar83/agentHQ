"""
gate_resolvers.py - Conflict resolution + archival for gate_agent.

Council premortem 2026-05-14 dropped auto-rebase as too dangerous (silent
data loss on non-overlapping insertions at same anchor). Replaced with
archive + tiered deterministic resolvers.

Tiers:
  HIGH_RISK_PREFIXES (constitutional)       -> halt + alert (handled in gate_agent)
  APPEND_ONLY_LOG_PATTERNS (chronological)  -> union resolver (keep both)
  Everything else                            -> branch-wins (theirs)

Mandatory pre-resolve archive: every conflict file has main/branch/resolved
versions saved under zzzArchive/gate-merges/<isotime>-<branch>/ before any
auto-resolution. Unwind is one cp away.
"""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agentsHQ.gate_resolvers")

# Files where chronological newest-first append is the only edit pattern.
# Conflicts in these files are almost always "both branches added a new
# entry at the same anchor". Union resolver merges them losslessly.
APPEND_ONLY_LOG_PATTERNS: tuple[str, ...] = (
    "docs/roadmap/",
    "data/inbound-signal-log.md",
    "data/changelog.md",
    "docs/audits/REGISTRY.md",
    "docs/audits/memory-enforcement-violations.md",
    "data/gate_log.jsonl",
)

ARCHIVE_DIR_REL = Path("zzzArchive/gate-merges")

# Conflict marker regex - captures ours and theirs blocks (re.DOTALL).
_CONFLICT_BLOCK = re.compile(
    r"<{7} (?P<head>[^\n]*)\n"
    r"(?P<ours>.*?)"
    r"={7}\n"
    r"(?P<theirs>.*?)"
    r">{7} (?P<tail>[^\n]*)\n",
    re.DOTALL,
)

# Session-log entry header pattern: "### <anything>"
_ENTRY_HEADER = re.compile(r"^### (.+)$", re.MULTILINE)


def is_append_only_log(filepath: str) -> bool:
    """True if filepath matches any append-only-log pattern."""
    return any(filepath.startswith(p) for p in APPEND_ONLY_LOG_PATTERNS)


def _sanitize_branch(branch: str) -> str:
    return branch.replace("/", "__").replace("\\", "__")


def _flatten_path(filepath: str) -> str:
    return filepath.replace("/", "__").replace("\\", "__")


def archive_conflict(
    repo_root: Path,
    branch: str,
    filepath: str,
    isotime: str,
) -> Path:
    """Snapshot main + branch versions of a conflict file before resolution.

    Uses `git show :2:<file>` (ours/main, stage 2) and `git show :3:<file>`
    (theirs/branch, stage 3). Returns the archive dir path.

    File may not have a :2:/:3: stage if it was added/deleted on only one
    side. Empty string written for missing stages; archive dir always created.
    """
    archive_dir = repo_root / ARCHIVE_DIR_REL / f"{isotime}-{_sanitize_branch(branch)}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    flat = _flatten_path(filepath)
    for stage, label in (("2", "main"), ("3", "branch")):
        proc = subprocess.run(
            ["git", "show", f":{stage}:{filepath}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        content = proc.stdout if proc.returncode == 0 else ""
        (archive_dir / f"{label}.{flat}").write_text(content, encoding="utf-8")
    logger.info("gate_resolvers: archived %s versions to %s", filepath, archive_dir)
    return archive_dir


def archive_resolved(archive_dir: Path, repo_root: Path, filepath: str) -> None:
    """Write resolved version to archive dir AFTER resolver runs."""
    flat = _flatten_path(filepath)
    resolved_content = (repo_root / filepath).read_text(encoding="utf-8")
    (archive_dir / f"resolved.{flat}").write_text(resolved_content, encoding="utf-8")
    logger.info("gate_resolvers: archived resolved version to %s", archive_dir)


def _split_entries(text: str) -> list[tuple[str, str]]:
    """Split chronological-log chunk into entries.

    Returns list of (header_line, full_block_including_header).
    Entries start at "### " and run to the next "### " or EOF.
    Empty header (header=="") means preamble text before first marker.
    """
    positions = [m.start() for m in _ENTRY_HEADER.finditer(text)]
    if not positions:
        return [("", text)] if text else []
    out: list[tuple[str, str]] = []
    if positions[0] > 0:
        out.append(("", text[: positions[0]]))
    for i, start in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        block = text[start:end]
        header_line = block.split("\n", 1)[0].strip()
        out.append((header_line, block))
    return out


def union_entries(ours: str, theirs: str) -> str:
    """Union session-log entries from ours + theirs.

    Both sides are chunks containing zero or more "### <header>" entries.
    Returns concatenation with duplicates removed; ours order preserved,
    theirs entries appended if their header not already in ours.

    Dedup key: full entry header line. Two identical headers with
    different body = ours wins (archive preserves theirs for unwind).
    """
    ours_entries = _split_entries(ours)
    theirs_entries = _split_entries(theirs)

    seen: set[str] = set()
    result: list[str] = []

    for header, block in ours_entries:
        if header == "":
            result.append(block)
        elif header not in seen:
            result.append(block)
            seen.add(header)

    for header, block in theirs_entries:
        if header and header not in seen:
            result.append(block)
            seen.add(header)

    return "".join(result)


def resolve_append_only_log(filepath: Path) -> int:
    """Resolve conflicts in an append-only log file via union of entries.

    Reads the file (containing <<<<<<< / ======= / >>>>>>> markers),
    replaces each conflict block with the union of ours + theirs entries.
    Returns number of conflict blocks resolved.
    """
    text = filepath.read_text(encoding="utf-8")
    count = 0

    def replace_block(m: re.Match) -> str:
        nonlocal count
        count += 1
        return union_entries(m.group("ours"), m.group("theirs"))

    resolved = _CONFLICT_BLOCK.sub(replace_block, text)
    filepath.write_text(resolved, encoding="utf-8")
    logger.info(
        "gate_resolvers: resolve_append_only_log %s -> %d block(s) merged",
        filepath, count,
    )
    return count


def resolve_branch_wins(repo_root: Path, filepath: str) -> None:
    """Use git checkout --theirs to take the branch version."""
    proc = subprocess.run(
        ["git", "checkout", "--theirs", filepath],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git checkout --theirs {filepath} failed: "
            f"{proc.stderr or proc.stdout}"
        )
    logger.info("gate_resolvers: resolve_branch_wins %s (theirs wins)", filepath)
