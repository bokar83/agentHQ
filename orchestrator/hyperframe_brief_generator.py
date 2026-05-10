import os
import re
import subprocess
import tempfile
import shutil

def _fix_html(html: str) -> str:
    """Post-process LLM HTML to fix common HyperFrames lint errors."""
    # Ensure data-start="0" on root composition element
    html = re.sub(
        r'(data-composition-id="main"(?![^>]*data-start))',
        r'\1 data-start="0"',
        html
    )
    # Inject window.__timelines if missing
    if "window.__timelines" not in html:
        inject = (
            '\n<script>\n'
            '  window.__timelines = window.__timelines || {};\n'
            '  const tl = gsap.timeline({ paused: true });\n'
            '  window.__timelines["main"] = tl;\n'
            '</script>'
        )
        html = html.replace("</body>", inject + "\n</body>")
    return html


ASPECT_DIMS = {
    "9:16": (1080, 1920),
    "1:1":  (1080, 1080),
    "16:9": (1920, 1080),
}

SYSTEM_PROMPT = """You convert social media posts into HyperFrames HTML compositions.
Output ONLY the raw HTML — no markdown fences, no explanation, nothing else.

Rules:
- viewport meta must match the provided width x height exactly
- data-composition-id="main" on root div
- data-width and data-height on root div must match viewport
- data-duration="30" (30 seconds total)
- exactly 4 clips: id="hook" (0-5s), id="s1" (5-13s), id="s2" (13-22s), id="cta" (22-30s)
- each clip: data-start, data-duration, data-track-index="1"
- all clips hidden initially via CSS opacity:0 — GSAP animates them in
- after every tl.to fade-out, add tl.set hard kill e.g. tl.set("#hook", { opacity: 0 }, 5.00)
- brand palette: background #0A0A0A, text #FFFFFF, accent #C8B560
- fonts: "Arial Black" for headlines (font-weight:900), Arial for body
- hook: punchy 1-line from post opening — largest font (88px)
- s1/s2: core points from post body — medium font (52px), color #CCCCCC
- cta: follow/engage prompt — accent color (#C8B560), 64px
- text must come from the post content, not be invented
- GSAP CDN: https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js
- window.__timelines["main"] = tl pattern required"""

USER_PROMPT_TEMPLATE = """Convert this social media post into a HyperFrames HTML composition.
Width: {width}px  Height: {height}px  Aspect ratio: {aspect_ratio}

POST:
{post_text}"""


class HyperframeBriefGenerator:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=os.environ.get("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                default_headers={"HTTP-Referer": "https://agentshq.io"},
            )
        return self._client

    def generate(self, post_text: str, aspect_ratio: str = "9:16") -> str:
        """Returns HTML string for the composition."""
        width, height = ASPECT_DIMS.get(aspect_ratio, (1080, 1920))
        response = self._get_client().chat.completions.create(
            model="anthropic/claude-sonnet-4.6",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        width=width, height=height,
                        aspect_ratio=aspect_ratio,
                        post_text=post_text[:2000]
                    )
                }
            ]
        )
        html = response.choices[0].message.content or ""
        html = html.strip()
        html = re.sub(r"^```[a-zA-Z]*\n?", "", html).rstrip("`").strip()
        html = _fix_html(html)
        return html

    def render_to_mp4(self, post_text: str, aspect_ratio: str, output_path: str) -> str:
        """Scaffold HyperFrames project, write HTML, lint, render. Returns output_path."""
        project_dir = tempfile.mkdtemp(prefix="hf_boost_")
        try:
            subprocess.run(
                ["npx", "hyperframes", "init", project_dir, "--non-interactive"],
                check=True, capture_output=True, text=True, timeout=60
            )
            html = self.generate(post_text, aspect_ratio)
            index_path = os.path.join(project_dir, "index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html)
            lint = subprocess.run(
                ["npx", "hyperframes", "lint"],
                cwd=project_dir, capture_output=True, text=True, timeout=30
            )
            if "error" in lint.stdout.lower() and "0 error" not in lint.stdout.lower():
                raise RuntimeError(f"HyperFrames lint errors:\n{lint.stdout[:500]}")
            result = subprocess.run(
                ["npx", "hyperframes", "render", "--quality", "standard", "--output", output_path],
                cwd=project_dir, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"HyperFrames render failed: {result.stderr[:300]}")
            return output_path
        finally:
            shutil.rmtree(project_dir, ignore_errors=True)
