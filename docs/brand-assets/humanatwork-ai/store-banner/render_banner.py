"""Render humanatwork.ai store banner.

Reads banner-source.html, screenshots at 1600x300 via Playwright (PNG),
then re-encodes to JPG via Pillow (quality 92). Verifies dimensions + file size.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image

HERE = Path(__file__).parent.resolve()
HTML = HERE / "banner-source.html"
PNG_OUT = HERE / "banner-gumroad-1600x300.png"
JPG_OUT = HERE / "banner-gumroad-1600x300.jpg"

WIDTH = 1600
HEIGHT = 300
MAX_BYTES = 10 * 1024 * 1024  # 10MB


def render() -> None:
    if not HTML.exists():
        sys.exit(f"missing source: {HTML}")

    url = HTML.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
        )
        page = ctx.new_page()
        page.set_viewport_size({"width": WIDTH, "height": HEIGHT})
        page.goto(url, wait_until="networkidle")
        # extra wait so google fonts settle
        page.wait_for_timeout(1500)

        page.screenshot(
            path=str(PNG_OUT),
            clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT},
            omit_background=False,
            type="png",
        )

        browser.close()

    # Verify PNG dimensions
    with Image.open(PNG_OUT) as img:
        assert img.size == (WIDTH, HEIGHT), f"PNG dims wrong: {img.size}"
        # Convert to RGB for JPG
        rgb = img.convert("RGB")
        rgb.save(JPG_OUT, format="JPEG", quality=92, optimize=True)

    # Verify JPG dimensions + sizes
    with Image.open(JPG_OUT) as img:
        assert img.size == (WIDTH, HEIGHT), f"JPG dims wrong: {img.size}"

    png_bytes = PNG_OUT.stat().st_size
    jpg_bytes = JPG_OUT.stat().st_size
    assert png_bytes < MAX_BYTES, f"PNG too large: {png_bytes} bytes"
    assert jpg_bytes < MAX_BYTES, f"JPG too large: {jpg_bytes} bytes"

    print(f"PNG: {PNG_OUT.name} dims=(1600, 300) size={png_bytes:,} bytes ({png_bytes/1024:.1f} KB)")
    print(f"JPG: {JPG_OUT.name} dims=(1600, 300) size={jpg_bytes:,} bytes ({jpg_bytes/1024:.1f} KB)")


if __name__ == "__main__":
    render()
