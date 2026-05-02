#!/usr/bin/env python3
"""Create local IDE skill links under .agents/skills."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_SKILLS_DIR = REPO_ROOT / ".agents" / "skills"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.absolute().relative_to(parent.absolute())
        return True
    except ValueError:
        return False


def _is_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _clear_entry(path: Path) -> None:
    if not _is_relative_to(path, AGENTS_SKILLS_DIR):
        raise RuntimeError(f"refusing to clear path outside {AGENTS_SKILLS_DIR}: {path}")

    if path.is_symlink():
        path.unlink()
        return

    if _is_junction(path):
        path.rmdir()
        return

    if path.is_file():
        path.unlink()
        return

    if path.is_dir():
        shutil.rmtree(path)
        return

    if path.exists():
        raise RuntimeError(f"unsupported filesystem entry: {path}")


def _create_windows_junction(source: Path, target: Path) -> None:
    command = ["cmd", "/c", "mklink", "/J", str(target), str(source)]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _create_link(source: Path, target: Path) -> None:
    if os.name == "nt":
        try:
            target.symlink_to(source, target_is_directory=True)
        except OSError:
            _create_windows_junction(source, target)
    else:
        target.symlink_to(source, target_is_directory=True)


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"Missing skills directory: {SKILLS_DIR}", file=sys.stderr)
        return 1

    AGENTS_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    for existing in AGENTS_SKILLS_DIR.iterdir():
        _clear_entry(existing)

    count = 0
    for skill_dir in sorted((path for path in SKILLS_DIR.iterdir() if path.is_dir()), key=lambda path: path.name.lower()):
        _create_link(skill_dir, AGENTS_SKILLS_DIR / skill_dir.name)
        count += 1

    print(f"Linked {count} skills into {AGENTS_SKILLS_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
