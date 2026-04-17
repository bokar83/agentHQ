# orchestrator/tests/test_design_context.py
import os
import sys
import pytest

# Make orchestrator importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from design_context import DesignContextLoader


def test_load_returns_string_for_website_build(tmp_path, monkeypatch):
    """load() returns non-empty string when styleguide files exist."""
    sg_dir = tmp_path / "styleguides"
    sg_dir.mkdir()
    (sg_dir / "styleguide_master.md").write_text("# Master\n## Color\n--color-primary: #00B7C2")
    (sg_dir / "styleguide_websites.md").write_text("# Websites\n## Layout\nmax-width: 1280px")

    monkeypatch.setattr(DesignContextLoader, "_STYLEGUIDE_DIR", str(sg_dir))

    result = DesignContextLoader.load("website_build")
    assert "color-primary" in result
    assert "1280px" in result


def test_load_returns_empty_string_when_files_missing(tmp_path, monkeypatch):
    """load() returns '' when styleguide directory doesn't exist — silent fallback."""
    monkeypatch.setattr(DesignContextLoader, "_STYLEGUIDE_DIR", str(tmp_path / "nonexistent"))

    result = DesignContextLoader.load("website_build")
    assert result == ""


def test_load_returns_empty_for_unknown_task_type():
    """load() returns '' for task types not in STYLEGUIDE_MAP."""
    result = DesignContextLoader.load("hunter_task")
    assert result == ""


def test_load_reference_returns_content(tmp_path, monkeypatch):
    """load_reference() returns file content when reference exists."""
    ref_dir = tmp_path / "design-references"
    ref_dir.mkdir()
    (ref_dir / "linear.md").write_text("# Linear Design\n## Colors\n#08090a background")

    monkeypatch.setattr(DesignContextLoader, "_REFERENCES_DIR", str(ref_dir))

    result = DesignContextLoader.load_reference("linear")
    assert "#08090a" in result


def test_load_reference_returns_empty_when_missing(tmp_path, monkeypatch):
    """load_reference() returns '' for unknown reference name."""
    monkeypatch.setattr(DesignContextLoader, "_REFERENCES_DIR", str(tmp_path))
    result = DesignContextLoader.load_reference("nonexistent-brand")
    assert result == ""
