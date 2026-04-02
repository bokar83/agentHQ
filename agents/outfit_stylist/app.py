"""
Outfit Stylist Agent — powered by Claude claude-opus-4-6 vision
Lets you upload clothing photos and get outfit suggestions.
"""

import base64
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Setup ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Outfit Stylist", version="1.0.0")

WARDROBE_DIR = Path(__file__).parent / "wardrobe"
WARDROBE_DIR.mkdir(exist_ok=True)

WARDROBE_INDEX = WARDROBE_DIR / "index.json"

SUPPORTED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── Wardrobe helpers ───────────────────────────────────────────────────────────

def load_wardrobe() -> list[dict]:
    if WARDROBE_INDEX.exists():
        return json.loads(WARDROBE_INDEX.read_text())
    return []


def save_wardrobe(items: list[dict]) -> None:
    WARDROBE_INDEX.write_text(json.dumps(items, indent=2))


def image_to_b64(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type) for a local image file."""
    suffix = path.suffix.lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
    media_type = media_map.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return data, media_type


# ── Claude helpers ─────────────────────────────────────────────────────────────

def analyze_clothing_item(image_b64: str, media_type: str) -> dict:
    """Ask Claude to identify and describe a clothing item."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                },
                {
                    "type": "text",
                    "text": (
                        "You are a professional fashion stylist analyzing a clothing item. "
                        "Look at this image and provide a JSON response with these fields:\n"
                        "- type: the clothing category (e.g. t-shirt, jeans, dress, jacket, sneakers, etc.)\n"
                        "- color: primary color(s)\n"
                        "- style: style descriptor (casual, formal, sporty, bohemian, etc.)\n"
                        "- season: best season(s) to wear (spring, summer, fall, winter, all-season)\n"
                        "- description: a brief 1-2 sentence description\n"
                        "- tags: array of 3-5 style tags\n\n"
                        "Respond ONLY with valid JSON, no markdown."
                    ),
                },
            ],
        }],
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def generate_outfit_suggestions(wardrobe: list[dict], context: str = "") -> str:
    """Ask Claude to suggest outfits from the current wardrobe."""
    if not wardrobe:
        return "Your wardrobe is empty. Upload some clothing items first!"

    wardrobe_summary = "\n".join(
        f"- [{item['id'][:8]}] {item['analysis'].get('type', 'item')}: "
        f"{item['analysis'].get('color', '')} {item['analysis'].get('style', '')} "
        f"({item['analysis'].get('description', '')})"
        for item in wardrobe
    )

    prompt = (
        f"You are a professional fashion stylist. Here is the user's wardrobe:\n\n"
        f"{wardrobe_summary}\n\n"
    )
    if context:
        prompt += f"User request: {context}\n\n"

    prompt += (
        "Create 3 complete outfit suggestions using items from this wardrobe. "
        "For each outfit:\n"
        "1. Give it a creative name\n"
        "2. List the specific items (use their descriptions)\n"
        "3. Describe when/where to wear it\n"
        "4. Give one styling tip\n\n"
        "Be specific and practical. Format clearly with headers."
    )

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def analyze_full_outfit(image_b64: str, media_type: str) -> str:
    """Analyze a complete outfit photo and give styling feedback."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1536,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                },
                {
                    "type": "text",
                    "text": (
                        "You are a professional fashion stylist. Analyze this outfit photo and provide:\n\n"
                        "1. **Outfit Breakdown** — describe each piece you can see\n"
                        "2. **Style Rating** — rate the overall look /10 with reasoning\n"
                        "3. **What Works** — 2-3 things done well\n"
                        "4. **Styling Tips** — 2-3 specific improvements or alternatives\n"
                        "5. **Occasion Match** — what occasions this outfit suits best\n"
                        "6. **Outfit Ideas** — 2 alternative ways to style these pieces differently\n\n"
                        "Be encouraging, specific, and practical."
                    ),
                },
            ],
        }],
    )
    return response.content[0].text


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(html_file.read_text())


@app.post("/upload-item")
async def upload_item(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(default=""),
):
    """Upload a single clothing item to the wardrobe."""
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    item_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix.lower() or ".jpg"
    dest = WARDROBE_DIR / f"{item_id}{suffix}"

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    image_b64, media_type = image_to_b64(dest)
    try:
        analysis = analyze_clothing_item(image_b64, media_type)
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(500, f"Claude analysis failed: {e}")

    wardrobe = load_wardrobe()
    item = {
        "id": item_id,
        "filename": dest.name,
        "notes": notes,
        "analysis": analysis,
    }
    wardrobe.append(item)
    save_wardrobe(wardrobe)

    return JSONResponse({"success": True, "item": item})


@app.post("/analyze-outfit")
async def analyze_outfit(file: UploadFile = File(...)):
    """Analyze a complete outfit photo (not saved to wardrobe)."""
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    image_b64 = base64.standard_b64encode(contents).decode()
    media_type = file.content_type

    try:
        feedback = analyze_full_outfit(image_b64, media_type)
    except Exception as e:
        raise HTTPException(500, f"Claude analysis failed: {e}")

    return JSONResponse({"success": True, "feedback": feedback})


@app.get("/wardrobe")
async def get_wardrobe():
    """Return all wardrobe items."""
    return JSONResponse(load_wardrobe())


@app.get("/wardrobe/{item_id}/image")
async def get_item_image(item_id: str):
    """Serve the image for a wardrobe item."""
    wardrobe = load_wardrobe()
    item = next((i for i in wardrobe if i["id"] == item_id), None)
    if not item:
        raise HTTPException(404, "Item not found")
    img_path = WARDROBE_DIR / item["filename"]
    if not img_path.exists():
        raise HTTPException(404, "Image file not found")
    return FileResponse(img_path)


@app.delete("/wardrobe/{item_id}")
async def delete_item(item_id: str):
    """Remove an item from the wardrobe."""
    wardrobe = load_wardrobe()
    item = next((i for i in wardrobe if i["id"] == item_id), None)
    if not item:
        raise HTTPException(404, "Item not found")

    img_path = WARDROBE_DIR / item["filename"]
    img_path.unlink(missing_ok=True)

    wardrobe = [i for i in wardrobe if i["id"] != item_id]
    save_wardrobe(wardrobe)
    return JSONResponse({"success": True})


@app.post("/suggest-outfits")
async def suggest_outfits(request: dict):
    """Generate outfit suggestions from the wardrobe."""
    context = request.get("context", "")
    wardrobe = load_wardrobe()
    suggestions = generate_outfit_suggestions(wardrobe, context)
    return JSONResponse({"success": True, "suggestions": suggestions})


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
