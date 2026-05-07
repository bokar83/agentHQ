import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        # Open one of your LinkedIn posts
        li_url = "https://linkedin.com/feed/update/urn:li:share:7455672693158305792"
        print(f"Navigating to {li_url}...")
        await page.goto(li_url)
        
        print("Waiting for page load...")
        await page.wait_for_timeout(8000)
        
        content = await page.content()
        print(f"Page source length: {len(content)}")
        
        # Capture text and elements in the page
        text_content = await page.evaluate("() => document.body.innerText")
        print("\n--- PAGE TEXT PREVIEW (first 1000 chars) ---")
        print(text_content[:1000])
        print("------------------------------------------")
        
        # Let's search for social engagement indicators like 'like', 'comment', numbers, etc.
        # LinkedIn social counts are usually in buttons or classes like 'social-details-social-counts'
        print("\nSearching for potential metrics in text:")
        lines = text_content.split("\n")
        for line in lines:
            line_s = line.strip().lower()
            if any(word in line_s for word in ["like", "comment", "reaction", "repost", "share", "view"]):
                print(f" - Match: {line.strip()}")
                
        # Let's query buttons/spans that might have numbers
        spans = await page.query_selector_all("span, button")
        print("\nAll buttons/spans with suspicious social content:")
        for span in spans:
            try:
                text = await span.text_content()
                if text:
                    text_s = text.strip()
                    # If it has a number or matches words
                    if any(word in text_s.lower() for word in ["like", "comment", "repost", "share", "view"]):
                        print(f" - [{span.locator('xpath=.').evaluate('el => el.tagName')}]: {text_s}")
            except Exception:
                pass
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
