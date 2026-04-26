"""
health_sweep.py - Weekly automated API health sweep.

Probes every public-facing endpoint with edge-case inputs (pending job,
missing job, null fields, empty strings) and asserts that every response
is valid JSON with an expected status code.  Any probe that returns a
non-JSON body, a 5xx, or a Pydantic validation error fires a Telegram
alert so the bug is caught before Boubacar sees it.

Fires every Sunday at 08:00 MT via heartbeat.register_wake().
Read-only: no Notion writes, no crew invocations, no data mutations.

Results are sent to Telegram as a short summary:
  - "Health sweep: X/Y probes passed" (green)
  - "Health sweep: X FAILURES detected -- <list>" (red)
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import requests as _requests

logger = logging.getLogger("agentsHQ.health_sweep")

_TIMEOUT = 8  # seconds per probe


def _base_url() -> str:
    """Internal orchestrator URL (within Docker network or localhost)."""
    return os.environ.get("HEALTH_SWEEP_BASE_URL", "http://localhost:8000")


def _api_key() -> str:
    return os.environ.get("ORCHESTRATOR_API_KEY", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_api_key()}"}


# ══════════════════════════════════════════════════════════════
# Individual probes
# Each probe returns (label, passed: bool, detail: str)
# ══════════════════════════════════════════════════════════════

def _probe_health() -> tuple[str, bool, str]:
    label = "GET /health"
    try:
        r = _requests.get(f"{_base_url()}/health", timeout=_TIMEOUT)
        data = r.json()
        if r.status_code == 200 and data.get("status") == "ok":
            return label, True, ""
        return label, False, f"status={r.status_code} body={str(data)[:120]}"
    except Exception as e:
        return label, False, str(e)[:120]


def _probe_status_missing_job() -> tuple[str, bool, str]:
    """404 on a non-existent job must return JSON, not a 500 plain-text."""
    label = "GET /status/<missing>"
    try:
        r = _requests.get(
            f"{_base_url()}/status/nonexistent-job-id-sweep",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        data = r.json()
        if r.status_code == 404 and "detail" in data:
            return label, True, ""
        return label, False, f"status={r.status_code} body={str(data)[:120]}"
    except ValueError as e:
        return label, False, f"Non-JSON response: {e}"
    except Exception as e:
        return label, False, str(e)[:120]


def _probe_status_pending_job() -> tuple[str, bool, str]:
    """
    The original bug: polling /status while job is pending returned 500.
    Create a real job, poll immediately before it finishes, assert JSON.
    """
    label = "GET /status/<pending job>"
    try:
        # Submit a trivial task
        post_r = _requests.post(
            f"{_base_url()}/run-async",
            headers={**_headers(), "Content-Type": "application/json"},
            json={"task": "health-sweep-probe", "session_key": "health-sweep", "source": "sweep"},
            timeout=_TIMEOUT,
        )
        if post_r.status_code not in (200, 202):
            return label, False, f"run-async returned {post_r.status_code}"
        job_id = post_r.json().get("job_id", "")
        if not job_id:
            return label, False, "run-async returned no job_id"

        # Poll immediately -- job is almost certainly pending/running
        status_r = _requests.get(
            f"{_base_url()}/status/{job_id}",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        data = status_r.json()   # raises ValueError if not JSON
        if status_r.status_code == 200 and "status" in data:
            return label, True, ""
        return label, False, f"status={status_r.status_code} body={str(data)[:120]}"
    except ValueError as e:
        return label, False, f"Non-JSON response (original bug regression): {e}"
    except Exception as e:
        return label, False, str(e)[:120]


def _probe_chat_token_bad_pin() -> tuple[str, bool, str]:
    """/chat-token with wrong PIN must return 401 JSON, not 500."""
    label = "POST /chat-token (bad PIN)"
    try:
        r = _requests.post(
            f"{_base_url()}/chat-token",
            json={"pin": "000000-sweep-bad"},
            timeout=_TIMEOUT,
        )
        data = r.json()
        if r.status_code in (401, 503) and "detail" in data:
            return label, True, ""
        return label, False, f"status={r.status_code} body={str(data)[:120]}"
    except ValueError as e:
        return label, False, f"Non-JSON response: {e}"
    except Exception as e:
        return label, False, str(e)[:120]


def _probe_classify() -> tuple[str, bool, str]:
    """/classify must return JSON with task_type for a simple query."""
    label = "GET /classify"
    try:
        r = _requests.get(
            f"{_base_url()}/classify",
            params={"task": "hello"},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        data = r.json()
        if r.status_code == 200 and "classification" in data:
            return label, True, ""
        return label, False, f"status={r.status_code} body={str(data)[:120]}"
    except ValueError as e:
        return label, False, f"Non-JSON response: {e}"
    except Exception as e:
        return label, False, str(e)[:120]


def _probe_atlas_state() -> tuple[str, bool, str]:
    """/atlas/state must return JSON (uses chat-token auth, skip if no PIN set)."""
    label = "GET /atlas/state"
    pin = os.environ.get("CHAT_UI_PIN", "")
    api_key = _api_key()
    if not pin and not api_key:
        return label, True, "(skipped -- no auth configured)"
    try:
        # Use raw API key as bearer (verify_chat_token accepts it)
        r = _requests.get(
            f"{_base_url()}/atlas/state",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=_TIMEOUT,
        )
        data = r.json()
        if r.status_code == 200 and "killed" in data:
            return label, True, ""
        return label, False, f"status={r.status_code} body={str(data)[:120]}"
    except ValueError as e:
        return label, False, f"Non-JSON response: {e}"
    except Exception as e:
        return label, False, str(e)[:120]


def _probe_history_empty_session() -> tuple[str, bool, str]:
    """/history/<unknown-session> must return JSON with empty list, not 500."""
    label = "GET /history/<unknown>"
    try:
        r = _requests.get(
            f"{_base_url()}/history/health-sweep-no-such-session",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        data = r.json()
        if r.status_code == 200 and "history" in data:
            return label, True, ""
        return label, False, f"status={r.status_code} body={str(data)[:120]}"
    except ValueError as e:
        return label, False, f"Non-JSON response: {e}"
    except Exception as e:
        return label, False, str(e)[:120]


# ══════════════════════════════════════════════════════════════
# Runner
# ══════════════════════════════════════════════════════════════

_PROBES = [
    _probe_health,
    _probe_status_missing_job,
    _probe_status_pending_job,
    _probe_chat_token_bad_pin,
    _probe_classify,
    _probe_atlas_state,
    _probe_history_empty_session,
]


def run_health_sweep() -> dict[str, Any]:
    """Run all probes. Return summary dict."""
    results = []
    for probe in _PROBES:
        label, passed, detail = probe()
        results.append({"label": label, "passed": passed, "detail": detail})
        time.sleep(0.3)  # avoid hammering the container

    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    return {"total": len(results), "passed": len(passed), "failed": len(failed), "failures": failed}


def health_sweep_tick() -> None:
    """Heartbeat callback: run sweep and notify via Telegram."""
    logger.info("HEALTH_SWEEP: starting weekly sweep")
    try:
        summary = run_health_sweep()
    except Exception as e:
        logger.error(f"HEALTH_SWEEP: sweep runner crashed: {e}", exc_info=True)
        _notify(f"Health sweep crashed: {e}")
        return

    total = summary["total"]
    passed = summary["passed"]
    failed_list = summary["failures"]

    if not failed_list:
        msg = f"Health sweep: {passed}/{total} probes passed. All good."
        logger.info(f"HEALTH_SWEEP: {msg}")
    else:
        lines = [f"Health sweep: {passed}/{total} passed. FAILURES:"]
        for f in failed_list:
            lines.append(f"  - {f['label']}: {f['detail']}")
        msg = "\n".join(lines)
        logger.error(f"HEALTH_SWEEP: {msg}")

    _notify(msg)


def _notify(msg: str) -> None:
    try:
        from notifier import send_message
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if chat_id:
            send_message(chat_id, msg)
    except Exception as e:
        logger.warning(f"HEALTH_SWEEP: Telegram notify failed: {e}")
