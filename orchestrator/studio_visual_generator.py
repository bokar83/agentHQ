"""
studio_visual_generator.py — Studio M3: Visual asset generation per scene.

M3.4 Mixed Motion: Scene 0 (Hook) and Scene 5 (Climax) get real Kai image-to-video
clips. Scenes 1-4 and 6 remain Ken Burns stills. Graceful fallback to Ken Burns on
any video API failure.
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("agentsHQ.studio_visual_generator")

_BATCH_SIZE = 3
_RETRY_DELAY_SEC = 5

# Scene indices that get real Kai image-to-video generation (M3.4 Mixed Motion).
# All other scenes use Ken Burns stills rendered by ffmpeg at publish time.
_VIDEO_MOTION_SCENES = frozenset({0, 5})  # 0=Hook, 5=Climax


_MOTION_SIDECAR_NAME = "motion_assets.json"


def generate_visuals(
    scenes: list[Any],  # list[Scene] from studio_scene_builder
    brand: dict[str, Any],
    *,
    dry_run: bool = False,
    project_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Generate image + video for every scene. Returns list[scene_assets].

    scene_assets[i]:
      {
        "scene_index": int,
        "motion_type": "video" | "ken_burns",  # "video" for scenes 0+5, else "ken_burns"
        "image_url": str,
        "image_drive_id": str,
        "image_local_path": str,
        "video_url": str,       # populated only for motion_type="video"
        "video_drive_id": str,
        "video_local_path": str,
      }

    When project_dir is provided, writes a motion_assets.json sidecar alongside
    manifest.json so render_publisher can route motion scenes to pre-generated clips.
    """
    channel_id = brand.get("channel_id", "unknown")
    results: list[dict[str, Any]] = [{}] * len(scenes)

    if dry_run:
        logger.info("[dry_run] visual_generator: returning stubs for %d scenes", len(scenes))
        stubs = [_stub_asset(i) for i in range(len(scenes))]
        _write_motion_sidecar(stubs, project_dir)
        return stubs

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

    _write_motion_sidecar(results, project_dir)
    return results


def _write_motion_sidecar(assets: list[dict[str, Any]], project_dir: Path | None) -> None:
    """Write motion_assets.json sidecar so render_publisher can find video clips."""
    if not project_dir:
        return
    try:
        sidecar = {a["scene_index"]: a for a in assets if a}
        (project_dir / _MOTION_SIDECAR_NAME).write_text(json.dumps(sidecar, indent=2))
        logger.info("visual_generator: motion sidecar written to %s", project_dir / _MOTION_SIDECAR_NAME)
    except Exception as exc:
        logger.warning("visual_generator: failed to write motion sidecar: %s", exc)


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
    """Generate assets for one scene.

    M3.4: Scenes in _VIDEO_MOTION_SCENES (Hook=0, Climax=5) get a real Kai
    image-to-video clip generated from the still image. All other scenes stay
    as Ken Burns stills. Falls back to Ken Burns on any video API error.

    Model: GPT Image 2 for stills. Hailuo image-to-video for motion scenes.
    Vault lookup first to reuse existing images and avoid Kai spend.
    """
    from kie_media import generate_image, generate_video

    prompt = getattr(scene, "image_prompt", "") or getattr(scene, "video_prompt", "")
    is_motion_scene = scene.index in _VIDEO_MOTION_SCENES

    # Check vault first
    vault_path = _vault_lookup(prompt)
    if vault_path:
        base = {
            "scene_index": scene.index,
            "motion_type": "ken_burns",
            "image_url": "", "image_drive_id": "",
            "image_local_path": vault_path,
            "video_url": "", "video_drive_id": "", "video_local_path": "",
        }
        if is_motion_scene:
            base = _generate_video_clip(base, prompt, channel_id)
        return base

    notion_id = f"studio_scene_{channel_id}_{scene.index}"

    img_result = generate_image(
        prompt=prompt,
        aspect_ratio="16:9",
        task_type="gpt_image_2_text",
        linked_content_id=notion_id,
    )

    asset = {
        "scene_index": scene.index,
        "motion_type": "ken_burns",
        "image_url": img_result.get("drive_url", ""),
        "image_drive_id": img_result.get("drive_file_id", ""),
        "image_local_path": img_result.get("local_path", ""),
        "video_url": "", "video_drive_id": "", "video_local_path": "",
    }

    if is_motion_scene:
        asset = _generate_video_clip(asset, prompt, channel_id)

    return asset


def _generate_video_clip(asset: dict[str, Any], prompt: str, channel_id: str) -> dict[str, Any]:
    """Attempt Kai image-to-video for a motion scene. Falls back to ken_burns on failure.

    Uses the Kai CDN source_url (local_path downloaded from Kai) as the image seed,
    NOT the Drive webViewLink — hailuo requires a direct media URL, not a Drive share.
    """
    from kie_media import generate_video

    # Prefer local_path as the source image; fall back to image_url (Kai CDN)
    source_image_url = asset.get("image_url", "")
    if not source_image_url:
        logger.warning(
            "visual_generator: scene %d motion skipped — no image_url for video seed",
            asset["scene_index"],
        )
        return asset

    logger.info(
        "visual_generator: scene %d (motion) — generating Kai image-to-video",
        asset["scene_index"],
    )
    try:
        vid_result = generate_video(
            prompt=prompt,
            aspect_ratio="9:16",
            task_type="image_to_video",
            linked_content_id=f"studio_motion_{channel_id}_{asset['scene_index']}",
            image_url=source_image_url,
        )
        asset["motion_type"] = "video"
        asset["video_url"] = vid_result.get("drive_url", "")
        asset["video_drive_id"] = vid_result.get("drive_file_id", "")
        asset["video_local_path"] = vid_result.get("local_path", "")
        logger.info(
            "visual_generator: scene %d motion clip ready → %s",
            asset["scene_index"], asset["video_local_path"],
        )
    except Exception as exc:
        logger.warning(
            "visual_generator: scene %d video generation failed, falling back to Ken Burns: %s",
            asset["scene_index"], exc,
        )
        # motion_type stays "ken_burns" — render_publisher will use Ken Burns as fallback

    return asset


# ─────────────────────────────────────────────────────────────────────────────
# Stub
# ─────────────────────────────────────────────────────────────────────────────

def _stub_asset(index: int, error: str = "") -> dict[str, Any]:
    return {
        "scene_index": index,
        "motion_type": "video" if index in _VIDEO_MOTION_SCENES else "ken_burns",
        "image_url": f"https://drive.google.com/stub_image_{index}",
        "image_drive_id": f"stub_img_{index}",
        "image_local_path": f"workspace/media/stub_scene_{index}.jpg",
        "video_url": f"https://drive.google.com/stub_video_{index}" if index in _VIDEO_MOTION_SCENES else "",
        "video_drive_id": f"stub_vid_{index}" if index in _VIDEO_MOTION_SCENES else "",
        "video_local_path": f"workspace/media/stub_scene_{index}.mp4" if index in _VIDEO_MOTION_SCENES else "",
        "error": error,
    }
