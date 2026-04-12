"""
gws_cli_tools.py — GWS CLI-backed BaseTool classes for Drive and Sheets operations.

All tools invoke the `gws` CLI binary via subprocess.
The CLI is authenticated via GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE env var,
which points to /app/secrets/gws-oauth-credentials.json inside the container.

Tool classes:
  GWSCliBase              — shared subprocess runner, env setup, error handling
  GWSDriveCreateFolderTool — create a folder in Drive
  GWSDriveMoveRenameTool   — rename + move a file in one PATCH call
  GWSDriveExportTool       — export Google Doc/Slides to plain text
  GWSDriveDownloadTool     — download a binary file (PDF) to /tmp
  GWSSheetsReadRangeTool   — read a range from a spreadsheet
  GWSSheetsAppendRowTool   — append a row to a spreadsheet range
"""

import os
import json
import subprocess
import logging
from typing import Any
from crewai.tools import BaseTool
from pydantic import Field

logger = logging.getLogger(__name__)

class GWSCliError(Exception):
    pass


class GWSCliBase:
    """Shared subprocess runner for all gws CLI tools."""

    def _run_gws(self, args: list[str], binary_output: bool = False) -> Any:
        """
        Run a gws command. Returns parsed JSON dict/list for JSON responses,
        or raw string for binary/text export responses.
        Raises GWSCliError on non-zero exit.
        """
        env = {
            **os.environ,
            "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE": os.environ.get(
                "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE",
                "/app/secrets/gws-oauth-credentials.json"
            ),
            "GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND": "file",
            "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": os.environ.get(
                "GOOGLE_WORKSPACE_CLI_CONFIG_DIR",
                "/app/.config/gws"
            ),
        }
        cmd = ["gws"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=not binary_output,
            env=env,
            timeout=30,
        )
        if result.returncode != 0:
            try:
                err = json.loads(result.stdout)
                msg = err.get("error", {}).get("message", result.stdout[:200])
            except Exception:
                msg = (result.stderr or result.stdout or "unknown error")[:200]
            raise GWSCliError(f"gws {' '.join(args[:3])} failed: {msg}")

        if binary_output:
            return result.stdout  # bytes
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return result.stdout


class GWSDriveCreateFolderTool(GWSCliBase, BaseTool):
    name: str = "drive_create_folder"
    description: str = (
        "Create a folder in Google Drive. "
        "Input JSON: {'name': 'folder name', 'parent_id': 'parent folder Drive ID'}. "
        "Returns JSON with the new folder's id, name, mimeType."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            name = data.get("name", "").strip()
            parent_id = data.get("parent_id", "").strip()
            if not name:
                return json.dumps({"error": "name is required"})
            body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
            if parent_id:
                body["parents"] = [parent_id]
            result = self._run_gws(["drive", "files", "create", "--json", json.dumps(body)])
            return json.dumps(result)
        except GWSCliError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"drive_create_folder failed: {e}"})


class GWSDriveMoveRenameTool(GWSCliBase, BaseTool):
    name: str = "drive_move_rename"
    description: str = (
        "Rename and/or move a file in Google Drive in a single operation. "
        "Input JSON: {'file_id': 'Drive file ID', 'new_name': 'standardized filename', "
        "'new_parent_id': 'target folder Drive ID', 'old_parent_id': 'current folder Drive ID'}. "
        "new_name and new_parent_id are both optional — omit either to skip that change. "
        "Returns JSON with updated file metadata."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            file_id = data.get("file_id", "").strip()
            if not file_id:
                return json.dumps({"error": "file_id is required"})

            params: dict = {"fileId": file_id}
            body: dict = {}

            if data.get("new_name"):
                body["name"] = data["new_name"].strip()
            if data.get("new_parent_id"):
                params["addParents"] = data["new_parent_id"].strip()
            if data.get("old_parent_id"):
                params["removeParents"] = data["old_parent_id"].strip()

            args = [
                "drive", "files", "update",
                "--params", json.dumps(params),
                "--json", json.dumps(body),
            ]
            result = self._run_gws(args)
            return json.dumps(result)
        except GWSCliError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"drive_move_rename failed: {e}"})


class GWSDriveExportTool(GWSCliBase, BaseTool):
    name: str = "drive_export_text"
    description: str = (
        "Export a Google Workspace document (Docs, Slides, Sheets) to plain text. "
        "Input JSON: {'file_id': 'Drive file ID', 'mime_type': 'source MIME type'}. "
        "Returns the plain text content as a string. "
        "Use this for Google Docs/Slides/Sheets — NOT for PDFs (use drive_download for those)."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            file_id = data.get("file_id", "").strip()
            if not file_id:
                return "error: file_id is required"
            params = {"fileId": file_id, "mimeType": "text/plain"}
            result = self._run_gws(["drive", "files", "export", "--params", json.dumps(params)])
            if isinstance(result, str):
                return result
            return json.dumps(result)
        except GWSCliError as e:
            return f"error: {e}"
        except Exception as e:
            return f"error: drive_export_text failed: {e}"


class GWSDriveDownloadTool(GWSCliBase, BaseTool):
    name: str = "drive_download_file"
    description: str = (
        "Download a binary file (e.g. PDF) from Google Drive to /tmp. "
        "Input JSON: {'file_id': 'Drive file ID', 'filename': 'local filename to save as'}. "
        "Returns the full local path where the file was saved, or an error string."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            file_id = data.get("file_id", "").strip()
            filename = os.path.basename(data.get("filename", f"{file_id}.bin").strip())
            if not file_id:
                return "error: file_id is required"
            local_path = f"/tmp/{filename}"
            params = {"fileId": file_id, "alt": "media"}
            args = ["drive", "files", "get", "--params", json.dumps(params), "--output", local_path]
            self._run_gws(args)
            return local_path
        except GWSCliError as e:
            return f"error: {e}"
        except Exception as e:
            return f"error: drive_download_file failed: {e}"


class GWSSheetsReadRangeTool(GWSCliBase, BaseTool):
    name: str = "sheets_read_range"
    description: str = (
        "Read a range of values from a Google Spreadsheet. "
        "Input JSON: {'spreadsheet_id': 'sheet ID', 'range': 'TabName!A:G'}. "
        "Returns JSON with a 'values' key containing a list of rows (each row is a list of strings)."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            sheet_id = data.get("spreadsheet_id", "").strip()
            range_str = data.get("range", "").strip()
            if not sheet_id or not range_str:
                return json.dumps({"error": "spreadsheet_id and range are required"})
            params = {"spreadsheetId": sheet_id, "range": range_str}
            result = self._run_gws(["sheets", "spreadsheets", "values", "get", "--params", json.dumps(params)])
            return json.dumps(result)
        except GWSCliError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"sheets_read_range failed: {e}"})


class GWSSheetsAppendRowTool(GWSCliBase, BaseTool):
    name: str = "sheets_append_row"
    description: str = (
        "Append one or more rows to a Google Spreadsheet range. "
        "Input JSON: {'spreadsheet_id': 'sheet ID', 'range': 'TabName!A:I', "
        "'values': ['col1', 'col2', ...]}. "
        "For multiple rows pass a list of lists: 'values': [['r1c1','r1c2'],['r2c1','r2c2']]. "
        "Returns JSON with update metadata."
    )

    def _run(self, input_data: str = "{}") -> str:
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            sheet_id = data.get("spreadsheet_id", "").strip()
            range_str = data.get("range", "").strip()
            values = data.get("values", [])
            if not sheet_id or not range_str or not values:
                return json.dumps({"error": "spreadsheet_id, range, and values are required"})
            if values and not isinstance(values[0], list):
                values = [values]
            params = {
                "spreadsheetId": sheet_id,
                "range": range_str,
                "valueInputOption": "USER_ENTERED",
                "insertDataOption": "INSERT_ROWS",
            }
            body = {"values": values}
            result = self._run_gws([
                "sheets", "spreadsheets", "values", "append",
                "--params", json.dumps(params),
                "--json", json.dumps(body),
            ])
            return json.dumps(result)
        except GWSCliError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"sheets_append_row failed: {e}"})


# ── Tool bundles ──────────────────────────────────────────────
GWS_DOC_ROUTING_TOOLS = [
    GWSDriveCreateFolderTool(),
    GWSDriveMoveRenameTool(),
    GWSDriveExportTool(),
    GWSDriveDownloadTool(),
    GWSSheetsReadRangeTool(),
    GWSSheetsAppendRowTool(),
]
