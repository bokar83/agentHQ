"""
studio_render_publisher.py - Studio M3: Render + Drive upload + Notion update.

Renders 3 formats using pure ffmpeg (no hyperframes, no Chrome):
  long_form  1920x1080 → Ken Burns images + narration + SRT captions
  shorts     1080x1920 → vertical crop/reframe of same scenes
  square     1080x1080 → square crop

After render:
  - Upload each MP4 to Drive
  - Update Notion Pipeline DB record: Asset_URL + Status=scheduled
  - Send Telegram + email notification
"""
from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("agentsHQ.studio_render_publisher")

_RENDERS_DIR = Path(os.environ.get("STUDIO_RENDERS_DIR", "/app/workspace/renders"))
_ASSETS_DIR = Path(os.environ.get("STUDIO_ASSETS_DIR", "/app/workspace/assets"))

_NOTION_TOKEN = (
    os.environ.get("NOTION_SECRET")
    or os.environ.get("NOTION_API_KEY")
    or ""
)
_PIPELINE_DB_ID = os.environ.get("NOTION_STUDIO_PIPELINE_DB_ID", "")

# Drive folder IDs — per-format subfolders created automatically under channel folder
_DRIVE_ASSET_LIBRARY_ROOT = (
    os.environ.get("DRIVE_ASSET_LIBRARY_ROOT")
    or os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    or "1T3uF6jDOo_RBTXIb4qE60_ZxUeqJj6gL"  # pragma: allowlist secret
)

# Shorts-first: render vertical 9:16 only until channels are monetized.
# Add long_form + square back when G4 ($1k/mo) is in sight.
_PLATFORM_SPECS = {
    "shorts": {"width": 1080, "height": 1920, "fps": 30},
}


def render_and_publish(
    composition: dict[str, Any],
    brand: dict[str, Any],
    notion_id: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Render all platform formats, upload to Drive, update Notion, notify Telegram.

    Returns:
      {
        "renders": {
          "long_form": {"local_path": str, "drive_url": str, "drive_file_id": str},
          "shorts": {...},
          "square": {...},
        },
        "notion_updated": bool,
        "primary_asset_url": str,   # long_form Drive URL
      }
    """
    project_dir = Path(composition["project_dir"])
    channel_id = brand.get("channel_id", "unknown")
    title = composition.get("title", composition.get("composition_html", "")[:60])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    renders: dict[str, Any] = {}

    for fmt, specs in _PLATFORM_SPECS.items():
        output_path = _render_format(project_dir, fmt, specs, channel_id, today, dry_run)
        if output_path and output_path.exists():
            drive_result = _upload_render(output_path, channel_id, fmt, today, dry_run)
            renders[fmt] = {
                "local_path": str(output_path),
                "drive_url": drive_result.get("webViewLink", ""),
                "drive_file_id": drive_result.get("id", ""),
            }
        else:
            renders[fmt] = {"local_path": "", "drive_url": "", "drive_file_id": ""}
            logger.warning("render_publisher: %s render missing for %s", fmt, channel_id)

    primary_url = renders.get("shorts", renders.get("long_form", {})).get("drive_url", "")
    notion_updated = _update_notion(notion_id, primary_url, dry_run)
    _notify_telegram(channel_id, notion_id, renders, dry_run, title=title)
    _notify_email(channel_id, notion_id, renders, dry_run)

    return {
        "renders": renders,
        "notion_updated": notion_updated,
        "primary_asset_url": primary_url,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────────────────────────────────────

def _render_format(
    project_dir: Path,
    fmt: str,
    specs: dict,
    channel_id: str,
    today: str,
    dry_run: bool,
) -> Path | None:
    out_dir = _RENDERS_DIR / channel_id / today / fmt
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%H%M%S")
    output_path = out_dir / f"{channel_id}_{fmt}_{today}_{ts}.mp4"

    if dry_run:
        output_path.write_bytes(b"")  # empty file, smoke test only
        logger.info("[dry_run] render_publisher: stub render %s", output_path)
        return output_path

    import json as _json
    manifest_path = project_dir / "manifest.json"
    if not manifest_path.exists():
        logger.error("render_publisher: no manifest.json in %s", project_dir)
        return None

    manifest = _json.loads(manifest_path.read_text())
    w, h, fps = specs["width"], specs["height"], specs["fps"]

    logger.info("render_publisher: ffmpeg rendering %s (%dx%d@%d)", fmt, w, h, fps)
    try:
        _ffmpeg_render(manifest, output_path, w, h, fps, fmt)
    except Exception as exc:
        logger.error("render_publisher: %s render failed: %s", fmt, exc)
        return None

    logger.info("render_publisher: %s complete → %s", fmt, output_path)
    return output_path


def _probe_duration(path: "Path") -> float:
    """Return duration in seconds of a video file via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _ffmpeg_render(
    manifest: dict,
    output_path: Path,
    width: int,
    height: int,
    fps: int,
    fmt: str,
) -> None:
    """Render MP4 from image scenes + audio using ffmpeg Ken Burns pipeline.

    Prepends channel intro and appends channel outro from static VPS assets.
    No captions burned in - SRT delivered as sidecar only.
    """
    import tempfile

    scenes = manifest["scenes"]
    audio_path = manifest.get("audio_path", "")
    brand = manifest.get("brand", {})
    channel_id = brand.get("channel_id", "")
    bg_color = brand.get("background_color", "#1E1433").lstrip("#")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    intro_asset = _ASSETS_DIR / "intros" / f"{channel_id}_intro.mp4"
    outro_asset = _ASSETS_DIR / "outros" / f"{channel_id}_outro.mp4"
    has_intro = intro_asset.exists()
    has_outro = outro_asset.exists()
    if not has_intro:
        logger.warning("render_publisher: intro asset missing for %s (%s)", channel_id, intro_asset)
    if not has_outro:
        logger.warning("render_publisher: outro asset missing for %s (%s)", channel_id, outro_asset)

    intro_dur = _probe_duration(intro_asset) if has_intro else 0.0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        clip_paths = []
        for scene in scenes:
            img = scene.get("image_path", "")
            dur = float(scene.get("duration_sec", 8.0))
            motion = scene.get("motion", "zoom_in")
            clip_out = tmp / f"clip_{scene['index']:03d}.mp4"

            if img and Path(img).exists():
                _render_ken_burns_clip(img, clip_out, dur, fps, width, height, motion)
            else:
                _render_color_clip(clip_out, dur, fps, width, height, bg_color)

            clip_paths.append(clip_out)

        all_clips = []
        if has_intro:
            all_clips.append(intro_asset)
        all_clips.extend(clip_paths)
        if has_outro:
            all_clips.append(outro_asset)

        concat_path = tmp / "concat.mp4"
        _concat_clips(all_clips, concat_path, scenes, fps)

        if audio_path and Path(audio_path).exists():
            mixed_path = tmp / "mixed.mp4"
            _mix_audio(concat_path, audio_path, mixed_path, intro_dur)
        else:
            mixed_path = concat_path

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mixed_path), "-c", "copy", str(output_path)],
            check=True, capture_output=True, timeout=300,
        )


def _ffmpeg(cmd: list, timeout: int = 300) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y"] + cmd,
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-1500:]}")


def _ken_burns_filter(motion: str, w: int, h: int, fps: int, dur: float) -> str:
    """Return ffmpeg zoompan filter string for Ken Burns effect."""
    frames = int(dur * fps)
    # Render at target resolution directly — 2x oversample (3840x2160) times out on VPS CPU
    d = frames

    effects = {
        "zoom_in":    f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps={fps}",
        "zoom_out":   f"zoompan=z='if(lte(zoom,1.0),1.5,max(1.0,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps={fps}",
        "pan_right":  f"zoompan=z='1.3':x='if(lte(on,1),0,min(x+2,iw/3))':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps={fps}",
        "pan_left":   f"zoompan=z='1.3':x='if(lte(on,1),iw/3,max(0,x-2))':y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps={fps}",
        "pan_up":     f"zoompan=z='1.3':x='iw/2-(iw/zoom/2)':y='if(lte(on,1),ih/3,max(0,y-2))':d={d}:s={w}x{h}:fps={fps}",
        "zoom_in_tl": f"zoompan=z='min(zoom+0.0015,1.5)':x='0':y='0':d={d}:s={w}x{h}:fps={fps}",
        "zoom_out_br":f"zoompan=z='if(lte(zoom,1.0),1.5,max(1.0,zoom-0.0015))':x='iw-iw/zoom':y='ih-ih/zoom':d={d}:s={w}x{h}:fps={fps}",
        "zoom_in_tr": f"zoompan=z='min(zoom+0.0015,1.5)':x='iw-iw/zoom':y='0':d={d}:s={w}x{h}:fps={fps}",
    }
    zp = effects.get(motion, effects["zoom_in"])
    return zp


def _render_ken_burns_clip(img: str, out: Path, dur: float, fps: int, w: int, h: int, motion: str) -> None:
    kb = _ken_burns_filter(motion, w, h, fps, dur)
    # For portrait/square formats, center-crop source to target aspect ratio
    # before Ken Burns so landscape images fill frame without letterboxing.
    if h > w:
        # portrait (shorts 1080x1920): crop width to ih*(w/h)
        crop = f"crop=ih*{w}/{h}:ih,"
    elif w == h:
        # square (1080x1080): crop to shortest side
        crop = "crop=min(iw\\,ih):min(iw\\,ih),"
    else:
        crop = ""
    _ffmpeg([
        "-loop", "1", "-i", img,
        "-vf", f"{crop}{kb}",
        "-t", str(dur),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ], timeout=600)


def _render_color_clip(out: Path, dur: float, fps: int, w: int, h: int, color: str) -> None:
    _ffmpeg([
        "-f", "lavfi", "-i", f"color=#{color}:size={w}x{h}:rate={fps}",
        "-t", str(dur), "-c:v", "libx264", "-preset", "fast", "-an",
        str(out),
    ])


def _render_title_card(out: Path, dur: float, fps: int, w: int, h: int,
                       title: str, bg: str, fg: str, font: str) -> None:
    # Wrap title at ~40 chars
    words = title.split()
    lines, line = [], []
    for word in words:
        line.append(word)
        if len(" ".join(line)) > 38:
            lines.append(" ".join(line[:-1]))
            line = [word]
    if line:
        lines.append(" ".join(line))
    text = r"\n".join(lines)

    drawtext = (
        f"drawtext=fontfile='{font}':text='{text}':"
        f"fontcolor=#{fg}:fontsize={w // 18}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"line_spacing=20"
    )
    _ffmpeg([
        "-f", "lavfi", "-i", f"color=#{bg}:size={w}x{h}:rate={fps}",
        "-vf", f"fade=t=in:st=0:d=0.5,fade=t=out:st={dur-0.5}:d=0.5,{drawtext}",
        "-t", str(dur), "-c:v", "libx264", "-preset", "fast", "-an",
        str(out),
    ])


def _render_outro_card(out: Path, dur: float, fps: int, w: int, h: int,
                       channel_name: str, bg: str, fg: str, font: str) -> None:
    subscribe = r"Like \& Subscribe"
    drawtext = (
        f"drawtext=fontfile='{font}':text='{channel_name}':"
        f"fontcolor=#{fg}:fontsize={w // 16}:x=(w-text_w)/2:y=(h/2-80),"
        f"drawtext=fontfile='{font}':text='{subscribe}':"
        f"fontcolor=white:fontsize={w // 28}:x=(w-text_w)/2:y=(h/2+40)"
    )
    _ffmpeg([
        "-f", "lavfi", "-i", f"color=#{bg}:size={w}x{h}:rate={fps}",
        "-vf", f"fade=t=in:st=0:d=0.5,{drawtext}",
        "-t", str(dur), "-c:v", "libx264", "-preset", "fast", "-an",
        str(out),
    ])


def _concat_clips(clips: list[Path], out: Path, scenes: list[dict], fps: int) -> None:
    # Simple concat without xfade for reliability; transitions can be added later
    list_file = out.parent / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in clips))
    _ffmpeg([
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ], timeout=300)


def _mix_audio(video: Path, audio: Path, out: Path, audio_delay: float) -> None:
    # Delay audio by intro_duration so narration starts after title card.
    # apad silences audio during the outro card. No -shortest so the full
    # video length (intro + scenes + outro) is preserved.
    _ffmpeg([
        "-i", str(video),
        "-i", str(audio),
        "-map", "0:v",
        "-map", "1:a",
        "-filter:a", f"adelay={int(audio_delay * 1000)}|{int(audio_delay * 1000)},apad",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        str(out),
    ], timeout=300)


def _burn_captions(video: Path, srt: Path, out: Path, w: int, h: int, font: str, fg: str) -> None:
    fontsize = w // 28
    subtitle_filter = (
        f"subtitles={srt}:force_style='"
        f"FontName=DejaVu Sans Bold,FontSize={fontsize},"
        f"PrimaryColour=&H00{fg[:6]}&,"
        f"OutlineColour=&H00000000&,Outline=2,Shadow=1,"
        f"MarginV=60,Alignment=2'"
    )
    _ffmpeg([
        "-i", str(video),
        "-vf", subtitle_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        str(out),
    ], timeout=600)


# ─────────────────────────────────────────────────────────────────────────────
# Drive upload
# ─────────────────────────────────────────────────────────────────────────────

def _upload_render(
    local_path: Path,
    channel_id: str,
    fmt: str,
    today: str,
    dry_run: bool,
) -> dict:
    if dry_run:
        return {"webViewLink": f"https://drive.google.com/stub_{fmt}", "id": f"stub_{fmt}"}
    try:
        from kie_media import _upload_to_drive, _find_or_create_folder
        channel_folder = _find_or_create_folder(channel_id, _DRIVE_ASSET_LIBRARY_ROOT)
        date_folder = _find_or_create_folder(today, channel_folder)
        fmt_folder = _find_or_create_folder(fmt, date_folder)
        return _upload_to_drive(local_path, fmt_folder, local_path.name, "video/mp4")
    except Exception as exc:
        logger.error("render_publisher: Drive upload failed for %s/%s: %s", fmt, local_path.name, exc)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Notion update
# ─────────────────────────────────────────────────────────────────────────────

def _update_notion(notion_id: str, asset_url: str, dry_run: bool) -> bool:
    if dry_run:
        logger.info("[dry_run] render_publisher: Notion update skipped for %s", notion_id)
        return True
    if not _NOTION_TOKEN or not notion_id:
        logger.warning("render_publisher: Notion update skipped (missing token or id)")
        return False
    try:
        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{notion_id}",
            headers={
                "Authorization": f"Bearer {_NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json={
                "properties": {
                    "Status": {"select": {"name": "scheduled"}},
                    "Asset URL": {"url": asset_url or None},
                    "Scheduled Date": {"date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%d")}},
                    "Platform": {"multi_select": [
                        {"name": "x"},
                        {"name": "Instagram"},
                        {"name": "tiktok"},
                        {"name": "YouTube"},
                    ]},
                }
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("render_publisher: Notion %s → scheduled", notion_id)
        return True
    except Exception as exc:
        logger.error("render_publisher: Notion update failed for %s: %s", notion_id, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Telegram notification
# ─────────────────────────────────────────────────────────────────────────────

def _notify_telegram(
    channel_id: str,
    notion_id: str,
    renders: dict,
    dry_run: bool,
    title: str = "",
) -> None:
    if dry_run:
        logger.info("[dry_run] render_publisher: Telegram notification skipped")
        return
    try:
        from notifier import send_message
        lf = renders.get("long_form", {})
        sh = renders.get("shorts", {})
        sq = renders.get("square", {})
        lf_url = lf.get("drive_url") or "MISSING"
        sh_url = sh.get("drive_url") or "MISSING"
        sq_url = sq.get("drive_url") or "MISSING"
        lines = [
            f"Video ready: {title or channel_id}",
            f"Channel: {channel_id}",
            f"Long form: {lf_url}",
            f"Shorts: {sh_url}",
            f"Square: {sq_url}",
            f"Notion: {notion_id}",
        ]
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
        send_message(chat_id, "\n".join(lines))
    except Exception as exc:
        logger.warning("render_publisher: Telegram notification failed: %s", exc)


_NOTIFY_EMAILS = "boubacar@catalystworks.consulting,bokar83@gmail.com,thatguy@boubacarbarry.com"


def _notify_email(
    channel_id: str,
    notion_id: str,
    renders: dict,
    dry_run: bool,
    title: str = "",
) -> None:
    if dry_run:
        logger.info("[dry_run] render_publisher: email notification skipped")
        return
    try:
        import subprocess
        lf = renders.get("long_form", {})
        sh = renders.get("shorts", {})
        sq = renders.get("square", {})
        lf_url = lf.get("drive_url") or "not available"
        sh_url = sh.get("drive_url") or "not available"
        sq_url = sq.get("drive_url") or "not available"

        subject = f"Studio render complete: {title or channel_id}"
        body = (
            f"<h2>Video Ready: {title or channel_id}</h2>"
            f"<p><b>Channel:</b> {channel_id}</p>"
            f"<h3>Assets</h3>"
            f"<ul>"
            f"<li><b>Long form (16:9):</b> <a href=\"{lf_url}\">{lf_url}</a></li>"
            f"<li><b>Shorts (9:16):</b> <a href=\"{sh_url}\">{sh_url}</a></li>"
            f"<li><b>Square (1:1):</b> <a href=\"{sq_url}\">{sq_url}</a></li>"
            f"</ul>"
            f"<p>Notion: {notion_id}</p>"
        )
        # Send from channel alias so recipient knows which channel produced it
        _channel_sender = {
            "under_the_baobab": "UnderTheBaobab@catalystworks.consulting",
            "ai_catalyst": "aiCatalyst@catalystworks.consulting",
            "first_generation_money": "1stGenMoney@catalystworks.consulting",
        }
        sender = _channel_sender.get(channel_id.lower().replace(" ", "_"), "boubacar@catalystworks.consulting")

        result = subprocess.run(
            ["gws", "gmail", "+send",
             "--to", _NOTIFY_EMAILS,
             "--from", sender,
             "--subject", subject,
             "--body", body,
             "--html"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            logger.info("render_publisher: email sent to %s", _NOTIFY_EMAILS)
        else:
            logger.warning("render_publisher: email send failed: %s", result.stderr[:200])
    except Exception as exc:
        logger.warning("render_publisher: email notification failed: %s", exc)
