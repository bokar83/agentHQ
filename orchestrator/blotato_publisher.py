"""
blotato_publisher.py - Atlas M7b. Verified-against-Blotato-API publisher.

Wraps the Blotato REST API for posting to LinkedIn + X (and any future
platform Blotato supports). Built on the API contract verified end-to-end
on 2026-04-25 during the M7a smoke test (LinkedIn 5 sec submit-to-live,
X 9 sec, both verbatim).

Used by orchestrator/auto_publisher.py to fire scheduled posts.
Platform-agnostic by design so Studio M4 can reuse the same publisher
for YouTube + IG + TikTok + Threads + Facebook + Pinterest + Bluesky.

API reference: https://help.blotato.com/api/api-reference (verified 2026-04-25)
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("agentsHQ.blotato_publisher")

BLOTATO_API_BASE = os.environ.get(
    "BLOTATO_API_BASE",
    "https://backend.blotato.com/v2",
)
DEFAULT_POLL_INTERVAL_SEC = 5
DEFAULT_POLL_TIMEOUT_SEC = 120

# Platforms Blotato accepts (verified on the GET /v2/users/me/accounts response
# during M7a). Atlas uses linkedin + twitter today; the rest are documented for
# Studio M4 reuse without refactor.
SUPPORTED_PLATFORMS = (
    "linkedin",
    "twitter",
    "facebook",
    "instagram",
    "pinterest",
    "tiktok",
    "threads",
    "bluesky",
    "youtube",
    "other",
)

# Atlas Content Board uses Notion's "X" platform name; Blotato's API uses
# "twitter". This dict normalizes Notion-side names to Blotato-side names.
NOTION_TO_BLOTATO_PLATFORM = {
    "X": "twitter",
    "LinkedIn": "linkedin",
    "Facebook": "facebook",
    "Instagram": "instagram",
    "Pinterest": "pinterest",
    "TikTok": "tiktok",
    "Threads": "threads",
    "Bluesky": "bluesky",
    "YouTube": "youtube",
}


@dataclass
class PublishResult:
    """Result of publish() + poll_until_terminal(). One of three terminal
    states: published, failed, timeout.
    """
    status: str  # 'published' | 'failed' | 'timeout'
    post_submission_id: Optional[str] = None
    public_url: Optional[str] = None
    error_message: Optional[str] = None
    elapsed_sec: float = 0.0
    raw_response: Optional[dict] = None

    @property
    def ok(self) -> bool:
        return self.status == "published"


class BlotatoPublisher:
    """Thin wrapper around POST /v2/posts + GET /v2/posts/{id}.

    Reads BLOTATO_API_KEY from env. Optional account ID env vars are read
    by the auto_publisher tick, not here, so the publisher stays
    platform-agnostic.

    Reuses one httpx client across calls for connection pooling.
    """

    def __init__(self, api_key: Optional[str] = None, base: Optional[str] = None):
        self.api_key = api_key or os.environ.get("BLOTATO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BLOTATO_API_KEY not set. "
                "Add it to the env before calling BlotatoPublisher()."
            )
        self.base = (base or BLOTATO_API_BASE).rstrip("/")
        self._client = None  # lazy-init httpx client

    def _http(self):
        """Lazy-init httpx client. Avoids importing httpx at module load
        so test environments without httpx can still import this module
        for type checks.
        """
        if self._client is None:
            import httpx
            self._client = httpx.Client(
                base_url=self.base,
                headers={
                    "blotato-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def publish(
        self,
        text: str,
        account_id: str,
        platform: str,
        *,
        media_urls: Optional[list] = None,
        scheduled_time_iso: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> str:
        """POST /v2/posts. Returns postSubmissionId for status polling.

        Args:
            text: post body, verbatim. Blotato publishes exactly what we send.
            account_id: Blotato accountId for this platform (from
                GET /v2/users/me/accounts; persistent per-account).
            platform: Blotato platform name (linkedin, twitter, etc.) OR
                a Notion-side name (LinkedIn, X) that this method normalizes.
            media_urls: list of public URLs for attached media. Pass empty
                list for text-only. Use BlotatoPublisher.upload_media() first
                if you have local files.
            scheduled_time_iso: optional ISO 8601 (with offset) for
                Blotato-side scheduling. None = publish immediately.
                CRITICAL: this is a root-level field in the API per
                Blotato docs; nesting it inside post causes silent
                immediate publication.
            page_id: LinkedIn-only optional Company Page ID. Omit for
                personal LinkedIn profile.

        Returns:
            postSubmissionId (str). Pass to poll_until_terminal() to
            get the final status + publicUrl.

        Raises:
            ValueError: missing required field, unsupported platform.
            RuntimeError: HTTP 4xx/5xx from Blotato.
        """
        if not text or not text.strip():
            raise ValueError("text must be non-empty")
        if not account_id:
            raise ValueError("account_id must be non-empty")

        # Normalize platform name (accept either Notion-side or Blotato-side).
        # Handle case variants (Notion stores lowercase: "x", "tiktok").
        _canon = {k.lower(): v for k, v in NOTION_TO_BLOTATO_PLATFORM.items()}
        bp = _canon.get(platform.lower(), platform).lower()

        # X/Twitter hard cap: 280 chars. Truncate with ellipsis.
        if bp == "twitter" and len(text) > 280:
            text = text[:277] + "..."
        if bp not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"unsupported platform {platform!r} "
                f"(after normalize: {bp!r}). "
                f"Supported: {SUPPORTED_PLATFORMS}"
            )

        target = {"targetType": bp}
        if bp == "linkedin" and page_id:
            target["pageId"] = page_id
        if bp == "tiktok":
            target.update({
                "privacyLevel": "PUBLIC_TO_EVERYONE",
                "disabledComments": False,
                "disabledDuet": False,
                "disabledStitch": False,
                "isBrandedContent": False,
                "isYourBrand": False,
                "isAiGenerated": True,
            })

        body = {
            "post": {
                "accountId": str(account_id),
                "content": {
                    "text": text,
                    "mediaUrls": list(media_urls or []),
                    "platform": bp,
                },
                "target": target,
            }
        }
        # CRITICAL: scheduledTime is a root-level sibling of post,
        # NOT inside post. Misnesting causes silent immediate publish.
        if scheduled_time_iso:
            body["scheduledTime"] = scheduled_time_iso

        client = self._http()
        try:
            resp = client.post("/posts", json=body)
        except Exception as e:
            raise RuntimeError(f"Blotato POST /v2/posts network error: {e}") from e

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Blotato POST /v2/posts returned {resp.status_code}: "
                f"{resp.text[:500]}"
            )

        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(
                f"Blotato POST /v2/posts returned non-JSON body: {resp.text[:500]}"
            ) from e

        post_id = (
            data.get("postSubmissionId")
            or data.get("id")
            or (data.get("post") or {}).get("id")
        )
        if not post_id:
            raise RuntimeError(
                f"Blotato POST /v2/posts returned no postSubmissionId: {data}"
            )

        logger.info(
            f"BLOTATO: published {bp} (account={account_id}) "
            f"submission_id={post_id} text_len={len(text)}"
        )
        return str(post_id)

    def get_status(self, post_submission_id: str) -> dict:
        """GET /v2/posts/{id}. Returns the parsed Blotato response.

        Possible status values per M7a smoke test: in-progress, published, failed.
        Published response includes publicUrl. Failed includes errorMessage.
        """
        if not post_submission_id:
            raise ValueError("post_submission_id must be non-empty")

        client = self._http()
        try:
            resp = client.get(f"/posts/{post_submission_id}")
        except Exception as e:
            raise RuntimeError(f"Blotato GET /v2/posts/{post_submission_id} network error: {e}") from e

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Blotato GET /v2/posts/{post_submission_id} returned {resp.status_code}: "
                f"{resp.text[:500]}"
            )

        try:
            return resp.json()
        except Exception as e:
            raise RuntimeError(
                f"Blotato GET /v2/posts/{post_submission_id} returned non-JSON: {resp.text[:500]}"
            ) from e

    def poll_until_terminal(
        self,
        post_submission_id: str,
        *,
        timeout_sec: int = DEFAULT_POLL_TIMEOUT_SEC,
        interval_sec: int = DEFAULT_POLL_INTERVAL_SEC,
    ) -> PublishResult:
        """Poll GET /v2/posts/{id} until status is terminal (published or
        failed) OR timeout elapses.

        Returns a PublishResult dataclass.
        """
        deadline = time.time() + timeout_sec
        start = time.time()
        last_response = None

        while time.time() < deadline:
            try:
                data = self.get_status(post_submission_id)
            except RuntimeError as e:
                logger.warning(
                    f"BLOTATO poll: transient error on {post_submission_id}: {e}"
                )
                time.sleep(interval_sec)
                continue

            last_response = data

            # Blotato response shape (verified M7a): top-level status field
            # OR nested under "post". Accept both.
            status = data.get("status") or (data.get("post") or {}).get("status") or ""
            status = status.lower()
            public_url = data.get("publicUrl") or (data.get("post") or {}).get("publicUrl")
            error_msg = data.get("errorMessage") or (data.get("post") or {}).get("errorMessage")

            if status == "published":
                elapsed = time.time() - start
                logger.info(
                    f"BLOTATO poll: {post_submission_id} published in {elapsed:.1f}s "
                    f"public_url={public_url}"
                )
                return PublishResult(
                    status="published",
                    post_submission_id=post_submission_id,
                    public_url=public_url,
                    elapsed_sec=elapsed,
                    raw_response=data,
                )

            if status == "failed":
                elapsed = time.time() - start
                logger.warning(
                    f"BLOTATO poll: {post_submission_id} failed in {elapsed:.1f}s "
                    f"error={error_msg}"
                )
                return PublishResult(
                    status="failed",
                    post_submission_id=post_submission_id,
                    error_message=error_msg or "Blotato returned status=failed with no errorMessage",
                    elapsed_sec=elapsed,
                    raw_response=data,
                )

            # Still in-progress, sleep + poll again.
            time.sleep(interval_sec)

        elapsed = time.time() - start
        logger.warning(
            f"BLOTATO poll: {post_submission_id} did not reach terminal "
            f"status within {timeout_sec}s (last_status={last_response})"
        )
        return PublishResult(
            status="timeout",
            post_submission_id=post_submission_id,
            error_message=f"Did not reach terminal status within {timeout_sec}s",
            elapsed_sec=elapsed,
            raw_response=last_response,
        )

    def publish_and_wait(
        self,
        text: str,
        account_id: str,
        platform: str,
        *,
        media_urls: Optional[list] = None,
        timeout_sec: int = DEFAULT_POLL_TIMEOUT_SEC,
    ) -> PublishResult:
        """Convenience wrapper: publish() + poll_until_terminal() in one call.

        Used by callers that do not need to persist post_submission_id between
        publish and poll. The auto_publisher tick does NOT use this; it
        persists the post_submission_id to Notion BEFORE polling so a poll-loop
        crash cannot lose the submission ID.
        """
        post_id = self.publish(
            text=text,
            account_id=account_id,
            platform=platform,
            media_urls=media_urls,
        )
        return self.poll_until_terminal(post_id, timeout_sec=timeout_sec)


# ═════════════════════════════════════════════════════════════════════════════
# Module-level convenience singletons + helpers (used by tools.py wiring)
# ═════════════════════════════════════════════════════════════════════════════

_singleton: Optional[BlotatoPublisher] = None


def get_publisher() -> BlotatoPublisher:
    """Lazy-init module-level singleton. Re-uses one httpx client across
    callers within a process.
    """
    global _singleton
    if _singleton is None:
        _singleton = BlotatoPublisher()
    return _singleton


def list_accounts() -> list:
    """GET /v2/users/me/accounts. Returns the items array.

    Used for ad-hoc verification that account IDs are still valid. Read-only,
    safe to call from anywhere.
    """
    pub = get_publisher()
    client = pub._http()
    resp = client.get("/users/me/accounts")
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"GET /v2/users/me/accounts returned {resp.status_code}: {resp.text[:500]}"
        )
    return resp.json().get("items", [])
