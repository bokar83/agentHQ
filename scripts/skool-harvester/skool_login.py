"""
Skool one-time login. Opens a browser, you log in, then this script auto-detects
that you're logged in and saves your session to a JSON file.

Detection: polls the page URL every 2 seconds. Once the URL leaves /login or
/signup AND a Skool cookie called 'auth_token' exists, it saves state and exits.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_PATH = Path.home() / ".claude" / "playwright-state" / "skool.json"
START_URL = "https://www.skool.com/login"
TIMEOUT_SECONDS = 600  # 10 minutes


def is_logged_in(page) -> bool:
    url = page.url
    if "/login" in url or "/signup" in url or url == "about:blank":
        return False
    if "skool.com" not in url:
        return False
    cookies = page.context.cookies("https://www.skool.com")
    cookie_names = {c["name"] for c in cookies}
    auth_markers = {"auth_token", "_session", "skool_session", "sessionid"}
    return bool(cookie_names & auth_markers)


def main():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto(START_URL)

        print()
        print("=" * 60)
        print("Browser is open. Log into Skool now.")
        print("This script will auto-detect login and save your session.")
        print("=" * 60)
        print()

        deadline = time.time() + TIMEOUT_SECONDS
        last_status = ""
        while time.time() < deadline:
            try:
                cookies = page.context.cookies("https://www.skool.com")
                cookie_names = sorted([c["name"] for c in cookies])
                status = f"url={page.url} cookies={len(cookies)} names={cookie_names[:5]}"
                if status != last_status:
                    print(f"[poll] {status}")
                    last_status = status
                if is_logged_in(page):
                    print("\n[OK] Login detected.")
                    break
            except Exception as e:
                print(f"[poll error] {e}")
            time.sleep(2)
        else:
            print("\n[TIMEOUT] No login detected. Saving state anyway.")

        context.storage_state(path=str(STATE_PATH))
        print(f"\nSaved session to: {STATE_PATH}")
        print(f"Session size: {STATE_PATH.stat().st_size} bytes")

        browser.close()


if __name__ == "__main__":
    sys.exit(main())
