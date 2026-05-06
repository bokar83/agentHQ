"""
beehiiv.py - Newsletter delivery integration.

Primary path: Listmonk (self-hosted, full send API).
Fallback path: Beehiiv draft creation (Enterprise send API not available on current plan).

Listmonk API: http://listmonk:9000/api
Beehiiv API: https://api.beehiiv.com/v2
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("agentsHQ.beehiiv")

BEEHIIV_API_BASE = "https://api.beehiiv.com"
LISTMONK_API_USER = "api_orchestrator"


def send_via_listmonk(
    title: str,
    content: str,
    subtitle: Optional[str] = None,
    send_at: Optional[str] = None,
) -> Optional[str]:
    """Create and schedule a campaign in Listmonk.

    Reads LISTMONK_URL, LISTMONK_API_TOKEN, LISTMONK_LIST_ID from env.
    Returns campaign ID on success, None on failure. Never raises.

    Args:
        title: Campaign subject line.
        content: HTML body.
        subtitle: Preview text (used as email preview in clients).
        send_at: ISO 8601 datetime to schedule send. None = immediate.
    """
    base_url = os.environ.get("LISTMONK_URL", "http://listmonk:9000").rstrip("/")
    token = os.environ.get("LISTMONK_API_TOKEN", "").strip()
    list_id = os.environ.get("LISTMONK_LIST_ID", "3").strip()

    if not token:
        logger.info("LISTMONK: LISTMONK_API_TOKEN not set; skipping.")
        return None

    try:
        import httpx
        auth = (LISTMONK_API_USER, token)

        # Step 1: create campaign
        payload = {
            "name": title,
            "subject": title,
            "lists": [int(list_id)],
            "from_email": os.environ.get(
                "LISTMONK_FROM_EMAIL",
                "Boubacar Barry <boubacar@catalystworks.consulting>"
            ),
            "type": "regular",
            "content_type": "html",
            "body": content,
            "send_at": send_at,
        }
        if subtitle:
            payload["altbody"] = subtitle

        resp = httpx.post(
            f"{base_url}/api/campaigns",
            json=payload,
            auth=auth,
            timeout=30.0,
        )
        if resp.status_code not in (200, 201):
            logger.error(
                f"LISTMONK: POST /api/campaigns returned {resp.status_code}: {resp.text[:500]}"
            )
            return None

        campaign_id = resp.json()["data"]["id"]
        logger.info(f"LISTMONK: campaign created id={campaign_id} title={title!r}")

        # Step 2: start (schedule) the campaign
        status_resp = httpx.put(
            f"{base_url}/api/campaigns/{campaign_id}/status",
            json={"status": "scheduled" if send_at else "running"},
            auth=auth,
            timeout=30.0,
        )
        if status_resp.status_code not in (200, 201):
            logger.error(
                f"LISTMONK: PUT /api/campaigns/{campaign_id}/status returned "
                f"{status_resp.status_code}: {status_resp.text[:300]}"
            )
            return str(campaign_id)

        logger.info(
            f"LISTMONK: campaign {campaign_id} {'scheduled for ' + send_at if send_at else 'started'}"
        )
        return str(campaign_id)

    except Exception as exc:
        logger.error(f"LISTMONK: error creating campaign: {exc}")
        return None


def create_draft(
    title: str,
    content: str,
    subtitle: Optional[str] = None,
) -> Optional[str]:
    """Deliver newsletter. Tries Listmonk first, falls back to Beehiiv draft.

    Returns delivery ID/URL on success, None on total failure.
    """
    # Primary: Listmonk
    result = send_via_listmonk(title, content, subtitle)
    if result:
        return result

    # Fallback: Beehiiv draft (manual send required)
    logger.info("LISTMONK failed or unconfigured; falling back to Beehiiv draft.")
    return _beehiiv_create_draft(title, content, subtitle)


def _beehiiv_create_draft(
    title: str,
    content: str,
    subtitle: Optional[str] = None,
) -> Optional[str]:
    """Create a draft post in Beehiiv (manual send required -- Enterprise plan needed for auto-send)."""
    api_key = os.environ.get("BEEHIIV_API_KEY", "").strip()
    pub_id = os.environ.get("BEEHIIV_PUBLICATION_ID", "").strip()

    if not api_key or not pub_id:
        logger.info("BEEHIIV: BEEHIIV_API_KEY or BEEHIIV_PUBLICATION_ID not set; skipping.")
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
    except Exception:
        logger.error(f"BEEHIIV: non-JSON response body: {resp.text[:500]}")
        return None

    post = data.get("data") or data
    post_id = post.get("id")
    post_url = post.get("url") or post.get("web_url")
    result = post_url or post_id

    if not result:
        logger.error(f"BEEHIIV: response missing id and url fields: {data}")
        return None

    logger.info(f"BEEHIIV: draft created title={title!r} id={post_id} url={post_url}")
    return str(result)
