import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        li_url = "https://linkedin.com/feed/update/urn:li:share:7455672693158305792"
        await page.goto(li_url)
        await page.wait_for_timeout(8000)
        
        print("Searching for elements with 'reaction' or 'comment' in attributes:")
        
        # We query elements and extract text + tag + attributes
        elements = await page.query_selector_all("*")
        for el in elements:
            try:
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                # We only care about small display elements
                if tag not in ["span", "button", "a", "div"]:
                    continue
                
                html = await el.evaluate("el => el.outerHTML")
                testid = await el.get_attribute("data-test-id")
                cls = await el.get_attribute("class")
                text = await el.text_content()
                text = text.strip() if text else ""
                
                # Filter for interesting metrics attributes
                match_id = testid and any(w in testid.lower() for w in ["reaction", "comment", "repost", "share", "social"])
                match_class = cls and any(w in cls.lower() for w in ["reaction", "comment", "repost", "share", "social"])
                
                if (match_id or match_class) and text and len(text) < 50:
                    print(f" - Tag: {tag}, text: '{text}'")
                    if testid: print(f"   data-test-id: {testid}")
                    if cls: print(f"   class: {cls}")
            except Exception:
                pass
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
