"""Unified video generation dispatcher, all job types: batch, ugc, cameo, narrative, ads, watermark_remove."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

MAX_JOBS_PER_TICK = 3
STALE_DISPATCHED_TTL_MINUTES = 30
VALID_JOB_TYPES = ("batch", "ugc", "cameo", "narrative", "ads", "watermark_remove")
HAIKU_MODEL = "anthropic/claude-haiku-4.5"


def _pg_conn():
    """Return a psycopg2 connection using env vars."""
    import psycopg2

    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=5432,
    )


def _haiku_json(prompt: str, fallback: Any) -> Any:
    try:
        import openai

        client = openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        response = client.chat.completions.create(
            model=HAIKU_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON only. No markdown. No explanation.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        content = (response.choices[0].message.content or "").strip()
        return json.loads(content)
    except Exception as e:
        logger.warning(f"video_crew haiku_json fallback used: {type(e).__name__}: {e}")
        return fallback


class VideoJobDispatcher:
    def enqueue_video_job(
        self,
        job_type,
        prompt,
        params=None,
        linked_content_id=None,
        requested_by="system",
    ) -> str:
        if job_type not in VALID_JOB_TYPES:
            raise ValueError(f"invalid job_type: {job_type}")
        if not prompt:
            raise ValueError("prompt is required")

        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO video_jobs (job_type, prompt, params_json, linked_content_id, requested_by)
                VALUES (%s, %s, %s::jsonb, %s, %s)
                RETURNING id
                """,
                (
                    job_type,
                    prompt,
                    json.dumps(params or {}),
                    linked_content_id,
                    requested_by,
                ),
            )
            job_id = str(cur.fetchone()[0])
            conn.commit()
            cur.close()
            return job_id
        finally:
            conn.close()

    def tick(self) -> dict:
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, job_type, prompt, params_json, linked_content_id, requested_by
                FROM video_jobs
                WHERE status = 'pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT %s
                """,
                (MAX_JOBS_PER_TICK,),
            )
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()

        processed = 0
        done = 0
        failed = 0

        for row in rows:
            job_id = str(row[0])
            if not self._claim_job(job_id):
                continue

            processed += 1
            job = {
                "id": job_id,
                "job_type": row[1],
                "prompt": row[2],
                "params_json": row[3] or {},
                "linked_content_id": row[4],
                "requested_by": row[5],
            }

            try:
                result_json = self._dispatch(job)
                self._complete_job(job_id, result_json)
                done += 1
            except Exception as e:
                self._fail_job(job_id, str(e))
                failed += 1

        return {"processed": processed, "done": done, "failed": failed}

    def _claim_job(self, job_id) -> bool:
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE video_jobs
                SET status = 'dispatched',
                    dispatched_at = NOW(),
                    attempts = attempts + 1
                WHERE id = %s
                  AND status = 'pending'
                RETURNING id
                """,
                (job_id,),
            )
            claimed = cur.fetchone() is not None
            conn.commit()
            cur.close()
            return claimed
        finally:
            conn.close()

    def _complete_job(self, job_id, result_json):
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE video_jobs
                SET status = 'done',
                    result_json = %s::jsonb,
                    error_msg = NULL,
                    completed_at = NOW()
                WHERE id = %s
                """,
                (json.dumps(result_json), job_id),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def _fail_job(self, job_id, error_msg):
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT attempts, max_attempts
                FROM video_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cur.fetchone()
            if not row:
                cur.close()
                conn.close()
                return

            attempts, max_attempts = int(row[0]), int(row[1])
            if attempts < max_attempts:
                cur.execute(
                    """
                    UPDATE video_jobs
                    SET status = 'pending',
                        error_msg = %s,
                        dispatched_at = NULL
                    WHERE id = %s
                    """,
                    (error_msg[:2000], job_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE video_jobs
                    SET status = 'failed',
                        error_msg = %s,
                        completed_at = NOW()
                    WHERE id = %s
                    """,
                    (error_msg[:2000], job_id),
                )
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def _cleanup_stale_dispatched(self):
        conn = _pg_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                f"""
                UPDATE video_jobs
                SET status = 'pending',
                    dispatched_at = NULL
                WHERE status = 'dispatched'
                  AND attempts < max_attempts
                  AND dispatched_at < NOW() - INTERVAL '{STALE_DISPATCHED_TTL_MINUTES} minutes'
                """
            )
            reset_count = cur.rowcount
            conn.commit()
            cur.close()
            if reset_count:
                logger.info(f"video_crew reset {reset_count} stale dispatched job(s)")
        finally:
            conn.close()

    def _dispatch(self, job: dict) -> dict:
        runners = {
            "watermark_remove": self._run_watermark_remove,
            "batch": self._run_batch,
            "cameo": self._run_cameo,
            "ugc": self._run_ugc,
            "narrative": self._run_narrative,
            "ads": self._run_ads,
        }
        return runners[job["job_type"]](job)

    def _run_watermark_remove(self, job: dict) -> dict:
        import kie_media

        params = job["params_json"] or {}
        video_url = params.get("video_url")
        if not video_url:
            raise ValueError("watermark_remove requires params.video_url")
        result = kie_media.sora_watermark_remover(video_url)
        return {"job_type": job["job_type"], "result": result}

    def _run_batch(self, job: dict) -> dict:
        import kie_media

        params = job["params_json"] or {}
        prompts = params.get("prompts") or [job["prompt"]]
        aspect_ratio = params.get("aspect_ratio", "16:9")
        videos = []
        for prompt in prompts:
            videos.append(
                kie_media.generate_video(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    task_type="text_to_video",
                    linked_content_id=job["linked_content_id"],
                )
            )
        return {"job_type": job["job_type"], "videos": videos}

    def _run_cameo(self, job: dict) -> dict:
        import kie_media

        params = job["params_json"] or {}
        character_image_url = params.get("character_image_url")
        if not character_image_url:
            raise ValueError("cameo requires params.character_image_url")
        result = kie_media._run_with_retries(
            "image_to_video",
            job["prompt"],
            {
                "image_url": character_image_url,
                "aspect_ratio": params.get("aspect_ratio", "16:9"),
            },
        )
        return {"job_type": job["job_type"], "result": result}

    def _run_ugc(self, job: dict) -> dict:
        import kie_media

        params = job["params_json"] or {}
        scene_count = int(params.get("scene_count", 3))
        fallback_scenes = [part.strip() for part in job["prompt"].split(".") if part.strip()]
        if not fallback_scenes:
            fallback_scenes = [job["prompt"]]
        fallback_scenes = fallback_scenes[:scene_count]
        scene_prompts = _haiku_json(
            (
                f"Split this script into exactly {scene_count} short UGC video scene prompts. "
                "Return a JSON array of strings only.\n\n"
                f"SCRIPT:\n{job['prompt']}"
            ),
            fallback_scenes,
        )
        videos = []
        for scene_prompt in scene_prompts:
            videos.append(
                kie_media._run_with_retries(
                    "image_to_video",
                    scene_prompt,
                    {
                        "image_url": params.get("character_image_url") or params.get("image_url"),
                        "aspect_ratio": params.get("aspect_ratio", "16:9"),
                    },
                )
            )
        return {"job_type": job["job_type"], "scene_prompts": scene_prompts, "videos": videos}

    def _run_narrative(self, job: dict) -> dict:
        import kie_media

        params = job["params_json"] or {}
        scenes = params.get("scenes") or [job["prompt"]]
        continuity_url = params.get("continuity_url")
        outputs = []
        for scene_prompt in scenes:
            extra_input = {"aspect_ratio": params.get("aspect_ratio", "16:9")}
            if continuity_url:
                extra_input["image_url"] = continuity_url
                result = kie_media._run_with_retries("image_to_video", scene_prompt, extra_input)
            else:
                result = kie_media._run_with_retries("text_to_video", scene_prompt, extra_input)
            urls = result.get("result_urls") or []
            if urls:
                continuity_url = urls[0]
            outputs.append({"prompt": scene_prompt, "result": result, "continuity_url": continuity_url})
        return {"job_type": job["job_type"], "scenes": outputs}

    def _run_ads(self, job: dict) -> dict:
        import kie_media

        params = job["params_json"] or {}
        structured_prompt = _haiku_json(
            (
                "Rewrite this ad brief into one concise, cinematic text-to-video prompt. "
                "Return JSON like {\"prompt\": \"...\"} only.\n\n"
                f"BRIEF:\n{job['prompt']}"
            ),
            {"prompt": job["prompt"]},
        )
        final_prompt = structured_prompt.get("prompt") or job["prompt"]
        result = kie_media.generate_video(
            prompt=final_prompt,
            aspect_ratio=params.get("aspect_ratio", "16:9"),
            task_type="text_to_video",
            linked_content_id=job["linked_content_id"],
        )
        return {"job_type": job["job_type"], "prompt": final_prompt, "result": result}


def enqueue_video_job(
    job_type,
    prompt,
    params=None,
    linked_content_id=None,
    requested_by="system",
) -> dict:
    dispatcher = VideoJobDispatcher()
    job_id = dispatcher.enqueue_video_job(
        job_type=job_type,
        prompt=prompt,
        params=params,
        linked_content_id=linked_content_id,
        requested_by=requested_by,
    )
    return {"job_id": job_id}


def run_video_tick() -> dict:
    from autonomy_guard import get_guard

    decision = get_guard().guard("video_crew", estimated_usd=2.0)
    if not decision.allowed:
        logger.info(f"video_crew tick blocked: {decision.reason}")
        return {"processed": 0, "done": 0, "failed": 0, "status": decision.decision_tag}
    if decision.dry_run:
        logger.info("video_crew tick dry-run: no cleanup or dispatch executed")
        return {"processed": 0, "done": 0, "failed": 0, "status": "dry-run"}

    dispatcher = VideoJobDispatcher()
    dispatcher._cleanup_stale_dispatched()
    result = dispatcher.tick()
    logger.info(f"video_crew tick result: {result}")
    return result
