"""fal.ai video upscale submission helpers."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("agentsHQ.upscale")


def submit_upscale_job(
    video_url: str,
    webhook_url: str,
    model: str = "fal-ai/topaz-video-upscale",
) -> str:
    """Submit a fal.ai upscale job and persist the pending row."""
    api_key = os.environ.get("FAL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("FAL_API_KEY is not set")

    resp = httpx.post(
        f"https://queue.fal.run/{model}",
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "video_url": video_url,
            "webhook_url": webhook_url,
            "webhookUrl": webhook_url,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    job_id = str(data.get("request_id") or data.get("job_id") or "").strip()
    if not job_id:
        raise RuntimeError(f"fal.ai submission returned no job id: {data}")

    try:
        from memory import _pg_conn

        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO upscale_jobs (job_id, source_url, status, webhook_url, model, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE
                SET source_url = EXCLUDED.source_url,
                    status = EXCLUDED.status,
                    webhook_url = EXCLUDED.webhook_url,
                    model = EXCLUDED.model
                """,
                (job_id, video_url, "pending", webhook_url, model),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"submit_upscale_job database write failed for {job_id}: {e}")
        raise

    return job_id
