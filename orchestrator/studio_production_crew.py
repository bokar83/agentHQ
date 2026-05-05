"""
studio_production_crew.py — Studio M3: End-to-end production orchestrator.

Entry points:
  run_production(notion_id)       — produce one qa-passed candidate
  studio_production_tick()        — scan Pipeline DB, run all qa-passed candidates
  CLI: python -m orchestrator.studio_production_crew --test
       python -m orchestrator.studio_production_crew --notion-id <id>

Pipeline:
  1. Fetch candidate from Notion Pipeline DB
  2. Load brand_config for channel
  3. Generate script (Sonnet)
  4. Run QA (10 checks)
  5. Generate voice (ElevenLabs)
  6. Build scenes (segment + prompt)
  7. Generate visuals (kie_media per scene)
  8. Compose (hyperframes project)
  9. Render + upload + update Notion
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

logger = logging.getLogger("agentsHQ.studio_production_crew")

_PIPELINE_DB_ID = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "")
_NOTION_TOKEN = (
    os.environ.get("NOTION_SECRET")
    or os.environ.get("NOTION_API_KEY")
    or ""
)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def run_production(notion_id: str, *, dry_run: bool = False) -> dict[str, Any]:
    """
    Full production run for one Pipeline DB candidate.
    Returns result dict with per-stage outcomes.
    """
    logger.info("production_crew: starting run for %s (dry_run=%s)", notion_id, dry_run)

    # Stage 1: Fetch candidate
    candidate = _fetch_candidate(notion_id)
    if not candidate:
        return {"error": f"candidate {notion_id} not found or missing required fields"}

    channel_id = candidate.get("channel_id", "")
    if not channel_id:
        return {"error": "candidate missing channel_id"}

    # Stage 2: Load brand config
    from studio_brand_config import load_brand_config
    brand = load_brand_config(channel_id)
    logger.info("production_crew: brand loaded for '%s'", channel_id)

    # Stage 3: Generate script
    from studio_script_generator import generate_script
    script = generate_script(candidate, brand, dry_run=dry_run)
    logger.info("production_crew: script generated (%d words)", script["word_count"])

    # Stage 4: QA
    from studio_qa_crew import run_qa
    niche = candidate.get("niche", "")
    # Derive length_target from brand duration — overrides stale Notion field
    _dur = brand.get("target_duration_sec", 55)
    if _dur <= 60:
        length_target = "short (<60s)"
    elif _dur <= 180:
        length_target = "medium (60-180s)"
    else:
        length_target = "long (3-15m)"
    qa_report = run_qa(
        script["full_text"],
        niche,
        length_target,
        notion_id=notion_id,
        channel=channel_id,
        title=script["title"],
    )

    if not qa_report.passed and not dry_run:
        failed_names = [c.name for c in qa_report.failed_checks]
        failed_details = [f"{c.name}: {c.detail}" for c in qa_report.failed_checks]
        # One auto-retry for fixable issues (retention loops, citations, formula)
        fixable = {"retention_loops", "source_citation", "four_part_formula"}
        if set(failed_names) <= fixable:
            logger.info("production_crew: QA retry — fixable failures: %s", failed_names)
            fix_hint = "IMPORTANT FIX REQUIRED: " + "; ".join(failed_details)
            retry_candidate = dict(candidate)
            retry_candidate["twist"] = (candidate.get("twist", "") + "\n\n" + fix_hint).strip()
            script = generate_script(retry_candidate, brand, dry_run=dry_run)
            qa_report = run_qa(script["full_text"], niche, length_target, notion_id=notion_id, channel=channel_id, title=script["title"])

    if not qa_report.passed:
        failed = [f"{c.name}: {c.detail}" for c in qa_report.failed_checks]
        logger.warning("production_crew: QA failed for %s: %s", notion_id, failed)
        _update_notion_status(notion_id, "qa-failed", "; ".join(failed))
        _notify_qa_fail(notion_id, channel_id, failed)
        return {"error": "QA failed", "failures": failed}

    logger.info("production_crew: QA passed [%s]", qa_report.summary())

    # Stage 5: Voice generation
    from studio_voice_generator import generate_voice
    voice = generate_voice(script, brand, dry_run=dry_run)
    logger.info(
        "production_crew: voice generated (%.1fs, provider=%s)",
        voice["duration_sec"], voice["provider"],
    )

    # Stage 6: Scene builder
    from studio_scene_builder import build_scenes
    scenes = build_scenes(script, voice, brand, dry_run=dry_run)
    logger.info("production_crew: %d scenes built", len(scenes))

    # Stage 7: Visual generation
    from studio_visual_generator import generate_visuals
    scene_assets = generate_visuals(scenes, brand, dry_run=dry_run)
    logger.info("production_crew: %d scene assets generated", len(scene_assets))

    # Stage 8: Compose
    from studio_composer import compose
    composition = compose(scenes, scene_assets, voice, script, brand, dry_run=dry_run)
    logger.info(
        "production_crew: composition built (%d scenes, project=%s)",
        len(composition.get("scenes", [])),
        composition["project_dir"],
    )

    # Stage 9: Render + publish
    from studio_render_publisher import render_and_publish
    result = render_and_publish(composition, brand, notion_id, dry_run=dry_run)
    logger.info(
        "production_crew: renders done. primary=%s notion_updated=%s",
        result["primary_asset_url"], result["notion_updated"],
    )

    return {
        "notion_id": notion_id,
        "channel_id": channel_id,
        "title": script["title"],
        "word_count": script["word_count"],
        "duration_sec": voice["duration_sec"],
        "scene_count": len(scenes),
        "renders": result["renders"],
        "primary_asset_url": result["primary_asset_url"],
        "notion_updated": result["notion_updated"],
    }


def studio_production_tick(*, dry_run: bool = False) -> list[dict]:
    """
    Heartbeat tick: find all Pipeline DB candidates with Status=qa-passed,
    run production on each one at a time.
    Called from scheduler.py (M3 heartbeat wiring, separate task).
    """
    candidates = _fetch_qa_passed_candidates()
    logger.info("production_tick: %d qa-passed candidates queued", len(candidates))
    results = []
    for candidate_id in candidates:
        try:
            result = run_production(candidate_id, dry_run=dry_run)
            results.append(result)
        except Exception as exc:
            logger.error("production_tick: failed for %s: %s", candidate_id, exc)
            results.append({"notion_id": candidate_id, "error": str(exc)})
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Notion helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_candidate(notion_id: str) -> dict | None:
    if not _NOTION_TOKEN:
        logger.error("production_crew: NOTION_SECRET not set")
        return None
    try:
        import httpx
        resp = httpx.get(
            f"https://api.notion.com/v1/pages/{notion_id}",
            headers={
                "Authorization": f"Bearer {_NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
            },
            timeout=10,
        )
        resp.raise_for_status()
        page = resp.json()
        return _page_to_candidate(page)
    except Exception as exc:
        logger.error("production_crew: cannot fetch candidate %s: %s", notion_id, exc)
        return None


def _page_to_candidate(page: dict) -> dict:
    props = page.get("properties", {})

    def _text(key: str) -> str:
        val = props.get(key, {})
        items = val.get("rich_text") or val.get("title") or []
        return "".join(t.get("plain_text", "") for t in items)

    def _select(key: str) -> str:
        sel = (props.get(key) or {}).get("select") or {}
        return sel.get("name", "")

    def _url(key: str) -> str:
        return (props.get(key) or {}).get("url") or ""

    return {
        "notion_id": page.get("id", ""),
        "title": _text("Title") or _text("Name"),
        "hook": _text("Hook") or _text("Title"),
        "twist": _text("Twist") or _text("Angle"),
        "niche": _select("Niche tag") or _select("Niche"),
        "channel_id": _select("Channel"),
        "length_target": _select("Length target") or "long (3-15m)",
        "source_url": _url("Source URL"),
        "status": _select("Status"),
    }


def _fetch_qa_passed_candidates() -> list[str]:
    if not _PIPELINE_DB_ID or not _NOTION_TOKEN:
        return []
    try:
        import httpx
        resp = httpx.post(
            f"https://api.notion.com/v1/databases/{_PIPELINE_DB_ID}/query",
            headers={
                "Authorization": f"Bearer {_NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
            },
            json={"filter": {"property": "Status", "select": {"equals": "qa-passed"}}},
            timeout=10,
        )
        resp.raise_for_status()
        return [p["id"] for p in resp.json().get("results", [])]
    except Exception as exc:
        logger.error("production_tick: cannot query Pipeline DB: %s", exc)
        return []


def _update_notion_status(notion_id: str, status: str, notes: str = "") -> None:
    if not _NOTION_TOKEN or not notion_id:
        return
    try:
        import httpx
        props: dict = {"Status": {"select": {"name": status}}}
        if notes:
            props["QA notes"] = {"rich_text": [{"text": {"content": notes[:1500]}}]}
        httpx.patch(
            f"https://api.notion.com/v1/pages/{notion_id}",
            headers={
                "Authorization": f"Bearer {_NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
            },
            json={"properties": props},
            timeout=10,
        )
    except Exception as exc:
        logger.warning("production_crew: Notion status update failed: %s", exc)


def _notify_qa_fail(notion_id: str, channel_id: str, failures: list[str]) -> None:
    try:
        import os
        from notifier import send_message
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
        send_message(
            chat_id,
            f"Studio QA failed\n"
            f"Channel: {channel_id}\n"
            f"Record: {notion_id}\n"
            f"Failures:\n" + "\n".join(f"  - {f}" for f in failures)
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# CLI / smoke test
# ─────────────────────────────────────────────────────────────────────────────

_SMOKE_TEST_CANDIDATE = {
    "notion_id": "smoke-test-placeholder",
    "title": "Why the First 3 Years of a Child's Life Change Everything",
    "hook": "Scientists discovered the first 3 years wire a child's brain for life — and most parents have no idea this window is closing.",
    "twist": "This isn't about education — it's about safety and connection. And it's simpler than anyone tells you.",
    "niche": "parenting-psychology",
    "channel_id": "under_the_baobab",
    "length_target": "long (3-15m)",
    "source_url": "",
    "status": "qa-passed",
}


def _run_smoke_test() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger.info("=== Studio M3 Smoke Test (dry_run=True) ===")

    from studio_brand_config import load_brand_config, is_brand_ready
    from studio_script_generator import generate_script
    from studio_qa_crew import run_qa
    from studio_voice_generator import generate_voice
    from studio_scene_builder import build_scenes
    from studio_visual_generator import generate_visuals
    from studio_composer import compose
    from studio_render_publisher import render_and_publish

    brand = load_brand_config("under_the_baobab")
    logger.info("brand_ready=%s", is_brand_ready("under_the_baobab"))

    script = generate_script(_SMOKE_TEST_CANDIDATE, brand, dry_run=True)
    logger.info("script: %d words, %d scenes_hint", script["word_count"], len(script["scenes_hint"]))

    qa = run_qa(
        script["full_text"],
        _SMOKE_TEST_CANDIDATE["niche"],
        notion_id="smoke-test",
        channel="under_the_baobab",
        title=script["title"],
    )
    logger.info("QA: passed=%s summary=%s", qa.passed, qa.summary())
    if not qa.passed:
        for c in qa.failed_checks:
            logger.warning("  FAIL %s: %s", c.name, c.detail)

    voice = generate_voice(script, brand, dry_run=True)
    logger.info("voice: %.1fs, %d timestamps, provider=%s", voice["duration_sec"], len(voice["timestamps"]), voice["provider"])

    scenes = build_scenes(script, voice, brand, dry_run=True)
    logger.info("scenes: %d total", len(scenes))
    for s in scenes:
        logger.info("  scene %d: %.1f-%.1fs | img_prompt=%.60s...", s.index, s.start_sec, s.end_sec, s.image_prompt)

    assets = generate_visuals(scenes, brand, dry_run=True)
    logger.info("assets: %d stubs", len(assets))

    composition = compose(scenes, assets, voice, script, brand, dry_run=True)
    logger.info("composition: project=%s scenes=%d", composition["project_dir"], len(composition.get("scenes", [])))

    result = render_and_publish(composition, brand, "smoke-test", dry_run=True)
    logger.info("renders: %s", {k: v.get("drive_url") for k, v in result["renders"].items()})
    logger.info("=== Smoke Test Complete ===")


if __name__ == "__main__":
    # Ensure orchestrator/ is on path when running as __main__ from repo root
    import pathlib as _pl
    _orc = str(_pl.Path(__file__).parent)
    if _orc not in sys.path:
        sys.path.insert(0, _orc)

    parser = argparse.ArgumentParser(description="Studio M3 Production Crew")
    parser.add_argument("--test", action="store_true", help="Run smoke test (dry_run)")
    parser.add_argument("--notion-id", help="Run production for a specific Notion record ID")
    parser.add_argument("--tick", action="store_true", help="Run production tick (all qa-passed)")
    parser.add_argument("--dry-run", action="store_true", help="Skip all API/render calls")
    args = parser.parse_args()

    if args.test:
        _run_smoke_test()
    elif args.notion_id:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
        result = run_production(args.notion_id, dry_run=args.dry_run)
        print(result)
    elif args.tick:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
        results = studio_production_tick(dry_run=args.dry_run)
        print(f"Processed {len(results)} candidates")
    else:
        parser.print_help()
        sys.exit(1)
