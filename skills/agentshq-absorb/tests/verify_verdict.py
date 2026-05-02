"""Verify a /agentshq-absorb verdict block has all required fields.

Usage:
    python verify_verdict.py < verdict.txt
    python verify_verdict.py path/to/verdict.txt
    python verify_verdict.py --fixtures fixtures.tsv

The verdict block is the plain-text section between 'ABSORB VERDICT :' and
the start of the first <details> section (or end of input).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    ("verdict", r"^(PROCEED|DON'T PROCEED|ARCHIVE-AND-NOTE)\s*$"),
    ("leverage", r"^Leverage:\s*(\S.+)$"),
    ("motion", r"^Motion / target:\s*(\S.+)$"),
    ("why", r"^Why\b"),
    ("placement", r"^Placement:\s*(\S.+)$"),
    ("runner_up", r"^Runner-up:\s*(\S.+)$"),
    ("next_action", r"^Next action:\s*(\S.+)$"),
    ("target_date", r"^Target date:\s*(\d{4}-\d{2}-\d{2})\s*$"),
]


def verify_verdict(text: str) -> tuple[bool, list[str]]:
    """Return (ok, missing_fields)."""
    lines = text.splitlines()
    missing: list[str] = []
    for name, pattern in REQUIRED_FIELDS:
        if not any(re.search(pattern, line, re.MULTILINE) for line in lines):
            missing.append(name)
    return (not missing, missing)


def verify_fixtures(tsv_path: Path) -> tuple[bool, list[str]]:
    """Load the fixtures TSV and confirm each row has 2 columns and a valid type."""
    valid_types = {
        "repo", "mcp-server", "n8n-workflow", "pdf",
        "raw-doc", "live-site", "skill", "unknown",
    }
    errors: list[str] = []
    with tsv_path.open(encoding="utf-8") as fh:
        rows = [line.rstrip("\n") for line in fh if line.strip()]
    header = rows[0].split("\t")
    if header != ["input", "expected_type"]:
        errors.append(f"bad header: {header}")
    for i, row in enumerate(rows[1:], start=2):
        cols = row.split("\t")
        if len(cols) != 2:
            errors.append(f"row {i}: expected 2 columns, got {len(cols)}")
            continue
        if cols[1] not in valid_types:
            errors.append(f"row {i}: invalid type {cols[1]!r}")
    return (not errors, errors)


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[1] == "--fixtures":
        ok, errors = verify_fixtures(Path(argv[2]))
        if ok:
            print("FIXTURES OK")
            return 0
        for err in errors:
            print(f"FIXTURE ERROR: {err}")
        return 1

    if len(argv) >= 2:
        text = Path(argv[1]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    ok, missing = verify_verdict(text)
    if ok:
        print("VERDICT OK: all 8 required fields present.")
        return 0
    print("VERDICT INCOMPLETE. Missing fields:")
    for field in missing:
        print(f"  - {field}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
