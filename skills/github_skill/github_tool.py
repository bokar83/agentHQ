import os
import json
import logging
from github import Github

logger = logging.getLogger(__name__)

def get_github_client():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in environment.")
    return Github(token)

def create_repo(name, description="", private=True):
    """Create a new GitHub repository."""
    g = get_github_client()
    user = g.get_user()
    repo = user.create_repo(name, description=description, private=private)
    return {"name": repo.name, "url": repo.html_url}

def create_issue(repo_name, title, body=""):
    """Create a new issue in a GitHub repository."""
    g = get_github_client()
    user = g.get_user()
    repo = user.get_repo(f"{user.login}/{repo_name}")
    issue = repo.create_issue(title=title, body=body)
    return {"number": issue.number, "url": issue.html_url}

def create_file(repo_name, path, content, message="Add file via agent"):
    """Create or update a file in a GitHub repository."""
    g = get_github_client()
    user = g.get_user()
    repo = user.get_repo(f"{user.login}/{repo_name}")
    try:
        contents = repo.get_contents(path)
        repo.update_file(contents.path, message, content, contents.sha)
        return f"Updated {path} in {repo_name}"
    except:
        repo.create_file(path, message, content)
        return f"Created {path} in {repo_name}"
