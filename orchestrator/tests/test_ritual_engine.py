"""
Unit tests for ritual_engine. Postgres is mocked via an in-memory store so the
state machine + finalize path can run without orc-postgres.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

import ritual_engine  # noqa: E402


# ──────────────────────────────────────────────────────────
# In-memory ritual_sessions store (replaces _conn)
# ──────────────────────────────────────────────────────────

class _FakeStore:
    def __init__(self):
        # session_id -> dict
        self.rows: dict[str, dict] = {}

    def insert(self, ritual_key, user_chat_id, payload):
        sid = str(uuid.uuid4())
        self.rows[sid] = {
            "id": sid,
            "ritual_key": ritual_key,
            "user_chat_id": user_chat_id,
            "current_step": 0,
            "awaiting": "pick",
            "payload": payload,
            "status": "active",
            "started_at": "2026-05-16T16:00:00Z",
            "completed_at": None,
        }
        return self.rows[sid]

    def get_active(self, ritual_key, user_chat_id):
        for r in self.rows.values():
            if (r["ritual_key"] == ritual_key
                    and r["user_chat_id"] == user_chat_id
                    and r["status"] == "active"):
                return r
        return None

    def get(self, sid):
        return self.rows.get(str(sid))

    def update(self, sid, **fields):
        if sid in self.rows:
            self.rows[sid].update(fields)
            return self.rows[sid]
        return None


@pytest.fixture
def fake_store(monkeypatch):
    store = _FakeStore()

    # Patch the four DB-touching primitives in ritual_engine.
    def fake_start_session(ritual_key, user_chat_id):
        cfg = ritual_engine.load_ritual_config(ritual_key)
        existing = store.get_active(ritual_key, user_chat_id)
        if existing:
            return existing
        payload = {
            "config_snapshot": {
                "title": cfg["title"],
                "n_steps": len(cfg["steps"]),
                "version": cfg.get("version", "v1"),
            },
            "answers": {},
        }
        return store.insert(ritual_key, user_chat_id, payload)

    def fake_get_active(ritual_key, user_chat_id):
        return store.get_active(ritual_key, user_chat_id)

    def fake_get(sid):
        return store.get(sid)

    def fake_cancel(sid):
        store.update(sid, status="cancelled")

    def fake_mark_completed(sid):
        store.update(str(sid), status="completed")

    def fake_record_pick(session_id, option_value):
        sess = store.get(session_id)
        if not sess or sess["status"] != "active":
            raise ritual_engine.RitualError("not active")
        if sess["awaiting"] != "pick":
            raise ritual_engine.RitualError(f"awaiting {sess['awaiting']}")
        cfg = ritual_engine.load_ritual_config(sess["ritual_key"])
        step = cfg["steps"][sess["current_step"]]
        valid = {opt[1]: opt[0] for opt in step["options"]}
        if option_value not in valid:
            raise ritual_engine.RitualError(f"invalid value {option_value}")
        payload = sess["payload"]
        payload.setdefault("answers", {})
        payload["answers"][step["id"]] = {
            "pick_value": option_value,
            "pick_label": valid[option_value],
            "rationale": None,
        }
        return store.update(session_id, awaiting="rationale", payload=payload)

    def fake_record_rationale(session_id, text):
        sess = store.get(session_id)
        if not sess or sess["status"] != "active":
            raise ritual_engine.RitualError("not active")
        if sess["awaiting"] != "rationale":
            raise ritual_engine.RitualError(f"awaiting {sess['awaiting']}")
        text = (text or "").strip()
        if not text:
            raise ritual_engine.RitualError("rationale empty")
        if len(text) > 500:
            text = text[:500] + "..."
        cfg = ritual_engine.load_ritual_config(sess["ritual_key"])
        step = cfg["steps"][sess["current_step"]]
        ans = sess["payload"]["answers"].get(step["id"])
        if not ans:
            raise ritual_engine.RitualError("no pick recorded")
        ans["rationale"] = text
        next_idx = sess["current_step"] + 1
        if next_idx >= len(cfg["steps"]):
            return store.update(session_id, awaiting="confirm", payload=sess["payload"])
        return store.update(session_id, awaiting="pick",
                            current_step=next_idx, payload=sess["payload"])

    monkeypatch.setattr(ritual_engine, "start_session", fake_start_session)
    monkeypatch.setattr(ritual_engine, "get_active_session", fake_get_active)
    monkeypatch.setattr(ritual_engine, "get_session", fake_get)
    monkeypatch.setattr(ritual_engine, "cancel_session", fake_cancel)
    monkeypatch.setattr(ritual_engine, "_mark_completed", fake_mark_completed)
    monkeypatch.setattr(ritual_engine, "record_pick", fake_record_pick)
    monkeypatch.setattr(ritual_engine, "record_rationale", fake_record_rationale)

    return store


# ──────────────────────────────────────────────────────────
# Config validation
# ──────────────────────────────────────────────────────────

def test_lr4_config_loads():
    cfg = ritual_engine.load_ritual_config("lr4_triad_lock")
    assert cfg["ritual_key"] == "lr4_triad_lock"
    assert len(cfg["steps"]) == 10
    assert "[READY]" in cfg["commit_subject_template"]


def test_lr5_config_loads():
    cfg = ritual_engine.load_ritual_config("lr5_conversion_scorecard")
    assert cfg["ritual_key"] == "lr5_conversion_scorecard"
    assert len(cfg["steps"]) >= 1
    assert "[READY]" in cfg["commit_subject_template"]


def test_unknown_ritual_raises():
    with pytest.raises(FileNotFoundError):
        ritual_engine.load_ritual_config("does_not_exist")


def test_validator_rejects_missing_ready_tag(tmp_path, monkeypatch):
    bad = {
        "ritual_key": "bad",
        "title": "Bad",
        "intro": "x",
        "output_file": "data/bad.md",
        "commit_subject_template": "no ready tag here",
        "commit_body_template": "",
        "steps": [{"id": "s1", "prompt": "?", "options": [["A", "a"]]}],
    }
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad))
    monkeypatch.setattr(ritual_engine, "RITUALS_DIR", tmp_path)
    with pytest.raises(ValueError, match="\\[READY\\]"):
        ritual_engine.load_ritual_config("bad")


# ──────────────────────────────────────────────────────────
# State machine
# ──────────────────────────────────────────────────────────

def test_start_session_creates_active(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "12345")
    assert sess["status"] == "active"
    assert sess["awaiting"] == "pick"
    assert sess["current_step"] == 0


def test_start_session_is_idempotent_per_user(fake_store):
    a = ritual_engine.start_session("lr4_triad_lock", "12345")
    b = ritual_engine.start_session("lr4_triad_lock", "12345")
    assert a["id"] == b["id"]


def test_record_pick_advances_awaiting(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u1")
    sess = ritual_engine.record_pick(sess["id"], "warm_replies")
    assert sess["awaiting"] == "rationale"
    assert sess["payload"]["answers"]["lane_1"]["pick_value"] == "warm_replies"


def test_record_pick_rejects_invalid_option(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u2")
    with pytest.raises(ritual_engine.RitualError):
        ritual_engine.record_pick(sess["id"], "NOT_A_VALID_VALUE")


def test_record_pick_rejects_when_awaiting_rationale(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u3")
    sess = ritual_engine.record_pick(sess["id"], "warm_replies")
    with pytest.raises(ritual_engine.RitualError):
        ritual_engine.record_pick(sess["id"], "audit_ship")


def test_record_rationale_advances_step(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u4")
    sess = ritual_engine.record_pick(sess["id"], "warm_replies")
    sess = ritual_engine.record_rationale(sess["id"], "warmth wins this week")
    assert sess["current_step"] == 1
    assert sess["awaiting"] == "pick"


def test_record_rationale_empty_rejected(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u5")
    sess = ritual_engine.record_pick(sess["id"], "warm_replies")
    with pytest.raises(ritual_engine.RitualError):
        ritual_engine.record_rationale(sess["id"], "   ")


def test_full_walk_lands_on_confirm(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u6")
    cfg = ritual_engine.load_ritual_config("lr4_triad_lock")
    for i, step in enumerate(cfg["steps"]):
        # always pick the first option
        first_value = step["options"][0][1]
        sess = ritual_engine.record_pick(sess["id"], first_value)
        sess = ritual_engine.record_rationale(sess["id"], f"rationale step {i}")
    assert sess["awaiting"] == "confirm"
    assert sess["current_step"] == len(cfg["steps"]) - 1


def test_lr5_full_walk(fake_store):
    sess = ritual_engine.start_session("lr5_conversion_scorecard", "u7")
    cfg = ritual_engine.load_ritual_config("lr5_conversion_scorecard")
    for i, step in enumerate(cfg["steps"]):
        first_value = step["options"][0][1]
        sess = ritual_engine.record_pick(sess["id"], first_value)
        sess = ritual_engine.record_rationale(sess["id"], f"r{i}")
    assert sess["awaiting"] == "confirm"


# ──────────────────────────────────────────────────────────
# Finalize / render
# ──────────────────────────────────────────────────────────

def test_render_summary_contains_all_steps(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u8")
    cfg = ritual_engine.load_ritual_config("lr4_triad_lock")
    for step in cfg["steps"]:
        sess = ritual_engine.record_pick(sess["id"], step["options"][0][1])
        sess = ritual_engine.record_rationale(sess["id"], "ok")
    summary = ritual_engine.render_summary(sess)
    for step in cfg["steps"]:
        assert step["id"] in summary["text"]
    # Confirm button present
    flat = [b for row in summary["buttons"] for b in row]
    assert any("ritual_confirm:" in d for (_, d) in flat)


def test_render_step_includes_cancel(fake_store):
    sess = ritual_engine.start_session("lr4_triad_lock", "u9")
    out = ritual_engine.render_step_prompt(sess)
    flat = [b for row in out["buttons"] for b in row]
    assert any("ritual_cancel:" in d for (_, d) in flat)


def test_finalize_dry_run_writes_file(fake_store, tmp_path):
    sess = ritual_engine.start_session("lr4_triad_lock", "u10")
    cfg = ritual_engine.load_ritual_config("lr4_triad_lock")
    for step in cfg["steps"]:
        sess = ritual_engine.record_pick(sess["id"], step["options"][0][1])
        sess = ritual_engine.record_rationale(sess["id"], "ok")
    assert sess["awaiting"] == "confirm"
    result = ritual_engine.finalize_session(sess["id"], repo_root=tmp_path, dry_run=True)
    out_path = Path(result["paths"][0])
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "L-R4 Triad Lock" in content
    assert "lane_1" in content
    assert "[READY]" in result["commit_subject"]


def test_finalize_rejects_before_confirm(fake_store, tmp_path):
    sess = ritual_engine.start_session("lr4_triad_lock", "u11")
    sess = ritual_engine.record_pick(sess["id"], "warm_replies")
    # Stop after 1 step - still awaiting rationale, not confirm.
    with pytest.raises(ritual_engine.RitualError):
        ritual_engine.finalize_session(sess["id"], repo_root=tmp_path, dry_run=True)


def test_finalize_appends_not_overwrites(fake_store, tmp_path):
    decisions_path = tmp_path / "data" / "lighthouse-decisions.md"
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_path.write_text("# existing\n\nSome prior content.\n", encoding="utf-8")

    sess = ritual_engine.start_session("lr4_triad_lock", "u12")
    cfg = ritual_engine.load_ritual_config("lr4_triad_lock")
    for step in cfg["steps"]:
        sess = ritual_engine.record_pick(sess["id"], step["options"][0][1])
        sess = ritual_engine.record_rationale(sess["id"], "ok")
    ritual_engine.finalize_session(sess["id"], repo_root=tmp_path, dry_run=True)
    final = decisions_path.read_text(encoding="utf-8")
    assert "Some prior content" in final
    assert "L-R4 Triad Lock" in final


def test_finalize_marks_completed(fake_store, tmp_path):
    sess = ritual_engine.start_session("lr4_triad_lock", "u13")
    cfg = ritual_engine.load_ritual_config("lr4_triad_lock")
    for step in cfg["steps"]:
        sess = ritual_engine.record_pick(sess["id"], step["options"][0][1])
        sess = ritual_engine.record_rationale(sess["id"], "ok")
    sid = sess["id"]
    ritual_engine.finalize_session(sid, repo_root=tmp_path, dry_run=True)
    final = fake_store.get(sid)
    assert final["status"] == "completed"
