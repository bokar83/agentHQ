"""Pre-commit hook: reject em dashes in markdown prose.

Allows the literal character inside inline code spans (between backticks), so
rule statements like `—` or `--` can cite the character they forbid.
Rejects everywhere else, including bare `--` (double hyphen em-dash surrogate).
"""

from __future__ import annotations

import re
import sys

INLINE_CODE = re.compile(r"`[^`]*`")
# Match real em/en dashes, and only prose `--` (adjacent to a word char on at
# least one side, or wrapped in spaces as an em-dash surrogate). Markdown table
# separators `| --- |` and horizontal rules `---` pass.
EM_DASH = re.compile(r"[\u2014\u2013]|(?:(?<=\w)--| -- )")


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


def check_file(path: str) -> list[tuple[int, str]]:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read().splitlines()
    stripped = strip_fenced_code(raw)
    violations: list[tuple[int, str]] = []
    for idx, line in enumerate(stripped, start=1):
        prose = strip_inline_code(line)
        if EM_DASH.search(prose):
            violations.append((idx, raw[idx - 1].rstrip()))
    return violations


def main(argv: list[str]) -> int:
    exit_code = 0
    for path in argv[1:]:
        violations = check_file(path)
        if violations:
            exit_code = 1
            print(f"\n{path}: em dash found (hard rule, rewrite the sentence)")
            for lineno, content in violations:
                print(f"  line {lineno}: {content}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
