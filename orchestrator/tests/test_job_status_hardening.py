# orchestrator/tests/test_job_status_hardening.py
#
# Regression tests for the "pending job poll returns 500" bug.
# Root cause: get_job() returned None for task_type/result/execution_time
# while a job was pending/running. JobStatusResponse(**job) then crashed
# Pydantic validation because defaults only apply to absent keys, not None.
# FastAPI returned plain-text "Internal Server Error" which the browser
# tried to JSON.parse(), producing the exact user-visible error message.
import os
import sys

import pytest

ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)

from schemas import JobStatusResponse


class TestJobStatusResponseWithNullDbFields:
    """
    JobStatusResponse must never raise ValidationError regardless of which
    fields the Postgres row has populated. A pending or running job has
    task_type=NULL, result=NULL, execution_time=NULL in the DB.
    """

    def test_pending_job_all_nulls_accepted(self):
        """Simulates get_job() return for a brand-new pending job."""
        row = {
            "job_id": "abc12345",
            "status": "pending",
            "task_type": None,
            "result": None,
            "files_created": [],
            "execution_time": None,
            "error": None,
        }
        resp = JobStatusResponse(**row)
        assert resp.job_id == "abc12345"
        assert resp.status == "pending"
        assert resp.task_type == "" or resp.task_type is None
        assert resp.result == "" or resp.result is None
        assert resp.execution_time == 0.0 or resp.execution_time is None

    def test_running_job_nulls_accepted(self):
        """Simulates get_job() return mid-execution."""
        row = {
            "job_id": "def67890",
            "status": "running",
            "task_type": None,
            "result": None,
            "files_created": [],
            "execution_time": None,
            "error": None,
        }
        resp = JobStatusResponse(**row)
        assert resp.status == "running"

    def test_completed_job_has_values(self):
        """Completed jobs must pass through real values unchanged."""
        row = {
            "job_id": "ghi11111",
            "status": "completed",
            "task_type": "chat",
            "result": "8",
            "files_created": [],
            "execution_time": 3.14,
            "error": None,
        }
        resp = JobStatusResponse(**row)
        assert resp.task_type == "chat"
        assert resp.result == "8"
        assert resp.execution_time == pytest.approx(3.14)

    def test_failed_job_with_error(self):
        """Failed jobs carry error text; result may be the friendly message."""
        row = {
            "job_id": "jkl22222",
            "status": "failed",
            "task_type": None,
            "result": "Task failed. (Diagnostic: some error)",
            "files_created": [],
            "execution_time": None,
            "error": "some error",
        }
        resp = JobStatusResponse(**row)
        assert resp.status == "failed"
        assert resp.error == "some error"


class TestGetJobNormalization:
    """
    get_job() must coerce None DB values to safe defaults so the dict it
    returns never causes a downstream ValidationError.
    """

    def test_get_job_coerces_none_to_defaults(self):
        from unittest.mock import MagicMock, patch

        fake_row = (
            "abc12345",   # job_id
            "pending",    # status
            None,         # task_type
            None,         # result
            [],           # files_created
            None,         # execution_time
            None,         # error
            "2026-04-26", # created_at
            "2026-04-26", # updated_at
        )

        with patch("memory._pg_conn") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor

            import memory
            result = memory.get_job("abc12345")

        assert result["task_type"] == ""
        assert result["result"] == ""
        assert result["execution_time"] == 0.0
        # Must not raise when fed to the response model
        resp = JobStatusResponse(**result)
        assert resp.status == "pending"
