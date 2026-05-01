"""
skills/linkedin_mvm/md_to_pdf.py
================================
Render a Markdown file to a clean PDF using markdown -> HTML -> Playwright.

Designed for the LinkedIn MVM AI Governance Field Guide. Professional layout,
serif body, sans-serif headers, A4, page numbers, running footer.

Run inside orc-crewai container:
  docker exec orc-crewai python3 -m skills.linkedin_mvm.md_to_pdf \\
      /app/path/to/source.md /app/path/to/output.pdf
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import markdown


CSS = """
@page {
    size: A4;
    margin: 22mm 20mm 25mm 20mm;
    @bottom-left {
        content: "AI Governance for Owner-Operator Firms | Catalyst Works | April 2026";
        font-family: 'Source Sans Pro', 'Helvetica', sans-serif;
        font-size: 8pt;
        color: #6b6b6b;
    }
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-family: 'Source Sans Pro', 'Helvetica', sans-serif;
        font-size: 8pt;
        color: #6b6b6b;
    }
}
@page :first {
    @bottom-left { content: ""; }
    @bottom-right { content: ""; }
}
html, body {
    font-family: 'Source Serif Pro', 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1d1d1f;
    margin: 0;
    padding: 0;
}
h1, h2, h3, h4 {
    font-family: 'Source Sans Pro', 'Helvetica', sans-serif;
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
    font-size: 18pt;
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
li {
    margin-bottom: 0.4em;
}
strong { font-weight: 600; color: #0f1d2e; }
em { color: #2a3f56; }
hr {
    border: none;
    border-top: 1px solid #d4d4d4;
    margin: 2em 0;
}
blockquote {
    border-left: 3px solid #0f1d2e;
    padding-left: 1em;
    margin: 1em 0;
    color: #4a4a4a;
    font-style: italic;
}
.cover {
    page-break-after: always;
    text-align: left;
    padding-top: 35vh;
}
.cover h1 {
    font-size: 38pt;
    margin-bottom: 0.1em;
}
.cover .subtitle {
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 18pt;
    color: #2a3f56;
    margin-bottom: 4em;
    font-weight: 300;
}
.cover .author {
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 12pt;
    color: #1d1d1f;
    line-height: 1.6;
}
.cover .author strong { font-size: 13pt; }
.disclaimer {
    font-size: 9pt;
    color: #6b6b6b;
    font-style: italic;
    border-top: 1px solid #d4d4d4;
    padding-top: 1em;
    margin-top: 3em;
}
a { color: #0f1d2e; text-decoration: underline; }
"""


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&family=Source+Serif+Pro:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
{cover}
{body}
</body>
</html>
"""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Strip YAML frontmatter; return (metadata, body)."""
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


def build_cover(meta: dict) -> str:
    title = meta.get("title", "AI Governance for Owner-Operator Firms")
    subtitle = meta.get("subtitle", "A Field Guide")
    author = meta.get("author", "Boubacar Barry")
    firm = meta.get("firm", "Catalyst Works Consulting")
    date = meta.get("date", "April 2026")
    return f"""
<div class="cover">
  <h1>{title}</h1>
  <div class="subtitle">{subtitle}</div>
  <div class="author">
    <strong>{author}</strong><br>
    {firm}<br>
    {date}
  </div>
</div>
"""


async def render_pdf(html: str, out_path: Path) -> None:
    from playwright.async_api import async_playwright
    out_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(
            path=str(out_path),
            format="A4",
            margin={"top": "22mm", "bottom": "25mm", "left": "20mm", "right": "20mm"},
            print_background=True,
            display_header_footer=True,
            footer_template='''
                <div style="font-size:8pt;font-family:Helvetica;color:#6b6b6b;width:100%;padding:0 18mm;display:flex;justify-content:space-between;">
                    <span>AI Governance for Owner-Operator Firms | Catalyst Works | April 2026</span>
                    <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
                </div>
            ''',
            header_template='<div></div>',
        )
        await browser.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path, help="Markdown source file")
    p.add_argument("output", type=Path, help="PDF output path")
    args = p.parse_args()

    if not args.source.exists():
        print(f"ERROR: source not found: {args.source}")
        return 2

    text = args.source.read_text(encoding="utf-8")
    meta, body_md = parse_frontmatter(text)

    # The first H1 in the body is redundant with the cover title; strip it.
    lines = body_md.split("\n")
    cleaned: list[str] = []
    h1_seen = False
    h2_skip = 0
    for ln in lines:
        if not h1_seen and ln.startswith("# "):
            h1_seen = True
            continue
        # The "## A Field Guide" + author block right after H1 in our doc are also
        # duplicates of cover. Skip a small number of lines after the H1 strip.
        if h1_seen and h2_skip < 6 and ln.strip().startswith(("## ", "By ", "Catalyst", "April", "Boubacar")):
            h2_skip += 1
            continue
        cleaned.append(ln)
    body_md = "\n".join(cleaned)

    body_html = markdown.markdown(
        body_md,
        extensions=["extra", "sane_lists", "smarty", "tables"],
    )

    html = HTML_TEMPLATE.format(
        title=meta.get("title", "AI Governance Field Guide"),
        css=CSS,
        cover=build_cover(meta),
        body=body_html,
    )

    asyncio.run(render_pdf(html, args.output))
    print(f"PDF written: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
