"""
PDF generator -- fixed cover spacing and heading orphan control.
Catalyst Works Consulting -- Coastal Clarity design system.
"""

import re
import sys
import markdown
from pathlib import Path
from xhtml2pdf import pisa

SRC_MD = Path("d:/Ai_Sandbox/agentsHQ/docs/ai-governance/Bou_CW-AI-Governance-Final-Playbook-2026-04-16.md")
OUT_PDF = Path("d:/Ai_Sandbox/agentsHQ/docs/ai-governance/Bou_20260416_REPORT_AIGovernanceFinal_Internal_v1.pdf")

raw = SRC_MD.read_text(encoding="utf-8")
if raw.startswith("---"):
    end = raw.index("---", 3)
    raw = raw[end + 3:].lstrip()
raw = re.sub(r"\n---\n", "\n\n", raw)

body_html = markdown.markdown(raw, extensions=["tables", "fenced_code", "sane_lists"])


def convert_callouts(html):
    def replacer(m):
        inner = m.group(1)
        lm = re.match(r"<strong>(NOTE|TIP|WARNING|DECISION|EXAMPLE|KEY FINDING):</strong>", inner)
        if lm:
            label = lm.group(1)
            rest = inner[lm.end():].strip()
            lc = "#E07B2E" if label == "WARNING" else "#C49A2E"
            bg = "#FFF8F0" if label == "WARNING" else "#F4F6F8"
            bc = "#E07B2E" if label == "WARNING" else "#C49A2E"
            return (
                f'<div style="background:{bg};border-left:4px solid {bc};'
                f'padding:10px 14px;margin:12px 0;border-radius:4px;">'
                f'<strong style="color:{lc};font-size:9pt;text-transform:uppercase;">{label}:</strong> '
                f'<span style="color:#2C2C2C;">{rest}</span></div>'
            )
        return m.group(0)
    return re.sub(
        r"<blockquote>\s*<p>(.*?)</p>\s*</blockquote>",
        replacer, html, flags=re.DOTALL,
    )


body_html = convert_callouts(body_html)
body_html = re.sub(r'<pre><code[^>]*>', '<pre class="code-block"><code>', body_html)

CSS = """
@page {
    size: A4;
    margin: 25mm 20mm 25mm 20mm;
    @frame header_frame {
        -pdf-frame-content: header_content;
        top: 10mm; left: 20mm; right: 20mm; height: 10mm;
    }
    @frame footer_frame {
        -pdf-frame-content: footer_content;
        bottom: 10mm; left: 20mm; right: 20mm; height: 10mm;
    }
}

@page cover_page {
    margin: 0;
    @frame main_frame { left: 0; right: 0; top: 0; bottom: 0; }
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    color: #2C2C2C;
    line-height: 1.5;
}

/* Cover -- single full-bleed navy block, no inter-element whitespace gaps.
   All child elements use margin: 0 with only bottom spacing via margin-bottom.
   Keep total height of all elements well under 297mm - 36mm padding = 261mm. */
.cover {
    -pdf-page-template: cover_page;
    background-color: #1B2A4A;
    padding: 18mm 20mm 18mm 20mm;
    height: 297mm;
    width: 210mm;
}
.cover-category {
    font-size: 9pt;
    font-weight: bold;
    color: #C49A2E;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0 0 4mm 0;
    padding-top: 10mm;
}
.cover-title {
    font-size: 26pt;
    font-weight: bold;
    color: #FFFFFF;
    line-height: 1.15;
    margin: 0 0 4mm 0;
}
.cover-gold-bar {
    background-color: #C49A2E;
    height: 4px;
    margin: 0 0 4mm 0;
}
.cover-subtitle {
    font-size: 12pt;
    color: #FFFFFF;
    line-height: 1.4;
    margin: 0 0 5mm 0;
}
.cover-prepared {
    font-size: 9pt;
    color: #CCCCCC;
    margin: 0 0 3mm 0;
}
.cover-meta {
    font-size: 8pt;
    color: #999999;
    margin: 0;
}

/* Running header/footer */
#header_content {
    font-size: 8pt;
    color: #6B7280;
    border-bottom: 1px solid #E5E7EB;
    padding-bottom: 3pt;
}
#footer_content {
    font-size: 8pt;
    color: #6B7280;
    border-top: 1px solid #E5E7EB;
    padding-top: 3pt;
    text-align: center;
}

/* Headings -- orphan control.
   page-break-after: avoid alone is insufficient in xhtml2pdf.
   -pdf-keep-with-next: true keeps each heading glued to its following content.
   Both properties are required; never use one without the other. */
h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1B2A4A;
    margin-top: 20px;
    margin-bottom: 12px;
    line-height: 1.2;
    page-break-after: avoid;
    -pdf-keep-with-next: true;
}
h2 {
    font-size: 15pt;
    font-weight: bold;
    color: #1B2A4A;
    border-bottom: 2px solid #C49A2E;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 12px;
    page-break-after: avoid;
    -pdf-keep-with-next: true;
}
h3 {
    font-size: 12pt;
    font-weight: bold;
    color: #2D4A7A;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
    -pdf-keep-with-next: true;
}
h4 {
    font-size: 10pt;
    font-weight: bold;
    color: #2C2C2C;
    text-transform: uppercase;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
    -pdf-keep-with-next: true;
}

p { margin-bottom: 8px; line-height: 1.55; }

/* Tables */
table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 9pt; page-break-inside: avoid; }
thead tr { background-color: #1B2A4A; }
thead th { color: #FFFFFF; font-weight: bold; font-size: 9pt; padding: 8px 10px; text-align: left; border: 1px solid #2D4A7A; }
tbody tr:nth-child(even) { background-color: #F4F6F8; }
tbody td { color: #2C2C2C; font-size: 9pt; padding: 7px 10px; border: 1px solid #E5E7EB; vertical-align: top; }

/* Code */
pre.code-block { background-color: #2C2C2C; border-radius: 4px; padding: 12px; margin: 16px 0; page-break-inside: avoid; }
pre.code-block code { font-family: Courier, monospace; font-size: 8pt; color: #E8C86A; line-height: 1.5; background: transparent; }
code { font-family: Courier, monospace; font-size: 9pt; background-color: #F4F6F8; padding: 1px 4px; border-radius: 3px; color: #1B2A4A; }

/* Lists */
ul { margin: 8px 0 8px 20px; padding-left: 0; }
ul li { margin-bottom: 4px; font-size: 10pt; line-height: 1.5; list-style-type: disc; color: #2C2C2C; }
ol { margin: 8px 0 8px 20px; padding-left: 0; }
ol li { margin-bottom: 5px; font-size: 10pt; line-height: 1.5; color: #2C2C2C; }
"""

HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>{CSS}</style>
</head>
<body>

<div id="header_content">
  <table width="100%"><tr>
    <td>Catalyst Works Consulting</td>
    <td align="right">AI Governance Final Playbook 2026</td>
  </tr></table>
</div>

<div id="footer_content">
  Catalyst Works Consulting &nbsp;|&nbsp;
  <pdf:pagenumber /> of <pdf:pagecount />
  &nbsp;|&nbsp; 2026-04-16
</div>

<div class="cover">
  <div class="cover-category">Internal Strategic Report</div>
  <div class="cover-title">Catalyst Works AI Governance Final Playbook 2026</div>
  <div class="cover-gold-bar"></div>
  <div class="cover-subtitle">Operational AI Governance<br/>Where AI policy becomes margin protection</div>
  <div class="cover-prepared">Prepared for: Boubacar Barry, Founder - Catalyst Works Consulting</div>
  <div class="cover-meta">Date: 2026-04-16 &nbsp;&nbsp; Version 2.0 - Final &nbsp;&nbsp; Classification: Internal</div>
</div>

<pdf:nextpage />

<div class="content-body">
{body_html}
</div>

</body>
</html>"""

print("Rendering PDF with xhtml2pdf...")
with open(str(OUT_PDF), "wb") as f:
    result = pisa.CreatePDF(HTML, dest=f, encoding="utf-8")

if result.err:
    print(f"Errors: {result.err}")
    sys.exit(1)
else:
    print(f"PDF written: {OUT_PDF}")
    print(f"Size: {OUT_PDF.stat().st_size // 1024} KB")
