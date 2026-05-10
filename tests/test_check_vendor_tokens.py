# tests/test_check_vendor_tokens.py
"""Tests for vendor token scanner. NEVER put real token values here.
Use synthetic tokens: same prefix+length pattern, not real credentials."""
from __future__ import annotations
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "check_vendor_tokens.py"

def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_vendor_tokens", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_script_exists():
    assert SCRIPT.exists()

def test_detects_vercel_token_in_markdown_table(tmp_path):
    mod = _load()
    fake_token = "vcp_" + "A" * 40  # synthetic — not a real credential
    f = tmp_path / "audit.md"
    f.write_text(f"| Token | `{fake_token}` |")
    hits = mod.scan_file(str(f))
    assert len(hits) == 1
    assert "vcp_" in hits[0]

def test_detects_openai_style_key(tmp_path):
    mod = _load()
    fake_key = "sk-" + "B" * 48
    f = tmp_path / "notes.md"
    f.write_text(f"key = {fake_key}")
    hits = mod.scan_file(str(f))
    assert len(hits) == 1

def test_ignores_redacted_token(tmp_path):
    mod = _load()
    f = tmp_path / "audit.md"
    f.write_text("| Token | `vcp_REDACTED_rotate_via_vercel_dashboard` |")
    hits = mod.scan_file(str(f))
    assert len(hits) == 0

def test_ignores_short_prefix(tmp_path):
    mod = _load()
    f = tmp_path / "doc.md"
    f.write_text("The prefix vcp_ is used by Vercel tokens.")
    hits = mod.scan_file(str(f))
    assert len(hits) == 0

def test_clean_file_passes(tmp_path):
    mod = _load()
    f = tmp_path / "clean.md"
    f.write_text("# Normal markdown\nNo tokens here.")
    assert mod.scan_file(str(f)) == []
