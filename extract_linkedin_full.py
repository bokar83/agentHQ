import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Mock or read live URLs
urls = [
    "https://linkedin.com/feed/update/urn:li:share:7455672693158305792",
    "https://linkedin.com/feed/update/urn:li:share:7457784705296404480",
    "https://linkedin.com/feed/update/urn:li:share:7457841854001299456"
]

async def parse_linkedin_post(page, url):
    print(f"\nParsing LinkedIn URL: {url}")
    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(5000) # Give it 5s to render JS
        
        reactions = 0
        comments = 0
        shares = 0
        
        # 1. Reaction Count
        react_el = await page.query_selector("[data-test-id='social-actions__reaction-count']")
        if react_el:
            text = await react_el.text_content()
            if text:
                try:
                    reactions = int("".join(filter(str.isdigit, text)))
                except ValueError:
                    pass
        else:
            # Fallback to general reactions element
            react_el2 = await page.query_selector("[data-test-id='social-actions__reactions']")
            if react_el2:
                text = await react_el2.text_content()
                if text:
                    try:
                        reactions = int("".join(filter(str.isdigit, text)))
                    except ValueError:
                        pass
                        
        # 2. Comment Count
        # LinkedIn public posts typically show comments count in data-test-id="social-actions__comments"
        # or as text like "3 comments" inside some elements
        comment_el = await page.query_selector("[data-test-id='social-actions__comments']")
        if comment_el:
            text = await comment_el.text_content()
            if text:
                try:
                    comments = int("".join(filter(str.isdigit, text)))
                except ValueError:
                    pass
        else:
            # Let's search page innerText for line starting with / containing "comment"
            body_text = await page.evaluate("() => document.body.innerText")
            for line in body_text.split("\n"):
                line_s = line.strip().lower()
                if "comment" in line_s and any(c.isdigit() for c in line_s):
                    # Extract numbers
                    nums = "".join(filter(str.isdigit, line_s))
                    if nums:
                        comments = int(nums)
                        break
                        
        print(f" -> Success! Reactions (Likes): {reactions}, Comments: {comments}")
        return {"url": url, "reactions": reactions, "comments": comments}
    except Exception as e:
        print(f" -> Error parsing {url}: {e}")
        return {"url": url, "error": str(e)}

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        results = []
        for url in urls:
            res = await parse_linkedin_post(page, url)
            results.append(res)
            
        await browser.close()
        print("\nFinal LinkedIn Results:")
        print(results)

if __name__ == "__main__":
    asyncio.run(main())
