"""Test classroom pagination to find the page-2 URL pattern."""

import json
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skool_harvest import STATE_PATH, WORKSPACE_BASE

CANDIDATES = [
    "https://www.skool.com/robonuggets/classroom?p=2",
    "https://www.skool.com/robonuggets/classroom?page=2",
    "https://www.skool.com/robonuggets/classroom?pageNumber=2",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state=str(STATE_PATH),
        viewport={"width": 1280, "height": 900},
    )
    page = context.new_page()
    out_dir = WORKSPACE_BASE / "robonuggets"

    results = []
    for url in CANDIDATES:
        print(f"\n--- {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("load", timeout=20000)
        except Exception:
            pass
        time.sleep(2)
        html = page.content()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not m:
            results.append({"url": url, "error": "no __NEXT_DATA__"})
            continue
        d = json.loads(m.group(1))
        pp = d.get("props", {}).get("pageProps", {})
        page_no = pp.get("page")
        all_courses = pp.get("allCourses") or []
        first_titles = [
            ((c.get("metadata") or {}).get("title") or "").encode("ascii", "replace").decode("ascii")
            for c in all_courses[:3]
        ]
        print(f"  page={page_no} allCourses={len(all_courses)} titles[:3]={first_titles}")
        results.append(
            {
                "url": url,
                "page": page_no,
                "course_count": len(all_courses),
                "first_titles": first_titles,
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_pagination_probe.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    browser.close()
