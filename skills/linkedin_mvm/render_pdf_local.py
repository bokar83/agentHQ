"""
skills/linkedin_mvm/render_pdf_local.py
=======================================
Render the AI Governance Field Guide markdown to PDF using local Chrome's
headless --print-to-pdf mode. No Playwright, no chromium install.

Run from agentsHQ root:
  python -m skills.linkedin_mvm.render_pdf_local <source.md> <output.pdf>

Defaults to v4 source -> deliverables/ai-governance/<v4-name>.pdf if no args.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[2]

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page {
    size: A4;
    margin: 22mm 20mm 25mm 20mm;
}
html, body {
    font-family: 'Source Serif Pro', 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1d1d1f;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}
h1, h2, h3, h4 {
    font-family: 'Source Sans Pro', -apple-system, 'Helvetica Neue', Arial, sans-serif;
    color: #0f1d2e;
    line-height: 1.3;
    margin-top: 1.6em;
    margin-bottom: 0.5em;
    page-break-after: avoid;
}
h1 {
    font-size: 28pt;
    font-weight: 700;
    margin-top: 0;
    letter-spacing: -0.01em;
}
h2 {
    font-size: 17pt;
    font-weight: 600;
    border-bottom: 2px solid #0f1d2e;
    padding-bottom: 0.2em;
    margin-top: 2em;
}
h3 {
    font-size: 13pt;
    font-weight: 600;
    color: #2a3f56;
}
p {
    margin: 0 0 0.7em 0;
    text-align: justify;
    hyphens: auto;
}
ul, ol {
    margin: 0.4em 0 1em 1.5em;
    padding: 0;
}
li { margin-bottom: 0.35em; }
strong { font-weight: 600; color: #0f1d2e; }
em { color: #2a3f56; font-style: italic; }
hr {
    border: none;
    border-top: 1px solid #d4d4d4;
    margin: 1.8em 0;
}
blockquote {
    border-left: 3px solid #0f1d2e;
    padding-left: 1em;
    margin: 1em 0;
    color: #4a4a4a;
    font-style: italic;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 10pt;
}
th, td {
    border: 1px solid #d4d4d4;
    padding: 6px 10px;
    text-align: left;
    vertical-align: top;
}
th {
    background: #f4f6f8;
    font-family: 'Source Sans Pro', -apple-system, sans-serif;
    font-weight: 600;
    color: #0f1d2e;
}
.cover {
    page-break-after: always;
    text-align: left;
    padding-top: 30vh;
}
.cover h1 {
    font-size: 36pt;
    margin-bottom: 0.1em;
    line-height: 1.15;
}
.cover .subtitle {
    font-family: 'Source Sans Pro', -apple-system, sans-serif;
    font-size: 16pt;
    color: #2a3f56;
    margin-bottom: 4em;
    font-weight: 300;
    line-height: 1.4;
}
.cover .author {
    font-family: 'Source Sans Pro', -apple-system, sans-serif;
    font-size: 11pt;
    color: #1d1d1f;
    line-height: 1.7;
}
.cover .author .name { font-size: 13pt; font-weight: 600; }
.disclaimer {
    font-size: 9pt;
    color: #6b6b6b;
    font-style: italic;
    border-top: 1px solid #d4d4d4;
    padding-top: 1em;
    margin-top: 3em;
}
a {
    color: #0f1d2e;
    text-decoration: underline;
    word-break: break-all;
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="cover">
  <h1>{title}</h1>
  <div class="subtitle">{subtitle}</div>
  <div class="author">
    <span class="name">{author}</span><br>
    {firm}<br>
    {date}
  </div>
</div>
{body}
</body>
</html>
"""


def find_chrome() -> str:
    for p in CHROME_PATHS:
        if p and Path(p).exists():
            return p
    raise RuntimeError(f"Chrome / Edge not found. Tried: {CHROME_PATHS}")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    front = text[4:end].strip()
    body = text[end + 4:].lstrip("\n")
    meta: dict = {}
    for line in front.split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, body


def strip_redundant_cover_lines(body_md: str) -> str:
    """Source markdown also has H1 + cover info inline; strip so we don't double-print."""
    lines = body_md.split("\n")
    out: list[str] = []
    h1_seen = False
    skip_window = 0
    for ln in lines:
        if not h1_seen and ln.startswith("# "):
            h1_seen = True
            skip_window = 8
            continue
        if h1_seen and skip_window > 0:
            stripped = ln.strip()
            if stripped.startswith(("## ", "By ", "Catalyst", "April")) or stripped == "" or stripped == "---":
                skip_window -= 1
                continue
            else:
                skip_window = 0
        out.append(ln)
    # Drop one leading separator
    while out and out[0].strip() in ("", "---"):
        out.pop(0)
    return "\n".join(out)


def render_html(source_md: Path, meta_overrides: dict | None = None) -> str:
    text = source_md.read_text(encoding="utf-8")
    meta, body_md = parse_frontmatter(text)
    if meta_overrides:
        meta.update(meta_overrides)
    body_md = strip_redundant_cover_lines(body_md)
    body_html = markdown.markdown(
        body_md,
        extensions=["extra", "sane_lists", "smarty", "tables"],
    )
    return HTML_TEMPLATE.format(
        title=meta.get("title", "AI Governance Field Guide"),
        subtitle=meta.get("subtitle", "A Field Guide for the Founder Who Still Runs the Business"),
        author=meta.get("author", "Boubacar Barry"),
        firm=meta.get("firm", "Catalyst Works Consulting"),
        date=meta.get("date", "April 2026"),
        css=CSS,
        body=body_html,
    )


def chrome_print_to_pdf(html: str, out_pdf: Path, chrome_path: str) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="fg_render_"))
    try:
        html_file = tmp_dir / "doc.html"
        html_file.write_text(html, encoding="utf-8")
        # file:/// URL format
        file_url = "file:///" + str(html_file).replace("\\", "/")
        cmd = [
            chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out_pdf}",
            "--no-margins",
            "--virtual-time-budget=10000",
            file_url,
        ]
        subprocess.run(cmd, check=True, timeout=90)
        if not out_pdf.exists():
            raise RuntimeError(f"Chrome did not produce PDF at {out_pdf}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?",
                    default=str(ROOT / "docs" / "ai-governance" / "CONTENT_AIGovernance_reference_2026-04-30_field-guide-public-v4.md"),
                    help="Markdown source file")
    ap.add_argument("output", nargs="?",
                    default=str(ROOT / "deliverables" / "ai-governance" / "CONTENT_AIGovernance_reference_2026-04-30_field-guide-public-v4.pdf"),
                    help="PDF output path")
    args = ap.parse_args()

    source = Path(args.source)
    output = Path(args.output)
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        return 2

    chrome = find_chrome()
    print(f"Chrome: {chrome}")
    print(f"Source: {source}")
    print(f"Output: {output}")

    html = render_html(source)
    chrome_print_to_pdf(html, output, chrome)
    size_kb = output.stat().st_size / 1024
    print(f"PDF written: {output}  ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
