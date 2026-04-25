"""
Skool single-lesson harvester. Loads saved session, navigates to a lesson URL,
dumps everything: HTML, screenshot, all links, all visible text, attached files,
and any JSON-looking blobs (n8n workflows, code snippets).

Usage:
    python skool_harvest.py <lesson_url> [<output_subdir>]

Example:
    python skool_harvest.py https://www.skool.com/robonuggets/classroom/abc123 first-test

Outputs to: workspace/skool-harvest/<community>/<output_subdir>/
(community slug is parsed from the URL automatically)
"""

import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path.home() / ".claude" / "playwright-state" / "skool.json"
WORKSPACE_BASE = REPO_ROOT / "workspace" / "skool-harvest"


def community_from_url(url: str) -> str:
    """Extract the community slug from a Skool URL.
    e.g. https://www.skool.com/robonuggets/classroom/abc -> 'robonuggets'.
    """
    parts = urlparse(url).path.strip("/").split("/")
    return parts[0] if parts and parts[0] else "unknown-community"


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    return parts[-1] if parts else "lesson"


def harvest(lesson_url: str, subdir: str | None = None):
    if not STATE_PATH.exists():
        print(f"ERROR: no saved session at {STATE_PATH}")
        print("Run skool_login.py first.")
        sys.exit(1)

    community = community_from_url(lesson_url)
    out_dir = WORKSPACE_BASE / community / (subdir or slug_from_url(lesson_url))
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[harvest] output dir: {out_dir}")
    print(f"[harvest] lesson url: {lesson_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=str(STATE_PATH),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # capture network responses to spot JSON / file downloads
        responses = []
        page.on("response", lambda r: responses.append({
            "url": r.url,
            "status": r.status,
            "content_type": r.headers.get("content-type", ""),
        }))

        print("[harvest] navigating...")
        page.goto(lesson_url, wait_until="domcontentloaded", timeout=60000)
        # Skool keeps a persistent socket so networkidle never fires.
        try:
            page.wait_for_load_state("load", timeout=30000)
        except Exception:
            pass
        time.sleep(3)
        # Skool lesson body is in a scrollable React panel. Scroll the panel and
        # the window to force lazy-rendered content (rich text, attachments) to mount.
        for _ in range(8):
            page.mouse.wheel(0, 1200)
            time.sleep(0.6)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)

        print(f"[harvest] landed at: {page.url}")
        print(f"[harvest] title: {page.title()}")

        # 1. screenshot (full page)
        screenshot_path = out_dir / "screenshot.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[harvest] saved screenshot: {screenshot_path.stat().st_size} bytes")

        # 2. raw HTML
        html_path = out_dir / "page.html"
        html_path.write_text(page.content(), encoding="utf-8")
        print(f"[harvest] saved HTML: {html_path.stat().st_size} bytes")

        # 3. visible text (cleaned)
        text = page.inner_text("body")
        text_path = out_dir / "text.txt"
        text_path.write_text(text, encoding="utf-8")
        print(f"[harvest] saved text: {text_path.stat().st_size} bytes")

        # 4. all links on the page
        links = page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.innerText.trim().slice(0, 200),
                href: a.href,
            }))
        """)
        (out_dir / "links.json").write_text(
            json.dumps(links, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[harvest] saved {len(links)} links")

        # 5b. extract Skool resource metadata from inline JSON state
        import re as _re
        attachments = []
        try:
            html_raw = page.content()
            # Skool embeds a "resources":"[{...}]" string per lesson in the SSR payload.
            for m in _re.finditer(r'"resources":"(\[.*?\])"', html_raw):
                raw = m.group(1).encode("utf-8").decode("unicode_escape")
                try:
                    items = json.loads(raw)
                    for it in items:
                        if isinstance(it, dict) and it.get("file_id"):
                            attachments.append(it)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"[harvest] attachment-meta extraction failed: {e}")
        (out_dir / "attachments_meta.json").write_text(
            json.dumps(attachments, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[harvest] found {len(attachments)} resource attachment(s) in metadata")

        # 5c. click each resource label to trigger a download, capture URL
        downloads_dir = out_dir / "downloads"
        downloads_dir.mkdir(exist_ok=True)
        download_records = []
        try:
            resource_labels = page.locator("span.styled__ResourceLabel-sc-1wq200d-3")
            n_resources = resource_labels.count()
            print(f"[harvest] found {n_resources} clickable resource(s)")
            for i in range(n_resources):
                label = resource_labels.nth(i)
                title = label.inner_text()
                print(f"[harvest] clicking resource {i+1}/{n_resources}: {title}")
                try:
                    label.click(timeout=5000)
                    # Click may open a preview modal. Look for an explicit download trigger.
                    time.sleep(1.5)
                    download_triggers = [
                        'a[download]',
                        'a[href*="api2.skool.com"][href*="download"]',
                        'button:has-text("Download")',
                        'a:has-text("Download")',
                        '[aria-label*="ownload"]',
                    ]
                    triggered = False
                    for sel in download_triggers:
                        loc = page.locator(sel).first
                        if loc.count() > 0 and loc.is_visible():
                            print(f"[harvest]   trying trigger: {sel}")
                            try:
                                with page.expect_download(timeout=15000) as dl_info:
                                    loc.click(timeout=5000)
                                dl = dl_info.value
                                safe_name = _re.sub(r'[<>:"/\\|?*]', "_", dl.suggested_filename)
                                save_path = downloads_dir / safe_name
                                dl.save_as(str(save_path))
                                download_records.append({
                                    "title": title,
                                    "trigger": sel,
                                    "url": dl.url,
                                    "suggested_filename": dl.suggested_filename,
                                    "saved_to": str(save_path),
                                    "size_bytes": save_path.stat().st_size,
                                })
                                print(f"[harvest]   downloaded: {save_path.name} ({save_path.stat().st_size} bytes)")
                                triggered = True
                                break
                            except Exception as e:
                                print(f"[harvest]   trigger {sel} failed: {e}")
                                continue
                    if not triggered:
                        # Snapshot what's on screen so we can debug selector
                        snap_html = page.content()
                        debug_path = out_dir / f"debug_after_click_{i+1}.html"
                        debug_path.write_text(snap_html, encoding="utf-8")
                        download_records.append({
                            "title": title,
                            "error": "no download trigger matched",
                            "debug_html": str(debug_path),
                        })
                        print(f"[harvest]   no trigger matched. saved DOM to {debug_path.name}")
                    # Try to close any modal before next click
                    try:
                        page.keyboard.press("Escape")
                        time.sleep(0.5)
                    except Exception:
                        pass
                except Exception as e:
                    download_records.append({"title": title, "error": str(e)})
                    print(f"[harvest] click for {title} failed: {e}")
        except Exception as e:
            print(f"[harvest] resource-click pass failed: {e}")
        (out_dir / "downloads_log.json").write_text(
            json.dumps(download_records, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # 5. find n8n-flavored JSON blobs anywhere on the page
        candidates = page.evaluate(r"""
            () => {
                const out = [];
                // <pre> and <code> blocks
                document.querySelectorAll('pre, code').forEach((el, i) => {
                    const txt = el.innerText;
                    if (txt && txt.length > 50) {
                        out.push({ source: 'pre/code', idx: i, text: txt });
                    }
                });
                // attached files (download links)
                document.querySelectorAll('a[download], a[href*=".json"]').forEach((a) => {
                    out.push({ source: 'download_link', href: a.href, text: a.innerText });
                });
                return out;
            }
        """)

        json_blobs = []
        for c in candidates:
            if "text" in c:
                txt = c["text"].strip()
                if (txt.startswith("{") and txt.endswith("}")) or (
                    txt.startswith("[") and txt.endswith("]")
                ):
                    try:
                        parsed = json.loads(txt)
                        json_blobs.append({"source": c["source"], "json": parsed})
                    except json.JSONDecodeError:
                        json_blobs.append({"source": c["source"], "raw_text": txt[:5000]})

        (out_dir / "candidates.json").write_text(
            json.dumps(candidates, indent=2, ensure_ascii=False)[:500000], encoding="utf-8"
        )
        (out_dir / "json_blobs.json").write_text(
            json.dumps(json_blobs, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[harvest] candidates: {len(candidates)}, parseable JSON blobs: {len(json_blobs)}")

        # 6. video / iframe sources (lessons often embed YouTube / Vimeo)
        media = page.evaluate("""
            () => {
                const videos = Array.from(document.querySelectorAll('video')).map(v => ({
                    src: v.currentSrc || v.src,
                    poster: v.poster,
                }));
                const iframes = Array.from(document.querySelectorAll('iframe')).map(f => ({
                    src: f.src,
                    title: f.title,
                }));
                return { videos, iframes };
            }
        """)
        (out_dir / "media.json").write_text(
            json.dumps(media, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[harvest] videos: {len(media['videos'])}, iframes: {len(media['iframes'])}")

        # 7. network log (filter for JSON / download responses)
        interesting = [
            r for r in responses
            if "json" in r["content_type"].lower()
            or "octet-stream" in r["content_type"].lower()
            or r["url"].endswith(".json")
        ]
        (out_dir / "network_interesting.json").write_text(
            json.dumps(interesting, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[harvest] network interesting: {len(interesting)} of {len(responses)}")

        # 8. summary
        summary = {
            "url": lesson_url,
            "final_url": page.url,
            "title": page.title(),
            "html_bytes": html_path.stat().st_size,
            "text_chars": len(text),
            "links_count": len(links),
            "candidates": len(candidates),
            "json_blobs": len(json_blobs),
            "videos": len(media["videos"]),
            "iframes": len(media["iframes"]),
            "network_interesting": len(interesting),
        }
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n[DONE] summary: {json.dumps(summary, indent=2)}")

        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    url = sys.argv[1]
    sub = sys.argv[2] if len(sys.argv) > 2 else None
    harvest(url, sub)
