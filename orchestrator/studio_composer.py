"""
studio_composer.py — Studio M3: Assemble voiceover + visuals + captions via hyperframes.

Flow:
  1. npx hyperframes init <project_dir> --non-interactive --audio <audio_path>
  2. Write index.html composition (scenes, captions, branded intro/outro)
  3. npx hyperframes lint
  4. Return project_dir path (render happens in studio_render_publisher)

Brand values (colors, fonts, intro/outro) loaded from brand_config.
Placeholder values used until M2 ships final brand identity.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agentsHQ.studio_composer")

_HF_CMD = os.environ.get("HYPERFRAMES_CMD", "npx hyperframes")
_COMPOSITIONS_DIR = Path(os.environ.get("STUDIO_COMPOSITIONS_DIR", "workspace/compositions"))


def compose(
    scenes: list[Any],               # list[Scene] from studio_scene_builder
    scene_assets: list[dict],        # from studio_visual_generator
    voice: dict[str, Any],           # from studio_voice_generator
    script: dict[str, Any],
    brand: dict[str, Any],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Build a hyperframes project for the video.

    Returns:
      {
        "project_dir": str,
        "composition_html": str,
        "lint_passed": bool,
        "lint_output": str,
      }
    """
    channel_id = brand.get("channel_id", "unknown")
    title = script.get("title", "untitled")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    project_name = f"{channel_id}_{_slugify(title)}_{ts}"
    project_dir = _COMPOSITIONS_DIR / project_name

    html = _build_composition_html(scenes, scene_assets, voice, script, brand)

    if dry_run:
        logger.info("[dry_run] composer: skipping hyperframes CLI calls")
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "index.html").write_text(html, encoding="utf-8")
        return {
            "project_dir": str(project_dir),
            "composition_html": html,
            "lint_passed": True,
            "lint_output": "[dry_run] lint skipped",
        }

    audio_path = voice.get("audio_path", "")
    project_dir.mkdir(parents=True, exist_ok=True)

    _hf_init(project_dir, audio_path)
    (project_dir / "index.html").write_text(html, encoding="utf-8")
    lint_passed, lint_output = _hf_lint(project_dir)

    if not lint_passed:
        logger.warning("hyperframes lint errors in %s:\n%s", project_dir, lint_output)

    return {
        "project_dir": str(project_dir),
        "composition_html": html,
        "lint_passed": lint_passed,
        "lint_output": lint_output,
    }


# ─────────────────────────────────────────────────────────────────────────────
# hyperframes CLI calls
# ─────────────────────────────────────────────────────────────────────────────

def _hf_init(project_dir: Path, audio_path: str) -> None:
    cmd = _HF_CMD.split() + ["init", str(project_dir), "--non-interactive"]
    abs_audio = str(Path(audio_path).resolve()) if audio_path else ""
    if abs_audio and Path(abs_audio).exists():
        cmd += ["--audio", abs_audio]
    _run(cmd, cwd=str(project_dir.parent))


def _hf_lint(project_dir: Path) -> tuple[bool, str]:
    cmd = _HF_CMD.split() + ["lint", "--json"]
    result = _run(cmd, cwd=str(project_dir), capture=True)
    return result.returncode == 0, result.stdout + result.stderr


def _run(
    cmd: list[str],
    cwd: str = ".",
    capture: bool = False,
) -> subprocess.CompletedProcess:
    logger.debug("composer: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        timeout=120,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HTML composition builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_composition_html(
    scenes: list[Any],
    scene_assets: list[dict],
    voice: dict[str, Any],
    script: dict[str, Any],
    brand: dict[str, Any],
) -> str:
    title = script.get("title", "Untitled")
    primary = brand.get("primary_color", "#C8A96E")
    bg = brand.get("background_color", "#1A0F00")
    font = brand.get("font_family", "Playfair Display")
    font_body = brand.get("font_family_body", "Inter")
    channel_name = brand.get("display_name", "Studio")
    intro_dur = brand.get("intro_duration_sec", 3)
    outro_dur = brand.get("outro_duration_sec", 4)
    total_dur = voice.get("duration_sec", 60.0)
    timestamps = voice.get("timestamps", [])

    scenes_html = "\n".join(
        _scene_block(i, scene, scene_assets[i] if i < len(scene_assets) else {})
        for i, scene in enumerate(scenes)
    )

    # Build timestamps JSON for caption script (controlled internal data, not user input)
    timestamps_json = json.dumps([
        {"w": t["word"], "s": t["start"], "e": t["end"]}
        for t in timestamps
    ])

    intro_end = intro_dur
    outro_start = int(total_dur + intro_dur)
    outro_end = int(total_dur + intro_dur + outro_dur)
    total_comp_dur = outro_end

    comp_id = _slugify(title)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1920, height=1080">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{bg};font-family:'{font_body}',sans-serif}}
    #root{{position:relative;width:1920px;height:1080px;overflow:hidden}}
    .scene{{position:absolute;top:0;left:0;width:1920px;height:1080px;opacity:0;overflow:hidden}}
    .scene video,.scene img{{width:100%;height:100%;object-fit:cover}}
    #captions{{position:absolute;bottom:80px;left:50%;transform:translateX(-50%);z-index:100;text-align:center;max-width:1400px;pointer-events:none}}
    .cap-word{{display:inline-block;font-family:'{font_body}',sans-serif;font-size:52px;font-weight:700;color:white;text-shadow:2px 2px 8px rgba(0,0,0,.9);margin:0 4px;opacity:.6}}
    .cap-word.active{{color:{primary};opacity:1}}
    #intro{{position:absolute;top:0;left:0;width:1920px;height:1080px;background:{bg};display:flex;align-items:center;justify-content:center;z-index:200}}
    #intro h1{{font-family:'{font}',serif;font-size:96px;color:{primary};text-align:center;max-width:1400px;line-height:1.2}}
    #outro{{position:absolute;top:0;left:0;width:1920px;height:1080px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:200;opacity:0}}
    #outro h2{{font-family:'{font}',serif;font-size:72px;color:{primary}}}
    #outro p{{font-size:36px;color:white;margin-top:24px}}
  </style>
</head>
<body>
  <div
    id="root"
    data-composition-id="{comp_id}"
    data-start="0"
    data-duration="{total_comp_dur}"
    data-width="1920"
    data-height="1080"
  >
    <div id="intro" class="clip" data-start="0" data-duration="{intro_end}">
      <h1>{_escape_html(title)}</h1>
    </div>

    {scenes_html}

    <div id="captions"></div>

    <div id="outro" class="clip" data-start="{outro_start}" data-duration="{outro_end - outro_start}">
      <h2>{_escape_html(channel_name)}</h2>
      <p>Share this if it helped someone you love.</p>
    </div>
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});

    var INTRO = {intro_dur};
    var WORDS = {timestamps_json};

    // Intro fade
    tl.fromTo("#intro h1",{{opacity:0,y:40}},{{opacity:1,y:0,duration:1,ease:"power2.out"}}, 0.3);
    tl.to("#intro",{{opacity:0,duration:.5}}, {intro_dur - 0.5});
    tl.set("#intro",{{display:"none"}}, {intro_dur});

    // Scene fades
    document.querySelectorAll(".scene").forEach(function(el){{
      var s = parseFloat(el.dataset.start);
      var dur = parseFloat(el.dataset.duration || 0);
      tl.to(el, {{opacity:1, duration:.5}}, s);
      tl.to(el, {{opacity:0, duration:.5}}, s + dur - 0.5);
      tl.set(el, {{opacity:0, visibility:"hidden"}}, s + dur);
    }});

    // Outro
    tl.to("#outro", {{opacity:1, duration:.8}}, {outro_start});

    // Word-level captions
    var container = document.getElementById("captions");
    WORDS.forEach(function(w, i){{
      var span = document.createElement("span");
      span.className = "cap-word";
      span.id = "cw"+i;
      span.textContent = w.w + " ";
      container.appendChild(span);
      tl.set("#cw"+i, {{className:"cap-word active"}}, w.s + INTRO);
      tl.set("#cw"+i, {{className:"cap-word"}}, w.e + INTRO);
    }});

    window.__timelines["{comp_id}"] = tl;
  </script>
</body>
</html>"""


def _scene_block(index: int, scene: Any, assets: dict) -> str:
    video_path = assets.get("video_local_path", "")
    image_path = assets.get("image_local_path", "")
    start = getattr(scene, "start_sec", 0.0)
    end = getattr(scene, "end_sec", 10.0)

    duration = round(end - start, 2)

    # Use absolute paths — hyperframes file server resolves from project dir,
    # but our media lives in /app/workspace which may not be relative to project dir
    def _abs(p: str) -> str:
        return str(Path(p).resolve()) if p else ""

    abs_video = _abs(video_path)
    abs_image = _abs(image_path)

    if abs_video and Path(abs_video).exists():
        media = f'<video id="scene-{index}-media" src="{abs_video}" muted playsinline></video>'
    elif abs_image and Path(abs_image).exists():
        media = f'<img id="scene-{index}-media" src="{abs_image}" alt="">'
    else:
        media = f'<div id="scene-{index}-media" style="background:#1a1a1a;width:100%;height:100%"></div>'

    return (
        f'  <div class="scene clip" id="scene-{index}" '
        f'data-timeline="scene-{index}" '
        f'data-start="{start:.2f}" data-duration="{duration}">\n'
        f'    {media}\n'
        f'  </div>'
    )


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _escape_attr(text: str) -> str:
    return text.replace('"', "&quot;").replace("'", "&#39;")


def _slugify(text: str, max_len: int = 40) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text.strip())
    slug = "-".join(s for s in slug.split("-") if s)
    return slug[:max_len] or "untitled"
