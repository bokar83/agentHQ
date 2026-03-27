"""
scan_secrets.py — Workspace secret scanner
Part of SecureWatch (agentsHQ security-agent)

Scans all text files in the workspace for known secret patterns.
"""

import re
from pathlib import Path
from typing import Optional

# ── Secret patterns ───────────────────────────────────────────────────────────
SECRET_PATTERNS = [
    (r"sk-or-v1-[a-zA-Z0-9]{60,}", "OpenRouter API Key"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub Personal Access Token"),
    (r"ghs_[a-zA-Z0-9]{36,}", "GitHub Server Token"),
    (r"ntn_[a-zA-Z0-9]{40,}", "Notion Integration Secret"),
    (r"secret_[a-zA-Z0-9]{43,}", "Notion Integration Secret (alt)"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"AIzaSy[a-zA-Z0-9_-]{33}", "Google API Key"),
    (r"xoxb-[0-9]+-[a-zA-Z0-9]+", "Slack Bot Token"),
    (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
    (r"Bearer\s+[a-zA-Z0-9_\-\.]{40,}", "Bearer Token"),
]

# ── Files / patterns to always skip ──────────────────────────────────────────
# These files are allowed to REFERENCE patterns (e.g., documentation)
ALLOWLISTED_FILES = {
    "scan_secrets.py",  # This file itself
    "pre-commit",       # Pre-commit hook (contains pattern strings)
    "SKILL.md",         # Skill docs reference patterns
    "AGENT.md",         # Agent docs reference patterns
}

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".bin", ".pyc",
    ".db", ".sqlite", ".sqlite3", ".pkl", ".pt", ".pth",
    ".mp4", ".mp3", ".wav", ".avi", ".mov",
}


def is_likely_placeholder(value: str) -> bool:
    """Return True if the matched value looks like a placeholder, not a real secret."""
    placeholder_indicators = [
        "YOUR_", "CHANGE_THIS", "PLACEHOLDER", "xxxx", "EXAMPLE",
        "fake", "test", "dummy", "sample", "xxx",
    ]
    return any(p.lower() in value.lower() for p in placeholder_indicators)


def scan_workspace_for_secrets(
    root: str,
    skip_dirs: Optional[set] = None,
    skip_files: Optional[set] = None,
) -> list[dict]:
    """
    Scan all text files under `root` for secret patterns.
    Returns a list of findings dicts.
    """
    if skip_dirs is None:
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv"}
    if skip_files is None:
        skip_files = {".env"}

    compiled_patterns = [(re.compile(pattern), label) for pattern, label in SECRET_PATTERNS]
    findings = []
    root_path = Path(root)

    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip directories
        if any(part in skip_dirs for part in file_path.parts):
            continue

        # Skip allowlisted files
        if file_path.name in ALLOWLISTED_FILES:
            continue

        # Skip explicitly excluded files (e.g., local .env — OK to have secrets)
        if file_path.name in skip_files and file_path.name.startswith(".env"):
            continue

        # Skip binary files
        if file_path.suffix.lower() in BINARY_EXTENSIONS:
            continue

        # Try to read as text
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for pattern, label in compiled_patterns:
                matches = pattern.findall(line)
                for match in matches:
                    if not is_likely_placeholder(match):
                        relative_path = str(file_path.relative_to(root_path))
                        findings.append({
                            "type": label,
                            "file": relative_path,
                            "line": line_num,
                            "severity": "CRITICAL",
                            "message": f"{label} found in {relative_path}:{line_num}",
                            "snippet": line.strip()[:120],  # Truncated for safety
                        })

    return findings


if __name__ == "__main__":
    import sys
    import json

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    results = scan_workspace_for_secrets(root)
    if results:
        print(f"❌ Found {len(results)} secret(s):")
        print(json.dumps(results, indent=2))
        sys.exit(1)
    else:
        print("✅ No secrets found.")
        sys.exit(0)
