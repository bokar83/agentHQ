"""Hero v2: Concept A — illuminated notebook page with one handwritten line.

No people, no faces. Subject on right third, H1 lives left.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path

env_path = Path(__file__).resolve().parents[3] / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))
from orchestrator import kie_media  # noqa: E402

PROMPT = (
    "Cinematic editorial photography, top-down close shot of an open leather-bound notebook resting on a dark surface. "
    "Cream-colored unlined paper. ONE single handwritten line of cursive ink near the top of the right page, deliberately illegible (out-of-focus enough that no specific letters can be read). "
    "Rest of the page is intentionally blank. No pen visible, no hands, no lamp visible in frame. "
    "Lighting: a single soft pool of warm light hitting the page itself, with a subtle cool cyan rim-light bleeding in from the left edge. "
    "Background: deep navy-black surface fading to pure black at the edges. The notebook's leather cover has a clay-colored warmth where it catches the light. "
    "Mood: quiet diagnostic precision. Late evening. The page feels held in stillness. Photographic, not illustrated, not stylized, no text overlays anywhere except the single inked line on the page. "
    "Composition: notebook occupies the RIGHT TWO-THIRDS of the frame. Left one-third is intentional negative space, dark navy fading to black, where headline text overlay will sit. "
    "16:9 landscape, 1440x900. No people, no faces, no hands, no text characters legible, no AI cliches (no robots, no circuits, no glowing brains, no holograms). "
    "Reference colors: deep navy #071A2E for shadows, soft cyan #00B7C2 as cool rim light, warm clay #B47C57 on the leather binding."
)

print("Calling kie_media._run_with_retries(text_to_image) for Concept A...")
result = kie_media._run_with_retries(
    task_type="text_to_image",
    prompt=PROMPT,
    extra_input={"aspect_ratio": "16:9"},
)
print(json.dumps(result, indent=2, default=str))

urls = result.get("result_urls") or []
if not urls:
    print("[!] No result URLs returned.")
    sys.exit(1)

out_dir = Path(__file__).resolve().parent / "mockups"
target = out_dir / "hero-v2-concept-a.png"
byte_count = kie_media._download_asset(urls[0], target)
print(f"\nSaved Concept A hero to: {target}  ({byte_count:,} bytes)")
