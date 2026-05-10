#!/usr/bin/env python3
# scripts/check_vendor_tokens.py
"""Scan staged files for vendor-prefixed API tokens that detect-secrets misses.

SAFE_WORDS: tokens containing these strings are skipped. This is a footgun --
adding REDACTED to a real token makes it pass. Document every safe-word use.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

PATTERNS = re.compile(
    r'\b(vcp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{32,}|'
    r'ghp_[A-Za-z0-9]{36,}|ghs_[A-Za-z0-9]{36,}|'
    r'xoxb-\d+-\w{10,}|xoxp-\d+-\w{10,}|AKIA[0-9A-Z]{16})\b'
)
SAFE = re.compile(r'REDACTED|EXAMPLE|PLACEHOLDER|YOUR_TOKEN|<[A-Z_]+>', re.I)

def scan_file(path: str) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    hits = []
    for m in PATTERNS.finditer(text):
        token = m.group(0)
        context = text[max(0, m.start()-30):m.end()+30]
        if not SAFE.search(context):
            line = text[:m.start()].count("\n") + 1
            hits.append(f"{path}:{line}: {token[:16]}... ({len(token)} chars)")
    return hits

def main() -> int:
    staged = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        text=True
    ).splitlines()
    hits = [h for f in staged for h in scan_file(f.strip()) if f.strip()]
    if hits:
        print("VENDOR TOKEN DETECTED in staged files:", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        print("Remove/redact token. If audit doc: add REDACTED safe-word.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
