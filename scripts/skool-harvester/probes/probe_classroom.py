"""Inspect the classroom DOM so we know what selectors to scrape."""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skool_harvest import STATE_PATH, WORKSPACE_BASE, community_from_url

URL = "https://www.skool.com/robonuggets/classroom"

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
    time.sleep(4)

    # Probe several candidate selectors
    info = page.evaluate(r"""
        () => {
            const out = {};
            const probes = [
                ['a[href*="/classroom/"]', 'classroom anchors'],
                ['a[href*="?md="]', 'md-anchors'],
                ['[data-testid*="course"]', 'data-testid course'],
                ['[data-testid*="lesson"]', 'data-testid lesson'],
                ['[class*="Course"]', 'class*=Course'],
                ['[class*="Lesson"]', 'class*=Lesson'],
                ['[role="button"]', 'role=button'],
                ['[role="article"]', 'role=article'],
                ['h2', 'h2 (any)'],
                ['h3', 'h3 (any)'],
            ];
            probes.forEach(([sel, label]) => {
                const els = document.querySelectorAll(sel);
                out[label] = els.length;
            });
            // sample h2/h3 text
            out.h2_sample = Array.from(document.querySelectorAll('h2')).slice(0, 5).map(h => h.innerText.trim());
            out.h3_sample = Array.from(document.querySelectorAll('h3')).slice(0, 8).map(h => h.innerText.trim());
            // Sample any <a> tag href patterns under the main content
            const main = document.querySelector('main') || document.body;
            const anchors = Array.from(main.querySelectorAll('a')).slice(0, 30);
            out.anchor_sample = anchors.map(a => ({ href: a.href, text: (a.innerText || '').trim().slice(0, 60) }));
            // Sample clickable divs
            const clickables = Array.from(document.querySelectorAll('[role="button"], [tabindex="0"]')).slice(0, 20);
            out.clickable_sample = clickables.map(c => ({
                tag: c.tagName,
                role: c.getAttribute('role'),
                text: (c.innerText || '').trim().slice(0, 80),
                cls: (c.className || '').toString().slice(0, 100),
            }));
            // Try to find any element whose innerText looks like a lesson title (e.g. starts with "R" + digits)
            const allTexts = Array.from(document.querySelectorAll('*')).filter(e => {
                const t = (e.innerText || '').trim();
                return t.length > 0 && t.length < 200 && /^R\d+/.test(t) && e.children.length < 3;
            }).slice(0, 10);
            out.r_pattern_hits = allTexts.map(e => ({
                tag: e.tagName,
                text: (e.innerText || '').trim().slice(0, 100),
                cls: (e.className || '').toString().slice(0, 100),
            }));
            return out;
        }
    """)

    out_dir = WORKSPACE_BASE / community_from_url(URL)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_classroom_probe.html").write_text(page.content(), encoding="utf-8")

    import json
    print(json.dumps(info, indent=2, ensure_ascii=False)[:6000])
    print(f"\n[probe] DOM saved to {out_dir / '_classroom_probe.html'}")
    page.screenshot(path=str(out_dir / "_classroom_probe.png"), full_page=True)
    browser.close()
