"""
NotebookLM auth refresh + fallback notifier.

Run on a schedule (every 3 days). Flow:
1. Check if cookies are still valid (quick API probe)
2. If valid and < 72h old: skip (nothing to do)
3. If valid but > 72h old: attempt headless refresh using browser profile
4. If headless refresh succeeds: scp fresh cookies to local Windows machine (if reachable)
5. If headless refresh fails (Google session expired): send Telegram alert + write marker file
   so the next Claude session picks it up and prompts for manual re-login

Usage:
    python scripts/notebooklm_auth_refresh.py          # Full refresh attempt
    python scripts/notebooklm_auth_refresh.py --check  # Status check only, no refresh
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

NOTEBOOKLM_HOME = Path(os.environ.get("NOTEBOOKLM_HOME", Path.home() / ".notebooklm"))
STORAGE_PATH = NOTEBOOKLM_HOME / "storage_state.json"
BROWSER_PROFILE = NOTEBOOKLM_HOME / "browser_profile"
MARKER_FILE = NOTEBOOKLM_HOME / "REAUTH_NEEDED"

TELEGRAM_BOT_TOKEN = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

REFRESH_INTERVAL_HOURS = 72  # refresh every 3 days


def get_cookie_age_hours():
    if not STORAGE_PATH.exists():
        return float("inf")
    return (time.time() - os.path.getmtime(STORAGE_PATH)) / 3600


def check_cookies_valid():
    try:
        from notebooklm.auth import load_auth_from_storage, fetch_tokens
        cookies = load_auth_from_storage()
        asyncio.run(fetch_tokens(cookies))
        return True
    except Exception:
        return False


def refresh_headless():
    """Use persistent browser profile to refresh cookies without a browser window."""
    if not BROWSER_PROFILE.exists():
        print("No browser profile -- headless refresh not possible on this machine.")
        return False

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed.")
        return False

    print(f"Headless refresh using profile: {BROWSER_PROFILE}")
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE),
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--password-store=basic"],
                ignore_default_args=["--enable-automation"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto("https://notebooklm.google.com/", wait_until="networkidle", timeout=30000)
            except Exception as e:
                print(f"Page load warning: {e}")

            current_url = page.url
            if "notebooklm.google.com" in current_url and "accounts.google.com" not in current_url:
                context.storage_state(path=str(STORAGE_PATH))
                context.close()
                print(f"Cookies refreshed. Saved to: {STORAGE_PATH}")
                return True
            else:
                context.close()
                print(f"Google session expired. Redirected to: {current_url}")
                return False
    except Exception as e:
        print(f"Headless refresh error: {e}")
        return False


def send_telegram(message):
    """Send a Telegram message via the orchestrator bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set -- cannot send alert.")
        return False
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False


def write_marker(reason):
    """Write a marker file so the next Claude session detects the need to re-auth."""
    NOTEBOOKLM_HOME.mkdir(parents=True, exist_ok=True)
    MARKER_FILE.write_text(
        f"REAUTH_NEEDED\nReason: {reason}\nTimestamp: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n"
        "Action: Run `.venv\\Scripts\\python.exe -m notebooklm login` in agentsHQ PowerShell,\n"
        "        then: scp C:/Users/HUAWEI/.notebooklm/storage_state.json root@72.60.209.109:~/.notebooklm/storage_state.json\n"
    )
    print(f"Marker written: {MARKER_FILE}")


def clear_marker():
    if MARKER_FILE.exists():
        MARKER_FILE.unlink()
        print("Cleared REAUTH_NEEDED marker.")


def main():
    check_only = "--check" in sys.argv

    age = get_cookie_age_hours()
    valid = check_cookies_valid()

    print(f"Cookie age: {age:.1f} hours | Valid: {valid}")

    if check_only:
        if not valid:
            print("REAUTH NEEDED")
            sys.exit(1)
        sys.exit(0)

    # Clear any stale marker if cookies are fine
    if valid and MARKER_FILE.exists():
        clear_marker()

    # Skip refresh if cookies are fresh enough
    if valid and age < REFRESH_INTERVAL_HOURS:
        print(f"Cookies fresh ({age:.1f}h < {REFRESH_INTERVAL_HOURS}h). No refresh needed.")
        sys.exit(0)

    # Attempt headless refresh
    print("Attempting headless refresh...")
    success = refresh_headless()

    if success:
        # Verify
        if check_cookies_valid():
            print("Refresh verified. Cookies working.")
            clear_marker()
            sys.exit(0)
        else:
            success = False

    # Headless failed -- session truly expired, need manual login
    reason = "Headless refresh failed. Google session has expired."
    print(f"ERROR: {reason}")
    write_marker(reason)

    msg = (
        "NotebookLM auth expired and could not be refreshed automatically.\n\n"
        "Action required:\n"
        "1. Open agentsHQ PowerShell\n"
        "2. Run: .venv\\Scripts\\python.exe -m notebooklm login\n"
        "3. Sign in, wait for NotebookLM homepage, press ENTER in the terminal\n"
        "4. Then run: scp C:/Users/HUAWEI/.notebooklm/storage_state.json root@72.60.209.109:~/.notebooklm/storage_state.json\n\n"
        "Or open Claude Code and it will detect the REAUTH_NEEDED marker and guide you."
    )
    sent = send_telegram(msg)
    print(f"Telegram alert sent: {sent}")
    sys.exit(1)


if __name__ == "__main__":
    main()
