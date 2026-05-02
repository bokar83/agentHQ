#!/usr/bin/env python3
"""Lint skill frontmatter and generate docs/SKILLS_INDEX.md."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
INDEX_PATH = REPO_ROOT / "docs" / "SKILLS_INDEX.md"


class SkillLintError(ValueError):
    pass


@dataclass(frozen=True)
class Skill:
    directory: str
    name: str
    description: str


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_frontmatter(skill_file: Path) -> dict[str, str]:
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillLintError("missing opening YAML frontmatter delimiter")

    try:
        close_index = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise SkillLintError("missing closing YAML frontmatter delimiter") from exc

    frontmatter = lines[1:close_index]
    data: dict[str, str] = {}
    current_key: str | None = None
    block_lines: list[str] = []

    def finish_block() -> None:
        nonlocal current_key, block_lines
        if current_key is not None:
            data[current_key] = " ".join(line.strip() for line in block_lines if line.strip()).strip()
            current_key = None
            block_lines = []

    for line_number, raw_line in enumerate(frontmatter, start=2):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        if current_key is not None and (raw_line.startswith(" ") or raw_line.startswith("\t")):
            block_lines.append(raw_line)
            continue

        finish_block()
        if raw_line.startswith(" ") or raw_line.startswith("\t"):
            continue

        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$", raw_line)
        if not match:
            raise SkillLintError(f"invalid YAML mapping line {line_number}: {raw_line}")

        key, value = match.group(1), (match.group(2) or "").strip()
        if value in {">", "|", ">-", "|-", ">+", "|+"}:
            current_key = key
            block_lines = []
        else:
            data[key] = _strip_quotes(value)

    finish_block()
    return data


def _load_submodule_paths(repo_root) -> set[str]:
    """Read .gitmodules and return submodule paths relative to repo root."""
    gm = repo_root / ".gitmodules"
    if not gm.is_file():
        return set()
    paths: set[str] = set()
    try:
        for line in gm.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("path"):
                _, _, val = line.partition("=")
                val = val.strip()
                if val:
                    paths.add(val.replace("\\", "/"))
    except OSError:
        pass
    return paths


def load_skills() -> tuple[list[Skill], list[str]]:
    skills: list[Skill] = []
    errors: list[str] = []

    if not SKILLS_DIR.is_dir():
        return skills, [f"{SKILLS_DIR}: skills directory does not exist"]

    submodule_paths = _load_submodule_paths(REPO_ROOT)

    for skill_dir in sorted((path for path in SKILLS_DIR.iterdir() if path.is_dir()), key=lambda path: path.name.lower()):
        # Skip git submodules. Community skill collections like skills/community
        # follow their own internal structure (plugins/<x>/skills/<y>/SKILL.md)
        # and are linted by their upstream repo, not this one.
        rel = skill_dir.relative_to(REPO_ROOT).as_posix()
        if rel in submodule_paths:
            continue
        # Also skip nested clones (.git directory) and non-worktree submodule
        # checkouts (.git file pointing at gitdir).
        git_marker = skill_dir / ".git"
        if git_marker.is_file() or git_marker.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{skill_dir.relative_to(REPO_ROOT)}: missing SKILL.md")
            continue

        try:
            metadata = _parse_frontmatter(skill_file)
        except (OSError, UnicodeDecodeError, SkillLintError) as exc:
            errors.append(f"{skill_file.relative_to(REPO_ROOT)}: {exc}")
            continue

        name = metadata.get("name", "").strip()
        description = metadata.get("description", "").strip()
        if not name:
            errors.append(f"{skill_file.relative_to(REPO_ROOT)}: missing frontmatter field 'name'")
        if not description:
            errors.append(f"{skill_file.relative_to(REPO_ROOT)}: missing frontmatter field 'description'")
        if name and description:
            skills.append(Skill(skill_dir.name, name, description))

    return skills, errors


def write_index(skills: list[Skill]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Skills Index",
        "",
        "Generated by `python scripts/lint_and_index_skills.py`.",
        "",
        f"Total skills: {len(skills)}",
        "",
    ]
    for skill in skills:
        description = " ".join(skill.description.split())
        description = description.replace("—", "-").replace("–", "-").replace("--", "-")
        lines.append(f"- `{skill.name}` (`skills/{skill.directory}/`): {description}")

    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    skills, errors = load_skills()
    if errors:
        print("Skill lint failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    write_index(skills)
    print(f"Indexed {len(skills)} skills in {INDEX_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
