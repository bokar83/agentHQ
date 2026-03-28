"""
audit_git.py — Git hygiene auditor
Part of SecureWatch (agentsHQ security-agent)

Checks git-tracked files against a blocklist of sensitive file patterns
and verifies .gitignore has all critical entries.
"""

import subprocess
from pathlib import Path
from typing import Optional


# Files / patterns that should NEVER be git-tracked
SENSITIVE_TRACKED_PATTERNS = [
    ".env",
    ".env.txt",
    ".env.bak",
    ".env.local",
    "env.txt",
    ".playwright-mcp",
    "console-",  # playwright console logs
    "secrets.json",
    "secrets.yaml",
    "credentials.json",
]

# Patterns that MUST be in .gitignore
REQUIRED_GITIGNORE_ENTRIES = [
    ".env",
    "*.env",
    "*.env.txt",
    ".playwright-mcp",
    "logs/",
    "outputs/",
    "zzzArchive/",
    "qdrant_data",
    "postgres_data",
]


def get_tracked_files(workspace: str) -> list[str]:
    """Return list of all files currently tracked by git."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip().splitlines()
    except Exception as e:
        return []


def check_gitignore(workspace: str) -> list[dict]:
    """Verify that all required patterns are in .gitignore."""
    findings = []
    gitignore_path = Path(workspace) / ".gitignore"

    if not gitignore_path.exists():
        findings.append({
            "type": "MISSING_GITIGNORE",
            "severity": "CRITICAL",
            "message": "No .gitignore file found — all files could be committed accidentally",
        })
        return findings

    content = gitignore_path.read_text(encoding="utf-8")
    for pattern in REQUIRED_GITIGNORE_ENTRIES:
        if pattern not in content:
            findings.append({
                "type": "MISSING_GITIGNORE_ENTRY",
                "severity": "WARNING",
                "message": f".gitignore is missing entry: '{pattern}'",
                "file": ".gitignore",
            })

    return findings


def audit_git_hygiene(workspace: str) -> list[dict]:
    """
    Run a full git hygiene audit.
    Returns list of findings.
    """
    findings = []

    # Check for sensitive tracked files
    tracked = get_tracked_files(workspace)
    for tracked_file in tracked:
        for pattern in SENSITIVE_TRACKED_PATTERNS:
            if pattern.lower() in tracked_file.lower():
                findings.append({
                    "type": "SENSITIVE_FILE_TRACKED",
                    "severity": "CRITICAL",
                    "file": tracked_file,
                    "message": f"Sensitive file is tracked by git: {tracked_file}",
                    "action": f"Run: git rm --cached '{tracked_file}' and add to .gitignore",
                })
                break

    # Check .gitignore completeness
    findings.extend(check_gitignore(workspace))

    return findings


if __name__ == "__main__":
    import sys
    import json

    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    results = audit_git_hygiene(workspace)
    if results:
        print(f"[WARN] Found {len(results)} git hygiene issue(s):")
        print(json.dumps(results, indent=2))
        sys.exit(1)
    else:
        print("[OK] Git hygiene looks good.")
        sys.exit(0)
