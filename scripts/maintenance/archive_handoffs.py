#!/usr/bin/env python3
"""
Handoff folder auto-archive.
Rule: any docs/handoff/*.md older than ARCHIVE_AFTER_DAYS gets moved to docs/handoff/archive/.
Run manually or via cron. Never deletes — only moves.

Usage:
    python scripts/maintenance/archive_handoffs.py [--dry-run] [--days 7]
"""

import argparse
import shutil
from datetime import date, timedelta
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HANDOFF_DIR = REPO_ROOT / "docs" / "handoff"
ARCHIVE_DIR = HANDOFF_DIR / "archive"
ARCHIVE_AFTER_DAYS = 7
DATE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})-")


def main():
    parser = argparse.ArgumentParser(description="Archive old handoff files")
    parser.add_argument("--dry-run", action="store_true", help="Print what would move, don't move")
    parser.add_argument("--days", type=int, default=ARCHIVE_AFTER_DAYS, help="Archive files older than N days")
    args = parser.parse_args()

    cutoff = date.today() - timedelta(days=args.days)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    moved = []
    skipped = []
    no_date = []

    for f in sorted(HANDOFF_DIR.glob("*.md")):
        m = DATE_PATTERN.match(f.name)
        if not m:
            no_date.append(f.name)
            continue
        file_date = date.fromisoformat(m.group(1))
        if file_date < cutoff:
            dest = ARCHIVE_DIR / f.name
            if not args.dry_run:
                shutil.move(str(f), str(dest))
            moved.append(f"{f.name} ({file_date})")
        else:
            skipped.append(f"{f.name} ({file_date})")

    label = "[DRY RUN] " if args.dry_run else ""
    print(f"{label}Cutoff: {cutoff} (>{args.days} days old)")
    print(f"\n{label}ARCHIVED ({len(moved)}):")
    for x in moved:
        print(f"  {x}")
    print(f"\n{label}KEPT ({len(skipped)}):")
    for x in skipped:
        print(f"  {x}")
    if no_date:
        print(f"\n{label}NO-DATE (skipped, review manually) ({len(no_date)}):")
        for x in no_date:
            print(f"  {x}")


if __name__ == "__main__":
    main()
