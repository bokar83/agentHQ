#!/usr/bin/env python3
"""Smoke test for scripts/check_hermes_write_boundary.py.

Spawns a throwaway git repo per case, stages the requested files with
the requested author identity, and runs the boundary script. Stdlib
only. Exit 0 only if all cases pass; otherwise exit 1 with a summary.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_hermes_write_boundary.py"


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=full_env)


def _git_init(workdir: Path, author_name: str, author_email: str) -> None:
    _run(["git", "init", "-q"], workdir)
    _run(["git", "config", "user.email", author_email], workdir)
    _run(["git", "config", "user.name", author_name], workdir)
    _run(["git", "config", "commit.gpgsign", "false"], workdir)


def _stage_files(workdir: Path, rel_paths: list[str]) -> None:
    for rel in rel_paths:
        target = workdir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("placeholder\n", encoding="utf-8")
        _run(["git", "add", rel], workdir)


def _run_boundary(workdir: Path, author_name: str, author_email: str) -> tuple[int, str, str]:
    env = {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": author_name,
        "GIT_COMMITTER_EMAIL": author_email,
    }
    proc = _run([sys.executable, str(SCRIPT)], workdir, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def case(name: str, expected_exit: int, files: list[str],
         author_name: str, author_email: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="hermes-boundary-test-") as tmp:
        workdir = Path(tmp)
        _git_init(workdir, author_name, author_email)
        _stage_files(workdir, files)
        rc, out, err = _run_boundary(workdir, author_name, author_email)
        ok = rc == expected_exit
        detail = (
            f"[{name}] expected exit {expected_exit}, got {rc}\n"
            f"  stdout: {out.strip()}\n"
            f"  stderr: {err.strip()}"
        )
        return ok, detail


def main() -> int:
    cases = [
        case(
            "hermes-allowed-ctq-social-refs",
            expected_exit=0,
            files=["skills/ctq-social/references/foo.md"],
            author_name="hermes",
            author_email="hermes@agentshq.local",
        ),
        case(
            "hermes-forbidden-SKILL.md",
            expected_exit=1,
            files=["skills/ctq-social/SKILL.md"],
            author_name="hermes",
            author_email="hermes@agentshq.local",
        ),
        case(
            "hermes-not-allowlisted-skill",
            expected_exit=1,
            files=["skills/studio/references/bar.md"],
            author_name="hermes",
            author_email="hermes@agentshq.local",
        ),
        case(
            "human-passthrough",
            expected_exit=0,
            files=["CLAUDE.md", "scripts/anything.py"],
            author_name="Boubacar Barry",
            author_email="boubacar@catalystworks.consulting",
        ),
    ]
    failures = []
    for ok, detail in cases:
        marker = "PASS" if ok else "FAIL"
        print(f"{marker}: {detail.splitlines()[0]}")
        if not ok:
            failures.append(detail)
    if failures:
        print("\n--- FAILURE DETAILS ---")
        for f in failures:
            print(f)
            print()
        return 1
    print(f"\nAll {len(cases)} cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
