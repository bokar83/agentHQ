"""
async_poll.py -- Shared Kie AI async job polling utility.

Replaces the flat sleep loop in kie_media._poll_task with exponential backoff,
configurable endpoints, and a high-res mode flag. Used by:
  - kie_media.py (Veo3, image, video tasks via /jobs/recordInfo)
  - sora_watermark_remover (same endpoint, different model)
  - audio_remix via Suno V5 (/generate/record-info)
  - Any future Kie model that follows the createTask -> poll pattern

Sankofa Council note (2026-04-27): build as shared primitive from day one,
not a Veo3-specific fix. Every Kie async call reuses this module.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

KIE_BASE = "https://api.kie.ai"

# Polling endpoints -- Kie uses two different paths depending on API surface
ENDPOINT_JOBS = "/api/v1/jobs/recordInfo"          # createTask jobs (video, watermark)
ENDPOINT_GENERATE = "/api/v1/generate/record-info"  # generate jobs (Suno, image models)


class PollTimeout(Exception):
    pass


class PollFailed(Exception):
    pass


def poll_until_done(
    task_id: str,
    headers: dict,
    endpoint: str = ENDPOINT_JOBS,
    interval: float = 5.0,
    max_wait: float = 600.0,
    backoff_factor: float = 1.5,
    backoff_cap: float = 30.0,
) -> dict:
    """
    Poll a Kie AI task until it reaches a terminal state.

    Args:
        task_id: The taskId returned by createTask or generate endpoint.
        headers: Auth headers dict ({"Authorization": "Bearer <key>"}).
        endpoint: Which poll endpoint to use (ENDPOINT_JOBS or ENDPOINT_GENERATE).
        interval: Initial poll interval in seconds.
        max_wait: Total timeout in seconds before raising PollTimeout.
        backoff_factor: Multiply interval by this on each attempt (1.0 = flat).
        backoff_cap: Maximum interval between polls regardless of backoff.

    Returns:
        dict with keys: state, result_urls, cost_time_ms, raw_data

    Raises:
        PollFailed: Task reached a failed terminal state.
        PollTimeout: max_wait exceeded with no terminal state.
    """
    url = f"{KIE_BASE}{endpoint}"
    elapsed = 0.0
    current_interval = interval

    while elapsed < max_wait:
        resp = httpx.get(url, headers=headers, params={"taskId": task_id}, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        data = body.get("data", {})
        state = data.get("state", "")

        if state == "success":
            result_raw = data.get("resultJson", "{}")
            result = json.loads(result_raw) if isinstance(result_raw, str) else (result_raw or {})
            urls = result.get("resultUrls", []) or []
            if not urls:
                raise PollFailed(f"Task {task_id} succeeded but returned no resultUrls: {result}")
            return {
                "state": "success",
                "result_urls": urls,
                "cost_time_ms": data.get("costTime", 0),
                "raw_data": data,
            }

        if state == "fail":
            raise PollFailed(
                f"Task {task_id} failed: {data.get('failMsg', 'unknown')} "
                f"(code={data.get('failCode')})"
            )

        logger.debug("poll %s state=%r elapsed=%.0fs next=%.1fs", task_id[:8], state, elapsed, current_interval)
        time.sleep(current_interval)
        elapsed += current_interval
        current_interval = min(current_interval * backoff_factor, backoff_cap)

    raise PollTimeout(f"Task {task_id} timed out after {max_wait}s")


def submit_and_poll(
    create_url: str,
    create_payload: dict,
    headers: dict,
    poll_endpoint: str = ENDPOINT_JOBS,
    interval: float = 5.0,
    max_wait: float = 600.0,
) -> dict:
    """
    POST to a Kie create endpoint, extract taskId, then poll until done.

    Returns same dict as poll_until_done plus task_id.
    Raises httpx.HTTPError on create failure, PollFailed/PollTimeout on poll failure.
    """
    resp = httpx.post(create_url, headers=headers, json=create_payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise PollFailed(f"createTask failed: {body.get('msg')} (code={body.get('code')})")
    task_id = body.get("data", {}).get("taskId")
    if not task_id:
        raise PollFailed(f"createTask returned no taskId: {body}")

    result = poll_until_done(task_id, headers, endpoint=poll_endpoint, interval=interval, max_wait=max_wait)
    result["task_id"] = task_id
    return result


def high_res_params(base_params: dict, enabled: bool = False) -> dict:
    """
    Inject high-res mode into a Veo3 request payload when enabled.
    Veo3-fast defaults to 1080p; high-res bumps to 4K where supported.
    """
    if not enabled:
        return base_params
    return {**base_params, "resolution": "4k"}
