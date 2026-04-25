"""
video_analyze.py - Reference video analysis via Gemini Files API.

Uploads a local video to Google's Gemini Files API, polls until processing is
ACTIVE, asks Gemini to extract structured fields (hook / person / setting /
camera / product interaction / pacing / tone / dialogue / audio / authenticity /
prompt notes), and returns both the parsed dict and a human-readable summary.

Two analysis modes:
  - "ugc"        : original R57 UGC-ad framing (good for product/lifestyle ads)
  - "tear_down"  : competitor / inspiration tear-down (good for client work,
                   content pipeline, Catalyst Works analysis)

Pattern adapted from R57 (RoboNuggets) lesson, but:
  - uses agentsHQ logging (logger), not print_status
  - no R57 config/utils dependencies
  - default model upgraded to gemini-2.5-flash with 2.0 fallback handled by caller
  - exposes analyze() as the canonical entry point

Env vars (read at call time, not import time):
  - GOOGLE_API_KEY  (required for any call)

Cleanup is automatic: the uploaded file is deleted from Gemini Files even on
failure. We never leave videos hanging in your Google quota.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import os
import time
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ---- API endpoints ----------------------------------------------------------

_UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
_FILES_URL = "https://generativelanguage.googleapis.com/v1beta/files/{name}"
_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

DEFAULT_MODEL = "gemini-2.0-flash"

_SUPPORTED_MIME: dict[str, str] = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/avi",
    ".webm": "video/webm",
    ".wmv": "video/wmv",
    ".mpg": "video/mpeg",
    ".mpeg": "video/mpeg",
    ".flv": "video/x-flv",
    ".3gp": "video/3gpp",
}

# ---- Analysis prompts -------------------------------------------------------

_PROMPT_UGC = """Analyze this UGC (User Generated Content) ad video in detail.
Extract everything that would help recreate or build on this style for new UGC ads.

Return your analysis in EXACTLY this format (keep the labels, fill in the values):

HOOK: [What happens in the first 2-3 seconds that grabs attention]
PERSON: [Gender, approximate age range, appearance, clothing style]
SETTING: [Background, location, indoor/outdoor, time of day, lighting quality and color]
CAMERA: [Angle - selfie/eye-level/below/above; distance - close-up/mid/wide; movement - static/slight drift/handheld shake]
PRODUCT INTERACTION: [How the product is held, shown, or referenced; specific angles; label visibility]
PACING: [Overall speed - fast/medium/slow; cut frequency; use of pauses or holds]
TONE & ENERGY: [Emotional register - e.g. genuinely excited, calm and informative, playful, surprised, etc.]
DIALOGUE: [Key phrases or direct quotes; speaking style - natural/casual vs scripted; pace of speech]
AUDIO: [Music - yes/no/type; ambient sound; voice characteristics - tone, accent, energy]
AUTHENTICITY SCORE: [1-10 score and one sentence reason]
PROMPT NOTES:
- [Key element 1 to emphasize when writing image/video prompts]
- [Key element 2]
- [Key element 3]
"""

_PROMPT_TEARDOWN = """Tear this video down for competitive analysis.
The goal is to extract why it works (or does not), so we can build on its strengths.

Return your analysis in EXACTLY this format (keep the labels, fill in the values):

HOOK: [What grabs attention in the first 2-3 seconds; specific technique used]
PERSON: [Who is on camera; demographic and apparent role - founder, employee, influencer, voice-over]
SETTING: [Where it was shot; production value; staging vs candid; what the location says about the brand]
CAMERA: [Shot composition; angle changes; movement style; production complexity]
PRODUCT INTERACTION: [How the product or service is demonstrated; what is shown vs told]
PACING: [Speed and rhythm; how attention is held across the runtime]
TONE & ENERGY: [Emotional register and what audience it is designed for]
DIALOGUE: [Spoken script or captions; rhetorical structure - hook/problem/solution/CTA]
AUDIO: [Music choice and effect; sound design; voice quality]
AUTHENTICITY SCORE: [1-10 score and one sentence on whether this reads as authentic vs produced]
PROMPT NOTES:
- [What we should steal for our own video]
- [What we should avoid or do differently]
- [What underlying technique made this work, that we can apply]
"""

PROMPTS = {"ugc": _PROMPT_UGC, "tear_down": _PROMPT_TEARDOWN}


# ---- Internals --------------------------------------------------------------

def _api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    return key


def _headers() -> dict[str, str]:
    return {"x-goog-api-key": _api_key()}


def _get_mime(path: Path) -> str:
    ext = path.suffix.lower()
    mime = _SUPPORTED_MIME.get(ext)
    if not mime:
        guess, _ = mimetypes.guess_type(str(path))
        mime = guess
    if not mime or not mime.startswith("video/"):
        raise ValueError(
            f"Unsupported video format '{ext}'. "
            f"Supported: {', '.join(sorted(_SUPPORTED_MIME))}"
        )
    return mime


def _upload(path: Path) -> dict[str, str]:
    size = path.stat().st_size
    mime = _get_mime(path)
    init = requests.post(
        _UPLOAD_URL,
        headers={
            **_headers(),
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime,
            "Content-Type": "application/json",
        },
        json={"file": {"display_name": path.name}},
        timeout=30,
    )
    if init.status_code != 200:
        raise RuntimeError(f"Upload init failed ({init.status_code}): {init.text[:300]}")
    upload_url = init.headers.get("x-goog-upload-url")
    if not upload_url:
        raise RuntimeError("Gemini did not return an upload URL")

    with path.open("rb") as f:
        body = f.read()
    up = requests.post(
        upload_url,
        headers={
            "Content-Length": str(size),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        },
        data=body,
        timeout=300,
    )
    if up.status_code not in (200, 201):
        raise RuntimeError(f"Upload failed ({up.status_code}): {up.text[:300]}")
    meta = up.json().get("file", up.json())
    return {"name": meta["name"], "uri": meta["uri"], "mimeType": mime}


def _wait_active(name: str, max_wait: int = 120, poll: int = 5) -> None:
    name_id = name.removeprefix("files/")
    started = time.time()
    while time.time() - started < max_wait:
        r = requests.get(_FILES_URL.format(name=name_id), headers=_headers(), timeout=30)
        if r.status_code == 200:
            state = r.json().get("state", "UNKNOWN")
            if state == "ACTIVE":
                return
            if state == "FAILED":
                raise RuntimeError(f"Gemini processing FAILED: {r.json()}")
        time.sleep(poll)
    raise TimeoutError(f"Gemini file did not become ACTIVE within {max_wait}s")


def _delete(name: str) -> None:
    name_id = name.removeprefix("files/")
    try:
        requests.delete(_FILES_URL.format(name=name_id), headers=_headers(), timeout=30)
    except Exception as e:
        logger.warning(f"video_analyze cleanup failed for {name}: {e}")


def _generate(file_uri: str, mime: str, prompt: str, model: str) -> str:
    payload = {
        "contents": [
            {
                "parts": [
                    {"fileData": {"mimeType": mime, "fileUri": file_uri}},
                    {"text": prompt},
                ]
            }
        ]
    }
    r = requests.post(
        _GENERATE_URL.format(model=model),
        headers={**_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=180,
    )
    if r.status_code != 200:
        raise RuntimeError(f"generateContent {r.status_code}: {r.text[:400]}")
    cands = r.json().get("candidates") or []
    if not cands:
        raise RuntimeError(f"No candidates: {r.json()}")
    parts = cands[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Empty Gemini response")
    return text


_FIELD_MAP = {
    "HOOK:": "hook",
    "PERSON:": "person",
    "SETTING:": "setting",
    "CAMERA:": "camera",
    "PRODUCT INTERACTION:": "product_interaction",
    "PACING:": "pacing",
    "TONE & ENERGY:": "tone",
    "DIALOGUE:": "dialogue",
    "AUDIO:": "audio",
    "AUTHENTICITY SCORE:": "authenticity_score",
}


def _parse(raw: str) -> dict[str, Any]:
    out: dict[str, Any] = {k: "" for k in _FIELD_MAP.values()}
    out["prompt_notes"] = []
    out["raw"] = raw

    current = None
    notes_mode = False
    for line in raw.splitlines():
        s = line.strip()
        if s.upper().startswith("PROMPT NOTES"):
            notes_mode = True
            current = None
            continue
        if notes_mode:
            if s.startswith("-"):
                out["prompt_notes"].append(s.lstrip("- ").strip())
            elif s:
                out["prompt_notes"].append(s)
            continue
        matched = False
        for label, key in _FIELD_MAP.items():
            if s.upper().startswith(label):
                current = key
                v = s[len(label):].strip().strip("[]")
                if v:
                    out[key] = v
                matched = True
                break
        if not matched and current and s:
            out[current] = (out[current] + " " + s).strip()
    return out


def _summary(parsed: dict[str, Any], name: str = "") -> str:
    title = f"## Reference Video Analysis: {name}" if name else "## Reference Video Analysis"
    lines = [title, ""]
    label_order = [
        ("hook", "Hook"),
        ("person", "Person"),
        ("setting", "Setting"),
        ("camera", "Camera"),
        ("product_interaction", "Product Interaction"),
        ("pacing", "Pacing"),
        ("tone", "Tone & Energy"),
        ("dialogue", "Dialogue"),
        ("audio", "Audio"),
        ("authenticity_score", "Authenticity"),
    ]
    for k, lbl in label_order:
        v = parsed.get(k)
        if v:
            lines.append(f"**{lbl}:** {v}")
    if parsed.get("prompt_notes"):
        lines.append("\n**Prompt Notes:**")
        for n in parsed["prompt_notes"]:
            lines.append(f"  - {n}")
    return "\n".join(lines)


# ---- Public API -------------------------------------------------------------

def analyze(
    file_path: str | os.PathLike,
    mode: str = "ugc",
    custom_prompt: str | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """
    Analyze one local video file.

    Args:
        file_path: Path to .mp4/.mov/.webm/etc.
        mode: "ugc" or "tear_down". Ignored if custom_prompt is provided.
        custom_prompt: Override the default prompt entirely.
        model: Gemini model ID (default gemini-2.0-flash).

    Returns:
        dict with parsed fields + 'raw', 'summary', 'mode', 'model'.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)

    prompt = custom_prompt or PROMPTS.get(mode)
    if not prompt:
        raise ValueError(f"Unknown mode '{mode}'. Use 'ugc', 'tear_down', or pass custom_prompt.")

    started = time.time()
    file_meta = _upload(path)
    file_name = file_meta["name"]
    try:
        _wait_active(file_name)
        raw = _generate(file_meta["uri"], file_meta["mimeType"], prompt, model)
    finally:
        _delete(file_name)

    parsed = _parse(raw)
    parsed["summary"] = _summary(parsed, name=path.name)
    parsed["mode"] = mode if not custom_prompt else "custom"
    parsed["model"] = model
    parsed["elapsed_seconds"] = round(time.time() - started, 1)
    return parsed


def analyze_many(
    file_paths: list[str | os.PathLike],
    mode: str = "ugc",
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Sequential batch wrapper."""
    analyses = []
    for p in file_paths:
        analyses.append(analyze(p, mode=mode, model=model))
    combined = "\n\n".join(a.get("summary", "") for a in analyses)
    return {"analyses": analyses, "combined_summary": combined}


# ---- CrewAI tool wrapper ----------------------------------------------------

def _build_tool():
    from crewai.tools import BaseTool

    class VideoAnalyzeTool(BaseTool):
        """
        Analyze a local reference video with Gemini and return structured fields.

        Input JSON:
          - file_path (str, required): local video path
          - mode (str, default "ugc"): "ugc" or "tear_down"
          - model (str, optional): Gemini model id

        Output (str): JSON with parsed fields + summary + raw.
        """

        name: str = "video_analyze"
        description: str = (
            "Analyze a local video file (.mp4, .mov, .webm, .avi) with Gemini. "
            "Extracts hook, person, setting, camera, pacing, tone, dialogue, "
            "audio, authenticity, prompt notes. Use mode 'ugc' for ad analysis, "
            "'tear_down' for competitor / inspiration analysis. "
            "Input JSON: {\"file_path\": \"...\", \"mode\": \"ugc\"}."
        )

        def _run(self, input_data: str | dict) -> str:
            try:
                data = json.loads(input_data) if isinstance(input_data, str) else input_data
                file_path = data.get("file_path")
                if not file_path:
                    return json.dumps({"error": "file_path is required"})
                mode = data.get("mode", "ugc")
                model = data.get("model", DEFAULT_MODEL)
                result = analyze(file_path, mode=mode, model=model)
                return json.dumps(
                    {k: v for k, v in result.items() if k != "raw"},
                    ensure_ascii=False,
                )[:8000]
            except Exception as e:
                logger.exception("video_analyze tool failed")
                return json.dumps({"error": str(e)})

    return VideoAnalyzeTool()


def get_tools() -> list[Any]:
    return [_build_tool()]


# ---- CLI smoke test ---------------------------------------------------------

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Analyze a video with Gemini")
    p.add_argument("file_path", help="Path to a local video file")
    p.add_argument("--mode", default="ugc", choices=["ugc", "tear_down"])
    p.add_argument("--model", default=DEFAULT_MODEL)
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not os.environ.get("GOOGLE_API_KEY"):
        print("GOOGLE_API_KEY is not set. Aborting smoke test.")
        raise SystemExit(2)
    out = analyze(args.file_path, mode=args.mode, model=args.model)
    print(json.dumps({k: v for k, v in out.items() if k != "raw"}, indent=2))
