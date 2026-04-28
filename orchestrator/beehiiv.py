"""
beehiiv.py - beehiiv REST API integration for newsletter crew.

Creates draft posts in beehiiv via POST /v2/publications/{pub_id}/posts.
Non-fatal: any failure is logged and returns None so the newsletter
still saves to Drive regardless of beehiiv availability.

API reference: https://developers.beehiiv.com/docs/v2/
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("agentsHQ.beehiiv")

BEEHIIV_API_BASE = "https://api.beehiiv.com"


def create_draft(
    title: str,
    content: str,
    subtitle: Optional[str] = None,
) -> Optional[str]:
    """Create a draft post in beehiiv.

    Reads BEEHIIV_API_KEY and BEEHIIV_PUBLICATION_ID from env.
    Returns the post URL or post ID on success, or None on any failure.
    Never raises: failures are logged and swallowed so the newsletter
    pipeline stays non-fatal.

    Args:
        title: Post title (subject line).
        content: HTML body of the newsletter.
        subtitle: Optional subtitle / preview text for the post.

    Returns:
        Post URL string on success, or None on failure / missing env vars.
    """
    api_key = os.environ.get("BEEHIIV_API_KEY", "").strip()
    pub_id = os.environ.get("BEEHIIV_PUBLICATION_ID", "").strip()

    if not api_key or not pub_id:
        logger.info(
            "BEEHIIV: BEEHIIV_API_KEY or BEEHIIV_PUBLICATION_ID not set; "
            "skipping beehiiv draft creation."
        )
        return None

    payload: dict = {
        "status": "draft",
        "title": title,
        "content": {
            "free": {
                "web": {
                    "type": "html",
                    "value": content,
                }
            }
        },
    }
    if subtitle:
        payload["subtitle"] = subtitle

    url = f"{BEEHIIV_API_BASE}/v2/publications/{pub_id}/posts"

    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    except Exception as exc:
        logger.error(f"BEEHIIV: network error creating draft: {exc}")
        return None

    if resp.status_code not in (200, 201):
        logger.error(
            f"BEEHIIV: POST /v2/publications/{pub_id}/posts returned "
            f"{resp.status_code}: {resp.text[:500]}"
        )
        return None

    try:
        data = resp.json()
    except Exception as exc:
        logger.error(f"BEEHIIV: non-JSON response body: {resp.text[:500]}")
        return None

    # beehiiv wraps the post under a "data" key
    post = data.get("data") or data
    post_id = post.get("id")
    post_url = post.get("url") or post.get("web_url")

    result = post_url or post_id
    if not result:
        logger.error(f"BEEHIIV: response missing id and url fields: {data}")
        return None

    logger.info(
        f"BEEHIIV: draft created title={title!r} id={post_id} url={post_url}"
    )
    return str(result)
