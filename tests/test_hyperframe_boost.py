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


def test_query_candidates_returns_top3():
    from orchestrator.hyperframe_boost_agent import HyperframeBoostAgent
    import unittest.mock as mock

    fake_pages = [
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

    agent = HyperframeBoostAgent.__new__(HyperframeBoostAgent)

    with mock.patch.object(agent, '_notion_query', return_value=fake_pages):
        candidates = agent._query_candidates()

    assert len(candidates) == 3
    assert candidates[0]["total_score"] >= candidates[1]["total_score"]
