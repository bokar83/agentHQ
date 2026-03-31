"""
saver.py — Save agent output to GitHub and Google Drive.

Env vars required:
  GITHUB_TOKEN                  — personal access token (repo scope)
  GITHUB_USERNAME               — GitHub handle (bokar83)
  GITHUB_REPO                   — repo name (agentHQ)
  GOOGLE_SERVICE_ACCOUNT_JSON   — path to service account JSON on disk
  GOOGLE_DRIVE_FOLDER_ID        — Drive folder ID for outputs
"""
import os
import re
import time
import logging

logger = logging.getLogger("agentsHQ.saver")

# Import Github at module level so patch("saver.Github") works in tests.
# Falls back to None when PyGithub is not installed (tests mock it anyway).
try:
    from github import Github
except ImportError:
    Github = None  # type: ignore[assignment,misc]

# Import MediaInMemoryUpload at module level so it is patchable and so that
# a missing googleapiclient package doesn't crash the module on import.
try:
    from googleapiclient.http import MediaInMemoryUpload
except ImportError:
    MediaInMemoryUpload = None  # type: ignore[assignment,misc]

GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "bokar83")
GITHUB_REPO     = os.environ.get("GITHUB_REPO", "agentHQ")
DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
SA_JSON_PATH    = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")


def _slugify(text: str) -> str:
    """Convert title to a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:60]


def _get_drive_service():
    """Build and return an authenticated Google Drive service client."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        SA_JSON_PATH,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build("drive", "v3", credentials=creds)


def save_to_github(title: str, task_type: str, content: str) -> str:
    """
    Push a markdown file to GitHub under outputs/{task_type}/{slug}-{ts}.md.
    Returns the GitHub blob URL, or empty string on failure.
    """
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not set — skipping GitHub save")
        return ""
    try:
        gh   = Github(GITHUB_TOKEN)
        repo = gh.get_user(GITHUB_USERNAME).get_repo(GITHUB_REPO)
        slug = _slugify(title)
        ts   = int(time.time())
        path = f"outputs/{task_type}/{slug}-{ts}.md"
        _, commit = repo.create_file(
            path,
            f"agent output: {title[:60]}",
            content,
            branch="main",
        )
        url = commit.html_url
        logger.info(f"GitHub save: {url}")
        return url
    except Exception as e:
        logger.error(f"GitHub save failed: {e}")
        return ""


def save_to_drive(title: str, task_type: str, content: str) -> str:
    """
    Upload a markdown file to Google Drive outputs folder.
    Returns the webViewLink, or empty string on failure.
    """
    if not DRIVE_FOLDER_ID or not SA_JSON_PATH:
        logger.warning("Drive config incomplete — skipping Drive save")
        return ""
    try:
        service  = _get_drive_service()
        slug     = _slugify(title)
        ts       = int(time.time())
        filename = f"{slug}-{ts}.md"
        metadata = {
            "name":    filename,
            "parents": [DRIVE_FOLDER_ID],
        }
        media = (
            MediaInMemoryUpload(
                content.encode("utf-8"),
                mimetype="text/markdown",
                resumable=False,
            )
            if MediaInMemoryUpload is not None
            else content.encode("utf-8")
        )
        result = service.files().create(
            body=metadata,
            media_body=media,
            fields="id,webViewLink",
        ).execute()
        url = result.get("webViewLink", "")
        logger.info(f"Drive save: {url}")
        return url
    except Exception as e:
        logger.error(f"Drive save failed: {e}")
        return ""
