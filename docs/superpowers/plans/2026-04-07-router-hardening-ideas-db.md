# Router Hardening + agentsHQ Ideas Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the router so task-like messages never silently fall through to chat, add a Notion Ideas database for brain dumps, and wire compound "do X then email me" requests end-to-end.

**Architecture:** A new `_shortcut_classify()` function runs before the obvious-chat pre-filter in the Telegram handler and API endpoint, catching GWS/notion/memory phrases before they're eaten. A new `notion_capture` crew writes to and reads from a fixed-ID Notion database. Compound request metadata flows from the router through to `_run_background_job()` which fires a follow-up GWS draft after any primary crew completes.

**Tech Stack:** Python 3.11, CrewAI, Notion API v1 (httpx), FastAPI, Docker (orc-crewai container on VPS 72.60.209.109)

---

## File Map

| File | Role |
|---|---|
| `orchestrator/router.py` | Add `notion_capture` type, GWS shortcuts, compound metadata, routing rule |
| `orchestrator/orchestrator.py` | Add `_shortcut_classify()`, wire pre-filter bypass, post-crew email hook, save_memory chat tool |
| `orchestrator/tools.py` | Add `NotionCreateIdeaTool`, `NotionQueryIdeasTool`, `NOTION_CAPTURE_TOOLS`, `SaveMemoryTool` |
| `orchestrator/crews.py` | Add `build_notion_capture_crew()`, register it |
| `orchestrator/agents.py` | Add `build_notion_capture_agent()` |
| `orchestrator/notifier.py` | Add `notion_capture` labels |
| `skills/notion_skill/notion_tool.py` | Add `create_database()`, `query_database()` |
| `scripts/bootstrap_ideas_db.py` | One-time DB creation + seeding |
| `docker-compose.yml` | Pass `IDEAS_DB_ID` env var |

---

## Task 1: Extend `notion_tool.py` with `create_database` and `query_database`

**Files:**
- Modify: `skills/notion_skill/notion_tool.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_notion_tool.py`:

```python
import os, pytest
os.environ["NOTION_SECRET"] = "fake_token_for_testing"  # pragma: allowlist secret

from unittest.mock import patch, MagicMock


def test_query_database_returns_results():
    from skills.notion_skill.notion_tool import query_database
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": [{"id": "abc", "properties": {"Name": {"title": [{"plain_text": "Test Idea"}]}}}]}
    mock_resp.raise_for_status = lambda: None
    with patch("httpx.post", return_value=mock_resp):
        results = query_database("fake-db-id")
    assert len(results) == 1
    assert results[0]["id"] == "abc"


def test_create_database_returns_id():
    from skills.notion_skill.notion_tool import create_database
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": "new-db-id-123", "url": "https://notion.so/new-db-id-123"}
    mock_resp.raise_for_status = lambda: None
    with patch("httpx.post", return_value=mock_resp):
        result = create_database("parent-page-id", "agentsHQ Ideas")
    assert result["id"] == "new-db-id-123"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd d:/Ai_Sandbox/agentsHQ
python -m pytest tests/test_notion_tool.py -v 2>&1 | head -30
```

Expected: `ImportError` or `AttributeError` — functions don't exist yet.

- [ ] **Step 3: Add `create_database` and `query_database` to `notion_tool.py`**

Append to `skills/notion_skill/notion_tool.py` after the existing `append_block` function:

```python
def create_database(parent_page_id: str, title: str) -> dict:
    """Create a new Notion database under the given parent page."""
    headers = get_notion_headers()
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": {
            "Name": {"title": {}},
            "Content": {"rich_text": {}},
            "Source": {
                "select": {
                    "options": [
                        {"name": "Telegram", "color": "blue"},
                        {"name": "Manual", "color": "gray"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "New", "color": "green"},
                        {"name": "Reviewed", "color": "yellow"},
                        {"name": "Archived", "color": "gray"},
                    ]
                }
            },
            "Category": {
                "select": {
                    "options": [
                        {"name": "Tool", "color": "purple"},
                        {"name": "Agent", "color": "blue"},
                        {"name": "Feature", "color": "orange"},
                        {"name": "Business", "color": "red"},
                        {"name": "Personal", "color": "pink"},
                    ]
                }
            },
            "Created": {"date": {}},
        },
    }
    r = httpx.post("https://api.notion.com/v1/databases", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def query_database(database_id: str, filter: dict = None, sorts: list = None) -> list:
    """Query records from a Notion database. Returns list of page objects."""
    headers = get_notion_headers()
    payload = {}
    if filter:
        payload["filter"] = filter
    if sorts:
        payload["sorts"] = sorts
    else:
        payload["sorts"] = [{"property": "Created", "direction": "descending"}]
    r = httpx.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=headers,
        json=payload,
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def create_idea_page(database_id: str, title: str, content: str, category: str = "Feature") -> str:
    """Create a new idea page in the Ideas database. Returns the Notion URL."""
    from datetime import date
    headers = get_notion_headers()
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},
            "Source": {"select": {"name": "Telegram"}},
            "Status": {"select": {"name": "New"}},
            "Category": {"select": {"name": category}},
            "Created": {"date": {"start": date.today().isoformat()}},
        },
    }
    r = httpx.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return r.json().get("url", "")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_notion_tool.py -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add skills/notion_skill/notion_tool.py tests/test_notion_tool.py
git commit -m "feat: add create_database, query_database, create_idea_page to notion_tool"
```

---

## Task 2: Add Notion Capture Tools to `tools.py`

**Files:**
- Modify: `orchestrator/tools.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_notion_tool.py`:

```python
def test_notion_create_idea_tool_requires_env():
    """NotionCreateIdeaTool returns error string if IDEAS_DB_ID not set."""
    import importlib
    import sys
    # Remove cached module if present
    for mod in list(sys.modules.keys()):
        if "tools" in mod and "orchestrator" not in mod:
            pass
    os.environ.pop("IDEAS_DB_ID", None)
    from orchestrator.tools import NotionCreateIdeaTool
    tool = NotionCreateIdeaTool()
    result = tool._run('{"title": "Test", "content": "Hello"}')
    assert "IDEAS_DB_ID" in result or "Error" in result
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/test_notion_tool.py::test_notion_create_idea_tool_requires_env -v
```

Expected: ImportError or AttributeError.

- [ ] **Step 3: Add tools to `orchestrator/tools.py`**

After the `NotionPageTool` class (around line 1028), add:

```python
class NotionCreateIdeaTool(BaseTool):
    """Creates a new idea record in the agentsHQ Ideas Notion database."""
    name: str = "create_notion_idea"
    description: str = (
        "Save a new idea or brain dump to the agentsHQ Ideas database in Notion. "
        "Input: JSON with 'title' (string, short name for the idea), "
        "'content' (string, full description), "
        "and optional 'category' (Tool|Agent|Feature|Business|Personal, default: Feature)."
    )

    def _run(self, input_data: str) -> str:
        db_id = os.environ.get("IDEAS_DB_ID", "")
        if not db_id:
            return "Error: IDEAS_DB_ID env var not set. Run scripts/bootstrap_ideas_db.py first."
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            title = data.get("title", "Untitled Idea")
            content = data.get("content", "")
            category = data.get("category", "Feature")
            from skills.notion_skill.notion_tool import create_idea_page
            url = create_idea_page(db_id, title, content, category)
            return f"Idea saved to Notion: '{title}' — {url}"
        except Exception as e:
            return f"Error saving idea: {e}"


class NotionQueryIdeasTool(BaseTool):
    """Queries the agentsHQ Ideas Notion database and returns recent entries."""
    name: str = "query_notion_ideas"
    description: str = (
        "Read ideas from the agentsHQ Ideas database. "
        "Input: optional JSON with 'status' filter (New|Reviewed|Archived) "
        "and 'limit' (default 20). Returns formatted list of ideas."
    )

    def _run(self, input_data: str = "{}") -> str:
        db_id = os.environ.get("IDEAS_DB_ID", "")
        if not db_id:
            return "Error: IDEAS_DB_ID env var not set. Run scripts/bootstrap_ideas_db.py first."
        try:
            data = {}
            if input_data:
                try:
                    data = json.loads(input_data) if isinstance(input_data, str) else input_data
                except Exception:
                    pass
            from skills.notion_skill.notion_tool import query_database
            filter_obj = None
            if data.get("status"):
                filter_obj = {
                    "property": "Status",
                    "select": {"equals": data["status"]},
                }
            results = query_database(db_id, filter=filter_obj)
            if not results:
                return "No ideas found in the database."
            limit = int(data.get("limit", 20))
            lines = [f"agentsHQ Ideas ({len(results[:limit])} entries):\n"]
            for r in results[:limit]:
                props = r.get("properties", {})
                name = ""
                name_prop = props.get("Name", {}).get("title", [])
                if name_prop:
                    name = name_prop[0].get("plain_text", "Untitled")
                content_prop = props.get("Content", {}).get("rich_text", [])
                content = content_prop[0].get("plain_text", "")[:200] if content_prop else ""
                status = props.get("Status", {}).get("select", {})
                status_name = status.get("name", "New") if status else "New"
                category = props.get("Category", {}).get("select", {})
                category_name = category.get("name", "") if category else ""
                lines.append(f"- [{status_name}] {name} ({category_name})")
                if content:
                    lines.append(f"  {content}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error querying ideas: {e}"


NOTION_CAPTURE_TOOLS = [NotionCreateIdeaTool(), NotionQueryIdeasTool()]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_notion_tool.py::test_notion_create_idea_tool_requires_env -v
```

Expected: PASSED.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/tools.py tests/test_notion_tool.py
git commit -m "feat: add NotionCreateIdeaTool, NotionQueryIdeasTool, NOTION_CAPTURE_TOOLS"
```

---

## Task 3: Add `SaveMemoryTool` to Chat's Function-Call Tool List

**Files:**
- Modify: `orchestrator/orchestrator.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_chat_memory_tool.py`:

```python
import os, sys
sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
os.environ.setdefault("NOTION_SECRET", "fake")
os.environ.setdefault("OPENROUTER_API_KEY", "fake")

from unittest.mock import patch, MagicMock


def test_save_memory_tool_in_chat_tools():
    """run_chat() tool list must include save_memory function."""
    import orchestrator
    # Inspect the tools list defined inside run_chat via source inspection
    import inspect
    src = inspect.getsource(orchestrator.run_chat)
    assert "save_memory" in src, "save_memory tool not found in run_chat tool definitions"
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd d:/Ai_Sandbox/agentsHQ
python -m pytest tests/test_chat_memory_tool.py -v
```

Expected: FAILED — "save_memory tool not found".

- [ ] **Step 3: Add `save_memory` tool definition and handler in `run_chat()`**

In `orchestrator/orchestrator.py`, inside `run_chat()`, add to the `tools` list (after the `retrieve_output_file` tool dict, before the closing `]`):

```python
        {
            "type": "function",
            "function": {
                "name": "save_memory",
                "description": (
                    "Persist a fact, preference, or note to long-term memory. "
                    "Call this when the user says 'remember this', 'add to memory', "
                    "'save this', 'store this', 'note this down', or shares information "
                    "they want kept (brand colors, preferences, facts, etc.). "
                    "Do NOT call for ideas — use the crew for that."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "The fact or preference to save, written as a complete sentence."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category label e.g. 'brand', 'preference', 'contact', 'system'."
                        }
                    },
                    "required": ["fact"]
                }
            }
        },
```

In the same `run_chat()` function, inside the tool-call dispatch block (`if fn_name == "query_system"` ... `elif fn_name == "retrieve_output_file"` ...), add:

```python
                elif fn_name == "save_memory":
                    import json as _json
                    args = _json.loads(tool_call.function.arguments or "{}")
                    fact = args.get("fact", "")
                    category = args.get("category", "general")
                    try:
                        from memory import save_conversation_turn, save_to_memory
                        tag = f"[MEMORY:{category.upper()}] {fact}"
                        save_conversation_turn(session_key, "assistant", tag)
                        save_to_memory(
                            task_request=tag,
                            task_type="memory_capture",
                            result_summary=fact,
                            files_created=[],
                            execution_time=0,
                            from_number=session_key,
                        )
                        tool_result = f"Saved to memory: {fact}"
                    except Exception as mem_e:
                        tool_result = f"Memory save failed: {mem_e}"
                    logger.info(f"Chat used save_memory: {fact[:80]}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_chat_memory_tool.py -v
```

Expected: PASSED.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/orchestrator.py tests/test_chat_memory_tool.py
git commit -m "feat: add save_memory function-call tool to run_chat()"
```

---

## Task 4: Add `notion_capture` Task Type and GWS Shortcuts to `router.py`

**Files:**
- Modify: `orchestrator/router.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_router.py`:

```python
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest tests/test_router.py -v
```

Expected: Most FAILED — shortcuts don't exist yet.

- [ ] **Step 3: Add `notion_capture` to `TASK_TYPES` dict**

In `orchestrator/router.py`, add after the `enrich_leads` entry (around line 135):

```python
    "notion_capture": {
        "description": (
            "Capture an idea, brain dump, thought, or note into the agentsHQ Ideas Notion database. "
            "Also handles REVIEWING the ideas list when the user asks to see what's in there. "
            "Use this for: add to ideas, save this idea, note this down, brain dump, capture this thought, "
            "put in my backlog, review my ideas, what ideas do I have. "
            "Do NOT use for redesigning Notion pages — that is notion_overhaul."
        ),
        "keywords": [
            "add to my ideas", "add to ideas", "save this idea", "capture this",
            "note this down", "brain dump", "put in my backlog", "to-dos",
            "ideas list", "review my ideas", "what ideas", "pull up my ideas",
            "remember this for later", "add this idea", "put that in",
        ],
        "crew": "notion_capture_crew",
    },
    "memory_capture": {
        "description": (
            "Save a specific fact, preference, or piece of information to long-term memory. "
            "Use when the user says 'remember this', 'add to memory', 'save this to memory', "
            "'store this', or shares data they want kept (brand colors, preferences, settings). "
            "This is handled in chat mode with the save_memory tool — no crew needed."
        ),
        "keywords": [
            "remember this", "add to memory", "save this to memory", "store this",
            "note this", "keep this in mind", "save to memory",
        ],
        "crew": None,  # handled by chat save_memory tool
    },
```

- [ ] **Step 4: Add shortcuts to `_keyword_shortcut()`**

In `orchestrator/router.py`, inside `_keyword_shortcut()`, add these blocks **before** the existing `enrich_leads` block:

```python
    # notion_capture — add idea, review ideas, brain dump (must run before chat prefix check)
    notion_capture_triggers = [
        "add to my ideas", "add to ideas", "save this idea", "capture this idea",
        "note this down", "brain dump", "put in my backlog", "ideas list",
        "review my ideas", "what ideas do i have", "pull up my ideas",
        "add this to my", "put that in there", "put this in notion",
        "add to my to-do", "add to my todos", "add to my to-dos",
        "remember this for later",
    ]
    if any(t in lower for t in notion_capture_triggers):
        return "notion_capture"

    # memory_capture — save facts/preferences (distinct from ideas)
    memory_capture_triggers = [
        "save this to memory", "add to memory", "remember this:", "store this in memory",
        "keep this in mind", "add to your memory", "save to memory",
        "here are my", "here is my", "these are my",
    ]
    if any(t in lower for t in memory_capture_triggers):
        return "memory_capture"

    # gws_task — calendar and gmail phrases short enough to fool obvious-chat filter
    gws_shortcut_triggers = [
        "what's on my calendar", "whats on my calendar", "what is on my calendar",
        "check my calendar", "show my calendar", "list my events",
        "add event", "add to calendar", "create event", "schedule meeting",
        "delete event", "remove event", "cancel event",
        "draft email", "send email", "email me", "send me an email",
        "check my email", "search my email", "search gmail", "check gmail",
    ]
    if any(t in lower for t in gws_shortcut_triggers):
        return "gws_task"
```

- [ ] **Step 5: Update the LLM routing rule in `classify_task()` prompt**

In `orchestrator/router.py`, inside `classify_task()`, find the `ROUTING RULES:` section in the prompt string and append this rule:

```python
# Find this line in the prompt:
# "- CRITICAL DISTINCTION — hunter_task vs crm_outreach:"
# Add BEFORE that line:

"""- CRITICAL DISTINCTION — notion_overhaul vs notion_capture:
  * notion_overhaul = REDESIGN or RESTRUCTURE an existing Notion page/workspace (visual, layout, style)
  * notion_capture = ADD, SAVE, LOG, or REVIEW ideas/notes/thoughts in the Ideas database
  * "Add to my ideas list", "save this idea", "capture this thought" → notion_capture
  * "Redesign my Notion", "overhaul my workspace", "update the layout" → notion_overhaul
- CRITICAL DISTINCTION — memory_capture vs notion_capture:
  * memory_capture = save a FACT or PREFERENCE to memory (brand colors, settings, preferences)
  * notion_capture = save an IDEA, CONCEPT, or PROJECT THOUGHT to the Ideas database
  * "Remember my brand colors are teal" → memory_capture
  * "Add this app idea to my list" → notion_capture
"""
```

The exact edit to make in the prompt f-string — find the line:
```
- CRITICAL DISTINCTION — hunter_task vs crm_outreach:
```
And insert before it:
```
- CRITICAL DISTINCTION — notion_overhaul vs notion_capture:
  * notion_overhaul = REDESIGN or RESTRUCTURE an existing Notion page/workspace (visual, layout, style)
  * notion_capture = ADD, SAVE, LOG, or REVIEW ideas/notes/thoughts in the Ideas database
  * "Add to my ideas list", "save this idea", "capture this thought" → notion_capture
  * "Redesign my Notion", "overhaul my workspace", "update the layout" → notion_overhaul
- CRITICAL DISTINCTION — memory_capture vs notion_capture:
  * memory_capture = save a FACT or PREFERENCE (brand colors, settings, preferences)
  * notion_capture = save an IDEA, CONCEPT, or PROJECT THOUGHT to the Ideas database
```

- [ ] **Step 6: Add compound-request metadata to `extract_metadata()`**

In `orchestrator/router.py`, update `extract_metadata()`:

```python
EMAIL_FOLLOWUP_TRIGGERS = [
    "send me an email",
    "email me about this",
    "email me a summary",
    "email me the results",
    "send an email",
    "and email me",
    "also email me",
    "email this to me",
    "send this to my email",
    "send to bokar83",
    "send to catalystworks",
]

def extract_metadata(user_request: str) -> dict:
    """
    Extract routing metadata from the raw request string.
    Returns a dict merged into task routing decisions.
    """
    lower = user_request.lower()
    has_email_followup = any(trigger in lower for trigger in EMAIL_FOLLOWUP_TRIGGERS)
    return {
        "high_stakes": any(trigger in lower for trigger in HIGH_STAKES_TRIGGERS),
        "has_email_followup": has_email_followup,
    }
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
python -m pytest tests/test_router.py -v
```

Expected: All 9 PASSED.

- [ ] **Step 8: Commit**

```bash
git add orchestrator/router.py tests/test_router.py
git commit -m "feat: add notion_capture, memory_capture task types + GWS/idea keyword shortcuts + compound email metadata"
```

---

## Task 5: Add `_shortcut_classify()` to `orchestrator.py` and Wire Pre-Filter Bypass

**Files:**
- Modify: `orchestrator/orchestrator.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_chat_memory_tool.py`:

```python
def test_shortcut_classify_notion_capture():
    import orchestrator
    result = orchestrator._shortcut_classify("Add to my ideas list: build a voice coach")
    assert result == "notion_capture"


def test_shortcut_classify_gws_short_message():
    import orchestrator
    result = orchestrator._shortcut_classify("what's on my calendar")
    assert result == "gws_task"


def test_shortcut_classify_returns_none_for_chat():
    import orchestrator
    result = orchestrator._shortcut_classify("hey how are you")
    assert result is None
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest tests/test_chat_memory_tool.py -v -k "shortcut"
```

Expected: FAILED — `_shortcut_classify` doesn't exist.

- [ ] **Step 3: Add `_shortcut_classify()` to `orchestrator.py`**

In `orchestrator/orchestrator.py`, add this function directly above `_classify_obvious_chat()` (around line 872):

```python
def _shortcut_classify(msg: str):
    """
    Run keyword shortcuts BEFORE the obvious-chat pre-filter.
    Returns a task_type string if matched, else None.
    This prevents short messages from being swallowed by _classify_obvious_chat().
    """
    from router import _keyword_shortcut
    return _keyword_shortcut(msg)
```

- [ ] **Step 4: Wire `_shortcut_classify()` into both entry points**

**Entry point 1** — `process_telegram_update()` (around line 916):

Find this block:
```python
    if _classify_obvious_chat(text):
        task_type = "chat"
    else:
        from router import classify_task
        classification = classify_task(text)
        task_type = classification.get("task_type", "unknown")
```

Replace with:
```python
    # Shortcut classify runs FIRST — catches task phrases before obvious-chat filter eats them
    _shortcut = _shortcut_classify(text)
    if _shortcut and _shortcut != "memory_capture":
        task_type = _shortcut
        classification = {"task_type": _shortcut, "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _shortcut == "memory_capture":
        # memory_capture is handled in chat via save_memory tool — treat as chat
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    elif _classify_obvious_chat(text):
        task_type = "chat"
        classification = {"task_type": "chat", "confidence": 0.95, "is_unknown": False, "has_email_followup": False}
    else:
        from router import classify_task, extract_metadata
        classification = classify_task(text)
        metadata = extract_metadata(text)
        classification.update(metadata)
        task_type = classification.get("task_type", "unknown")
```

**Entry point 2** — the `/run` API endpoint (around line 1084). Find the equivalent `if _classify_obvious_chat(request.task):` block and apply the same replacement pattern, using `request.task` instead of `text`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_chat_memory_tool.py -v
```

Expected: All PASSED.

- [ ] **Step 6: Commit**

```bash
git add orchestrator/orchestrator.py tests/test_chat_memory_tool.py
git commit -m "feat: add _shortcut_classify() — runs before obvious-chat pre-filter in both entry points"
```

---

## Task 6: Wire Post-Crew Email Follow-Up Hook in `_run_background_job()`

**Files:**
- Modify: `orchestrator/orchestrator.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_chat_memory_tool.py`:

```python
def test_has_email_followup_metadata_extraction():
    from router import extract_metadata
    meta = extract_metadata("Research AI trends and send me an email about it")
    assert meta["has_email_followup"] is True

def test_no_email_followup_for_plain_task():
    from router import extract_metadata
    meta = extract_metadata("Research AI trends")
    assert meta["has_email_followup"] is False
```

- [ ] **Step 2: Run to verify**

```bash
python -m pytest tests/test_chat_memory_tool.py -v -k "email_followup"
```

Expected: PASSED (metadata extraction is already wired from Task 4).

- [ ] **Step 3: Add post-crew email hook in `_run_background_job()`**

In `orchestrator/orchestrator.py`, inside `_run_background_job()`, find the existing hunter email block:

```python
        # ── Email hunter results ──────────────────────────────────
        if task_type == "hunter_task":
```

**Before** that block, insert:

```python
        # ── Compound request: email follow-up ────────────────────
        # If the original message asked to "also send me an email about this",
        # spin a minimal GWS crew to draft the summary email after the main task.
        has_email_followup = classification.get("has_email_followup", False) if isinstance(classification, dict) else False
        if has_email_followup and task_type not in ("chat", "gws_task", "crm_outreach"):
            try:
                from crews import build_gws_crew
                email_task_text = (
                    f"Create a Gmail draft to bokar83@gmail.com and catalystworks.ai@gmail.com "
                    f"with subject 'agentsHQ Result: {title[:60]}'. "
                    f"Body: Format the following result as clean HTML with a header, "
                    f"bullet points for key findings, and a closing note. "
                    f"Result to format:\n\n{summary[:3000]}"
                )
                email_crew = build_gws_crew(email_task_text)
                email_crew.kickoff()
                send_message(chat_id, "Email draft created in your Gmail — go check it.")
                logger.info(f"Compound email follow-up draft created for job {job_id}")
            except Exception as e:
                logger.warning(f"Compound email follow-up failed (non-fatal): {e}")
```

Also, ensure `classification` is passed into `_run_background_job()`. Find the function signature:

```python
def _run_background_job(
    task: str,
    from_number: str,
    session_key: str,
    job_id: str,
) -> None:
```

Update to:

```python
def _run_background_job(
    task: str,
    from_number: str,
    session_key: str,
    job_id: str,
    classification: dict = None,
) -> None:
```

And update the call site in `process_telegram_update()` (around line 935):

```python
        loop.run_in_executor(
            None,
            lambda: _run_background_job(
                task=text,
                from_number=chat_id,
                session_key=crew_session_key,
                job_id=job_id,
                classification=classification,
            )
        )
```

Do the same for the `/run` endpoint call site.

- [ ] **Step 4: Commit**

```bash
git add orchestrator/orchestrator.py
git commit -m "feat: post-crew email hook — compound 'do X and email me' requests now fire a GWS draft"
```

---

## Task 7: Add `build_notion_capture_agent()` and `build_notion_capture_crew()`

**Files:**
- Modify: `orchestrator/agents.py`
- Modify: `orchestrator/crews.py`

- [ ] **Step 1: Add agent to `agents.py`**

In `orchestrator/agents.py`, add the import at the top of the file in the `from tools import (...)` block:

```python
    NOTION_CAPTURE_TOOLS,
```

Then add the agent builder function after `build_gws_agent()` (around line 835):

```python
def build_notion_capture_agent() -> Agent:
    """Builds the Notion Capture Agent — writes and reads from the agentsHQ Ideas database."""
    from tools import NOTION_CAPTURE_TOOLS
    return Agent(
        role="Ideas Curator",
        goal=(
            "Capture ideas, thoughts, and brain dumps into the agentsHQ Ideas Notion database. "
            "Also retrieve and summarize existing ideas when Boubacar wants to review them. "
            "Always confirm what was saved or retrieved."
        ),
        backstory=(
            "You are Boubacar's personal ideas vault. Every thought, concept, and wild idea "
            "he throws at you gets captured cleanly in Notion. You extract a crisp title from "
            "whatever he says, preserve the full content, categorize it sensibly, and confirm. "
            "When he wants to review his ideas, you pull them out, format them cleanly, "
            "and highlight anything that looks ready to act on."
        ),
        tools=NOTION_CAPTURE_TOOLS,
        llm=select_llm("planner", "moderate"),
        verbose=False,
        allow_delegation=False,
        max_iter=5,
    )
```

- [ ] **Step 2: Add crew to `crews.py`**

In `orchestrator/crews.py`, add after `build_gws_crew()` (around line 1687):

```python
def build_notion_capture_crew(user_request: str) -> Crew:
    """
    Crew for: notion_capture
    Single-agent crew that saves an idea to or retrieves ideas from the agentsHQ Ideas database.
    Write mode: triggered by "add to my ideas", "save this", "brain dump", etc.
    Review mode: triggered by "review my ideas", "what ideas do I have", etc.
    """
    from agents import build_notion_capture_agent
    agent = build_notion_capture_agent()

    # Determine mode from request
    lower = user_request.lower()
    review_triggers = [
        "review my ideas", "what ideas", "show my ideas", "pull up my ideas",
        "list my ideas", "what's in my ideas", "whats in my ideas",
        "read my ideas", "see my ideas",
    ]
    is_review = any(t in lower for t in review_triggers)

    if is_review:
        task_description = (
            f"The user wants to review their saved ideas.\n\n"
            f"REQUEST: {user_request}\n\n"
            f"Steps:\n"
            f"1. Call query_notion_ideas with an empty input to get all recent ideas.\n"
            f"2. Format the results clearly: group by Status (New first), show title, category, and a one-line summary.\n"
            f"3. If there are more than 10 ideas, summarize the oldest ones and show the 10 most recent in full.\n"
            f"4. Flag any ideas with Status='New' that look particularly actionable."
        )
        expected_output = (
            "A clean formatted list of all ideas from the Notion database, "
            "grouped by status, with titles, categories, and summaries. "
            "Actionable 'New' ideas are highlighted."
        )
    else:
        task_description = (
            f"The user wants to save a new idea or note.\n\n"
            f"REQUEST: {user_request}\n\n"
            f"Steps:\n"
            f"1. Extract a short, clear title (5-10 words max) from the request.\n"
            f"2. Use the full request text as the content — do not summarize or truncate.\n"
            f"3. Pick the most fitting category: Tool, Agent, Feature, Business, or Personal.\n"
            f"4. Call create_notion_idea with the title, content, and category.\n"
            f"5. Confirm to the user: what was saved, the title, and that it's in Notion."
        )
        expected_output = (
            "Confirmation that the idea was saved: title, category, and Notion URL. "
            "One sentence confirmation to the user."
        )

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )
```

- [ ] **Step 3: Register the crew in `CREW_REGISTRY`**

In `orchestrator/crews.py`, find the `CREW_REGISTRY` dict (around line 1840) and add:

```python
    "notion_capture_crew":    build_notion_capture_crew,
```

- [ ] **Step 4: Commit**

```bash
git add orchestrator/agents.py orchestrator/crews.py
git commit -m "feat: add build_notion_capture_agent and build_notion_capture_crew"
```

---

## Task 8: Add `notion_capture` Labels to `notifier.py`

**Files:**
- Modify: `orchestrator/notifier.py`

- [ ] **Step 1: Add entries to `TASK_TYPE_LABELS` and `TASK_TYPE_CREWS`**

In `orchestrator/notifier.py`, in the `TASK_TYPE_LABELS` dict (around line 43), add:

```python
    "notion_capture":          "Ideas Agent is capturing your thought in Notion",
    "memory_capture":          "Got it — saving to memory",
```

In the `TASK_TYPE_CREWS` dict (around line 68), add:

```python
    "notion_capture":          "Ideas Curator (Notion write/read)",
```

- [ ] **Step 2: Commit**

```bash
git add orchestrator/notifier.py
git commit -m "feat: add notion_capture labels to notifier"
```

---

## Task 9: Bootstrap Script — Create and Seed the Ideas Database

**Files:**
- Create: `scripts/bootstrap_ideas_db.py`

- [ ] **Step 1: Write the bootstrap script**

Create `scripts/bootstrap_ideas_db.py`:

```python
#!/usr/bin/env python3
"""
One-time bootstrap: create the agentsHQ Ideas Notion database and seed it.

Usage (run locally or on VPS):
    NOTION_SECRET=<token> NOTION_PARENT_PAGE_ID=<page_id> python scripts/bootstrap_ideas_db.py

The script will:
1. Create the "agentsHQ Ideas" database under the given parent page.
2. Seed it with the first known idea (Practice Runner).
3. Print the new DB ID — copy it to .env as IDEAS_DB_ID.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from skills.notion_skill.notion_tool import create_database, create_idea_page

PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "")
if not PARENT_PAGE_ID:
    print("ERROR: Set NOTION_PARENT_PAGE_ID env var to the Notion page where the DB should live.")
    print("  Find it: open a Notion page, copy the last 32 chars of the URL (no dashes).")
    sys.exit(1)

print("Creating agentsHQ Ideas database in Notion...")
result = create_database(PARENT_PAGE_ID, "agentsHQ Ideas")
db_id = result["id"]
db_url = result.get("url", "")
print(f"Database created!")
print(f"  ID:  {db_id}")
print(f"  URL: {db_url}")
print()
print("Seeding first idea: Practice Runner...")

seed_ideas = [
    {
        "title": "Practice Runner — AI Roleplay Feedback Tool",
        "content": (
            "An app or tool where Boubacar can record himself or have a conversation with an AI "
            "to practice different scenarios: running a session with a client, speaking a language, "
            "doing interviews, sales calls, presentations. After the practice session, the AI gives "
            "detailed feedback on performance and what to improve. "
            "Preferred modality: video (primary), voice, or chat. "
            "Potential positioning: personal coach for high-stakes conversations. "
            "Side project — not a client deliverable."
        ),
        "category": "Tool",
    },
]

for idea in seed_ideas:
    url = create_idea_page(db_id, idea["title"], idea["content"], idea["category"])
    print(f"  Seeded: '{idea['title']}' — {url}")

print()
print("=" * 60)
print("NEXT STEP: Add this to your .env and docker-compose.yml:")
print(f"  IDEAS_DB_ID={db_id}")
print("=" * 60)
```

- [ ] **Step 2: Find the agentsHQ workspace parent page ID in Notion**

Open Notion, navigate to the agentsHQ top-level page. Copy the URL — it looks like:
`https://www.notion.so/Your-Page-Title-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

The last 32 hex chars (with no dashes) is the page ID.

- [ ] **Step 3: Run the script locally**

```bash
cd d:/Ai_Sandbox/agentsHQ
NOTION_SECRET=${NOTION_SECRET} \
NOTION_PARENT_PAGE_ID=<your-parent-page-id> \
python scripts/bootstrap_ideas_db.py
```

Expected output:
```
Creating agentsHQ Ideas database in Notion...
Database created!
  ID:  xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  URL: https://notion.so/...
Seeding first idea: Practice Runner...
  Seeded: 'Practice Runner — AI Roleplay Feedback Tool' — https://notion.so/...

============================
NEXT STEP: Add to .env and docker-compose.yml:
  IDEAS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
============================
```

- [ ] **Step 4: Commit the script**

```bash
git add scripts/bootstrap_ideas_db.py
git commit -m "feat: bootstrap script to create and seed agentsHQ Ideas Notion database"
```

---

## Task 10: Wire `IDEAS_DB_ID` into `docker-compose.yml` and Deploy

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add `IDEAS_DB_ID` to docker-compose env passthrough**

In `docker-compose.yml`, inside the `orc-crewai` service `environment:` block, find the Notion secret line:

```yaml
      - NOTION_SECRET=${NOTION_SECRET}
```

Add directly after it:

```yaml
      - IDEAS_DB_ID=${IDEAS_DB_ID}
```

- [ ] **Step 2: Add `IDEAS_DB_ID` to `.env` on VPS**

```bash
ssh root@72.60.209.109 "echo 'IDEAS_DB_ID=<the-db-id-from-bootstrap>' >> /root/agentsHQ/.env"
```

Replace `<the-db-id-from-bootstrap>` with the actual ID printed by the bootstrap script.

- [ ] **Step 3: Commit docker-compose change**

```bash
git add docker-compose.yml
git commit -m "feat: pass IDEAS_DB_ID env var to orc-crewai container"
```

- [ ] **Step 4: Deploy to VPS**

```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d --build orc-crewai"
```

Wait ~60 seconds for container to start.

- [ ] **Step 5: Verify container is healthy**

```bash
ssh root@72.60.209.109 "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep orc-crewai"
```

Expected: `orc-crewai   Up X minutes (healthy)`

---

## Task 11: End-to-End Smoke Tests via Telegram

- [ ] **Test 1: Notion capture — write mode**

Send to Telegram: `Add to my ideas list: I want to build a daily reflection tool where I voice-record my thoughts and AI gives me a weekly summary`

Expected:
- Remoat shows briefing: "Ideas Agent is capturing your thought in Notion"
- agentsHQ bot replies: confirmation with title and "saved to Notion"
- Verify: open Notion agentsHQ Ideas DB, new record appears

- [ ] **Test 2: Notion capture — review mode**

Send to Telegram: `Review my ideas`

Expected:
- Bot returns formatted list of ideas including Practice Runner and the one from Test 1

- [ ] **Test 3: Short GWS message**

Send to Telegram: `what's on my calendar`

Expected:
- Briefing: "Google Workspace Agent is on it"
- Bot returns calendar events (not a chat response)

- [ ] **Test 4: Compound request**

Send to Telegram: `Research the top 3 AI coaching apps out there and send me an email about it`

Expected:
- Briefing: "Research Agent is on the case"
- After research completes: bot replies with research summary
- Second message: "Email draft created in your Gmail"
- Verify Gmail: draft exists at bokar83@gmail.com

- [ ] **Test 5: Memory save via chat**

Send to Telegram: `save this to memory: my primary target market is service-based SMBs with 5-50 employees`

Expected:
- Bot acknowledges in chat: "Saved to memory: ..."
- No briefing (stays in chat mode, no crew spin)

- [ ] **Test 6: Original failing message**

Send to Telegram the original Practice Runner message verbatim.

Expected:
- Routes to `notion_capture` (not chat)
- Idea saved to Notion
- GWS email draft created (compound request: "Send me an email about this as well")

---

## Self-Review Checklist

### Spec Coverage

| Spec Requirement | Task |
|---|---|
| Fix `_classify_obvious_chat` execution order | Task 5 |
| New `notion_capture` task type | Task 4 |
| `create_database()` / `query_database()` | Task 1 |
| `NotionCreateIdeaTool` / `NotionQueryIdeasTool` | Task 2 |
| `NOTION_CAPTURE_TOOLS` bundle | Task 2 |
| `notion_capture` crew (write + review mode) | Task 7 |
| `notion_capture` agent | Task 7 |
| `notion_capture` notifier labels | Task 8 |
| Compound request `has_email_followup` metadata | Task 4 |
| Post-crew GWS email hook | Task 6 |
| GWS keyword shortcuts promoted | Task 4 + Task 5 |
| `save_memory` chat tool | Task 3 |
| `memory_capture` task type (routes to chat) | Task 4 |
| `create_idea_page()` in notion_tool | Task 1 |
| Ideas DB creation bootstrap | Task 9 |
| Practice Runner seeded | Task 9 |
| `IDEAS_DB_ID` env var | Task 10 |
| deploy + smoke tests | Tasks 10-11 |

All spec requirements covered. No gaps found.

### Placeholder Scan

No TBD, TODO, or "handle edge cases" found. Every step has exact code.

### Type Consistency

- `create_idea_page(database_id, title, content, category)` defined in Task 1, called in `NotionCreateIdeaTool._run()` in Task 2. Signatures match.
- `query_database(database_id, filter, sorts)` defined in Task 1, called in `NotionQueryIdeasTool._run()` in Task 2. Signatures match.
- `build_notion_capture_crew(user_request)` defined in Task 7, registered as `"notion_capture_crew"` in `CREW_REGISTRY`. `get_crew_type("notion_capture")` returns `"notion_capture_crew"`. Matches.
- `_shortcut_classify(msg)` defined in Task 5, returns `str | None`. Called in `process_telegram_update()` with `text`. Types match.
- `classification` dict passed to `_run_background_job()` as kwarg `classification=classification`. Defaulted to `None` if missing. `has_email_followup` read with `.get()` with default `False`. Safe.
