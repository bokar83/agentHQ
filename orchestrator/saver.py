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
    "linkedin_x_campaign": "deliverables/social",
    "code_task": "deliverables/code",
    "hunter_task": "leads",
    "general_writing": "deliverables",
    "voice_polishing": "deliverables",
    "prompt_engineering": "deliverables",
    "news_brief": "deliverables/research",
    "gws_task": "deliverables",
    "notion_tasks": "deliverables",
    "notion_capture": "deliverables",
    "crm_outreach": "deliverables",
    "enrich_leads": "leads",
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


NOTION_TOKEN = os.environ.get("NOTION_SECRET", "")
FORGE_CONTENT_DB = os.environ.get("FORGE_CONTENT_DB", "")


def save_to_notion_content_board(title: str, task_type: str, drive_url: str, draft: str = "") -> str:
    """
    Create a draft entry on the Notion content board with the Drive URL attached.
    Returns the Notion page URL on success, empty string on failure.

    Maps task_type to Platform:
      social_content / linkedin_x_campaign / voice_polishing -> LinkedIn
      general_writing / content_push_to_drive -> LinkedIn (default, editable after)
    """
    if not NOTION_TOKEN or not FORGE_CONTENT_DB:
        logger.warning("Notion config incomplete -- skipping content board save")
        return ""

    platform_map = {
        "social_content": "LinkedIn",
        "linkedin_x_campaign": "LinkedIn",
        "voice_polishing": "LinkedIn",
        "general_writing": "LinkedIn",
        "content_push_to_drive": "LinkedIn",
    }
    platform = platform_map.get(task_type, "LinkedIn")

    try:
        import urllib.request
        import json as _json

        properties: dict = {
            "Title": {"title": [{"text": {"content": title[:100]}}]},
            "Status": {"select": {"name": "Draft"}},
            "Platform": {"multi_select": [{"name": platform}]},
        }
        if drive_url:
            properties["Drive URL"] = {"url": drive_url}
        if draft:
            properties["Draft"] = {"rich_text": [{"text": {"content": draft[:2000]}}]}

        payload = _json.dumps({
            "parent": {"database_id": FORGE_CONTENT_DB},
            "properties": properties,
        }).encode()

        req = urllib.request.Request(
            "https://api.notion.com/v1/pages",
            data=payload,
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
        page_url = data.get("url", "")
        logger.info(f"Notion content board: {page_url}")
        return page_url
    except Exception as e:
        logger.error(f"Notion content board save failed: {e}")
        return ""
