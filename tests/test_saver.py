"""Tests for saver.py — GitHub and Drive calls are mocked."""
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("GITHUB_TOKEN", "ghp_test")
os.environ.setdefault("GITHUB_USERNAME", "bokar83")
os.environ.setdefault("GITHUB_REPO", "agentHQ")
os.environ.setdefault("GOOGLE_DRIVE_FOLDER_ID", "1wb2ZdYkLdSy-oWQ3bWZWgRXOIgX59t2N")
os.environ.setdefault("GOOGLE_OAUTH_CREDENTIALS_JSON", "/tmp/fake-oauth.json")

import sys
sys.path.insert(0, "orchestrator")


def test_save_to_github_returns_url():
    mock_repo = MagicMock()
    mock_repo.create_file.return_value = {
        "content": MagicMock(),
        "commit": MagicMock(html_url="https://github.com/bokar83/agentHQ/blob/main/outputs/research/test.md"),
    }
    with patch("saver.Github") as mock_github_cls:
        mock_github_cls.return_value.get_user.return_value.get_repo.return_value = mock_repo
        from saver import save_to_github
        url = save_to_github("Test Report", "research_report", "# Hello\nThis is content.")
        assert "github.com" in url
        mock_repo.create_file.assert_called_once()
        call_path = mock_repo.create_file.call_args.args[0]
        assert call_path.startswith("outputs/research_report/")
        assert call_path.endswith(".md")


def test_save_to_github_slugifies_title():
    mock_repo = MagicMock()
    mock_repo.create_file.return_value = {
        "content": MagicMock(),
        "commit": MagicMock(html_url="https://github.com/bokar83/agentHQ/blob/main/outputs/research/test.md"),
    }
    with patch("saver.Github") as mock_github_cls:
        mock_github_cls.return_value.get_user.return_value.get_repo.return_value = mock_repo
        from saver import save_to_github
        save_to_github("My Report: Special/Chars!", "research_report", "content")
        call_path = mock_repo.create_file.call_args.args[0]
        assert " " not in call_path
        assert "/" not in call_path.split("outputs/research_report/")[1]


def test_save_to_github_returns_empty_on_error():
    with patch("saver.Github") as mock_github_cls:
        mock_github_cls.side_effect = Exception("auth failed")
        from saver import save_to_github
        url = save_to_github("Test", "code_task", "content")
        assert url == ""


def test_save_to_drive_returns_url():
    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_service.files.return_value = mock_files
    mock_files.create.return_value.execute.return_value = {
        "id": "abc123",
        "webViewLink": "https://drive.google.com/file/d/abc123/view"
    }
    # Patch both the service builder and MediaInMemoryUpload at the saver module level
    with patch("saver._get_drive_service", return_value=mock_service), \
         patch("saver.MediaInMemoryUpload", return_value=MagicMock()):
        from saver import save_to_drive
        url = save_to_drive("My Report", "research_report", "# Content")
        assert "drive.google.com" in url


def test_save_to_drive_returns_empty_on_error():
    with patch("saver._get_drive_service", side_effect=Exception("creds failed")):
        from saver import save_to_drive
        url = save_to_drive("Test", "code_task", "content")
        assert url == ""
