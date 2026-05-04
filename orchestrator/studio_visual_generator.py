"""
studio_visual_generator.py — Studio M3: Visual asset generation per scene.

Wraps kie_media.generate_image + generate_video.
Runs scenes in parallel batches of 3 (API rate limit buffer).

For each scene:
  1. generate_image (seedream/4.5, 16:9) → still
  2. generate_video (hailuo image-to-video) → clip

Returns list of scene asset dicts, one per scene.
"""
from __future__ import annotations

import concurrent.futures
import logging
import time
from typing import Any

logger = logging.getLogger("agentsHQ.studio_visual_generator")

_BATCH_SIZE = 3
_RETRY_DELAY_SEC = 5


def generate_visuals(
    scenes: list[Any],  # list[Scene] from studio_scene_builder
    brand: dict[str, Any],
    *,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """
    Generate image + video for every scene. Returns list[scene_assets].

    scene_assets[i]:
      {
        "scene_index": int,
        "image_url": str,
        "image_drive_id": str,
        "video_url": str,
        "video_drive_id": str,
        "image_local_path": str,
        "video_local_path": str,
      }
    """
    channel_id = brand.get("channel_id", "unknown")
    results: list[dict[str, Any]] = [{}] * len(scenes)

    if dry_run:
        logger.info("[dry_run] visual_generator: returning stubs for %d scenes", len(scenes))
        return [_stub_asset(i) for i in range(len(scenes))]

    # Process in batches to stay within kie.ai rate limits
    batches = [scenes[i:i + _BATCH_SIZE] for i in range(0, len(scenes), _BATCH_SIZE)]

    for batch_idx, batch in enumerate(batches):
        logger.info(
            "visual_generator: batch %d/%d (%d scenes)",
            batch_idx + 1, len(batches), len(batch),
        )
        batch_results = _process_batch(batch, channel_id)
        for scene, result in zip(batch, batch_results):
            results[scene.index] = result

        # Brief pause between batches
        if batch_idx < len(batches) - 1:
            time.sleep(_RETRY_DELAY_SEC)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Batch processor
# ─────────────────────────────────────────────────────────────────────────────

def _process_batch(
    scenes: list[Any],
    channel_id: str,
) -> list[dict[str, Any]]:
    """Run image + video generation for a batch of scenes in parallel."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=_BATCH_SIZE) as executor:
        futures = {
            executor.submit(_generate_scene_assets, scene, channel_id): scene
            for scene in scenes
        }
        results = []
        for future in concurrent.futures.as_completed(futures):
            scene = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                logger.error(
                    "visual_generator: scene %d failed: %s",
                    scene.index, exc,
                )
                result = _stub_asset(scene.index, error=str(exc))
            results.append((scene.index, result))

    # Sort by scene index to maintain order
    results.sort(key=lambda x: x[0])
    return [r for _, r in results]


def _vault_lookup(prompt: str) -> str:
    """Return local video path from asset vault if tags match, else empty string."""
    import json, pathlib, re
    vault_path = pathlib.Path("/app/configs/asset_vault.json")
    if not vault_path.exists():
        return ""
    try:
        vault = json.loads(vault_path.read_text())
        query_words = set(re.findall(r'[a-z]+', prompt.lower())) - {"a","an","the","of","in","with","and","to","for","on","slow","cinematic","zoom"}
        best_path, best_score = "", 0
        for asset in vault.get("assets", []):
            if not pathlib.Path(asset["path"]).exists():
                continue
            tags = set(asset.get("tags", []))
            score = len(query_words & tags)
            if score > best_score and score >= 2:
                best_score, best_path = score, asset["path"]
        if best_path:
            logger.info("visual_generator: vault hit (score=%d) for scene: %s", best_score, prompt[:60])
        return best_path
    except Exception as e:
        logger.warning("visual_generator: vault lookup failed: %s", e)
        return ""


def _generate_scene_assets(scene: Any, channel_id: str) -> dict[str, Any]:
    """Generate still image for one scene. Images only — ffmpeg handles motion/assembly.

    Model: GPT Image 2 (best quality, handles complex prompts well).
    Vault lookup first to reuse existing images and avoid Kai spend.
    No video generation — Ken Burns motion applied at render time by ffmpeg.
    """
    from kie_media import generate_image

    prompt = getattr(scene, "image_prompt", "") or getattr(scene, "video_prompt", "")

    # Check vault first
    vault_path = _vault_lookup(prompt)
    if vault_path:
        return {
            "scene_index": scene.index,
            "image_url": "", "image_drive_id": "",
            "image_local_path": vault_path,
            "video_url": "", "video_drive_id": "", "video_local_path": "",
        }

    notion_id = f"studio_scene_{channel_id}_{scene.index}"

    img_result = generate_image(
        prompt=prompt,
        aspect_ratio="16:9",
        task_type="gpt_image_2_text",
        linked_content_id=notion_id,
    )

    return {
        "scene_index": scene.index,
        "image_url": img_result.get("drive_url", ""),
        "image_drive_id": img_result.get("drive_file_id", ""),
        "image_local_path": img_result.get("local_path", ""),
        "video_url": "", "video_drive_id": "", "video_local_path": "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Stub
# ─────────────────────────────────────────────────────────────────────────────

def _stub_asset(index: int, error: str = "") -> dict[str, Any]:
    return {
        "scene_index": index,
        "image_url": f"https://drive.google.com/stub_image_{index}",
        "image_drive_id": f"stub_img_{index}",
        "image_local_path": f"workspace/media/stub_scene_{index}.jpg",
        "video_url": f"https://drive.google.com/stub_video_{index}",
        "video_drive_id": f"stub_vid_{index}",
        "video_local_path": f"workspace/media/stub_scene_{index}.mp4",
        "error": error,
    }
