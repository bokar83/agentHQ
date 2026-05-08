"""
memory_qmd.py -- Local semantic search via QMD (github.com/tobi/qmd).
Additive to memory.py (Qdrant). Use when Qdrant is unavailable or for
local-only searches over agent logs and session notes.
"""

import logging
import re
import shutil
import subprocess
from pathlib import Path
import sys

# Subprocess creation flags to suppress console window flashing on Windows
SUBPROCESS_FLAGS = 0x08000000 if sys.platform == "win32" else 0

logger = logging.getLogger(__name__)
_RESULT_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+):\s*(?P<snippet>.*)$")


def _default_index_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "workspace" / "memory-index"


def qmd_available() -> bool:
    """Check whether the qmd CLI is available on PATH."""
    try:
        return shutil.which("qmd") is not None
    except Exception as e:
        logger.warning(f"qmd_available failed (non-fatal): {e}")
        return False


def qmd_search(query: str, index_dir: str = None, top_k: int = 5) -> list[dict]:
    """Run a local QMD semantic search and return normalized results."""
    try:
        if not qmd_available():
            return []

        root = Path(index_dir) if index_dir else _default_index_dir()
        if not root.exists() or not any(root.iterdir()):
            return []

        result = subprocess.run(
            ["qmd", "query", query],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            creationflags=SUBPROCESS_FLAGS,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        matches = []
        for line in result.stdout.splitlines():
            parsed = _RESULT_RE.match(line.strip())
            if not parsed:
                continue
            matches.append(
                {
                    "file": parsed.group("file"),
                    "line": int(parsed.group("line")),
                    "snippet": parsed.group("snippet"),
                }
            )
            if len(matches) >= top_k:
                break
        return matches
    except Exception as e:
        logger.warning(f"qmd_search failed (non-fatal): {e}")
        return []


def index_document(file_path: str, index_dir: str = None) -> bool:
    """Copy a document into the QMD index directory for the next refresh."""
    try:
        source = Path(file_path)
        root = Path(index_dir) if index_dir else _default_index_dir()
        root.mkdir(parents=True, exist_ok=True)
        if not source.exists() or not source.is_file():
            return False

        destination = root / source.name
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.warning(f"index_document failed (non-fatal): {e}")
        return False


def qmd_search_with_fallback(query: str, top_k: int = 5) -> list[dict]:
    """Try QMD first, then fall back to Qdrant-backed memory search."""
    try:
        results = qmd_search(query=query, top_k=top_k)
        if results:
            return results

        from orchestrator.memory import query_memory

        fallback = query_memory(query, top_k=top_k)
        normalized = []
        for item in fallback:
            normalized.append(
                {
                    "file": item.get("file", "") if isinstance(item, dict) else "",
                    "line": item.get("line", 0) if isinstance(item, dict) else 0,
                    "snippet": (
                        item.get("snippet")
                        or item.get("summary")
                        or item.get("extracted_pattern")
                        or item.get("content")
                        or item.get("task_request")
                        or ""
                    ) if isinstance(item, dict) else "",
                }
            )
        return normalized[:top_k]
    except Exception as e:
        logger.warning(f"qmd_search_with_fallback failed (non-fatal): {e}")
        return []
