"""Validate docs/governance.manifest.json against docs/GOVERNANCE.md.

Compass M4 enforcement layer. The manifest is the LLM-readable mirror of
GOVERNANCE.md's routing table; drift between the two is a sprawl risk.
This script is the drift check.

Validations:

1. JSON parses.
2. Every entry in `rule_types` has a `name`, `source_of_truth`, and
   `enforcement` (non-empty list).
3. The routing-table row count in GOVERNANCE.md (Markdown table under
   "## Routing table") matches `len(rule_types)`. A mismatch means
   somebody added a row to one and forgot the other.
4. Every internal repo-path referenced as a source_of_truth or hook
   `script` exists on disk. (External tools like `external (Yelp/...)` are
   skipped.) Repo-relative paths starting with "docs/", "scripts/",
   "MEMORY.md", "data/", "Notion ", "<folder>", or containing `<...>`
   placeholders are tolerated; only paths that look like concrete repo
   paths (start with "docs/" or "scripts/" and end with a real extension)
   are checked.

Exit codes:
- 0 on success.
- 1 on any drift.

Usage:
    python scripts/validate_governance_manifest.py

Wire into pre-commit (Compass M4): the manifest is small enough to
validate on every commit that touches GOVERNANCE.md or the manifest.

See: docs/GOVERNANCE.md routing table; docs/roadmap/compass.md M4.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "docs" / "governance.manifest.json"
GOVERNANCE = REPO_ROOT / "docs" / "GOVERNANCE.md"


def _force_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _routing_row_count(markdown: str) -> int:
    """Count non-header rows in the first Markdown table under '## Routing table'."""
    lines = markdown.splitlines()
    in_section = False
    rows = 0
    saw_separator = False
    for line in lines:
        if line.strip().startswith("## Routing table"):
            in_section = True
            continue
        if not in_section:
            continue
        if line.strip().startswith("##"):
            break
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s|:\-]+\|$", stripped):
            saw_separator = True
            continue
        if not saw_separator:
            continue
        rows += 1
    return rows


def _is_concrete_repo_path(path: str) -> bool:
    """Heuristic: the string looks like a concrete in-repo path (not a placeholder)."""
    if "<" in path or ">" in path:
        return False
    if path.startswith("external"):
        return False
    if path.startswith("Notion"):
        return False
    if path.startswith("MEMORY.md at "):
        return False
    if " " in path:
        # Multi-word descriptions, not paths.
        return False
    if path.endswith("/"):
        return False
    # Accept docs/..., scripts/..., or MEMORY.md.
    if path.startswith(("docs/", "scripts/")):
        return True
    if path == "MEMORY.md":
        return True
    return False


def main() -> int:
    _force_utf8_stdout()

    if not MANIFEST.exists():
        print(f"FAIL: manifest not found at {MANIFEST.relative_to(REPO_ROOT)}")
        return 1
    if not GOVERNANCE.exists():
        print(f"FAIL: GOVERNANCE.md not found at {GOVERNANCE.relative_to(REPO_ROOT)}")
        return 1

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: manifest is not valid JSON: {exc}")
        return 1

    errors: list[str] = []

    rule_types = manifest.get("rule_types")
    if not isinstance(rule_types, list) or not rule_types:
        errors.append("manifest 'rule_types' must be a non-empty list")
    else:
        for i, entry in enumerate(rule_types):
            for key in ("name", "source_of_truth", "enforcement"):
                if key not in entry:
                    errors.append(f"rule_types[{i}] missing key '{key}'")
            if "enforcement" in entry and not entry["enforcement"]:
                errors.append(f"rule_types[{i}] enforcement is empty")

    if "conflict_resolution" not in manifest:
        errors.append("manifest missing 'conflict_resolution'")
    if "retirement_protocol" not in manifest:
        errors.append("manifest missing 'retirement_protocol'")

    md = GOVERNANCE.read_text(encoding="utf-8")
    md_rows = _routing_row_count(md)
    if isinstance(rule_types, list) and md_rows != len(rule_types):
        errors.append(
            f"routing-table drift: GOVERNANCE.md has {md_rows} rows, manifest has {len(rule_types)} rule_types"
        )

    # Check that hook scripts exist on disk.
    hooks = manifest.get("enforcement_hooks", {}).get("pre_commit", [])
    for hook in hooks:
        script = hook.get("script", "")
        if not _is_concrete_repo_path(script):
            continue
        if not (REPO_ROOT / script).exists():
            errors.append(f"hook '{hook.get('id')}' references missing script: {script}")

    if errors:
        print(f"FAIL: governance manifest validation surfaced {len(errors)} drift issue(s):")
        for e in errors:
            print(f"  - {e}")
        print()
        print("Fix: re-sync docs/governance.manifest.json with docs/GOVERNANCE.md.")
        print("If you added a routing-table row, mirror it under rule_types in the manifest.")
        return 1

    print(
        f"OK: governance manifest in sync with GOVERNANCE.md "
        f"({len(rule_types)} rule_types, {md_rows} routing-table rows, "
        f"{len(hooks)} hooks)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
