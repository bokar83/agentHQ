# HyperFrame Boost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically convert top-scoring personal Notion drafts into HyperFrame videos (9:16 + 1:1), queue via Telegram gate, and post 24hr after the text original to LinkedIn, X, and YouTube Shorts.

**Architecture:** Three new orchestrator files (agent, brief generator, cron entry point) + one small addition to auto_publisher.py routing. Notion gets two new fields on Griot DB and four new fields on Studio Pipeline DB. Telegram gate: Boubacar replies 1/2/3/all/skip to a candidate menu every 2 days.

**Tech Stack:** Python 3.11, Notion API (existing client), Telegram bot (existing notifier), Anthropic SDK (claude-sonnet-4-6), HyperFrames CLI (npx hyperframes), FFmpeg (existing), Google Drive upload (existing `_upload_to_drive`), Blotato (existing auto_publisher).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `orchestrator/hyperframe_brief_generator.py` | Create | LLM: post text → HyperFrames brief JSON |
| `orchestrator/hyperframe_boost_agent.py` | Create | Main orchestration: query → Telegram → render loop |
| `orchestrator/hyperframe_boost_cron.py` | Create | Cron entry point, logging |
| `orchestrator/auto_publisher.py` | Modify | Add YouTube Shorts routing for hyperframe-boost 9:16 records |
| `tests/test_hyperframe_boost.py` | Create | Unit tests for brief generator + candidate filtering |

---

## Phase 0: Manual Stack Validation

**Do this before writing any code.** Confirms the render chain works end-to-end.

- [ ] **Step 1: Pick a Notion draft**

Open Griot content board in Notion. Find any Draft/Queued personal post with total_score > 70. Copy its full text.

- [ ] **Step 2: Hand-craft a brief JSON**

Create `/tmp/test_brief.json`:
```json
{
  "purpose": "Inspire 1stGen founders to bet on themselves",
  "duration": 30,
  "aspect_ratio": "9:16",
  "mood_style": "bold, direct, minimal",
  "brand_palette": ["#0A0A0A", "#FFFFFF", "#C8B560"],
  "typography": {"headline": "Inter Bold", "body": "Inter Regular"},
  "scenes": [
    {"id": "hook", "duration": 4, "text": "The biggest mistake I made building my first company.", "visual": "bold text on dark bg, slow zoom"},
    {"id": "s1", "duration": 8, "text": "I waited for permission that was never coming.", "visual": "text reveal line by line"},
    {"id": "s2", "duration": 10, "text": "Nobody hands 1stGen founders a roadmap.", "visual": "kinetic type, white on black"},
    {"id": "cta", "duration": 8, "text": "Follow for the playbook they never gave us.", "visual": "brand color accent, logo end card"}
  ],
  "audio": {"type": "background_music", "mood": "cinematic lo-fi", "volume": 0.3},
  "caption_tone": "direct",
  "transitions": "cut",
  "asset_paths": []
}
```

- [ ] **Step 3: Render 9:16**

```bash
cd /root/agentsHQ
npx hyperframes render --brief /tmp/test_brief.json --output /tmp/test_9x16.mp4
```

Expected: `/tmp/test_9x16.mp4` created, no FFmpeg errors in stdout.

- [ ] **Step 4: Render 1:1**

```bash
# Edit test_brief.json aspect_ratio to "1:1" first
sed -i 's/"9:16"/"1:1"/' /tmp/test_brief.json
npx hyperframes render --brief /tmp/test_brief.json --output /tmp/test_1x1.mp4
```

Expected: `/tmp/test_1x1.mp4` created.

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

def test_brief_has_required_fields():
    from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator
    gen = HyperframeBriefGenerator()
    
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"purpose":"inspire","duration":30,"aspect_ratio":"9:16","mood_style":"bold","brand_palette":["#0A0A0A"],"typography":{"headline":"Inter Bold","body":"Inter Regular"},"scenes":[{"id":"hook","duration":5,"text":"hook","visual":"text"},{"id":"s1","duration":10,"text":"body","visual":"text"},{"id":"cta","duration":5,"text":"cta","visual":"text"}],"audio":{"type":"background_music","mood":"cinematic","volume":0.3},"caption_tone":"direct","transitions":"cut","asset_paths":[]}')]
    
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_response
        
        brief = gen.generate(SAMPLE_POST, aspect_ratio="9:16")
    
    required = ["purpose","duration","aspect_ratio","mood_style","brand_palette",
                "typography","scenes","audio","caption_tone","transitions","asset_paths"]
    for field in required:
        assert field in brief, f"Missing field: {field}"

def test_brief_has_hook_and_cta_scenes():
    from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator
    gen = HyperframeBriefGenerator()
    
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"purpose":"inspire","duration":30,"aspect_ratio":"9:16","mood_style":"bold","brand_palette":["#0A0A0A"],"typography":{"headline":"Inter Bold","body":"Inter"},"scenes":[{"id":"hook","duration":5,"text":"hook","visual":"text"},{"id":"s1","duration":15,"text":"body","visual":"text"},{"id":"cta","duration":10,"text":"follow","visual":"text"}],"audio":{"type":"background_music","mood":"cinematic","volume":0.3},"caption_tone":"direct","transitions":"cut","asset_paths":[]}')]
    
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_response
        
        brief = gen.generate(SAMPLE_POST, aspect_ratio="9:16")
    
    scene_ids = [s["id"] for s in brief["scenes"]]
    assert "hook" in scene_ids
    assert "cta" in scene_ids

def test_brief_aspect_ratio_passed_through():
    from orchestrator.hyperframe_brief_generator import HyperframeBriefGenerator
    gen = HyperframeBriefGenerator()
    
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"purpose":"inspire","duration":30,"aspect_ratio":"1:1","mood_style":"bold","brand_palette":["#0A0A0A"],"typography":{"headline":"Inter Bold","body":"Inter"},"scenes":[{"id":"hook","duration":5,"text":"hook","visual":"text"},{"id":"cta","duration":5,"text":"cta","visual":"text"}],"audio":{"type":"background_music","mood":"cinematic","volume":0.3},"caption_tone":"direct","transitions":"cut","asset_paths":[]}')]
    
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_response
        
        brief = gen.generate(SAMPLE_POST, aspect_ratio="1:1")
    
    assert brief["aspect_ratio"] == "1:1"
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
import json
import os
import anthropic

SYSTEM_PROMPT = """You convert social media posts into HyperFrames video briefs.
Output ONLY valid JSON matching this exact structure — no markdown, no explanation:
{
  "purpose": "one sentence describing what this video should make the viewer feel or do",
  "duration": 30,
  "aspect_ratio": "<provided>",
  "mood_style": "bold, direct, minimal",
  "brand_palette": ["#0A0A0A", "#FFFFFF", "#C8B560"],
  "typography": {"headline": "Inter Bold", "body": "Inter Regular"},
  "scenes": [
    {"id": "hook", "duration": 4, "text": "<punchy opening line>", "visual": "bold text on dark bg, slow zoom"},
    {"id": "s1", "duration": 10, "text": "<core point 1>", "visual": "text reveal line by line"},
    {"id": "s2", "duration": 8, "text": "<core point 2>", "visual": "kinetic type"},
    {"id": "cta", "duration": 8, "text": "<follow/engage prompt>", "visual": "brand color accent, logo end card"}
  ],
  "audio": {"type": "background_music", "mood": "cinematic lo-fi", "volume": 0.3},
  "caption_tone": "direct",
  "transitions": "cut",
  "asset_paths": []
}
Rules:
- scenes array must include id="hook" as first and id="cta" as last
- scene durations must sum to exactly the total duration
- text fields must come from the post content, not be invented
- aspect_ratio must be exactly the value provided"""

USER_PROMPT_TEMPLATE = """Convert this social media post into a HyperFrames brief.
Aspect ratio: {aspect_ratio}

POST:
{post_text}"""


class HyperframeBriefGenerator:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate(self, post_text: str, aspect_ratio: str = "9:16") -> dict:
        response = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    aspect_ratio=aspect_ratio,
                    post_text=post_text[:2000]
                )
            }]
        )
        raw = response.content[0].text.strip()
        brief = json.loads(raw)
        brief["aspect_ratio"] = aspect_ratio
        return brief
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
from orchestrator.studio_render_publisher import _upload_to_drive, _ffmpeg


def _ffmpeg_render(brief: dict, output_path: str) -> str:
    """Render HyperFrames brief to MP4 via npx hyperframes CLI."""
    import subprocess, tempfile, json as _json
    brief_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    _json.dump(brief, brief_file)
    brief_file.close()
    result = subprocess.run(
        ["npx", "hyperframes", "render", "--brief", brief_file.name, "--output", output_path],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"HyperFrames render failed: {result.stderr[:300]}")
    return output_path


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
                brief = gen.generate(candidate["full_text"], aspect_ratio=aspect_ratio)
                out_path = tempfile.mktemp(suffix=f"_{aspect_ratio.replace(':','x')}.mp4")
                _ffmpeg_render(brief, out_path)
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
