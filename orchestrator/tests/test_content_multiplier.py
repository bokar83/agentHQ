from __future__ import annotations

import json
import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


class _Resp:
    def __init__(self, content: str):
        self.choices = [MagicMock(message=MagicMock(content=content))]


def test_lens_classify_parses_json(monkeypatch):
    import content_multiplier_crew as crew

    payload = {
        "lenses": ["AI Strategy", "Systems Thinking"],
        "key_claim": "AI exposes broken workflows.",
        "unique_angle": "Most teams need process repair first.",
        "contrarian_read": "The tool is not the bottleneck.",
        "who_is_stuck": "Operators are stuck.",
        "channel_fit": ["AIC", "Boubacar-personal"],
        "skip_reason": "",
    }
    mock_llm = types.ModuleType("llm_helpers")
    mock_llm.call_llm = MagicMock(return_value=_Resp("```json\n" + json.dumps(payload) + "\n```"))

    with patch.dict("sys.modules", {"llm_helpers": mock_llm}):
        doc = crew.SourceDoc("Test", "text", "AI and operations", "raw text")
        result = crew.classify_lens(doc)

    assert result["lenses"] == ["AI Strategy", "Systems Thinking"]
    assert result["channel_fit"] == ["AIC", "Boubacar-personal"]
    mock_llm.call_llm.assert_called_once()


def test_piece_routing_channel_aware():
    import content_multiplier_crew as crew

    lens = {"channel_fit": ["UTB", "AIC"]}
    plans = crew.build_piece_plans(lens)

    assert [p.piece_type for p in plans] == ["video-UTB", "video-AIC", "quote", "newsletter"]
    assert all(p.number not in (1, 2, 3, 4, 5, 6) for p in plans)


def test_piece_routing_personal_plus_fgm_target_filter():
    import content_multiplier_crew as crew

    lens = {"channel_fit": ["Boubacar-personal", "FGM", "UTB"]}
    plans = crew.build_piece_plans(lens, target_channels=["Boubacar-personal", "FGM"])
    piece_types = [p.piece_type for p in plans]

    assert piece_types[:6] == ["LI-long", "X-thread", "X-single", "direct", "adjacent", "contrarian"]
    assert "video-FGM" in piece_types
    assert "video-UTB" not in piece_types


def test_ctq_regex_and_word_filters():
    import content_multiplier_crew as crew

    assert crew.ctq_reject_reason("Bad -- dash") == "dash pattern"
    assert crew.ctq_reject_reason("Bad \u2014 dash") == "dash pattern"
    assert crew.ctq_reject_reason("FGM is here") == "FGM acronym"
    assert crew.ctq_reject_reason("1stGen Money is here") is None
    assert crew.ctq_reject_reason("Use Loom for this") == "banned word: Loom"
    assert crew.ctq_reject_reason("This one weird trick works") == "banned word: one weird trick"


def test_cost_cap_hard_fails_before_sonnet_call():
    import content_multiplier_crew as crew

    guard = crew.CostGuard(cap_usd=0.01)
    with pytest.raises(crew.CostCapExceeded):
        guard.reserve_sonnet("x" * 100_000, output_tokens=800)


def test_multiply_source_writes_notion_and_sends_review(monkeypatch):
    import content_multiplier_crew as crew

    lens = {
        "lenses": ["AI Strategy"],
        "key_claim": "AI exposes weak workflows.",
        "unique_angle": "Repair the workflow before buying tools.",
        "contrarian_read": "The tool is not the bottleneck.",
        "who_is_stuck": "Operators",
        "channel_fit": ["Boubacar-personal"],
        "skip_reason": "",
    }

    def fake_call_llm(messages, **kwargs):
        if kwargs["model"] == crew.LENS_MODEL:
            return _Resp(json.dumps(lens))
        return _Resp("Strong hook\n\nDraft body for review.")

    mock_llm = types.ModuleType("llm_helpers")
    mock_llm.call_llm = MagicMock(side_effect=fake_call_llm)

    notion = MagicMock()
    notion.get_database_schema.return_value = {
        name: {}
        for name in (
            "Title",
            "Status",
            "Platform",
            "Topic",
            "Draft",
            "Hook",
            "Source URL",
            "Multiplier Run ID",
            "Piece Type",
            "Created From",
        )
    }
    notion.create_page.return_value = {"id": "page-id"}

    with patch.dict("sys.modules", {"llm_helpers": mock_llm}), \
         patch.object(crew, "_notion_client", return_value=notion), \
         patch.object(crew, "_send_batch_review", return_value=True), \
         patch.object(crew, "time") as mock_time:
        mock_time.time.return_value = 1770000000
        result = crew.multiply_source("raw source text", source_type="text")

    assert result["run_id"].endswith("_1770000000")
    assert result["pieces_written"] == 8
    assert result["pieces_dropped"] == 0
    assert result["telegram_sent"] is True
    assert result["mode"] == "verbatim"
    assert notion.create_page.call_count == 8
    assert mock_llm.call_llm.call_count == 9


# ─── Remix mode tests (added 2026-05-07) ──────────────────────────────────────

def _verbatim_lens():
    return {
        "lenses": ["AI Strategy"],
        "key_claim": "AI exposes weak workflows.",
        "unique_angle": "Repair the workflow before buying tools.",
        "contrarian_read": "The tool is not the bottleneck.",
        "who_is_stuck": "Operators",
        "channel_fit": ["Boubacar-personal"],
        "skip_reason": "",
    }


def _full_schema():
    return {
        name: {}
        for name in (
            "Title", "Status", "Platform", "Topic", "Draft", "Hook",
            "Source URL", "Multiplier Run ID", "Piece Type",
            "Source Treatment", "Created From",
        )
    }


def test_ctq_remix_rejects_source_url_leak():
    import content_multiplier_crew as crew

    body = "Boubacar's take. See https://example.com/source for more."
    reason = crew.ctq_reject_reason(
        body, mode="remix", forbidden_url="https://example.com/source"
    )
    assert reason == "remix leaked source URL"


def test_ctq_remix_rejects_forbidden_strip():
    import content_multiplier_crew as crew

    body = "Most agencies will tell you 78% of teams are unprepared."
    reason = crew.ctq_reject_reason(
        body, mode="remix", forbidden_strips=["78% of teams are unprepared"]
    )
    assert reason == "remix reproduced forbidden strip"


def test_ctq_verbatim_allows_source_url_in_body():
    import content_multiplier_crew as crew

    body = "Source: https://example.com/source"
    assert crew.ctq_reject_reason(body, mode="verbatim", forbidden_url="https://example.com/source") is None


def test_remix_mode_strips_url_from_notion_record(monkeypatch):
    """Remix mode must NOT write source_url into the Notion record's URL property."""
    import content_multiplier_crew as crew

    def fake_call_llm(messages, **kwargs):
        if kwargs["model"] == crew.LENS_MODEL:
            return _Resp(json.dumps(_verbatim_lens()))
        return _Resp("Boubacar hook\n\nClean original take.")

    mock_llm = types.ModuleType("llm_helpers")
    mock_llm.call_llm = MagicMock(side_effect=fake_call_llm)

    notion = MagicMock()
    notion.get_database_schema.return_value = _full_schema()
    notion.create_page.return_value = {"id": "page-id"}

    with patch.dict("sys.modules", {"llm_helpers": mock_llm}), \
         patch.object(crew, "_notion_client", return_value=notion), \
         patch.object(crew, "_send_batch_review", return_value=True), \
         patch.object(crew, "time") as mock_time:
        mock_time.time.return_value = 1770000000
        result = crew.multiply_source(
            "https://example.com/article",
            source_type="text",
            mode="remix",
            remix_notes={
                "fixable_strips": ["fabricated quote"],
                "concept_to_keep": "ops repair before tools",
                "remix_hint": "frame as Boubacar's POV",
            },
        )

    assert result["mode"] == "remix"
    assert result["pieces_written"] >= 1
    # Inspect first create_page call -- Source URL property must be empty / None.
    first_call = notion.create_page.call_args_list[0]
    props = first_call.kwargs["properties"]
    if "Source URL" in props:
        assert props["Source URL"]["url"] is None
    if "Source Treatment" in props:
        assert props["Source Treatment"]["select"]["name"] == "remix"


def test_auto_mode_qa_failed_aborts():
    import content_multiplier_crew as crew

    result = crew.multiply_source(
        "https://example.com/x",
        source_type="text",
        mode="auto",
        qa_verdict="qa-failed",
    )
    assert result["pieces_written"] == 0
    assert result["skip_reason"] == "qa-failed"
    assert result["mode"] == "auto"


def test_auto_mode_qa_remix_routes_to_remix(monkeypatch):
    import content_multiplier_crew as crew

    def fake_call_llm(messages, **kwargs):
        if kwargs["model"] == crew.LENS_MODEL:
            return _Resp(json.dumps(_verbatim_lens()))
        return _Resp("Hook line\n\nBody.")

    mock_llm = types.ModuleType("llm_helpers")
    mock_llm.call_llm = MagicMock(side_effect=fake_call_llm)

    notion = MagicMock()
    notion.get_database_schema.return_value = _full_schema()
    notion.create_page.return_value = {"id": "page-id"}

    with patch.dict("sys.modules", {"llm_helpers": mock_llm}), \
         patch.object(crew, "_notion_client", return_value=notion), \
         patch.object(crew, "_send_batch_review", return_value=True):
        result = crew.multiply_source(
            "https://example.com/x",
            source_type="text",
            mode="auto",
            qa_verdict="qa-remix",
            remix_notes={
                "fixable_strips": [],
                "concept_to_keep": "core idea",
                "remix_hint": "",
            },
        )

    assert result["mode"] == "remix"


def test_invalid_mode_raises():
    import content_multiplier_crew as crew

    with pytest.raises(ValueError):
        crew.multiply_source("text", mode="bogus")
