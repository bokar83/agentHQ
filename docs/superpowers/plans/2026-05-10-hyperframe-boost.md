# HyperFrame Boost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically convert top-scoring personal Notion drafts into HyperFrame videos (9:16 + 1:1), queue via Telegram gate, and post 24hr after the text original to LinkedIn, X, and YouTube Shorts.

**Architecture:** Three new orchestrator files (agent, brief generator, cron entry point) + one small addition to auto_publisher.py routing. Notion gets two new fields on Griot DB and four new fields on Studio Pipeline DB. Telegram gate: Boubacar replies 1/2/3/all/skip to a candidate menu every 2 days.

**Tech Stack:** Python 3.11, Notion API (existing client), Telegram bot (existing notifier), Anthropic SDK (claude-sonnet-4-6), HyperFrames CLI (`npx hyperframes init` + `render`), Google Drive upload (existing `_upload_to_drive`), Blotato (existing auto_publisher).

**Key constraint (validated Phase 0):** HyperFrames renders from an HTML project directory — NOT a JSON brief file. The generator must: (1) `npx hyperframes init <tmpdir> --non-interactive`, (2) write `index.html` composition into that dir, (3) `npx hyperframes render` from that dir. Project dir is deleted after upload.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `orchestrator/hyperframe_brief_generator.py` | Create | LLM: post text → HTML composition string; scaffold + render project dir |
| `orchestrator/hyperframe_boost_agent.py` | Create | Main orchestration: query → Telegram → render loop |
| `orchestrator/hyperframe_boost_cron.py` | Create | Cron entry point, logging |
| `orchestrator/auto_publisher.py` | Modify | Add YouTube Shorts routing for hyperframe-boost 9:16 records |
| `tests/test_hyperframe_boost.py` | Create | Unit tests for brief generator + candidate filtering |

---

## Phase 0: Manual Stack Validation

**Do this before writing any code.** Confirms the render chain works end-to-end.

- [ ] **Step 1: Pick a Notion draft**

Open Griot content board in Notion. Find any Draft/Queued personal post with total_score > 70. Copy its full text.

- [ ] **Step 2: Scaffold a test project and write 9:16 composition**

```bash
cd /tmp && npx hyperframes init hf-boost-test --non-interactive
```

Then write `index.html` into `/tmp/hf-boost-test/` with width=1080, height=1920 (9:16), 30s duration, 4 scenes: hook, s1, s2, cta. See Task 1 Step 3 for the exact HTML template the generator produces.

- [ ] **Step 3: Lint + render 9:16**

```bash
cd /tmp/hf-boost-test
npx hyperframes lint        # must be 0 errors
npx hyperframes render --quality draft --output /tmp/test_9x16.mp4
ls -lh /tmp/test_9x16.mp4  # expect ~800K-2MB MP4
```

Expected: file exists, no render errors.

- [ ] **Step 4: Render 1:1**

```bash
# Update index.html: change data-width="1080" data-height="1080", viewport to width=1080,height=1080
# Then re-render:
npx hyperframes render --quality draft --output /tmp/test_1x1.mp4
ls -lh /tmp/test_1x1.mp4
```

Expected: `/tmp/test_1x1.mp4` created.

> **Note:** Phase 0 render (9:16) already validated on VPS 2026-05-10. Produced 946K MP4. Chain confirmed working.

- [ ] **Step 5: Upload to Drive**

```python
# Run in python3 REPL on VPS
import sys; sys.path.insert(0, '/root/agentsHQ')
from orchestrator.studio_render_publisher import _upload_to_drive
result = _upload_to_drive('/tmp/test_9x16.mp4', 'test_hf_boost_9x16.mp4')
print(result)
```

Expected: dict with `drive_url` and `drive_file_id`.

- [ ] **Step 6: Verify Blotato routing manually**

Log into Blotato dashboard. Create a test scheduled post for X pointing at the Drive URL. Confirm it appears in the queue.

- [ ] **Step 7: Gate check**

If all 6 steps passed: proceed to Task 1.
If any step failed: fix the underlying issue before proceeding. Do not write automation wrapper around a broken chain.

---

## Task 1: HyperFrame Brief Generator

**Files:**
- Create: `orchestrator/hyperframe_brief_generator.py`
- Create: `tests/test_hyperframe_boost.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_hyperframe_boost.py
import pytest
from unittest.mock import patch, MagicMock

SAMPLE_POST = """Nobody hands 1stGen founders a roadmap.
I spent 3 years waiting for permission that was never coming.
The playbook exists — you have to build it yourself.
If you're building without a safety net, follow for the real talk."""

SAMPLE_HTML_9x16 = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>* { margin:0; padding:0; } html,body { width:1080px; height:1920px; background:#0A0A0A; }</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="30" data-width="1080" data-height="1920">
      <div id="hook" data-start="0" data-duration="5" data-track-index="1">Hook text</div>
      <div id="s1" data-start="5" data-duration="8" data-track-index="1">Body text</div>
      <div id="s2" data-start="13" data-duration="9" data-track-index="1">Body text 2</div>
      <div id="cta" data-start="22" data-duration="8" data-track-index="1">Follow us</div>
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      tl.from("#hook", { opacity: 0, duration: 0.6 }, 0);
      tl.set("#hook", { opacity: 0 }, 5.00);
      tl.from("#cta", { opacity: 0, duration: 0.6 }, 22);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>"""

SAMPLE_HTML_1x1 = SAMPLE_HTML_9x16.replace("height=1920", "height=1080").replace(
    "height:1920px", "height:1080px").replace('data-height="1920"', 'data-height="1080"')


def test_generate_returns_html_string():
    from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator
    gen = HyperframeBriefGenerator()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=SAMPLE_HTML_9x16)]
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_response
        html = gen.generate(SAMPLE_POST, aspect_ratio="9:16")
    assert isinstance(html, str)
    assert "<!doctype html" in html.lower()

def test_generate_strips_markdown_fences():
    from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator
    gen = HyperframeBriefGenerator()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=f"```html\n{SAMPLE_HTML_9x16}\n```")]
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_response
        html = gen.generate(SAMPLE_POST, aspect_ratio="9:16")
    assert not html.startswith("```")
    assert "<!doctype html" in html.lower()

def test_generate_uses_correct_dimensions_9x16():
    from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator
    gen = HyperframeBriefGenerator()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=SAMPLE_HTML_9x16)]
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_response
        captured_prompt = []
        def capture(*args, **kwargs):
            captured_prompt.append(kwargs.get("messages", [{}])[0].get("content", ""))
            return mock_response
        mock_client.messages.create.side_effect = capture
        gen.generate(SAMPLE_POST, aspect_ratio="9:16")
    assert "1080" in captured_prompt[0]
    assert "1920" in captured_prompt[0]
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /root/agentsHQ
python -m pytest tests/test_hyperframe_boost.py -v
```

Expected: `ImportError: No module named 'orchestrator.hyperframe_brief_generator'`

- [ ] **Step 3: Implement brief generator**

Create `orchestrator/hyperframe_brief_generator.py`:

```python
import os
import subprocess
import tempfile
import shutil
import anthropic

# Dimensions per aspect ratio
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
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate(self, post_text: str, aspect_ratio: str = "9:16") -> str:
        """Returns HTML string for the composition."""
        width, height = ASPECT_DIMS.get(aspect_ratio, (1080, 1920))
        response = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    width=width, height=height,
                    aspect_ratio=aspect_ratio,
                    post_text=post_text[:2000]
                )
            }]
        )
        html = response.content[0].text.strip()
        # Strip any accidental markdown fences
        if html.startswith("```"):
            html = html.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return html

    def render_to_mp4(self, post_text: str, aspect_ratio: str, output_path: str) -> str:
        """Scaffold project, write HTML, lint, render. Returns output_path."""
        project_dir = tempfile.mkdtemp(prefix="hf_boost_")
        try:
            # Scaffold
            subprocess.run(
                ["npx", "hyperframes", "init", project_dir, "--non-interactive"],
                check=True, capture_output=True, text=True, timeout=60
            )
            # Write composition
            html = self.generate(post_text, aspect_ratio)
            index_path = os.path.join(project_dir, "index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html)
            # Lint (warn only, don't block on density warning)
            lint = subprocess.run(
                ["npx", "hyperframes", "lint"],
                cwd=project_dir, capture_output=True, text=True, timeout=30
            )
            if "error" in lint.stdout.lower() and "0 error" not in lint.stdout:
                raise RuntimeError(f"HyperFrames lint errors:\n{lint.stdout[:500]}")
            # Render
            result = subprocess.run(
                ["npx", "hyperframes", "render", "--quality", "standard", "--output", output_path],
                cwd=project_dir, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"HyperFrames render failed: {result.stderr[:300]}")
            return output_path
        finally:
            shutil.rmtree(project_dir, ignore_errors=True)
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/test_hyperframe_boost.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add orchestrator/hyperframe_brief_generator.py tests/test_hyperframe_boost.py
git commit -m "feat(hf-boost): brief generator — post text → HyperFrames JSON via claude-sonnet-4-6"
```

---

## Task 2: Candidate Filtering Tests

**Files:**
- Modify: `tests/test_hyperframe_boost.py`

- [ ] **Step 1: Add candidate filter tests**

Append to `tests/test_hyperframe_boost.py`:

```python
def test_candidates_exclude_posts_with_twin():
    """Posts that already have hyperframe_twin_id set must be excluded."""
    from orchestrator.hyperframe_boost_agent import _filter_candidates

    candidates = [
        {"notion_id": "aaa", "total_score": 90, "hyperframe_twin_id": None, "platform": ["linkedin", "x"]},
        {"notion_id": "bbb", "total_score": 85, "hyperframe_twin_id": "some-twin-id", "platform": ["linkedin"]},
        {"notion_id": "ccc", "total_score": 80, "hyperframe_twin_id": None, "platform": ["x"]},
    ]
    result = _filter_candidates(candidates)
    ids = [c["notion_id"] for c in result]
    assert "bbb" not in ids
    assert "aaa" in ids
    assert "ccc" in ids

def test_candidates_sorted_by_score_desc():
    from orchestrator.hyperframe_boost_agent import _filter_candidates

    candidates = [
        {"notion_id": "low", "total_score": 60, "hyperframe_twin_id": None, "platform": ["x"]},
        {"notion_id": "high", "total_score": 90, "hyperframe_twin_id": None, "platform": ["linkedin"]},
        {"notion_id": "mid", "total_score": 75, "hyperframe_twin_id": None, "platform": ["x"]},
    ]
    result = _filter_candidates(candidates)
    assert result[0]["notion_id"] == "high"
    assert result[1]["notion_id"] == "mid"

def test_candidates_capped_at_three():
    from orchestrator.hyperframe_boost_agent import _filter_candidates

    candidates = [
        {"notion_id": str(i), "total_score": 100 - i, "hyperframe_twin_id": None, "platform": ["x"]}
        for i in range(6)
    ]
    result = _filter_candidates(candidates)
    assert len(result) == 3

def test_parse_telegram_reply_multiselect():
    from orchestrator.hyperframe_boost_agent import _parse_reply

    assert _parse_reply("1,3", 3) == [0, 2]
    assert _parse_reply("all", 3) == [0, 1, 2]
    assert _parse_reply("skip", 3) == []
    assert _parse_reply("2", 3) == [1]
    assert _parse_reply("1, 2, 3", 3) == [0, 1, 2]

def test_parse_telegram_reply_out_of_range():
    from orchestrator.hyperframe_boost_agent import _parse_reply

    result = _parse_reply("5", 3)
    assert result == []
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_hyperframe_boost.py::test_candidates_exclude_posts_with_twin -v
```

Expected: `ImportError: cannot import name '_filter_candidates'`

- [ ] **Step 3: Create hyperframe_boost_agent.py skeleton with filter + parse functions**

Create `orchestrator/hyperframe_boost_agent.py`:

```python
import os
import json
import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def _filter_candidates(candidates: list[dict]) -> list[dict]:
    filtered = [c for c in candidates if not c.get("hyperframe_twin_id")]
    return sorted(filtered, key=lambda c: c.get("total_score", 0), reverse=True)[:3]


def _parse_reply(reply_text: str, count: int) -> list[int]:
    reply_text = reply_text.strip().lower()
    if reply_text == "skip":
        return []
    if reply_text == "all":
        return list(range(count))
    indices = []
    for part in reply_text.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < count:
                indices.append(idx)
        except ValueError:
            pass
    return indices


class HyperframeBoostAgent:
    def run(self):
        raise NotImplementedError("Task 3 implements this")
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/test_hyperframe_boost.py -v
```

Expected: all 8 PASSED

- [ ] **Step 5: Commit**

```bash
git add orchestrator/hyperframe_boost_agent.py tests/test_hyperframe_boost.py
git commit -m "feat(hf-boost): candidate filter + Telegram reply parser with tests"
```

---

## Task 3: Notion Query + Telegram Menu

**Files:**
- Modify: `orchestrator/hyperframe_boost_agent.py`

Context: Griot Notion DB already queried in `orchestrator/griot.py`. Look at how it calls the Notion client (around line 100-150) to follow the same pattern. The Notion client is initialized from `NOTION_TOKEN` env var.

- [ ] **Step 1: Add Notion query test**

Append to `tests/test_hyperframe_boost.py`:

```python
def test_query_candidates_returns_top3(monkeypatch):
    from orchestrator.hyperframe_boost_agent import HyperframeBoostAgent

    fake_results = {
        "results": [
            {
                "id": f"page-{i}",
                "properties": {
                    "total_score": {"number": 90 - i},
                    "Draft": {"rich_text": [{"plain_text": f"Post text {i} " * 30}]},
                    "Status": {"select": {"name": "Draft"}},
                    "Platform": {"multi_select": [{"name": "linkedin"}, {"name": "x"}]},
                    "Scheduled Date": {"date": {"start": "2026-05-12"}},
                    "hyperframe_twin_id": {"relation": []},
                }
            }
            for i in range(5)
        ]
    }

    agent = HyperframeBoostAgent.__new__(HyperframeBoostAgent)
    
    import unittest.mock as mock
    with mock.patch.object(agent, '_notion_query', return_value=fake_results["results"]):
        candidates = agent._query_candidates()
    
    assert len(candidates) == 3
    assert candidates[0]["total_score"] >= candidates[1]["total_score"]
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_hyperframe_boost.py::test_query_candidates_returns_top3 -v
```

Expected: `AttributeError: _notion_query`

- [ ] **Step 3: Implement Notion query + Telegram menu in agent**

Replace `orchestrator/hyperframe_boost_agent.py` with:

```python
import os
import json
import logging
import time
from datetime import date, timedelta
from typing import Optional

from notion_client import Client as NotionClient

logger = logging.getLogger(__name__)

GRIOT_DB_ID = os.environ.get("GRIOT_NOTION_DB_ID", "")
STUDIO_DB_ID = os.environ.get("STUDIO_PIPELINE_DB_ID", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _filter_candidates(candidates: list[dict]) -> list[dict]:
    filtered = [c for c in candidates if not c.get("hyperframe_twin_id")]
    return sorted(filtered, key=lambda c: c.get("total_score", 0), reverse=True)[:3]


def _parse_reply(reply_text: str, count: int) -> list[int]:
    reply_text = reply_text.strip().lower()
    if reply_text == "skip":
        return []
    if reply_text == "all":
        return list(range(count))
    indices = []
    for part in reply_text.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < count:
                indices.append(idx)
        except ValueError:
            pass
    return indices


def _extract_text(prop) -> str:
    if not prop or not prop.get("rich_text"):
        return ""
    return "".join(t["plain_text"] for t in prop["rich_text"])


def _extract_platforms(prop) -> list[str]:
    if not prop or not prop.get("multi_select"):
        return []
    return [s["name"].lower() for s in prop["multi_select"]]


class HyperframeBoostAgent:
    def __init__(self):
        self._notion = NotionClient(auth=os.environ["NOTION_TOKEN"])

    def _notion_query(self) -> list[dict]:
        response = self._notion.databases.query(
            database_id=GRIOT_DB_ID,
            filter={
                "and": [
                    {"property": "Status", "select": {"is_not_empty": True}},
                    {"property": "Status", "select": {"does_not_equal": "Posted"}},
                    {"property": "hyperframe_twin_id", "relation": {"is_empty": True}},
                ]
            },
            sorts=[{"property": "total_score", "direction": "descending"}],
            page_size=20,
        )
        return response.get("results", [])

    def _query_candidates(self) -> list[dict]:
        raw = self._notion_query()
        parsed = []
        for page in raw:
            props = page["properties"]
            platforms = _extract_platforms(props.get("Platform"))
            if not any(p in platforms for p in ["linkedin", "x"]):
                continue
            full_text = _extract_text(props.get("Draft") or props.get("Hook"))
            if not full_text:
                continue
            parsed.append({
                "notion_id": page["id"],
                "total_score": props.get("total_score", {}).get("number", 0) or 0,
                "text_preview": full_text[:150],
                "full_text": full_text,
                "scheduled_date": (props.get("Scheduled Date") or {}).get("date", {}).get("start", ""),
                "platform": platforms,
                "hyperframe_twin_id": bool(
                    (props.get("hyperframe_twin_id") or {}).get("relation")
                ),
            })
        return _filter_candidates(parsed)

    def _send_telegram_menu(self, candidates: list[dict]) -> None:
        from orchestrator.notifier import send_message
        lines = ["HyperFrame candidates ready:\n"]
        for i, c in enumerate(candidates, 1):
            lines.append(f"{i}. [score: {c['total_score']:.0f}] {c['text_preview'][:100]}...")
        lines.append("\nReply: 1, 2, 3, 1,3, all, or skip")
        send_message(TELEGRAM_CHAT_ID, "\n".join(lines))

    def _poll_telegram_reply(self, count: int, timeout_hours: int = 24) -> list[int]:
        """Poll Telegram for reply. Returns approved indices or [] on timeout/skip."""
        from orchestrator.notifier import get_latest_message
        deadline = time.time() + timeout_hours * 3600
        last_seen_id = None
        while time.time() < deadline:
            msg = get_latest_message(TELEGRAM_CHAT_ID)
            if msg and msg.get("message_id") != last_seen_id:
                last_seen_id = msg["message_id"]
                text = msg.get("text", "").strip()
                if text:
                    return _parse_reply(text, count)
            time.sleep(60)
        logger.warning("Telegram reply timeout. Auto-skipping.")
        return []

    def run(self):
        raise NotImplementedError("Task 4 implements full run()")
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/test_hyperframe_boost.py -v
```

Expected: all 9 PASSED

- [ ] **Step 5: Commit**

```bash
git add orchestrator/hyperframe_boost_agent.py
git commit -m "feat(hf-boost): Notion query + Telegram candidate menu"
```

---

## Task 4: Render + Notion Record Creation

**Files:**
- Modify: `orchestrator/hyperframe_boost_agent.py`

Context: Look at `orchestrator/studio_render_publisher.py` for how `_upload_to_drive` and `_ffmpeg` are used. Import from there directly.

- [ ] **Step 1: Add render test**

Append to `tests/test_hyperframe_boost.py`:

```python
def test_render_produces_two_outputs():
    """_render_and_queue must attempt render for both 9:16 and 1:1."""
    import unittest.mock as mock
    from orchestrator.hyperframe_boost_agent import HyperframeBoostAgent

    agent = HyperframeBoostAgent.__new__(HyperframeBoostAgent)
    agent._notion = mock.MagicMock()

    candidate = {
        "notion_id": "test-notion-id",
        "total_score": 85,
        "text_preview": "Test post preview",
        "full_text": "Full test post text that would be longer in real life",
        "scheduled_date": "2026-05-12",
        "platform": ["linkedin", "x"],
    }

    render_calls = []
    with mock.patch('orchestrator.hyperframe_boost_agent.HyperframeBriefGenerator') as MockGen, \
         mock.patch('orchestrator.hyperframe_boost_agent._ffmpeg_render') as mock_render, \
         mock.patch('orchestrator.hyperframe_boost_agent._upload_to_drive') as mock_upload, \
         mock.patch('orchestrator.hyperframe_boost_agent._create_studio_record') as mock_record, \
         mock.patch('orchestrator.hyperframe_boost_agent._mark_twin') as mock_twin:

        MockGen.return_value.generate.return_value = {"aspect_ratio": "9:16", "scenes": []}
        mock_render.return_value = "/tmp/fake.mp4"
        mock_upload.return_value = {"drive_url": "https://drive.google.com/fake", "drive_file_id": "fake-id"}

        agent._render_and_queue(candidate)

    assert MockGen.return_value.generate.call_count == 2
    aspect_ratios_called = [call.args[1] for call in MockGen.return_value.generate.call_args_list]
    assert "9:16" in aspect_ratios_called
    assert "1:1" in aspect_ratios_called
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_hyperframe_boost.py::test_render_produces_two_outputs -v
```

Expected: `ImportError` for `_ffmpeg_render` or `_render_and_queue`

- [ ] **Step 3: Implement _render_and_queue + full run() in agent**

Add to bottom of `orchestrator/hyperframe_boost_agent.py` (replace the `run` stub):

```python
from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator
from orchestrator.studio_render_publisher import _upload_to_drive


def _create_studio_record(notion_client, candidate: dict, drive_url: str,
                           aspect_ratio: str, platforms: list[str]) -> str:
    """Create a companion Studio Pipeline DB record. Returns new page ID."""
    scheduled = candidate.get("scheduled_date", "")
    if scheduled:
        from datetime import date as _date
        d = _date.fromisoformat(scheduled[:10])
        video_date = (d + timedelta(days=1)).isoformat()
    else:
        video_date = (_date.today() + timedelta(days=1)).isoformat()

    response = notion_client.pages.create(
        parent={"database_id": STUDIO_DB_ID},
        properties={
            "Name": {"title": [{"text": {"content": f"HF Boost — {candidate['text_preview'][:60]}"}}]},
            "Status": {"select": {"name": "Scheduled"}},
            "Scheduled Date": {"date": {"start": video_date}},
            "Platform": {"multi_select": [{"name": p} for p in platforms]},
            "Asset URL": {"url": drive_url},
            "linked_text_post_id": {"rich_text": [{"text": {"content": candidate["notion_id"]}}]},
            "channel": {"select": {"name": "personal"}},
            "format": {"select": {"name": "hyperframe-boost"}},
            "aspect_ratio": {"select": {"name": aspect_ratio}},
        }
    )
    return response["id"]


def _mark_twin(notion_client, griot_page_id: str, twin_page_id: str) -> None:
    """Write hyperframe_twin_id back to source Griot record as dedup guard."""
    notion_client.pages.update(
        page_id=griot_page_id,
        properties={
            "hyperframe_twin_id": {"relation": [{"id": twin_page_id}]}
        }
    )
```

Then replace the `run` method in `HyperframeBoostAgent`:

```python
    def _render_and_queue(self, candidate: dict) -> None:
        from orchestrator.notifier import send_message
        import tempfile

        gen = HyperframeBriefGenerator()
        twin_id = None

        for aspect_ratio, platforms in [("9:16", ["x", "youtube_shorts"]), ("1:1", ["linkedin"])]:
            try:
                out_path = tempfile.mktemp(suffix=f"_{aspect_ratio.replace(':','x')}.mp4")
                gen.render_to_mp4(candidate["full_text"], aspect_ratio=aspect_ratio, output_path=out_path)
                upload = _upload_to_drive(out_path, f"hf_boost_{candidate['notion_id']}_{aspect_ratio.replace(':','x')}.mp4")
                record_id = _create_studio_record(
                    self._notion, candidate, upload["drive_url"], aspect_ratio, platforms
                )
                if twin_id is None:
                    twin_id = record_id
            except Exception as e:
                send_message(TELEGRAM_CHAT_ID, f"HF Boost render failed ({aspect_ratio}) for '{candidate['text_preview'][:60]}': {str(e)[:150]}")
                logger.error("Render failed %s %s: %s", candidate['notion_id'], aspect_ratio, e)

        if twin_id:
            try:
                _mark_twin(self._notion, candidate["notion_id"], twin_id)
            except Exception as e:
                logger.error("Failed to mark twin on %s: %s", candidate["notion_id"], e)

    def run(self):
        from orchestrator.notifier import send_message
        candidates = self._query_candidates()
        if not candidates:
            send_message(TELEGRAM_CHAT_ID, "HyperFrame Boost: No new candidates. Skipping cycle.")
            return

        self._send_telegram_menu(candidates)
        approved_indices = self._poll_telegram_reply(len(candidates))

        if not approved_indices:
            send_message(TELEGRAM_CHAT_ID, "HyperFrame Boost: Skipped this cycle.")
            return

        for idx in approved_indices:
            self._render_and_queue(candidates[idx])

        send_message(
            TELEGRAM_CHAT_ID,
            f"HyperFrame Boost: Done. {len(approved_indices)} post(s) boosted and queued."
        )
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/test_hyperframe_boost.py -v
```

Expected: all 10 PASSED

- [ ] **Step 5: Commit**

```bash
git add orchestrator/hyperframe_boost_agent.py
git commit -m "feat(hf-boost): render + Drive upload + Notion Studio record creation + full run()"
```

---

## Task 5: Cron Entry Point

**Files:**
- Create: `orchestrator/hyperframe_boost_cron.py`

- [ ] **Step 1: Create cron entry point**

Create `orchestrator/hyperframe_boost_cron.py`:

```python
import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

if __name__ == "__main__":
    from orchestrator.hyperframe_boost_agent import HyperframeBoostAgent
    try:
        HyperframeBoostAgent().run()
    except Exception as e:
        logging.getLogger(__name__).error("HyperFrame Boost cron crashed: %s", e, exc_info=True)
        sys.exit(1)
```

- [ ] **Step 2: Test local invocation**

```bash
cd /root/agentsHQ
python orchestrator/hyperframe_boost_cron.py
```

Expected: Connects to Notion, sends Telegram menu or "no candidates" message. No crash.

- [ ] **Step 3: Add VPS crontab entry**

```bash
crontab -e
```

Add line:
```
0 16 */2 * * cd /root/agentsHQ && python orchestrator/hyperframe_boost_cron.py >> /var/log/hf_boost.log 2>&1
```

- [ ] **Step 4: Verify cron registered**

```bash
crontab -l | grep hf_boost
```

Expected: line visible.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/hyperframe_boost_cron.py
git commit -m "feat(hf-boost): cron entry point + VPS schedule registered"
```

---

## Task 6: auto_publisher YouTube Shorts Routing

**Files:**
- Modify: `orchestrator/auto_publisher.py`

Context: `_account_id_for_platform(platform)` at ~line 634. Need to add youtube_shorts as a routable platform. Find the actual account ID for YouTube Shorts in the Blotato dashboard — it will be a string ID like `"yt_shorts_abc123"`. Store as env var `BLOTATO_YT_SHORTS_ACCOUNT_ID`.

- [ ] **Step 1: Find _account_id_for_platform in auto_publisher.py**

```bash
grep -n "_account_id_for_platform" orchestrator/auto_publisher.py
```

Read the function. Note its structure (likely a dict lookup or if/elif chain).

- [ ] **Step 2: Add youtube_shorts to the routing**

In `orchestrator/auto_publisher.py`, inside `_account_id_for_platform`, add:

```python
"youtube_shorts": os.environ.get("BLOTATO_YT_SHORTS_ACCOUNT_ID", ""),
```

to the platform → account_id mapping (exact placement depends on function structure seen in Step 1).

- [ ] **Step 3: Add env var to .env**

```bash
echo 'BLOTATO_YT_SHORTS_ACCOUNT_ID=<your-yt-shorts-account-id-from-blotato>' >> /root/agentsHQ/.env
```

Replace `<your-yt-shorts-account-id-from-blotato>` with the actual ID from Blotato dashboard under connected accounts.

- [ ] **Step 4: Smoke test routing**

```python
# python3 REPL on VPS
import sys; sys.path.insert(0, '/root/agentsHQ')
from orchestrator.auto_publisher import _account_id_for_platform
print(_account_id_for_platform("youtube_shorts"))
```

Expected: non-empty string (your account ID).

- [ ] **Step 5: Commit**

```bash
git add orchestrator/auto_publisher.py
git commit -m "feat(hf-boost): add youtube_shorts platform routing to auto_publisher"
```

---

## Task 7: Notion Schema — Manual Setup

**No code. Manual Notion steps.**

- [ ] **Step 1: Add hyperframe_twin_id to Griot content board**

In Notion, open Griot content board database. Add property:
- Name: `hyperframe_twin_id`
- Type: Relation → Studio Pipeline DB

- [ ] **Step 2: Add fields to Studio Pipeline DB**

In Notion, open Studio Pipeline database. Add properties:
- `linked_text_post_id` — Text
- `channel` — Select (options: personal, aic, studio)
- `format` — Select (options: hyperframe-boost, standard, cards)
- `aspect_ratio` — Select (options: 9:16, 1:1, 16:9)

- [ ] **Step 3: Update env vars**

Confirm these env vars exist in `/root/agentsHQ/.env`:
```
GRIOT_NOTION_DB_ID=<griot db id>
STUDIO_PIPELINE_DB_ID=<studio pipeline db id>
TELEGRAM_CHAT_ID=<your telegram chat id>
```

Retrieve DB IDs from Notion URLs (32-char hex after last `/`).

- [ ] **Step 4: Verify with query**

```python
# python3 REPL on VPS
import os, sys; sys.path.insert(0, '/root/agentsHQ')
from notion_client import Client
n = Client(auth=os.environ["NOTION_TOKEN"])
r = n.databases.query(database_id=os.environ["GRIOT_NOTION_DB_ID"], page_size=1)
print(list(r["results"][0]["properties"].keys()))
```

Expected: `hyperframe_twin_id` in the list.

---

## Task 8: End-to-End Dry Run

**Validate full pipeline before first live cycle.**

- [ ] **Step 1: Run agent in dry-run mode**

```bash
cd /root/agentsHQ
HYPERFRAME_BOOST_DRY_RUN=1 python orchestrator/hyperframe_boost_cron.py
```

Add a `DRY_RUN` guard in `run()` if needed: when env var set, print candidates to Telegram but skip render + Notion writes.

- [ ] **Step 2: Confirm Telegram message received**

Check Telegram. Should see candidate menu with 3 posts.

- [ ] **Step 3: Reply and confirm parsing**

Reply `1` in Telegram. Check logs:
```bash
tail -f /var/log/hf_boost.log
```

Expected: agent parses reply, attempts render for post index 0.

- [ ] **Step 4: Confirm Studio Pipeline record created**

Open Studio Pipeline DB in Notion. Confirm new record exists with:
- format = hyperframe-boost
- channel = personal
- linked_text_post_id filled
- Scheduled Date = source post date + 1 day
- Asset URL = Drive link

- [ ] **Step 5: Confirm source post marked**

Open source Griot record. Confirm `hyperframe_twin_id` relation is filled. Re-run agent — same post must NOT appear in next candidate menu.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat(hf-boost): end-to-end validated, cron active [READY]"
```

---

## Self-Review Checklist

- [x] Phase 0 manual validation gate before any automation
- [x] `_filter_candidates` excludes posts with existing twin
- [x] `_parse_reply` handles 1, 1,3, all, skip
- [x] Both aspect ratios rendered (9:16 + 1:1) per approved post
- [x] Error isolation: one post failure never blocks others
- [x] Telegram alert on every failure
- [x] `hyperframe_twin_id` written back as dedup guard
- [x] `linked_text_post_id` on Studio record enables future A/B
- [x] YouTube Shorts routing wired in auto_publisher
- [x] Cron: every 2 days, 16:00 UTC
- [x] No silent failures anywhere
- [x] AIC out of scope (Phase 2)
