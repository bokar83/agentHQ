"""Unit tests for flip_milestone() — uses mocked _pg_conn, no real DB needed."""
import sys, pathlib, pytest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "orchestrator"))


def _make_conn(fetchone_results=None):
    """Build a mock psycopg2 connection whose cursor.fetchone() returns items from the list in sequence."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.side_effect = fetchone_results or [None]
    return conn, cur


def test_flip_milestone_shipped_ok():
    """Happy path: existing active milestone flipped to shipped."""
    from atlas_dashboard import flip_milestone
    before = {"id": 1, "status": "active", "codename": "atlas", "mid": "M5"}
    after  = {"status": "shipped"}
    conn, cur = _make_conn([before, after])
    with patch("atlas_dashboard._pg_conn", return_value=conn):
        result = flip_milestone("atlas", "M5", "shipped")
    assert result["ok"] is True
    assert result["old_status"] == "active"
    assert result["new_status"] == "shipped"
    assert result["codename"] == "atlas"
    assert result["mid"] == "M5"


def test_flip_milestone_not_found():
    """Returns ok=False with 'not found' in error when mid doesn't exist."""
    from atlas_dashboard import flip_milestone
    conn, cur = _make_conn([None])  # fetchone returns None = row not found
    with patch("atlas_dashboard._pg_conn", return_value=conn):
        result = flip_milestone("atlas", "M999", "shipped")
    assert result["ok"] is False
    assert "not found" in result["error"].lower()


def test_flip_milestone_invalid_status():
    """Returns ok=False with 'invalid status' when unknown status passed — no DB call made."""
    from atlas_dashboard import flip_milestone
    result = flip_milestone("atlas", "M1", "flying")
    assert result["ok"] is False
    assert "invalid status" in result["error"].lower()


def test_flip_milestone_with_notes():
    """Notes parameter is included in the UPDATE when provided."""
    from atlas_dashboard import flip_milestone
    before = {"id": 1, "status": "queued", "codename": "atlas", "mid": "M5"}
    after  = {"status": "active"}
    conn, cur = _make_conn([before, after])
    with patch("atlas_dashboard._pg_conn", return_value=conn):
        result = flip_milestone("atlas", "M5", "active", notes="started today")
    assert result["ok"] is True
    # Verify the UPDATE call included the notes value somewhere in params
    update_calls = [c for c in cur.execute.call_args_list if "UPDATE" in str(c)]
    assert any("started today" in str(c) for c in update_calls)
