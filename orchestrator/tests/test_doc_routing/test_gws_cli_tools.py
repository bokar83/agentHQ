"""
Tests for GWS CLI tool classes.
All tests mock subprocess.run to avoid real Drive API calls.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


def make_mock_run(stdout: str, returncode: int = 0):
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    mock.stderr = ""
    return mock


class TestGWSCliBase:
    def test_run_gws_returns_parsed_json(self):
        from skills.doc_routing.gws_cli_tools import GWSCliBase
        base = GWSCliBase()
        mock_result = make_mock_run('{"id": "abc123", "name": "TestFolder"}')
        with patch("skills.doc_routing.gws_cli_tools.subprocess.run", return_value=mock_result) as mock_sub:
            result = base._run_gws(["drive", "files", "get", "--params", '{"fileId":"abc123"}'])
        assert result == {"id": "abc123", "name": "TestFolder"}

    def test_run_gws_raises_on_nonzero_exit(self):
        from skills.doc_routing.gws_cli_tools import GWSCliBase, GWSCliError
        base = GWSCliBase()
        mock_result = make_mock_run('{"error": {"message": "Not found"}}', returncode=1)
        with patch("skills.doc_routing.gws_cli_tools.subprocess.run", return_value=mock_result):
            with pytest.raises(GWSCliError, match="Not found"):
                base._run_gws(["drive", "files", "get", "--params", '{"fileId":"bad"}'])


class TestGWSDriveCreateFolder:
    def test_creates_folder_returns_id(self):
        from skills.doc_routing.gws_cli_tools import GWSDriveCreateFolderTool
        tool = GWSDriveCreateFolderTool()
        mock_result = make_mock_run('{"id": "folder123", "name": "01_Admin", "mimeType": "application/vnd.google-apps.folder"}')
        with patch("skills.doc_routing.gws_cli_tools.subprocess.run", return_value=mock_result):
            result = tool._run(json.dumps({"name": "01_Admin", "parent_id": "parent456"}))
        parsed = json.loads(result)
        assert parsed["id"] == "folder123"

    def test_missing_name_returns_error(self):
        from skills.doc_routing.gws_cli_tools import GWSDriveCreateFolderTool
        tool = GWSDriveCreateFolderTool()
        result = tool._run(json.dumps({"parent_id": "parent456"}))
        assert "error" in result.lower()


class TestGWSDriveMoveRename:
    def test_renames_and_moves_file(self):
        from skills.doc_routing.gws_cli_tools import GWSDriveMoveRenameTool
        tool = GWSDriveMoveRenameTool()
        mock_result = make_mock_run('{"id": "file123", "name": "CLIENT_AcmeCorp_notes_2026-04-12_discovery-call"}')  # pragma: allowlist secret
        with patch("skills.doc_routing.gws_cli_tools.subprocess.run", return_value=mock_result):
            result = tool._run(json.dumps({
                "file_id": "file123",
                "new_name": "CLIENT_AcmeCorp_notes_2026-04-12_discovery-call",  # pragma: allowlist secret
                "new_parent_id": "targetFolder456",
                "old_parent_id": "reviewQueue789"  # pragma: allowlist secret
            }))
        parsed = json.loads(result)
        assert parsed["id"] == "file123"


class TestGWSDriveExport:
    def test_exports_google_doc_to_text(self):
        from skills.doc_routing.gws_cli_tools import GWSDriveExportTool
        tool = GWSDriveExportTool()
        mock_result = make_mock_run("This is the document plain text content.")
        mock_result.stdout = "This is the document plain text content."
        with patch("skills.doc_routing.gws_cli_tools.subprocess.run", return_value=mock_result):
            result = tool._run(json.dumps({"file_id": "docABC", "mime_type": "application/vnd.google-apps.document"}))
        assert "document plain text" in result


class TestGWSSheetsReadRange:
    def test_reads_routing_matrix(self):
        from skills.doc_routing.gws_cli_tools import GWSSheetsReadRangeTool
        tool = GWSSheetsReadRangeTool()
        mock_data = {"values": [["Priority", "Signal Keywords", "Domain"], ["1", "agentsHQ,CrewAI", "CATALYST"]]}
        mock_result = make_mock_run(json.dumps(mock_data))
        with patch("skills.doc_routing.gws_cli_tools.subprocess.run", return_value=mock_result):
            result = tool._run(json.dumps({"spreadsheet_id": "sheet123", "range": "Routing Matrix!A:G"}))
        parsed = json.loads(result)
        assert parsed["values"][1][2] == "CATALYST"


class TestGWSSheetsAppendRow:
    def test_appends_row_to_log(self):
        from skills.doc_routing.gws_cli_tools import GWSSheetsAppendRowTool
        tool = GWSSheetsAppendRowTool()
        mock_result = make_mock_run('{"updates": {"updatedRows": 1}}')
        with patch("skills.doc_routing.gws_cli_tools.subprocess.run", return_value=mock_result):
            result = tool._run(json.dumps({
                "spreadsheet_id": "sheet123",
                "range": "Auto-Filed Log!A:I",
                "values": ["filename", "CLIENT", "path", "Client Notebook", "high", "0.95", "2026-04-12", "manual-upload"]
            }))
        parsed = json.loads(result)
        assert parsed["updates"]["updatedRows"] == 1
