"""Pre-commit hook: surface duplicate rule statements across governance surfaces.

Compass M2 enforcement layer. The Adding-a-new-rule protocol in
docs/GOVERNANCE.md says: "If it conflicts with an existing rule, retire the
older one or reconcile explicitly." Two contradictory rules in two surfaces
is the sprawl pattern. This hook catches the easy case: the SAME rule
written into a second surface.

Scope of the rule corpus (the set we deduplicate against):
- `docs/AGENT_SOP.md` (rules library)
- `docs/GOVERNANCE.md` (constitution)
- `docs/memory/*.md` (in-repo memory entries)
- every `AGENTS.md` at any depth

Behavior:
- Receives changed file paths from pre-commit (default invocation).
- Filters to files in the rule corpus.
- For each staged file, extracts NEW substantive lines from the staged diff
  (≥60 chars, not a heading, not a list bullet alone, not a code fence).
- Normalizes each new line (lowercase, strip punctuation, collapse whitespace,
  drop tokens <3 chars) and computes a token set.
- For each new line, scans every OTHER rule-corpus file for a near-duplicate
  using token Jaccard similarity (>=0.85). Same-file matches are ignored.
- Reports each near-duplicate with both source locations.

Exit:
- WARN-ONLY by default (exit 0 with stderr report). The signal is for the
  agent to consolidate, not to block commits.
- Set RULE_REDUNDANCY_STRICT=1 to fail the commit on findings.

Why this matters: rules duplicated across AGENT_SOP and memory and folder
AGENTS.md become impossible to retire (which copy is canonical?) and slowly
drift out of sync. The 2026-05-02 Sankofa audit named this as the #1 sprawl
risk. A grep-style mechanism is the simplest possible mitigation.

See: docs/GOVERNANCE.md "Adding a new rule"; docs/roadmap/compass.md M2.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
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
SKIP_DIRS = ("zzzArchive", ".git", "node_modules", ".venv", "external")
SKIP_FILES = {"docs/memory/MEMORY.md", "docs/memory/MEMORY_ARCHIVE.md"}

MIN_LINE_LEN = 60        # below this we don't bother fingerprinting
JACCARD_THRESHOLD = 0.85
TOKEN_RE = re.compile(r"[a-z0-9]{3,}")
HEADING_RE = re.compile(r"^\s*#")
BULLET_ONLY_RE = re.compile(r"^\s*[-*]\s*$")
FENCE_RE = re.compile(r"^\s*```")


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


def _normalize(line: str) -> tuple[str, frozenset[str]]:
    """Return (normalized_text, token_set) for a body line."""
    lowered = line.lower()
    tokens = frozenset(TOKEN_RE.findall(lowered))
    return lowered.strip(), tokens


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _extract_added_lines(file_rel: str) -> list[str]:
    """Return new prose lines (>= MIN_LINE_LEN, not heading/bullet/fence) from staged diff."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=0", "--", file_rel],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    added: list[str] = []
    for raw in result.stdout.splitlines():
        if not raw.startswith("+") or raw.startswith("+++"):
            continue
        body = raw[1:]
        stripped = body.strip()
        if len(stripped) < MIN_LINE_LEN:
            continue
        if HEADING_RE.match(body) or BULLET_ONLY_RE.match(body) or FENCE_RE.match(body):
            continue
        added.append(stripped)
    return added


def _iter_corpus_files(skip_rel: str) -> list[Path]:
    """Walk the corpus on disk, excluding `skip_rel` and gitignored regions."""
    out: list[Path] = []
    for pattern in CORPUS_PATTERNS:
        p = REPO_ROOT / pattern
        if p.exists():
            out.append(p)
    for glob in CORPUS_GLOBS:
        out.extend(REPO_ROOT.glob(glob))

    keep: list[Path] = []
    for p in out:
        try:
            rel = p.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        if rel == skip_rel:
            continue
        if not _is_corpus_file(rel):
            continue
        if not p.is_file():
            continue
        keep.append(p)
    return keep


def _file_lines(path: Path) -> list[tuple[int, str, frozenset[str]]]:
    """Return (lineno, normalized_text, token_set) for substantive lines."""
    out: list[tuple[int, str, frozenset[str]]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    in_fence = False
    for idx, raw in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = raw.strip()
        if len(stripped) < MIN_LINE_LEN:
            continue
        if HEADING_RE.match(raw) or BULLET_ONLY_RE.match(raw):
            continue
        text_norm, tokens = _normalize(stripped)
        if len(tokens) < 6:
            continue
        out.append((idx, text_norm, tokens))
    return out


def main(argv: list[str]) -> int:
    _force_utf8_stdout()
    strict = os.environ.get("RULE_REDUNDANCY_STRICT") == "1"

    findings: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        try:
            rel = path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        if not _is_corpus_file(rel):
            continue

        added = _extract_added_lines(rel)
        if not added:
            continue

        corpus_files = _iter_corpus_files(skip_rel=rel)
        # Lazily index each corpus file's lines.
        indexed: list[tuple[Path, list[tuple[int, str, frozenset[str]]]]] = []
        for cf in corpus_files:
            indexed.append((cf, _file_lines(cf)))

        for new_line in added:
            _, new_tokens = _normalize(new_line)
            if len(new_tokens) < 6:
                continue
            for cf, entries in indexed:
                for lineno, _other_text, other_tokens in entries:
                    if _jaccard(new_tokens, other_tokens) >= JACCARD_THRESHOLD:
                        try:
                            cf_rel = cf.resolve().relative_to(REPO_ROOT).as_posix()
                        except ValueError:
                            cf_rel = str(cf)
                        snippet = new_line[:120] + ("..." if len(new_line) > 120 else "")
                        findings.append(
                            f"{rel}: near-duplicate of {cf_rel}:{lineno}\n    new: {snippet}"
                        )
                        break  # one match per added line is enough

    if findings:
        header = "FAIL" if strict else "WARN"
        print(f"\n{header}: rule-redundancy hook flagged {len(findings)} near-duplicate line(s):")
        for f in findings:
            print(f"  - {f}")
        print()
        print("If this rule legitimately belongs in both places, leave a `*See also:*` cross-ref")
        print("instead of restating it. If you are migrating a rule, retire the older copy in the")
        print("same commit (archive to zzzArchive/ per the no-delete protocol).")
        print("Set RULE_REDUNDANCY_STRICT=1 to make this hook fail the commit.")
        return 1 if strict else 0

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
