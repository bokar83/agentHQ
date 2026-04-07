import sys
sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")

from router import _keyword_shortcut


def test_notion_capture_shortcut_add_to_ideas():
    result = _keyword_shortcut("Add to my ideas list a new concept about AI")
    assert result == "notion_capture"


def test_notion_capture_shortcut_remember_this():
    result = _keyword_shortcut("remember this for later: build a voice coach app")
    assert result == "notion_capture"


def test_notion_capture_shortcut_review_ideas():
    result = _keyword_shortcut("review my ideas")
    assert result == "notion_capture"


def test_notion_capture_shortcut_brain_dump():
    result = _keyword_shortcut("brain dump: I want to build a client dashboard")
    assert result == "notion_capture"


def test_gws_shortcut_calendar_short():
    result = _keyword_shortcut("what's on my calendar today")
    assert result == "gws_task"


def test_gws_shortcut_add_event():
    result = _keyword_shortcut("add event tomorrow 3pm team call")
    assert result == "gws_task"


def test_gws_shortcut_delete_event():
    result = _keyword_shortcut("delete event rdfddvtvdt")
    assert result == "gws_task"


def test_enrich_leads_still_works():
    result = _keyword_shortcut("enrich leads")
    assert result == "enrich_leads"


def test_memory_capture_shortcut():
    result = _keyword_shortcut("save this to memory: my brand colors are teal and orange")
    assert result == "memory_capture"
