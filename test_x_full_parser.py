import asyncio
import sys
import re
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    "https://x.com/boubacarbarry/status/2049836721752211703",
    "https://x.com/boubacarbarry/status/2051648799190184290",
    "https://x.com/boubacarbarry/status/2050198724752646626",
    "https://x.com/boubacarbarry/status/2051286201013809432"
]

def parse_count_from_label(label, default=0):
    if not label:
        return default
    # Extract first number from label (e.g. "12 Likes. Like" -> 12, "0 Replies" -> 0)
    match = re.search(r'(\d[\d,]*)\s', label)
    if match:
        num_str = match.group(1).replace(",", "")
        return int(num_str)
    # Check if there's any digit anywhere
    match_any = re.search(r'\d+', label)
    if match_any:
        return int(match_any.group(0))
    return default

async def parse_x_post(page, url):
    print(f"\nParsing X URL: {url}")
    try:
        await page.goto(url, timeout=30000)
        # Wait 8s for client-side JS and graphs to load
        await page.wait_for_timeout(8000)
        
        # 1. Parse Views
        # X renders views as a span containing "Views" and another span containing the count (e.g., "10") nearby.
        # Let's inspect elements containing text "Views" and extract adjacent counts.
        views = 0
        spans = await page.query_selector_all("span")
        for i, span in enumerate(spans):
            text = await span.text_content()
            if text and text.strip() == "Views":
                # Check previous spans or next spans
                # Usually the count is in a nearby sibling span
                # Let's check some previous siblings or the text around it
                # Let's evaluate the parent text or adjacent siblings
                parent_text = await span.evaluate("el => el.parentElement.innerText")
                if parent_text:
                    lines = [l.strip() for l in parent_text.split("\n") if l.strip()]
                    # Look for number in these lines
                    for line in lines:
                        cleaned = line.replace(",", "")
                        if cleaned.isdigit():
                            views = int(cleaned)
                            break
                if views > 0:
                    break
        
        # Fallback for Views
        if views == 0:
            for span in spans:
                text = await span.text_content()
                if text and "View" in text:
                    parent_text = await span.evaluate("el => el.parentElement.innerText")
                    match = re.search(r'([\d,]+)\s+View', parent_text or "")
                    if match:
                        views = int(match.group(1).replace(",", ""))
                        break
        
        # 2. Parse Actions (Replies, Reposts, Likes)
        replies = 0
        reposts = 0
        likes = 0
        
        # Replies
        reply_el = await page.query_selector("[data-testid='reply']")
        if reply_el:
            aria_label = await reply_el.get_attribute("aria-label")
            replies = parse_count_from_label(aria_label, 0)
            
        # Reposts
        retweet_el = await page.query_selector("[data-testid='retweet']")
        if retweet_el:
            aria_label = await retweet_el.get_attribute("aria-label")
            reposts = parse_count_from_label(aria_label, 0)
            
        # Likes
        like_el = await page.query_selector("[data-testid='like']")
        if like_el:
            aria_label = await like_el.get_attribute("aria-label")
            likes = parse_count_from_label(aria_label, 0)
            
        print(f" -> Success! Views: {views}, Likes: {likes}, Reposts: {reposts}, Replies: {replies}")
        return {
            "url": url,
            "views": views,
            "likes": likes,
            "reposts": reposts,
            "replies": replies
        }
    except Exception as e:
        print(f" -> Error: {e}")
        return {"url": url, "error": str(e)}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        results = []
        for url in urls:
            res = await parse_x_post(page, url)
            results.append(res)
            
        await browser.close()
        print("\nFinal X Results:")
        import json
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
