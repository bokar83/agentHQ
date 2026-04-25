"""Probe a course page to confirm its module list is in __NEXT_DATA__."""

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skool_harvest import STATE_PATH, WORKSPACE_BASE, community_from_url

# Pick a small course to probe (Start Here = 10 modules)
URL = "https://www.skool.com/robonuggets/classroom/7e5732ad"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state=str(STATE_PATH),
        viewport={"width": 1280, "height": 900},
    )
    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("load", timeout=30000)
    except Exception:
        pass
    time.sleep(3)

    html = page.content()
    out = WORKSPACE_BASE / community_from_url(URL) / "_course_probe.html"
    out.write_text(html, encoding="utf-8")

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        print("NO __NEXT_DATA__ found")
    else:
        data = json.loads(m.group(1))
        # Walk the props.pageProps tree to find anything that looks like a module list
        pp = data.get("props", {}).get("pageProps", {})
        keys = list(pp.keys())
        sizes = {k: (len(v) if isinstance(v, (list, dict)) else "scalar") for k, v in pp.items()}
        report = {"keys": keys, "sizes": sizes}

        # Look for any list whose items have name/metadata.title
        candidates = {}
        for k, v in pp.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                first = v[0]
                if any(x in first for x in ("metadata", "title", "name")):
                    candidates[k] = {
                        "len": len(v),
                        "sample_keys": list(first.keys())[:10],
                        "sample_titles": [
                            (it.get("metadata") or {}).get("title")
                            or it.get("title")
                            or it.get("name")
                            for it in v[:5]
                        ],
                    }
        report["module_candidates"] = candidates

        out_json = WORKSPACE_BASE / community_from_url(URL) / "_course_probe_summary.json"
        out_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Wrote probe summary to {out_json}")
    browser.close()
