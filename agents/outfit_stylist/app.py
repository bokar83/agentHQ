"""
AminoAI — Aesthetic Intelligence
Powered by Claude claude-opus-4-6 vision
"""

import asyncio
import base64
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# ── Setup ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="AminoAI", version="2.0.0")

BASE_DIR      = Path(__file__).parent
WARDROBE_DIR  = BASE_DIR / "wardrobe"
SAVES_FILE    = BASE_DIR / "saved_looks.json"
PROFILE_FILE  = BASE_DIR / "style_profile.json"

WARDROBE_DIR.mkdir(exist_ok=True)
WARDROBE_INDEX = WARDROBE_DIR / "index.json"

SUPPORTED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_STYLIST = (
    "You are Ami, a personal AI stylist for a stylish 15-year-old girl. "
    "Your tone is warm, encouraging, and fun — like a best friend who knows fashion. "
    "You understand current Gen-Z aesthetics: Y2K, dark academia, coquette, clean girl, "
    "soft girl, cottagecore, indie/alt, streetwear, and more. "
    "Give specific, practical advice using real item descriptions from the wardrobe. "
    "Always be positive and body-positive. Use a few tasteful emojis."
)

# ── Data helpers ───────────────────────────────────────────────────────────────

def load_wardrobe() -> list[dict]:
    if WARDROBE_INDEX.exists():
        return json.loads(WARDROBE_INDEX.read_text())
    return []

def save_wardrobe(items: list[dict]) -> None:
    WARDROBE_INDEX.write_text(json.dumps(items, indent=2))

def load_saves() -> list[dict]:
    if SAVES_FILE.exists():
        return json.loads(SAVES_FILE.read_text())
    return []

def write_saves(saves: list[dict]) -> None:
    SAVES_FILE.write_text(json.dumps(saves, indent=2))

def load_profile() -> dict:
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text())
    return {}

def write_profile(profile: dict) -> None:
    PROFILE_FILE.write_text(json.dumps(profile, indent=2))

def image_to_b64(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
    media_type = media_map.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return data, media_type

def wardrobe_item_with_url(item: dict) -> dict:
    """Add image_url to a wardrobe item dict."""
    return {**item, "image_url": f"/wardrobe/{item['id']}/image"}

def wardrobe_summary_text(wardrobe: list[dict]) -> str:
    lines = []
    for item in wardrobe:
        a = item.get("analysis", {})
        name = item.get("name") or a.get("type", "item")
        color = a.get("color", "")
        style = a.get("style", "")
        desc = a.get("description", "")
        lines.append(f"- {name} ({color}, {style}) — {desc}".strip(" —"))
    return "\n".join(lines)

# ── Claude helpers ─────────────────────────────────────────────────────────────

def analyze_clothing_item(image_b64: str, media_type: str, name: str = "", category: str = "", notes: str = "") -> dict:
    extra = ""
    if name:    extra += f" The item is called '{name}'."
    if category: extra += f" Category: {category}."
    if notes:   extra += f" User notes: {notes}."

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM_STYLIST,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                {"type": "text", "text": (
                    f"Analyze this clothing item and return ONLY valid JSON (no markdown) with these fields:\n"
                    f"- type: clothing category (e.g. crop top, wide-leg jeans, mini dress, chunky sneakers)\n"
                    f"- color: color(s) in a fun descriptive way (e.g. 'butter yellow', 'midnight navy')\n"
                    f"- style: aesthetic (e.g. coquette, Y2K, clean girl, dark academia)\n"
                    f"- season: best season(s)\n"
                    f"- vibe: one-word vibe (e.g. dreamy, edgy, cozy, glam)\n"
                    f"- description: 1-2 sentences, written like a fashion friend\n"
                    f"- tags: 4-5 style tags as an array\n"
                    f"- pairs_with: 2-3 item types this goes well with{extra}"
                )},
            ],
        }],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def analyze_full_outfit(image_b64: str, media_type: str, occasion: str = "") -> str:
    occ_line = f" The occasion is: {occasion}." if occasion else ""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM_STYLIST,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                {"type": "text", "text": (
                    f"Rate this outfit!{occ_line} Give honest, encouraging feedback like a stylish bestie. Structure your response exactly like this:\n\n"
                    "## ✨ The Look\n"
                    "[Describe the full outfit in 2-3 sentences with energy]\n\n"
                    "## ⭐ Vibe Score: X/10\n"
                    "[One sentence explaining the score]\n\n"
                    "## 💜 What's Working\n"
                    "[2-3 bullet points of genuine compliments]\n\n"
                    "## 🔥 Glow-Up Tips\n"
                    "[2-3 specific, actionable styling suggestions]\n\n"
                    "## 📍 Best For\n"
                    "[List 3-4 occasions this outfit is perfect for]\n\n"
                    "## 💡 Remix Ideas\n"
                    "[2 creative alternative ways to style these pieces]\n\n"
                    "Keep it fun, specific, and encouraging!"
                )},
            ],
        }],
    )
    return response.content[0].text


async def stream_outfit_suggestions(wardrobe: list[dict], vibes: list[str], occasion: str, weather: str, notes: str, profile: dict):
    if not wardrobe:
        yield "data: " + json.dumps({"text": "Your closet is empty! Add some pieces first. 👗"}) + "\n\n"
        yield "data: [DONE]\n\n"
        return

    vibe_str    = ", ".join(vibes) if vibes else "whatever feels right"
    profile_str = ""
    if profile.get("aesthetics"):
        profile_str = f"\nHer favourite aesthetics: {', '.join(profile['aesthetics'])}."
    if profile.get("loves"):
        profile_str += f" She loves: {profile['loves']}."

    prompt = (
        f"Here's Aminöa's closet:\n{wardrobe_summary_text(wardrobe)}\n\n"
        f"She wants: vibe = {vibe_str}"
        + (f", occasion = {occasion}" if occasion else "")
        + (f", weather = {weather}" if weather else "")
        + (f", extra notes = {notes}" if notes else "")
        + profile_str
        + "\n\nCreate **3 complete outfit looks** from her closet. For each:\n"
        "### Look 1 — [Creative Name]\n"
        "**Pieces:** [list specific items from her closet]\n"
        "**Vibe:** [aesthetic/mood]\n"
        "**Perfect for:** [occasions]\n"
        "**Styling tip:** [one specific pro tip]\n\n"
        "Be specific with real item names from her closet. Make it exciting and achievable! ✨"
    )

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM_STYLIST,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield "data: " + json.dumps({"text": text}) + "\n\n"
            await asyncio.sleep(0)

    yield "data: [DONE]\n\n"


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse((BASE_DIR / "static" / "index.html").read_text())


# Wardrobe ─────────────────────────────────────────────────────────────────────

@app.get("/wardrobe")
async def get_wardrobe():
    return JSONResponse([wardrobe_item_with_url(i) for i in load_wardrobe()])


@app.get("/wardrobe/stats")
async def wardrobe_stats():
    wardrobe = load_wardrobe()
    if not wardrobe:
        return JSONResponse({"count": 0, "top_colors": [], "top_styles": [], "top_tags": []})
    from collections import Counter
    colors = Counter(i.get("analysis", {}).get("color", "") for i in wardrobe if i.get("analysis", {}).get("color"))
    styles = Counter(i.get("analysis", {}).get("style", "") for i in wardrobe if i.get("analysis", {}).get("style"))
    tags   = Counter(t for i in wardrobe for t in i.get("analysis", {}).get("tags", []))
    return JSONResponse({
        "count": len(wardrobe),
        "top_colors": [c for c, _ in colors.most_common(3)],
        "top_styles": [s for s, _ in styles.most_common(3)],
        "top_tags":   [t for t, _ in tags.most_common(5)],
    })


@app.get("/wardrobe/{item_id}/image")
async def get_item_image(item_id: str):
    wardrobe = load_wardrobe()
    item = next((i for i in wardrobe if i["id"] == item_id), None)
    if not item:
        raise HTTPException(404, "Item not found")
    img_path = WARDROBE_DIR / item["filename"]
    if not img_path.exists():
        raise HTTPException(404, "Image file not found")
    return FileResponse(img_path)


@app.post("/upload-item")
async def upload_item(
    file: UploadFile = File(...),
    name: Optional[str] = Form(default=""),
    category: Optional[str] = Form(default=""),
    color_description: Optional[str] = Form(default=""),
):
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    item_id = str(uuid.uuid4())
    suffix  = Path(file.filename or "upload.jpg").suffix.lower() or ".jpg"
    dest    = WARDROBE_DIR / f"{item_id}{suffix}"

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    image_b64, media_type = image_to_b64(dest)
    try:
        analysis = analyze_clothing_item(image_b64, media_type, name, category, color_description)
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(500, f"AI analysis failed: {e}")

    wardrobe = load_wardrobe()
    item = {
        "id":       item_id,
        "filename": dest.name,
        "name":     name or analysis.get("type", "Item"),
        "category": category,
        "analysis": analysis,
    }
    wardrobe.append(item)
    save_wardrobe(wardrobe)

    return JSONResponse({**wardrobe_item_with_url(item), "success": True})


@app.delete("/wardrobe/{item_id}")
async def delete_item(item_id: str):
    wardrobe = load_wardrobe()
    item = next((i for i in wardrobe if i["id"] == item_id), None)
    if not item:
        raise HTTPException(404, "Item not found")
    (WARDROBE_DIR / item["filename"]).unlink(missing_ok=True)
    save_wardrobe([i for i in wardrobe if i["id"] != item_id])
    return JSONResponse({"success": True})


# Outfits ──────────────────────────────────────────────────────────────────────

@app.post("/stream-outfits")
async def stream_outfits(request: Request):
    body    = await request.json()
    wardrobe = load_wardrobe()
    profile  = load_profile()
    return StreamingResponse(
        stream_outfit_suggestions(
            wardrobe,
            vibes=body.get("vibes", []),
            occasion=body.get("occasion", ""),
            weather=body.get("weather", ""),
            notes=body.get("notes", ""),
            profile=profile,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/analyze-outfit")
async def analyze_outfit(
    file: UploadFile = File(...),
    occasion: Optional[str] = Form(default=""),
):
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")
    contents  = await file.read()
    image_b64 = base64.standard_b64encode(contents).decode()
    try:
        feedback = analyze_full_outfit(image_b64, file.content_type, occasion)
    except Exception as e:
        raise HTTPException(500, f"AI analysis failed: {e}")
    return JSONResponse({"success": True, "feedback": feedback})


# Saved Looks ──────────────────────────────────────────────────────────────────

@app.get("/saved-looks")
async def get_saved_looks():
    return JSONResponse(load_saves())


@app.post("/saved-looks")
async def save_look(request: Request):
    body = await request.json()
    saves = load_saves()
    look = {
        "id":      str(uuid.uuid4()),
        "text":    body.get("text", ""),
        "vibes":   body.get("vibes", []),
        "occasion": body.get("occasion", ""),
        "saved_at": __import__("datetime").datetime.now().isoformat(),
    }
    saves.insert(0, look)
    write_saves(saves)
    return JSONResponse({"success": True, "look": look})


@app.delete("/saved-looks/{look_id}")
async def delete_look(look_id: str):
    saves = load_saves()
    write_saves([s for s in saves if s["id"] != look_id])
    return JSONResponse({"success": True})


# Style Profile ────────────────────────────────────────────────────────────────

@app.get("/profile")
async def get_profile():
    return JSONResponse(load_profile())


@app.post("/profile")
async def update_profile(request: Request):
    body = await request.json()
    write_profile(body)
    return JSONResponse({"success": True})


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
