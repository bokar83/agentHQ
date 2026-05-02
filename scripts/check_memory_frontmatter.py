"""Pre-commit hook: every memory file has valid name/description/type frontmatter.

Compass M2 enforcement layer. Targets in-repo memory files at `docs/memory/*.md`.
The user's auto-memory at `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/` is
outside the repo and pre-commit cannot see it; this hook protects the in-repo
mirror that lives in `docs/memory/`.

Validates:
- File starts with a `---` line.
- Frontmatter closes with a second `---`.
- Frontmatter contains non-empty `name:`, `description:`, and `type:` fields.
- `type:` value is one of {feedback, reference, user, project}.

Skipped:
- The `MEMORY.md` index file itself (it is an index, not a memory entry).
- Any file under `zzzArchive/` (graveyard).

Behavior:
- Receives changed file paths from pre-commit (default invocation).
- Reports every offender with the specific missing field.
- Exits non-zero on any violation.

Why this matters: memory files without consistent frontmatter cannot be
indexed, classified, or retired by automated processes. The agent ecosystem
that reads memory expects the schema. Convert the rule from aspirational
(in `using-superpowers` skill) to enforced.

See: docs/GOVERNANCE.md routing table; docs/roadmap/compass.md M2.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALID_TYPES = {"feedback", "reference", "user", "project"}
REQUIRED_FIELDS = ("name", "description", "type")
SKIP_FILENAMES = {"MEMORY.md", "MEMORY_ARCHIVE.md"}


def _force_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _is_memory_file(path: Path) -> bool:
    """True if `path` is a memory entry we should validate."""
    try:
        rel = path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return False
    if not rel.startswith("docs/memory/"):
        return False
    if path.name in SKIP_FILENAMES:
        return False
    if "zzzArchive" in rel.split("/"):
        return False
    return path.suffix == ".md"


def _parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    """Return (fields, error). On success error is None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing opening '---' on first line"
    closing_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
    if closing_idx is None:
        return None, "missing closing '---' for frontmatter block"
    fields: dict[str, str] = {}
    for raw in lines[1:closing_idx]:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, None


def check_file(path: Path) -> list[str]:
    """Return list of human-readable violation strings for `path`."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"could not read file: {exc}"]
    fields, error = _parse_frontmatter(text)
    if fields is None:
        return [error or "frontmatter parse failed"]
    violations: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in fields or not fields[field]:
            violations.append(f"missing or empty '{field}:' field")
    if "type" in fields and fields["type"]:
        if fields["type"] not in VALID_TYPES:
            violations.append(
                f"type '{fields['type']}' is not one of {sorted(VALID_TYPES)}"
            )
    return violations


def main(argv: list[str]) -> int:
    _force_utf8_stdout()
    exit_code = 0
    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            continue
        if not _is_memory_file(path):
            continue
        violations = check_file(path)
        if violations:
            exit_code = 1
            try:
                rel = path.resolve().relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = str(path)
            print(f"\n{rel}: memory frontmatter invalid")
            for v in violations:
                print(f"  - {v}")

    if exit_code:
        print()
        print("Fix: every memory file needs YAML frontmatter at the top with")
        print("  name:, description:, and type: (one of feedback|reference|user|project).")
        print("Pattern reference: docs/memory/feedback_general.md")
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
