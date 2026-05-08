import asyncio
import sys
from playwright.async_api import async_playwright

# Set console output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        li_url = "https://linkedin.com/feed/update/urn:li:share:7455672693158305792"
        print(f"Navigating to {li_url}...")
        await page.goto(li_url)
        
        print("Waiting for page load...")
        await page.wait_for_timeout(8000)
        
        # Capture raw innerText of the page
        text_content = await page.evaluate("() => document.body.innerText")
        
        print("\n--- ALL LINES OF PAGE INNERTEXT (Filtered for reactions or counts) ---")
        lines = text_content.split("\n")
        for line_num, line in enumerate(lines):
            line_s = line.strip()
            if not line_s:
                continue
            # Print any line containing numbers, or social-related terms
            if any(word in line_s.lower() for word in ["like", "comment", "repost", "share", "reaction", "view"]):
                print(f"Line {line_num}: {line_s}")
            elif any(c.isdigit() for c in line_s) and len(line_s) < 100:
                print(f"Line {line_num} (Num): {line_s}")
                
        # Let's inspect the DOM elements that are typically used by LinkedIn for social counters
        print("\n--- INSPECTING SPECIFIC SELECTORS ---")
        # Let's find all buttons or elements with social classes
        selectors = [
            ".social-details-social-counts__reactions-count",
            ".social-details-social-counts__comments",
            ".social-details-social-counts__item",
            ".social-details-social-counts",
            "button[class*='social-counts']",
            "span[class*='social-counts']",
            ".social-action-bar",
            "article",
            "[data-test-id*='social']"
        ]
        
        for sel in selectors:
            elements = await page.query_selector_all(sel)
            if elements:
                print(f"Found {len(elements)} elements matching '{sel}':")
                for i, el in enumerate(elements[:5]):
                    text = await el.text_content()
                    html = await el.evaluate("el => el.outerHTML")
                    print(f"  - Match {i+1}: text={text.strip() if text else 'None'}")
                    print(f"    HTML: {html[:150]}...")
            else:
                print(f"No elements found for selector: '{sel}'")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
