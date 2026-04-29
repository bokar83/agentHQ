"""Pre-commit hook: reject em dashes in markdown prose.

By default, flags em-dash violations only on lines that are NEW in the staged
diff for each file. Pre-existing dirt in untouched lines is ignored. This
preserves the surgical-changes principle: don't punish the next person who
edits a file for sins they did not commit.

Use --full to scan the whole file regardless of diff (for ad-hoc cleanup).

Allows the literal character inside inline code spans (between backticks), so
rule statements like `—` or `--` can cite the character they forbid.
Rejects everywhere else, including bare `--` (double hyphen em-dash surrogate).
"""

from __future__ import annotations

import re
import subprocess
import sys

INLINE_CODE = re.compile(r"`[^`]*`")
# Match real em/en dashes, and only prose `--` (adjacent to a word char on at
# least one side, or wrapped in spaces as an em-dash surrogate). Markdown table
# separators `| --- |` and horizontal rules `---` pass.
EM_DASH = re.compile(r"[—–]|(?:(?<=\w)--| -- )")


def _force_utf8_stdout() -> None:
    """Avoid cp1252 crashes when printing offending lines that contain non-ASCII chars."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def strip_inline_code(line: str) -> str:
    return INLINE_CODE.sub("", line)


def strip_fenced_code(lines: list[str]) -> list[str]:
    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return out


def staged_added_line_numbers(path: str) -> set[int] | None:
    """Return the set of 1-indexed line numbers in `path` that are NEW or MODIFIED in the staged diff.

    Returns None if git is unavailable, the file is not staged, or the file is brand-new
    (in which case every line counts as new and the caller falls back to whole-file scan).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=0", "--", path],
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

    diff = result.stdout
    if not diff.strip():
        # No staged diff for this file. Could be: not staged at all (return None
        # so caller can decide), or rename/copy with no content change.
        return None

    # Brand-new files: the diff shows /dev/null as the source. Every line is new.
    # Return None so caller falls back to whole-file scan.
    if "/dev/null" in diff.split("\n", 8)[0:6][0:6][0]:
        # Crude but reliable: look for "new file mode" header
        pass
    if "\nnew file mode " in diff or diff.startswith("new file mode "):
        return None

    added: set[int] = set()
    # Diff hunks look like: @@ -OLDSTART[,OLDLEN] +NEWSTART[,NEWLEN] @@
    hunk_re = re.compile(r"^@@ .* \+(\d+)(?:,(\d+))? @@")
    current_lineno = 0
    in_hunk = False
    for line in diff.splitlines():
        m = hunk_re.match(line)
        if m:
            current_lineno = int(m.group(1))
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.add(current_lineno)
            current_lineno += 1
        elif line.startswith("-"):
            # Removed line, no advance in NEW file
            pass
        else:
            # Context line (rare with --unified=0) or empty
            current_lineno += 1
    return added


def check_file(path: str, full: bool = False) -> list[tuple[int, str]]:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read().splitlines()
    stripped = strip_fenced_code(raw)

    if full:
        target_lines: set[int] | None = None  # None means "all lines"
    else:
        target_lines = staged_added_line_numbers(path)
        # If staged_added_line_numbers returned None, fall back to whole-file scan
        # (matches the old behavior for new files / files without git context).

    violations: list[tuple[int, str]] = []
    for idx, line in enumerate(stripped, start=1):
        if target_lines is not None and idx not in target_lines:
            continue
        prose = strip_inline_code(line)
        if EM_DASH.search(prose):
            violations.append((idx, raw[idx - 1].rstrip()))
    return violations


def main(argv: list[str]) -> int:
    _force_utf8_stdout()
    full = False
    args = []
    for a in argv[1:]:
        if a == "--full":
            full = True
        else:
            args.append(a)

    exit_code = 0
    for path in args:
        violations = check_file(path, full=full)
        if violations:
            exit_code = 1
            print(f"\n{path}: em dash found (hard rule, rewrite the sentence)")
            for lineno, content in violations:
                print(f"  line {lineno}: {content}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
