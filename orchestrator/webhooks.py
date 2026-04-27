"""Webhook endpoints for asynchronous media callbacks."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("agentsHQ.webhooks")

router = APIRouter()


def _extract_result_url(payload: dict) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if isinstance(payload.get("output"), dict):
        data = payload["output"]
    if isinstance(payload.get("result"), dict):
        data = payload["result"]
    candidate = data.get("result_url") or data.get("video", {}).get("url")
    if candidate:
        return str(candidate)
    videos = data.get("videos") if isinstance(data, dict) else None
    if isinstance(videos, list) and videos:
        first = videos[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict) and first.get("url"):
            return str(first["url"])
    raise HTTPException(status_code=400, detail="Missing result_url in fal callback payload")


@router.post("/webhooks/fal-upscale")
async def fal_upscale_webhook(request: Request):
    payload = await request.json()
    job_id = str(payload.get("request_id") or payload.get("job_id") or "").strip()
    if not job_id:
        raise HTTPException(status_code=400, detail="Missing request_id/job_id in fal callback payload")

    result_url = _extract_result_url(payload)

    try:
        from memory import _pg_conn

        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE upscale_jobs
                   SET status = %s,
                       result_url = %s,
                       completed_at = NOW()
                 WHERE job_id = %s
                """,
                ("done", result_url, job_id),
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO upscale_jobs (job_id, status, result_url, completed_at)
                    VALUES (%s, %s, %s, NOW())
                    """,
                    (job_id, "done", result_url),
                )
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"fal_upscale_webhook database write failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to persist fal upscale callback") from e

    return {"ok": True, "job_id": job_id, "result_url": result_url}
