import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a premium browser context with typical browser headers and size
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        tweet_url = "https://x.com/boubacarbarry/status/2051286201013809432"
        print(f"Navigating to {tweet_url}...")
        await page.goto(tweet_url)
        
        # Wait for the view count text to appear or just wait 8 seconds
        print("Waiting for page load...")
        await page.wait_for_timeout(8000)
        
        # Capture text in the viewport
        content = await page.content()
        print(f"Page source length: {len(content)}")
        
        # Let's extract text of elements that contain 'Views'
        views_elements = await page.query_selector_all("span")
        print("\nAll SPAN elements containing 'View' or numbers:")
        for el in views_elements:
            text = await el.text_content()
            if text and ("View" in text or text.isdigit()):
                print(f" - {text.strip()}")
                
        # Let's try to extract metrics using specific aria-labels or testids
        print("\nChecking element attributes:")
        # X uses data-testid for action buttons
        testids = ["reply", "retweet", "like", "bookmark"]
        for testid in testids:
            el = await page.query_selector(f"[data-testid='{testid}']")
            if el:
                aria_label = await el.get_attribute("aria-label")
                text = await el.text_content()
                print(f" - {testid}: aria-label={aria_label}, text={text}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
