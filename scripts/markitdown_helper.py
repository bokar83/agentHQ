#!/usr/bin/env python3
"""
markitdown_helper.py — convert any artifact to clean Markdown.

Supported inputs:
  - Local file path (PDF, DOCX, PPTX, XLSX, HTML, images)
  - HTTP/HTTPS URL
  - YouTube URL (extracts transcript)

Usage:
  python scripts/markitdown_helper.py <path_or_url>
  python scripts/markitdown_helper.py <path_or_url> --out <output.md>
  python scripts/markitdown_helper.py <path_or_url> --print

Output:
  Writes Markdown to <source_stem>.md alongside the input file (local)
  or to workspace/markitdown/<slug>.md (URLs).
  Pass --out to override destination.
  Pass --print to stdout only (no file write).
"""

import argparse
import sys
import re
from pathlib import Path
from markitdown import MarkItDown


def slugify(text: str, maxlen: int = 60) -> str:
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^\w\s-]", "", text).strip()
    text = re.sub(r"[\s_]+", "-", text).lower()
    return text[:maxlen]


def convert(source: str, out_path: str | None, print_only: bool) -> None:
    m = MarkItDown()

    try:
        if source.startswith("http://") or source.startswith("https://"):
            result = m.convert_url(source)
            default_out = Path("workspace/markitdown") / f"{slugify(source)}.md"
        else:
            p = Path(source)
            if not p.exists():
                print(f"ERROR: file not found: {source}", file=sys.stderr)
                sys.exit(1)
            result = m.convert(str(p))
            default_out = p.with_suffix(".md")
    except Exception as e:
        print(f"ERROR: conversion failed: {e}", file=sys.stderr)
        sys.exit(1)

    md = result.text_content

    if print_only:
        sys.stdout.buffer.write(md.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        return

    dest = Path(out_path) if out_path else default_out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(md, encoding="utf-8")
    print(f"written: {dest}  ({len(md):,} chars)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert any artifact to Markdown.")
    parser.add_argument("source", help="File path or URL to convert")
    parser.add_argument("--out", help="Override output file path")
    parser.add_argument("--print", dest="print_only", action="store_true",
                        help="Print Markdown to stdout instead of writing a file")
    args = parser.parse_args()
    convert(args.source, args.out, args.print_only)


if __name__ == "__main__":
    main()
