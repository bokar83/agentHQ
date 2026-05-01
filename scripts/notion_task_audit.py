"""Notion Task Audit harvester.

Walks markdown feeders, extracts atomic tasks, classifies each, upserts to Notion.

Usage:
    python scripts/notion_task_audit.py --dry-run
    python scripts/notion_task_audit.py
    python scripts/notion_task_audit.py --mode=sweep --window=14d

See docs/superpowers/specs/2026-05-01-notion-task-audit-design.md for the design.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_NOTION_TASK_DB_ID = "249bcf1a302980739c26c61cad212477"
DEFAULT_LLM_MODEL = "anthropic/claude-haiku-4-5"
HARD_LLM_CALL_CAP = 200
HARD_LIVE_ROW_CAP = 200


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Notion Task Audit harvester")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to Notion or audit files; print what would happen.",
    )
    parser.add_argument(
        "--stages",
        default="all",
        help="Comma-separated stages to run: walk,extract,classify,dedupe,upsert,write. Default: all.",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "sweep"],
        default="full",
        help="full = full archaeology pass. sweep = bi-monthly maintenance over a recent window.",
    )
    parser.add_argument(
        "--window",
        default="14d",
        help="For --mode=sweep, only include feeders modified within this window. Default 14d.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"notion_task_audit: mode={args.mode} stages={args.stages} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
