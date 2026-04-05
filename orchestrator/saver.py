"""
saver.py — Save agent output to GitHub and Google Drive.

Env vars required:
  GITHUB_TOKEN                  — personal access token (repo scope)
  GITHUB_USERNAME               — GitHub handle (bokar83)
  GITHUB_REPO                   — repo name (agentHQ)
  GOOGLE_OAUTH_CREDENTIALS_JSON — path to user OAuth credentials JSON on disk
                                   (exported via: gws auth export --unmasked)
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

DRIVE_FOLDER_MAP = {
    "research_report": "deliverables/research",
    "consulting_deliverable": "deliverables/consulting",
    "website_build": "deliverables/websites",
    "3d_website_build": "deliverables/websites",
    "social_content": "deliverables/social",
    "code_task": "deliverables/code",
    "hunter_task": "leads",
    "general_writing": "deliverables",
    "voice_polishing": "deliverables",
    "prompt_engineering": "deliverables",
    "news_brief": "deliverables/research",
}


def get_drive_subfolder(task_type: str) -> str:
    """Return the Drive subfolder path for a given task type."""
    return DRIVE_FOLDER_MAP.get(task_type, "deliverables")


GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USERNAME   = os.environ.get("GITHUB_USERNAME", "bokar83")
GITHUB_REPO       = os.environ.get("GITHUB_REPO", "agentHQ")
DRIVE_FOLDER_ID   = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
OAUTH_CREDS_PATH  = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON", "")


def _slugify(text: str) -> str:
    """Convert title to a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:60]


def _get_drive_service():
    """Build and return an authenticated Google Drive service client using user OAuth."""
    import json
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    with open(OAUTH_CREDS_PATH) as f:
        info = json.load(f)
    creds = Credentials(
        token=None,
        refresh_token=info["refresh_token"],
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
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
        result = repo.create_file(
            path,
            f"agent output: {title[:60]}",
            content,
            branch="main",
        )
        url = result["commit"].html_url
        logger.info(f"GitHub save: {url}")
        return url
    except Exception as e:
        logger.error(f"GitHub save failed: {e}")
        return ""


def save_to_drive(title: str, task_type: str, content: str) -> str:
    """Upload a markdown file to Google Drive in the correct subfolder."""
    if not DRIVE_FOLDER_ID or not OAUTH_CREDS_PATH:
        logger.warning("Drive config incomplete -- skipping Drive save")
        return ""
    try:
        service = _get_drive_service()
        slug = _slugify(title)
        ts = int(time.time())
        filename = f"{slug}-{ts}.md"

        # Find or create subfolder
        subfolder = get_drive_subfolder(task_type)
        parent_id = DRIVE_FOLDER_ID
        for folder_name in subfolder.split("/"):
            parent_id = _find_or_create_folder(service, folder_name, parent_id)

        metadata = {"name": filename, "parents": [parent_id]}
        if MediaInMemoryUpload is None:
            raise ImportError("google-api-python-client not installed")
        media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="text/markdown", resumable=False)
        result = service.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
        url = result.get("webViewLink", "")
        logger.info(f"Drive save: {url}")
        return url
    except Exception as e:
        logger.error(f"Drive save failed: {e}")
        return ""


def _find_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    """Find a subfolder by name under parent, or create it."""
    query = f"'{parent_id}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]
