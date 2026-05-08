"""
social_analytics.py — Social Media Engagement Analytics Tracking Pipeline
========================================================================
This module pulls live engagement metrics (views, likes, comments, reposts)
for posts on LinkedIn and X (Twitter) using headless Playwright. It then:
  1. Writes the metrics back to the Notion Content Board.
  2. Saves a timestamped record to Postgres for historical trend tracking.
  3. Sends a premium Telegram summary to Boubacar.

Can be run on-demand or scheduled daily at 08:00 AM MT.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("agentsHQ.social_analytics")

# ─────────────────────────────────────────────────────────────────────
# Env and Paths Setup
# ─────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_HERE)
sys.path.append(os.path.dirname(_HERE))

def load_env(path: str = ".env"):
    """Robust fallback dotenv loader."""
    root_path = os.path.join(os.path.dirname(_HERE), path)
    if os.path.exists(root_path):
        with open(root_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip("'").strip('"')
                    os.environ[key.strip()] = val

load_env()

# Self-healing Postgres defaults for local windows run when tunnels are needed
if "POSTGRES_PASSWORD" in os.environ:
    if "POSTGRES_HOST" not in os.environ:
        os.environ["POSTGRES_HOST"] = "localhost"
    if "POSTGRES_USER" not in os.environ:
        os.environ["POSTGRES_USER"] = "postgres"
    if "POSTGRES_DB" not in os.environ:
        os.environ["POSTGRES_DB"] = "postgres"
    if "POSTGRES_PORT" not in os.environ:
        os.environ["POSTGRES_PORT"] = "5432"

# ─────────────────────────────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────────────────────────────
def ensure_db_schema() -> None:
    """Ensure that the post_engagement_analytics table exists in Postgres."""
    try:
        from skills.coordination import _connect
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS post_engagement_analytics (
                    id SERIAL PRIMARY KEY,
                    notion_id VARCHAR(255) NOT NULL,
                    title TEXT,
                    platform VARCHAR(50),
                    url TEXT,
                    date_checked TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    reposts INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0
                );
            """)
            conn.commit()
            logger.info("Database post_engagement_analytics table verified/created.")
    except Exception as e:
        logger.error(f"Failed to verify database schema: {e}")

# ─────────────────────────────────────────────────────────────────────
# Helper: Send Telegram Notification
# ─────────────────────────────────────────────────────────────────────
def send_telegram_summary(msg: str) -> None:
    """Send a Telegram notification to the owner."""
    try:
        from notifier import send_message
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
        if chat_id:
            send_message(str(chat_id), msg)
            logger.info("Sent Telegram summary alert.")
    except Exception as e:
        logger.warning(f"Failed to send Telegram alert: {e}")

# ─────────────────────────────────────────────────────────────────────
# Parser Helpers
# ─────────────────────────────────────────────────────────────────────
def parse_count_from_label(label: Optional[str], default: int = 0) -> int:
    """Extract number from aria-labels (e.g., '12 Likes. Like' -> 12)."""
    if not label:
        return default
    match = re.search(r'(\d[\d,]*)\s', label)
    if match:
        num_str = match.group(1).replace(",", "")
        return int(num_str)
    match_any = re.search(r'\d+', label)
    if match_any:
        return int(match_any.group(0))
    return default

# ─────────────────────────────────────────────────────────────────────
# Playwright Metric Scraping Core
# ─────────────────────────────────────────────────────────────────────
async def scrape_x_metrics(page: Any, url: str) -> Dict[str, int]:
    """Extract views, likes, comments, and reposts from public X post."""
    metrics = {"views": 0, "likes": 0, "comments": 0, "reposts": 0}
    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(8000) # Wait for client-side load
        
        # 1. Parse Views
        spans = await page.query_selector_all("span")
        for span in spans:
            text = await span.text_content()
            if text and text.strip() == "Views":
                parent_text = await span.evaluate("el => el.parentElement.innerText")
                if parent_text:
                    lines = [l.strip() for l in parent_text.split("\n") if l.strip()]
                    for line in lines:
                        cleaned = line.replace(",", "")
                        if cleaned.isdigit():
                            metrics["views"] = int(cleaned)
                            break
                if metrics["views"] > 0:
                    break
        
        # Views fallback
        if metrics["views"] == 0:
            for span in spans:
                text = await span.text_content()
                if text and "View" in text:
                    parent_text = await span.evaluate("el => el.parentElement.innerText")
                    match = re.search(r'([\d,]+)\s+View', parent_text or "")
                    if match:
                        metrics["views"] = int(match.group(1).replace(",", ""))
                        break
        
        # 2. Parse Actions (Replies, Reposts, Likes)
        reply_el = await page.query_selector("[data-testid='reply']")
        if reply_el:
            aria_label = await reply_el.get_attribute("aria-label")
            metrics["comments"] = parse_count_from_label(aria_label, 0)
            
        retweet_el = await page.query_selector("[data-testid='retweet']")
        if retweet_el:
            aria_label = await retweet_el.get_attribute("aria-label")
            metrics["reposts"] = parse_count_from_label(aria_label, 0)
            
        like_el = await page.query_selector("[data-testid='like']")
        if like_el:
            aria_label = await like_el.get_attribute("aria-label")
            metrics["likes"] = parse_count_from_label(aria_label, 0)
            
    except Exception as e:
        logger.warning(f"Error scraping X metrics for {url}: {e}")
    return metrics

async def scrape_linkedin_metrics(page: Any, url: str) -> Dict[str, int]:
    """Extract reactions and comments from public LinkedIn post."""
    metrics = {"views": 0, "likes": 0, "comments": 0, "reposts": 0}
    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(6000)
        
        # 1. Parse Reactions (Likes)
        react_el = await page.query_selector("[data-test-id='social-actions__reaction-count']")
        if react_el:
            text = await react_el.text_content()
            if text:
                try:
                    metrics["likes"] = int("".join(filter(str.isdigit, text)))
                except ValueError:
                    pass
        else:
            react_el2 = await page.query_selector("[data-test-id='social-actions__reactions']")
            if react_el2:
                text = await react_el2.text_content()
                if text:
                    try:
                        metrics["likes"] = int("".join(filter(str.isdigit, text)))
                    except ValueError:
                        pass
                        
        # 2. Parse Comments
        comment_el = await page.query_selector("[data-test-id='social-actions__comments']")
        if comment_el:
            text = await comment_el.text_content()
            if text:
                try:
                    metrics["comments"] = int("".join(filter(str.isdigit, text)))
                except ValueError:
                    pass
        else:
            # Slower body innerText scan fallback
            body_text = await page.evaluate("() => document.body.innerText")
            for line in body_text.split("\n"):
                line_s = line.strip().lower()
                if "comment" in line_s and any(c.isdigit() for c in line_s):
                    nums = "".join(filter(str.isdigit, line_s))
                    if nums:
                        metrics["comments"] = int(nums)
                        break
                        
    except Exception as e:
        logger.warning(f"Error scraping LinkedIn metrics for {url}: {e}")
    return metrics

# ─────────────────────────────────────────────────────────────────────
# Main Pipeline Function
# ─────────────────────────────────────────────────────────────────────
async def pull_social_analytics_async() -> Dict[str, Any]:
    """Connect to Notion + Postgres, scrape public pages, update databases, and alert."""
    ensure_db_schema()
    
    token = (os.environ.get("NOTION_API_KEY")
             or os.environ.get("NOTION_TOKEN")
             or os.environ.get("NOTION_SECRET"))
    db_id = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
    
    if not token:
        logger.error("No Notion token found; aborting social analytics run.")
        return {"success": False, "error": "Missing Notion token"}
        
    try:
        from skills.forge_cli.notion_client import NotionClient
        notion = NotionClient(secret=token)
    except Exception as e:
        logger.error(f"Cannot initialize Notion client: {e}")
        return {"success": False, "error": f"Notion init failed: {e}"}
        
    # 1. Fetch posted items from Content Board
    try:
        filter_obj = {
            "property": "Status",
            "select": {
                "equals": "Posted"
            }
        }
        all_posted = notion.query_database(db_id, filter_obj=filter_obj)
        logger.info(f"Retrieved {len(all_posted)} total Posted items from Notion Content Board.")
    except Exception as e:
        logger.error(f"Failed to query Notion Content Board: {e}")
        return {"success": False, "error": f"Notion query failed: {e}"}
        
    # We filter for items posted within the last 14 days to keep execution fast and focused
    recent_posted = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
    
    for item in all_posted:
        props = item.get("properties", {})
        posted_date_prop = props.get("Posted Date", {}).get("date")
        
        # If there is a posted date, check if it falls within last 14 days.
        # Fallback to including it if there's no Posted Date but it was edited recently.
        is_recent = False
        if posted_date_prop and posted_date_prop.get("start"):
            try:
                p_dt = datetime.fromisoformat(posted_date_prop["start"].replace("Z", "+00:00"))
                if p_dt.tzinfo is None:
                    p_dt = p_dt.replace(tzinfo=timezone.utc)
                if p_dt >= cutoff_date:
                    is_recent = True
            except Exception:
                pass
        else:
            # Fallback: check last_edited_time
            last_edited = item.get("last_edited_time")
            if last_edited:
                try:
                    le_dt = datetime.fromisoformat(last_edited.replace("Z", "+00:00"))
                    if le_dt >= cutoff_date:
                        is_recent = True
                except Exception:
                    pass
                    
        if is_recent:
            recent_posted.append(item)
            
    logger.info(f"Filtered to {len(recent_posted)} items posted within the last 14 days.")
    if not recent_posted:
        return {"success": True, "message": "No recent posts found to check."}
        
    # 2. Execute scraping using Playwright
    from playwright.async_api import async_playwright
    
    scraped_stats = []
    updated_notion_count = 0
    saved_db_count = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        # Import Postgres connector
        from skills.coordination import _connect
        
        for item in recent_posted:
            page_id = item["id"]
            props = item.get("properties", {})
            
            title_prop = props.get("Title", {}).get("title", [])
            title = title_prop[0].get("plain_text", "") if title_prop else "Untitled"
            
            x_url = props.get("X Posted URL", {}).get("url")
            li_url = props.get("LinkedIn Posted URL", {}).get("url")
            
            if not x_url and not li_url:
                continue
                
            logger.info(f"Processing recent post: '{title}'")
            
            # Scrape X if URL exists
            x_metrics = None
            if x_url:
                logger.info(f" - Scraping X: {x_url}")
                x_metrics = await scrape_x_metrics(page, x_url)
                
            # Scrape LinkedIn if URL exists
            li_metrics = None
            if li_url:
                logger.info(f" - Scraping LinkedIn: {li_url}")
                li_metrics = await scrape_linkedin_metrics(page, li_url)
                
            # Compile best combined metrics for Notion
            views = (x_metrics.get("views", 0) if x_metrics else 0) + (li_metrics.get("views", 0) if li_metrics else 0)
            likes = (x_metrics.get("likes", 0) if x_metrics else 0) + (li_metrics.get("likes", 0) if li_metrics else 0)
            comments = (x_metrics.get("comments", 0) if x_metrics else 0) + (li_metrics.get("comments", 0) if li_metrics else 0)
            reposts = (x_metrics.get("reposts", 0) if x_metrics else 0) + (li_metrics.get("reposts", 0) if li_metrics else 0)
            
            # Step A: Update Notion properties
            notion_properties = {
                "Views": {"number": views},
                "Likes": {"number": likes},
                "Comments": {"number": comments},
                "Reposts": {"number": reposts}
            }
            try:
                notion.update_page(page_id, notion_properties)
                updated_notion_count += 1
                logger.info(f"   -> Notion updated! V:{views} L:{likes} C:{comments} R:{reposts}")
            except Exception as notion_err:
                logger.error(f"   -> Failed to update Notion page {page_id}: {notion_err}")
                
            # Step B: Log to Postgres database
            try:
                with _connect() as conn, conn.cursor() as cur:
                    if x_metrics:
                        cur.execute("""
                            INSERT INTO post_engagement_analytics (notion_id, title, platform, url, views, likes, comments, reposts, replies)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (page_id, title, "X", x_url, x_metrics["views"], x_metrics["likes"], x_metrics["comments"], x_metrics["reposts"], 0))
                    if li_metrics:
                        cur.execute("""
                            INSERT INTO post_engagement_analytics (notion_id, title, platform, url, views, likes, comments, reposts, replies)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (page_id, title, "LinkedIn", li_url, li_metrics["views"], li_metrics["likes"], li_metrics["comments"], li_metrics["reposts"], 0))
                    conn.commit()
                    saved_db_count += (1 if x_metrics else 0) + (1 if li_metrics else 0)
            except Exception as db_err:
                logger.error(f"   -> Failed to log to Postgres database: {db_err}")
                
            scraped_stats.append({
                "title": title,
                "x": x_metrics,
                "linkedin": li_metrics,
                "total": {"views": views, "likes": likes, "comments": comments, "reposts": reposts}
            })
            
        await browser.close()
        
    # 3. Format & Send Telegram Summary
    if scraped_stats:
        # Sort by Likes to highlight the winner
        scraped_stats.sort(key=lambda s: s["total"]["likes"], reverse=True)
        top_post = scraped_stats[0]
        
        # Build individual line breakdown
        breakdown_lines = []
        for s in scraped_stats[:5]: # Top 5 recent posts
            breakdown_lines.append(
                f"• *{s['title'][:45]}...*\n"
                f"  Likes: {s['total']['likes']} | Comments: {s['total']['comments']} | Views: {s['total']['views']}"
            )
        breakdown_str = "\n".join(breakdown_lines)
        
        msg = (
            f"📈 *Social Media Engagement Daily Feed*\n\n"
            f"Verified and updated *{updated_notion_count}* posts in your Notion Content Board.\n\n"
            f"🏆 *Top Performing Recent Post:*\n"
            f"\"{top_post['title']}\"\n"
            f"└ Likes: {top_post['total']['likes']} | Comments: {top_post['total']['comments']} | Views: {top_post['total']['views']}\n\n"
            f"🔥 *Breakdown (Recent Top Posts):*\n"
            f"{breakdown_str}\n\n"
            f"Analytics synced successfully. Great progress! 🚀"
        )
        send_telegram_summary(msg)
        
    logger.info(f"Social analytics completed. Notion updated: {updated_notion_count}, DB logged: {saved_db_count}")
    return {
        "success": True,
        "notion_updated": updated_notion_count,
        "db_logged": saved_db_count,
        "posts": scraped_stats
    }

def run_pull_social_analytics() -> Dict[str, Any]:
    """Synchronous entrypoint wrapper."""
    return asyncio.run(pull_social_analytics_async())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    print("Starting Social Analytics engagement retrieval pipeline...")
    result = run_pull_social_analytics()
    print("Social Analytics Run Result Summary:")
    print(result)
