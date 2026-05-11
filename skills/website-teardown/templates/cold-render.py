"""Render cold-teardown .md files to rich HTML using the full repertoire.
- TL;DR card (with fit score, /100 normalized)
- Before/After mandates per leak
- Paste-ready email card
- Collapsible analysis notes
- Card-grid index
Run: python render.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent

STYLE = """
:root {
  --bg:#0f1115; --panel:#161a22; --panel-2:#1c2230; --ink:#e8eaed; --ink-dim:#9aa3b2;
  --accent:#c9a84c; --accent-2:#e8c468; --line:#232936; --warn:#ff8b6b; --ok:#5fb878;
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  padding:2rem 1rem 6rem; }
.wrap { max-width: 820px; margin: 0 auto; }
.nav { margin-bottom: 1.5rem; }
.nav a { color: var(--accent); text-decoration: none; font-size: 14px; }
.nav a:hover { text-decoration: underline; }

h1 { font-size: 30px; line-height: 1.18; margin: 0 0 0.3em; letter-spacing: -0.015em; }
.tagline { color: var(--ink-dim); margin: 0 0 1.8em; font-size: 15px; }

.tldr {
  background: linear-gradient(135deg, #1a1f2b, #161a22);
  border: 1px solid var(--accent); border-radius: 10px;
  padding: 1.4em 1.5em; margin-bottom: 2.5em;
  display: grid; grid-template-columns: 1fr auto; gap: 1.5em; align-items: center;
}
@media (max-width: 600px) { .tldr { grid-template-columns: 1fr; } }
.tldr-label { display:inline-block; background:var(--accent); color:#0a0c10;
  font-size:11px; font-weight:700; letter-spacing:0.08em;
  padding:3px 8px; border-radius:3px; margin-bottom:0.6em; }
.tldr h2 { font-size: 20px; margin: 0 0 0.5em; color: var(--accent-2); }
.tldr p { margin: 0.4em 0 0; font-size: 15.5px; color: var(--ink); }
.tldr strong { color: #fff; }

.score-pill { text-align:center; min-width:120px; }
.score-num { font-size:42px; font-weight:700; line-height:1; color: var(--score, var(--ok)); }
.score-denom { font-size: 18px; color: var(--ink-dim); }
.score-label { font-size:11px; letter-spacing:0.1em; color:var(--ink-dim); margin-top:0.3em; text-transform:uppercase; }

.verdict-badge { display:inline-block; padding:4px 10px; border-radius:4px;
  font-size:12px; font-weight:700; letter-spacing:0.08em; }
.v-send { background: var(--ok); color: #0a0c10; }
.v-skip { background: var(--warn); color: #0a0c10; }

section { margin: 2.5em 0; }
h2.section-h { font-size: 21px; color: var(--accent);
  border-bottom: 1px solid var(--line); padding-bottom: 0.4em; margin-bottom: 1em; }

.email-card {
  background: #0a0c10; border: 1px solid var(--accent); border-radius: 6px;
  padding: 1.2em 1.4em; margin: 1em 0;
  font-family: "SF Mono", Menlo, Consolas, monospace;
  font-size: 14.5px; line-height: 1.55;
  white-space: pre-wrap; color: #cdd2dc; position: relative;
}
.email-card .subj { color: var(--accent); font-weight: 600; display:block; margin-bottom: 0.8em; }
.email-card .sig { color: var(--ink-dim); }
.copy-hint { position:absolute; top:8px; right:12px; font-size:11px;
  color:var(--ink-dim); font-family: -apple-system, sans-serif; }

.leak {
  background: var(--panel); border-left: 3px solid var(--warn);
  padding: 1em 1.2em; margin: 0.8em 0; border-radius: 4px;
}
.leak-num { color: var(--warn); font-weight:700; font-size:12px;
  letter-spacing:0.1em; margin-bottom:0.4em; display:block; }
.leak h4 { margin: 0 0 0.5em; font-size: 16.5px; color: #fff; }
.leak p { margin: 0.4em 0; font-size: 15px; }
.leak .verify { color: var(--ink-dim); font-size: 14px; font-style: italic; }

.fix {
  background: var(--panel); border-left: 3px solid var(--ok);
  padding: 1em 1.2em; margin: 0.8em 0; border-radius: 4px;
}
.fix-num { color: var(--ok); font-weight:700; font-size:12px;
  letter-spacing:0.1em; margin-bottom:0.4em; display:block; }
.fix h4 { margin: 0 0 0.4em; font-size: 16px; color: #fff; }
.fix p { margin: 0; font-size: 15px; }

details {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 6px; padding: 0.7em 1.2em; margin-bottom: 0.6em;
}
summary { cursor: pointer; font-weight: 600; font-size: 16px;
  list-style: none; color: var(--accent-2); padding: 0.3em 0; }
summary::-webkit-details-marker { display: none; }
summary::before { content: "\\25B8"; display: inline-block; margin-right: 0.6em;
  color: var(--ink-dim); transition: transform 0.15s; }
details[open] summary::before { transform: rotate(90deg); }
.notes-grid { display:grid; gap:0.5em; padding-top:0.7em; }
.note-row { display:grid; grid-template-columns: 200px 1fr; gap:1em;
  padding:0.4em 0; border-bottom: 1px solid var(--line); font-size: 14.5px; }
.note-row:last-child { border-bottom: none; }
.note-row .k { color: var(--ink-dim); }

.hook-card {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 6px; padding: 1em 1.2em; margin: 0.8em 0;
}
.hook-card .label { font-size:11px; color:var(--accent); font-weight:700;
  letter-spacing:0.08em; margin-bottom:0.3em; display:block; }
.hook-card .text { font-size: 16px; color: #fff; }

.foot { color: var(--ink-dim); font-size: 12px; text-align: center; margin-top: 4em; }
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{style}</style>
</head>
<body>
<div class="wrap">
<div class="nav"><a href="index.html">&larr; All teardowns</a></div>

<h1>{biz}</h1>
<p class="tagline">{niche} &middot; {city} &middot; <a href="{site}" style="color:var(--accent);">{site_label}</a> &middot; <a href="mailto:{owner}" style="color:var(--accent);">{owner}</a></p>

<div class="tldr">
<div>
<span class="tldr-label">TL;DR</span>
<h2>{tldr_h}</h2>
<p>{tldr_body}</p>
</div>
<div class="score-pill" style="--score: {score_color};">
<div class="score-num">{score_100}<span class="score-denom">/100</span></div>
<div class="score-label">Cold-send fit</div>
<div style="margin-top:0.6em;"><span class="verdict-badge v-send">{verdict}</span></div>
</div>
</div>

<section>
<h2 class="section-h">Paste-ready email</h2>
<div class="email-card"><span class="copy-hint">copy &amp; send</span>{email_html}</div>
</section>

<section>
<h2 class="section-h">Subject options</h2>
<div class="hook-card"><span class="label">OPTION A</span><div class="text">{subj_a}</div></div>
<div class="hook-card"><span class="label">OPTION B</span><div class="text">{subj_b}</div></div>
</section>

<section>
<h2 class="section-h">3 conversion leaks</h2>
{leaks_html}
</section>

<section>
<h2 class="section-h">3 fixes Signal Works would ship</h2>
{fixes_html}
</section>

<details>
<summary>Internal analysis notes</summary>
<div class="notes-grid">
{notes_html}
</div>
</details>

<div class="foot">agent_outputs/teardowns/{filename} &middot; localhost:8765</div>
</div>
</body>
</html>
"""

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cold Teardowns - Batch Index</title>
<style>
:root {{ --bg:#0f1115;--panel:#161a22;--ink:#e8eaed;--ink-dim:#9aa3b2;
  --accent:#c9a84c;--line:#232936;--ok:#5fb878;--warn:#ff8b6b; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  padding: 2.5rem 1rem 4rem; }}
.wrap {{ max-width: 820px; margin: 0 auto; }}
h1 {{ font-size: 30px; margin: 0 0 0.3em; letter-spacing: -0.015em; }}
.sub {{ color: var(--ink-dim); margin: 0 0 2em; }}
.batch-tldr {{
  background: linear-gradient(135deg, #1a1f2b, #161a22);
  border: 1px solid var(--accent); border-radius: 10px;
  padding: 1.2em 1.4em; margin-bottom: 2em;
}}
.batch-tldr .label {{ display:inline-block; background:var(--accent); color:#0a0c10;
  font-size:11px; font-weight:700; letter-spacing:0.08em;
  padding:3px 8px; border-radius:3px; margin-bottom:0.6em; }}
.batch-tldr h2 {{ font-size:19px; color:var(--accent); margin:0 0 0.5em; }}
.batch-tldr p {{ margin: 0.4em 0; font-size: 15px; }}
.card {{ display:grid; grid-template-columns: 1fr auto; align-items:center; gap:1em;
  background:var(--panel); border:1px solid var(--line); border-radius:8px;
  padding:1.1em 1.3em; margin-bottom:0.9em; text-decoration:none; color:var(--ink);
  transition: border-color 0.15s; }}
.card:hover {{ border-color: var(--accent); }}
.card-title {{ font-size:18px; font-weight:600; color:#fff; margin-bottom:0.2em; }}
.card-meta {{ color: var(--ink-dim); font-size:13.5px; }}
.card-score {{ text-align:center; min-width:60px; }}
.card-score .n {{ font-size:24px; font-weight:700; color:var(--score, var(--ok)); line-height:1; }}
.card-score .d {{ font-size: 11px; color:var(--ink-dim); }}
.card-tag {{ display:inline-block; background:var(--ok); color:#0a0c10;
  padding:1px 7px; border-radius:3px; font-size:11px; font-weight:700; margin-left:0.5em; }}
.foot {{ color: var(--ink-dim); font-size:12px; text-align:center; margin-top:3em; }}
</style>
</head>
<body>
<div class="wrap">
<h1>Cold Teardowns - Batch 1</h1>
<p class="sub">3 Utah trade leads &middot; status=new &middot; council-aligned templates &middot; ready to send</p>

<div class="batch-tldr">
<span class="label">BATCH STATUS</span>
<h2>3 / 3 ready. Average cold-send fit: {avg_score}/100.</h2>
<p>All 3 use the council-mandated frame: <strong>witnessed loss, not findings</strong>. No referral-anchor P.S. yet (first SW client lands EOW). Calendly CTA hardcoded. Send via gws to both inboxes.</p>
<p style="color:var(--ink-dim);font-size:13px;margin-top:0.7em;">Council ceiling without referral anchor: ~1% reply rate. With anchor (batch 2+): 5-10%.</p>
</div>

{cards}

<p style="margin-top:2em;"><a href="council-review.html" style="color:var(--accent);">View full Sankofa Council Review &rarr;</a></p>

<div class="foot">agent_outputs/teardowns/index.html &middot; localhost:8765</div>
</div>
</body>
</html>
"""


def extract_meta(text):
    meta = {"niche": "", "city": "", "owner": "", "site": "", "biz": ""}
    biz_match = re.search(r"^#\s+(.+?)\s+(?:—|--)\s+Cold Teardown", text, re.M)
    if biz_match: meta["biz"] = biz_match.group(1).strip()
    for line in text.splitlines()[:10]:
        m = re.search(r"\*\*Niche:\*\*\s*([^|]+)", line)
        if m: meta["niche"] = m.group(1).strip()
        m = re.search(r"\*\*City:\*\*\s*([^|]+)", line)
        if m: meta["city"] = m.group(1).strip()
        m = re.search(r"\*\*Owner:\*\*\s*(\S+)", line)
        if m: meta["owner"] = m.group(1).strip()
        m = re.search(r"\*\*Site:\*\*\s*(\S+)", line)
        if m: meta["site"] = m.group(1).strip()
    return meta


def extract_section(text, header_contains):
    """Find a ## header containing header_contains substring, return body until next ## or EOF."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and header_contains.lower() in line.lower():
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def extract_subjects(text):
    a = re.search(r"\*\*Subject line option A:\*\*\s*(.+)", text)
    b = re.search(r"\*\*Subject line option B:\*\*\s*(.+)", text)
    return (a.group(1).strip() if a else ""), (b.group(1).strip() if b else "")


def extract_email_body(text):
    return extract_section(text, "Cold-Email Body")


def extract_leaks(text):
    sec = extract_section(text, "The Reality")
    leaks = []
    pattern = re.compile(r"###\s+Leak\s+(\d+):\s*(.+?)\n(.*?)(?=###\s+Leak\s+\d+:|\Z)", re.S)
    for m in pattern.finditer(sec):
        num = m.group(1)
        title = m.group(2).strip()
        body = m.group(3).strip()
        what = re.search(r"\*\*What's happening:\*\*\s*(.+?)(?=\*\*Why|\Z)", body, re.S)
        why = re.search(r"\*\*Why it costs them money:\*\*\s*(.+?)(?=\*\*How|\Z)", body, re.S)
        verify = re.search(r"\*\*How they can verify in 60 sec:\*\*\s*(.+?)$", body, re.S)
        leaks.append({
            "num": num, "title": title,
            "what": what.group(1).strip() if what else "",
            "why": why.group(1).strip() if why else "",
            "verify": verify.group(1).strip() if verify else "",
        })
    return leaks


def extract_fixes(text):
    sec = extract_section(text, "The Redesign Blueprint")
    fixes = []
    for m in re.finditer(r"^(\d+)\.\s+\*\*(.+?):\*\*\s*(.+?)(?=\n\d+\.|\Z)", sec, re.M | re.S):
        fixes.append({
            "num": m.group(1),
            "title": m.group(2).strip(),
            "body": m.group(3).strip(),
        })
    return fixes


def extract_notes(text):
    sec = extract_section(text, "Analysis Notes")
    notes = []
    for m in re.finditer(r"-\s+\*\*(.+?):\*\*\s*(.+)", sec):
        notes.append((m.group(1).strip(), m.group(2).strip()))
    return notes


def extract_fit_score(text):
    m = re.search(r"\*\*Internal fit score \(1-10\):\*\*\s*(\d+)", text)
    return int(m.group(1)) if m else 5


def extract_hook(text):
    m = re.search(r"\*\*Opening hook[^:]*:\*\*\s*(.+)", text)
    return m.group(1).strip() if m else ""


def score_color(score_100):
    if score_100 >= 80: return "var(--ok)"
    if score_100 >= 60: return "var(--accent)"
    return "var(--warn)"


def render_email_html(body):
    # body opens with "Subject: ..." line
    subj_match = re.match(r"Subject:\s*(.+?)\n", body)
    if subj_match:
        subj = subj_match.group(1).strip()
        rest = body[subj_match.end():].strip()
        return f'<span class="subj">Subject: {subj}</span>{rest}'
    return body


def main():
    md_files = sorted(HERE.glob("*_teardown.md"))
    cards = []
    scores = []
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        meta = extract_meta(text)
        biz = meta["biz"] or md.stem
        fit_10 = extract_fit_score(text)
        score_100 = fit_10 * 10
        scores.append(score_100)
        sa, sb = extract_subjects(text)
        email_body = extract_email_body(text)
        email_html = render_email_html(email_body)
        hook = extract_hook(text)
        leaks = extract_leaks(text)
        fixes = extract_fixes(text)
        notes = extract_notes(text)

        leaks_html = ""
        for lk in leaks:
            leaks_html += (
                f'<div class="leak"><span class="leak-num">LEAK {lk["num"]}</span>'
                f'<h4>{lk["title"]}</h4>'
                f'<p><strong>What\'s happening:</strong> {lk["what"]}</p>'
                f'<p><strong>Why it costs them money:</strong> {lk["why"]}</p>'
                f'<p class="verify">Verify in 60 sec: {lk["verify"]}</p></div>'
            )
        fixes_html = ""
        for fx in fixes:
            fixes_html += (
                f'<div class="fix"><span class="fix-num">FIX {fx["num"]}</span>'
                f'<h4>{fx["title"]}</h4><p>{fx["body"]}</p></div>'
            )
        notes_html = ""
        for k, v in notes:
            notes_html += f'<div class="note-row"><div class="k">{k}</div><div>{v}</div></div>'

        site_label = meta["site"].replace("https://", "").replace("http://", "").rstrip("/")
        page = PAGE.format(
            title=biz,
            style=STYLE,
            biz=biz,
            niche=meta["niche"], city=meta["city"], site=meta["site"],
            site_label=site_label, owner=meta["owner"],
            tldr_h=f"{biz.split(',')[0]} = SEND.",
            tldr_body=hook or "Council-aligned cold email ready to ship.",
            score_100=score_100, score_color=score_color(score_100),
            verdict="SEND",
            email_html=email_html,
            subj_a=sa, subj_b=sb,
            leaks_html=leaks_html, fixes_html=fixes_html, notes_html=notes_html,
            filename=md.name.replace(".md", ".html"),
        )
        out = HERE / md.name.replace(".md", ".html")
        out.write_text(page, encoding="utf-8")
        print(f"wrote {out.name}")

        cards.append(
            f'<a class="card" href="{out.name}" style="--score: {score_color(score_100)};">'
            f'<div><div class="card-title">{biz}</div>'
            f'<div class="card-meta">{meta["niche"]} &middot; {meta["city"]} &middot; {meta["owner"]} '
            f'<span class="card-tag">SEND</span></div></div>'
            f'<div class="card-score"><div class="n">{score_100}</div><div class="d">/100</div></div>'
            f'</a>'
        )

    avg = round(sum(scores) / len(scores)) if scores else 0
    index = HERE / "index.html"
    index.write_text(INDEX.format(cards="\n".join(cards), avg_score=avg), encoding="utf-8")
    print(f"wrote index.html ({len(md_files)} cards, avg={avg})")


if __name__ == "__main__":
    main()
