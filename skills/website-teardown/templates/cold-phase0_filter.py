"""Phase 0: Cold-mode pre-filter for cold-teardown skill.
Decides PURSUE / DEFER / DROP per lead before running full teardown.
Cheap: 1 HTTP fetch + 1 Haiku call per site. ~$0.001 each.
Outputs phase0-board.html in this dir.
Usage: python phase0_filter.py
"""
import json
import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("d:/Ai_Sandbox/agentsHQ/.env")

HERE = Path(__file__).parent
OUT = HERE / "phase0-board.html"

# === Backlog: 10 remaining (batch 1 already done) ===
LEADS = [
    {"id": 2625, "name": "Fisher HVAC",                            "niche": "HVAC",         "city": "Salt Lake City", "reviews": "139 (4.9★)", "url": "https://fisherhvacslc.com/",          "email": "fisherhvac1@gmail.com"},
    {"id": 2628, "name": "Snowbird Roofing & Siding LLC",          "niche": "Roofing",      "city": "Provo / Orem",   "reviews": "106 (4.8★)", "url": "https://snowbirdroofingandsiding.com/","email": "snowbird@roofinghandsiding.com"},
    {"id": 2614, "name": "Elevated Sport and Spine",                "niche": "Chiropractic", "city": "Salt Lake City", "reviews": "32 (5.0★)",  "url": "https://www.elevatedsportandspine.com/","email": "elevatedsportandspine@gmail.com"},
    {"id": 2611, "name": "Park City Children's Dental Specialist",  "niche": "Dental",       "city": "Salt Lake City", "reviews": "124 (4.9★)", "url": "http://www.pcdentalkids.com/",        "email": "info@pcdentalkids.com"},
    {"id": 2624, "name": "Maple Ridge Chiropractic & Massage",      "niche": "Chiropractic", "city": "Provo",          "reviews": "121 (4.9★)", "url": "http://mrchiro.com/",                 "email": "mapleridgechiropractic@gmail.com"},
    {"id": 2630, "name": "Mr. Rooter Plumbing of Provo-Orem",       "niche": "Plumbing",     "city": "Provo",          "reviews": "34 (4.9★)",  "url": "https://mrrooter.com/provo-orem/",    "email": "bridget.mcneil@mrrooter.com"},
    {"id": 2627, "name": "Dr. Gary Wilson",                         "niche": "Dental",       "city": "Provo",          "reviews": "48 (4.5★)",  "url": "https://provofamilydentistry.com/",   "email": "info@provofamilydentistry.com"},
    {"id": 2626, "name": "Salt Lake Chiropractic Sports & Wellness","niche": "Chiropractic", "city": "Salt Lake City", "reviews": "37 (5.0★)",  "url": "https://murray-sports-mall-chiropractor.com/","email": "docaltman@protonmail.com"},
    {"id": 2613, "name": "Peterson Plumbing Supply",                "niche": "Plumbing Supply", "city": "Provo",       "reviews": "49 (4.6★)",  "url": "https://petersonplumbingsupply.com/", "email": "jennie@petersonplumbingsupply.com"},
    {"id": 2623, "name": "QXO",                                     "niche": "Roofing",      "city": "Provo",          "reviews": "54 (4.4★)",  "url": "https://www.qxo.com/",                "email": "ben.eddy@qxo.com"},
]


def fetch_site(url: str, timeout: int = 15) -> tuple[str, dict]:
    """Return (html, signals_dict). Lenient on SSL since target sites vary in cert health."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            raw = resp.read()
            size_kb = len(raw) // 1024
            html = raw.decode("utf-8", errors="ignore")
    except Exception as e:
        return "", {"fetch_error": str(e)[:200], "html_size_kb": 0}

    signals = {"html_size_kb": size_kb}
    # copyright year
    yrs = re.findall(r"(?:©|&copy;|copyright)\s*(?:\w+\s+)?(\d{4})", html, re.I)
    signals["copyright_years"] = sorted(set(yrs))[-3:] if yrs else []
    # viewport meta
    signals["mobile_viewport"] = bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html, re.I))
    # framework hints
    signals["wix"] = "wix.com" in html.lower() or "wixstatic" in html.lower()
    signals["squarespace"] = "squarespace" in html.lower()
    signals["wordpress"] = "wp-content" in html.lower() or "wp-includes" in html.lower()
    signals["tailwind"] = "tailwind" in html.lower()
    signals["bootstrap3"] = "bootstrap/3." in html.lower() or "bootstrap-3" in html.lower()
    # carousel / slideshow markers
    signals["slideshow"] = bool(re.search(r"slick|carousel|slideshow|owl-carousel|swiper", html, re.I))
    # form field count (rough)
    inputs = re.findall(r'<input[^>]+type=["\'](?!hidden|submit|button)[^"\']*["\']', html, re.I)
    textareas = re.findall(r"<textarea", html, re.I)
    selects = re.findall(r"<select", html, re.I)
    signals["form_inputs_visible"] = len(inputs) + len(textareas) + len(selects)
    # schema markup
    signals["jsonld_schema"] = "application/ld+json" in html.lower()
    # "Built by" agency credit (hard-stop hint)
    built_by = re.search(r"(?:built|designed|powered|website)\s+by\s+([^<\n]{3,60})", html, re.I)
    signals["built_by_credit"] = built_by.group(0).strip()[:80] if built_by else ""
    # title + h1
    t = re.search(r"<title[^>]*>([^<]+)", html, re.I)
    signals["title"] = (t.group(1).strip() if t else "")[:200]
    h1 = re.findall(r"<h1[^>]*>([^<]+)", html, re.I)
    signals["h1"] = [x.strip()[:120] for x in h1[:3]]
    # 404 / closed business hints
    body_lower = html.lower()
    signals["site_404_or_closed"] = (
        "404" in (signals["title"] or "").lower()
        or "this domain is for sale" in body_lower
        or "site is currently unavailable" in body_lower
        or "permanently closed" in body_lower
    )

    return html, signals


def classify_via_llm(lead: dict, signals: dict, html_snippet: str) -> dict:
    """Call OpenRouter Haiku 4.5 for a structured verdict."""
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )

    system = """You are a website-pre-filter for Signal Works, an agency that rebuilds local trade-business websites in Utah.

Decide whether THIS site is worth a full conversion-teardown email pitch. Score on "datedness + conversion-leak surface area". Higher = bigger gap between current site and modern standard = better pitch target.

Return STRICT JSON only:
{
  "datedness_score": 0-100,
  "verdict": "PURSUE" | "DEFER" | "DROP",
  "verdict_reason": "one-sentence why",
  "hard_stop": null | "agency_owned" | "site_dead" | "closed_business" | "already_modern" | "out_of_scope",
  "leaks_visible": ["3-7 specific things that look broken or outdated"],
  "tier_estimate": "Signal Works baseline" | "Signal Works Pro" | "Catalyst Works custom" | null,
  "owner_eyetest_one_liner": "one sentence Boubacar would read to remember this site"
}

Scoring rubric:
- 70-100 = PURSUE. Dated (pre-2022 design language), slow, broken forms, no mobile sticky CTA, generic template, big conversion-leak surface.
- 40-69 = DEFER. Mid-tier. Modernish but craft-gap exists. Not urgent; revisit later.
- 0-39 = DROP. Already polished or fundamentally fine. No pitch to make.

Hard-stop rules (auto-DROP regardless of score):
- "agency_owned": footer credits a marketing agency ("Built by", "Designed by"). They're already a competitor client.
- "site_dead": fetch failed, 404, domain expired, "site unavailable"
- "closed_business": "permanently closed", no products, no CTA
- "already_modern": clearly Apple-tier, dark-mode-toggle, custom animations, full-bleed video hero — nothing to fix
- "out_of_scope": national chain or corporate giant (e.g. QXO is a multi-billion-dollar roll-up), not an owner-operated trade business

When in doubt between PURSUE and DEFER, lean PURSUE if there's any obvious form/mobile/copyright signal. Boubacar would rather see one extra option than miss a deal."""

    user = f"""LEAD: {lead['name']} — {lead['niche']} — {lead['city']}
URL: {lead['url']}
Google reviews: {lead['reviews']}

SIGNALS (from auto-scan):
{json.dumps(signals, indent=2)}

HTML SNIPPET (first 6000 chars of the homepage):
{html_snippet[:6000]}

Return JSON verdict only."""

    try:
        resp = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
        raw = resp.choices[0].message.content.strip()
        # strip ```json fences if present
        raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.M).strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "datedness_score": 0,
            "verdict": "DROP",
            "verdict_reason": f"LLM error: {str(e)[:120]}",
            "hard_stop": "site_dead",
            "leaks_visible": [],
            "tier_estimate": None,
            "owner_eyetest_one_liner": "LLM classification failed",
        }


def process_lead(lead: dict) -> dict:
    print(f"[{lead['id']}] fetching {lead['url']}...", flush=True)
    html, signals = fetch_site(lead["url"])
    if signals.get("fetch_error") or signals.get("site_404_or_closed"):
        verdict = {
            "datedness_score": 0,
            "verdict": "DROP",
            "verdict_reason": signals.get("fetch_error") or "Site 404 / closed business signals",
            "hard_stop": "site_dead",
            "leaks_visible": [],
            "tier_estimate": None,
            "owner_eyetest_one_liner": "Could not load site",
        }
    else:
        verdict = classify_via_llm(lead, signals, html)
    out = {**lead, "signals": signals, "verdict": verdict}
    print(f"[{lead['id']}] {verdict['verdict']} ({verdict['datedness_score']}/100) — {verdict['verdict_reason'][:80]}", flush=True)
    return out


def render_board(results: list[dict]) -> str:
    # group by verdict
    pursue = [r for r in results if r["verdict"]["verdict"] == "PURSUE"]
    defer  = [r for r in results if r["verdict"]["verdict"] == "DEFER"]
    drop   = [r for r in results if r["verdict"]["verdict"] == "DROP"]

    def score_color(s):
        if s >= 70: return "var(--ok)"
        if s >= 40: return "var(--accent)"
        return "var(--warn)"

    def render_card(r):
        v = r["verdict"]
        s = v["datedness_score"]
        c = score_color(s)
        verdict_tag = {"PURSUE": "v-pursue", "DEFER": "v-defer", "DROP": "v-drop"}[v["verdict"]]
        hard_stop = f' &middot; <span class="hard-stop">HARD STOP: {v["hard_stop"]}</span>' if v.get("hard_stop") else ""
        leaks = v.get("leaks_visible") or []
        leaks_html = "".join(f"<li>{x}</li>" for x in leaks) if leaks else "<li style='color:var(--ink-dim)'>(no leaks listed)</li>"
        sig = r["signals"]
        sig_chips = []
        if sig.get("wix"): sig_chips.append("Wix")
        if sig.get("squarespace"): sig_chips.append("Squarespace")
        if sig.get("wordpress"): sig_chips.append("WordPress")
        if sig.get("tailwind"): sig_chips.append("Tailwind")
        if sig.get("bootstrap3"): sig_chips.append("Bootstrap 3")
        if not sig.get("mobile_viewport"): sig_chips.append("NO MOBILE VIEWPORT")
        if sig.get("slideshow"): sig_chips.append("carousel")
        if sig.get("copyright_years"): sig_chips.append(f"©{sig['copyright_years'][-1]}")
        if sig.get("html_size_kb"): sig_chips.append(f"{sig['html_size_kb']}KB")
        if sig.get("form_inputs_visible"): sig_chips.append(f"{sig['form_inputs_visible']} form fields")
        sig_html = " &middot; ".join(f'<span class="chip">{x}</span>' for x in sig_chips)
        return f"""
<div class="lead-card">
  <div class="lead-header">
    <div>
      <div class="biz-name">{r['name']}</div>
      <div class="biz-meta">{r['niche']} &middot; {r['city']} &middot; {r['reviews']} &middot; <a href="{r['url']}" target="_blank">{r['url']}</a>{hard_stop}</div>
    </div>
    <div class="score-pill" style="--score:{c}">
      <div class="score-num">{s}<span class="score-denom">/100</span></div>
      <span class="verdict-badge {verdict_tag}">{v['verdict']}</span>
    </div>
  </div>
  <div class="lead-body">
    <p class="eyetest">{v.get('owner_eyetest_one_liner', '')}</p>
    <p class="reason"><strong>Why:</strong> {v.get('verdict_reason', '')}</p>
    <div class="chips">{sig_html}</div>
    <details><summary>Leaks visible ({len(leaks)})</summary><ul>{leaks_html}</ul></details>
  </div>
</div>
""".strip()

    def render_group(title, items, label):
        if not items: return ""
        cards = "\n".join(render_card(x) for x in items)
        return f"""<section><h2 class="section-h">{title} <span class="count">{len(items)}</span></h2>{cards}</section>"""

    avg = round(sum(r["verdict"]["datedness_score"] for r in results) / len(results)) if results else 0

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Phase 0 Pre-Filter: Backlog Triage</title>
<style>
:root {{
  --bg:#0f1115; --panel:#161a22; --panel-2:#1c2230; --ink:#e8eaed; --ink-dim:#9aa3b2;
  --accent:#c9a84c; --accent-2:#e8c468; --line:#232936; --warn:#ff8b6b; --ok:#5fb878; --defer:#c9a84c;
}}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  padding: 2rem 1rem 5rem; }}
.wrap {{ max-width: 940px; margin: 0 auto; }}
.nav {{ margin-bottom: 1.4rem; }}
.nav a {{ color: var(--accent); text-decoration: none; font-size: 14px; }}

h1 {{ font-size: 30px; margin: 0 0 0.2em; letter-spacing: -0.015em; }}
.sub {{ color: var(--ink-dim); margin: 0 0 1.8em; font-size: 15px; }}

.tldr {{
  background: linear-gradient(135deg, #1a1f2b, #161a22);
  border: 1px solid var(--accent); border-radius: 10px;
  padding: 1.4em 1.5em; margin-bottom: 2.5em;
  display:grid; grid-template-columns: 1fr auto; gap:1.5em; align-items:center;
}}
.tldr-label {{ display:inline-block; background:var(--accent); color:#0a0c10;
  font-size:11px; font-weight:700; letter-spacing:0.08em;
  padding:3px 8px; border-radius:3px; margin-bottom:0.6em; }}
.tldr h2 {{ font-size:20px; margin:0 0 0.4em; color:var(--accent-2); }}
.tldr p {{ margin: 0.4em 0; font-size:15px; }}
.counters {{ display:flex; gap:1em; margin-top:0.8em; }}
.counter {{ background:var(--panel); padding:0.6em 1em; border-radius:6px; min-width:80px; text-align:center; }}
.counter .n {{ font-size:24px; font-weight:700; line-height:1; }}
.counter .l {{ font-size:11px; color:var(--ink-dim); letter-spacing:0.08em; margin-top:0.2em; text-transform:uppercase; }}
.c-pursue .n {{ color: var(--ok); }}
.c-defer .n {{ color: var(--defer); }}
.c-drop .n {{ color: var(--warn); }}

.batch-score-pill {{ text-align:center; min-width:140px; }}
.batch-score-pill .n {{ font-size:44px; font-weight:700; color:var(--accent); line-height:1; }}
.batch-score-pill .d {{ font-size:18px; color:var(--ink-dim); }}
.batch-score-pill .l {{ font-size:11px; color:var(--ink-dim); letter-spacing:0.1em; margin-top:0.3em; text-transform:uppercase; }}

section {{ margin: 2.5em 0; }}
h2.section-h {{ font-size:21px; color:var(--accent); border-bottom:1px solid var(--line);
  padding-bottom:0.4em; margin-bottom:1em; }}
h2.section-h .count {{ float:right; color:var(--ink-dim); font-size:14px; }}

.lead-card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px;
  padding:1.1em 1.3em; margin-bottom:1em; }}
.lead-card:hover {{ border-color: var(--accent); }}
.lead-header {{ display:grid; grid-template-columns:1fr auto; gap:1em; align-items:center; }}
.biz-name {{ font-size:18px; font-weight:600; color:#fff; }}
.biz-meta {{ color: var(--ink-dim); font-size:13.5px; margin-top:0.2em; }}
.biz-meta a {{ color: var(--accent); text-decoration: none; }}
.biz-meta a:hover {{ text-decoration: underline; }}
.hard-stop {{ color: var(--warn); font-weight: 600; }}

.score-pill {{ text-align:center; min-width:110px; }}
.score-num {{ font-size:32px; font-weight:700; color:var(--score, var(--ok)); line-height:1; }}
.score-denom {{ font-size:14px; color:var(--ink-dim); }}
.verdict-badge {{ display:inline-block; padding:3px 9px; border-radius:4px;
  font-size:11px; font-weight:700; letter-spacing:0.08em; margin-top:0.4em; }}
.v-pursue {{ background: var(--ok); color: #0a0c10; }}
.v-defer {{ background: var(--defer); color: #0a0c10; }}
.v-drop {{ background: var(--warn); color: #0a0c10; }}

.lead-body {{ margin-top: 0.8em; }}
.eyetest {{ font-style: italic; color:#fff; margin: 0 0 0.5em; font-size:15.5px; }}
.reason {{ font-size: 14.5px; margin: 0.3em 0 0.8em; color:var(--ink); }}

.chips {{ display:flex; flex-wrap:wrap; gap:0.4em; margin-bottom:0.6em; }}
.chip {{ background: var(--panel-2); color: var(--ink-dim); font-size:12px;
  padding: 2px 8px; border-radius: 3px; font-family: monospace; }}

details {{ margin-top:0.6em; }}
summary {{ cursor:pointer; font-size:14px; color: var(--accent-2);
  list-style: none; padding: 0.3em 0; }}
summary::-webkit-details-marker {{ display:none; }}
summary::before {{ content:"\\25B8"; display:inline-block; margin-right:0.4em;
  color: var(--ink-dim); transition: transform 0.15s; }}
details[open] summary::before {{ transform: rotate(90deg); }}
details ul {{ margin: 0.4em 0 0; padding-left: 1.4em; font-size: 14px; }}
details li {{ margin-bottom: 0.25em; }}

.foot {{ color: var(--ink-dim); font-size:12px; text-align:center; margin-top:3em; }}
</style>
</head>
<body>
<div class="wrap">
<div class="nav"><a href="index.html">&larr; Batch index</a> &middot; <a href="council-review.html">Council review</a></div>

<h1>Phase 0 Pre-Filter</h1>
<p class="sub">10 backlog leads auto-classified by datedness &middot; PURSUE / DEFER / DROP &middot; ~$0.01 total spend</p>

<div class="tldr">
  <div>
    <span class="tldr-label">TL;DR</span>
    <h2>{len(pursue)} PURSUE &middot; {len(defer)} DEFER &middot; {len(drop)} DROP</h2>
    <p>Auto-gate ran on all {len(results)} leads. Datedness score = bigger number means bigger gap between their site and modern standard, which means a better cold-teardown target.</p>
    <div class="counters">
      <div class="counter c-pursue"><div class="n">{len(pursue)}</div><div class="l">PURSUE</div></div>
      <div class="counter c-defer"><div class="n">{len(defer)}</div><div class="l">DEFER</div></div>
      <div class="counter c-drop"><div class="n">{len(drop)}</div><div class="l">DROP</div></div>
    </div>
  </div>
  <div class="batch-score-pill">
    <div class="n">{avg}<span class="d">/100</span></div>
    <div class="l">Backlog avg datedness</div>
  </div>
</div>

{render_group("PURSUE &middot; run full teardown", pursue, "pursue")}
{render_group("DEFER &middot; revisit next quarter", defer, "defer")}
{render_group("DROP &middot; skip, do not pitch", drop, "drop")}

<div class="foot">agent_outputs/teardowns/phase0-board.html &middot; localhost:8765</div>
</div>
</body>
</html>
"""


def main():
    print(f"Running Phase 0 pre-filter on {len(LEADS)} leads in parallel...\n")
    results = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(process_lead, lead): lead for lead in LEADS}
        for f in as_completed(futures):
            try:
                results.append(f.result())
            except Exception as e:
                lead = futures[f]
                print(f"[{lead['id']}] ERROR: {e}", flush=True)
                results.append({**lead, "signals": {"fetch_error": str(e)}, "verdict": {
                    "datedness_score": 0, "verdict": "DROP",
                    "verdict_reason": f"processing error: {e}",
                    "hard_stop": "site_dead", "leaks_visible": [],
                    "tier_estimate": None, "owner_eyetest_one_liner": "processing failed",
                }})

    # sort: PURSUE first (highest score first), then DEFER, then DROP
    order_key = {"PURSUE": 0, "DEFER": 1, "DROP": 2}
    results.sort(key=lambda r: (order_key.get(r["verdict"]["verdict"], 3), -r["verdict"]["datedness_score"]))

    html = render_board(results)
    OUT.write_text(html, encoding="utf-8")
    print(f"\nwrote {OUT}")
    pursue_count = sum(1 for r in results if r["verdict"]["verdict"] == "PURSUE")
    print(f"PURSUE={pursue_count}  DEFER={sum(1 for r in results if r['verdict']['verdict']=='DEFER')}  DROP={sum(1 for r in results if r['verdict']['verdict']=='DROP')}")


if __name__ == "__main__":
    main()
