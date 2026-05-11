"""
test_heartbeat_tracing.py — Milestone 18 HALO Heartbeat Tracing Unit Tests
========================================================================
Verifies:
  - Mock wake registration and fire emits OTel start and completed spans
  - Trace ID is successfully popped from tracer cache on wake completion/failure
  - Exception inside callback generates a failure span and fails open safely
  - Trace-writing errors never crash the heartbeat background fire loop
"""
import os
import sys
import json
import uuid
import tempfile
from datetime import datetime

# Insert orchestrator path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))

import pytest
import pytz

from heartbeat import register_wake, unregister_wake, _fire, WakeRegistration, SELF_TEST_CREW


@pytest.fixture
def temp_trace_file():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def test_heartbeat_tracing_success(temp_trace_file, monkeypatch):
    """Test successful wake tracing writes starting and completed spans sharing a trace ID."""
    from halo_tracer import HaloTracer
    import halo_tracer

    # Set up active tracer pointing to temp file
    tracer = HaloTracer(temp_trace_file)
    monkeypatch.setattr(halo_tracer, "_tracer", tracer)

    called = False
    def mock_callback():
        nonlocal called
        called = True

    wake_name = f"test-wake-{uuid.uuid4().hex[:6]}"
    crew_name = SELF_TEST_CREW
    wake = WakeRegistration(
        name=wake_name,
        crew_name=crew_name,
        callback=mock_callback,
    )

    now = datetime.now(pytz.timezone("America/Denver"))
    _fire(wake, now)

    assert called is True

    # Read output spans
    with open(temp_trace_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()]

    # Should contain exactly two spans: started and completed
    assert len(lines) == 2

    start_span = lines[0]
    completed_span = lines[1]

    # Ensure spans share trace ID
    assert start_span["trace_id"] == completed_span["trace_id"]
    assert len(start_span["trace_id"]) > 0

    # Verify span structure
    assert start_span["name"] == f"heartbeat.wake.{wake_name}"
    assert start_span["attributes"]["heartbeat.wake_name"] == wake_name
    assert start_span["attributes"]["heartbeat.crew_name"] == crew_name
    assert start_span["attributes"]["inference.observation_kind"] == "SERVER"
    assert start_span["status"]["code"] == "STATUS_CODE_OK"

    assert completed_span["name"] == f"heartbeat.wake.{wake_name}"
    assert completed_span["status"]["code"] == "STATUS_CODE_OK"

    # Verify cache is cleared
    with tracer._lock:
        assert crew_name not in tracer._crew_traces


def test_heartbeat_tracing_failure(temp_trace_file, monkeypatch):
    """Test callback exception correctly writes a failure span with error message."""
    from halo_tracer import HaloTracer
    import halo_tracer

    tracer = HaloTracer(temp_trace_file)
    monkeypatch.setattr(halo_tracer, "_tracer", tracer)

    def failing_callback():
        raise ValueError("CRITICAL_TEST_ERROR")

    wake_name = f"test-failing-wake"
    crew_name = SELF_TEST_CREW
    wake = WakeRegistration(
        name=wake_name,
        crew_name=crew_name,
        callback=failing_callback,
    )

    now = datetime.now(pytz.timezone("America/Denver"))
    _fire(wake, now) # Should handle error inside callback and not crash

    # Read output spans
    with open(temp_trace_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()]

    assert len(lines) == 2
    start_span = lines[0]
    failed_span = lines[1]

    assert start_span["trace_id"] == failed_span["trace_id"]
    assert failed_span["status"]["code"] == "STATUS_CODE_ERROR"
    assert "CRITICAL_TEST_ERROR" in failed_span["status"]["message"]
    assert failed_span["attributes"]["error.message"] == "CRITICAL_TEST_ERROR"

    # Verify cache is cleared
    with tracer._lock:
        assert crew_name not in tracer._crew_traces


def test_heartbeat_tracing_fail_open(monkeypatch):
    """Test tracer exceptions never propagate to interrupt the wake callback execution."""
    import halo_tracer

    # Mock a malfunctioning tracer that raises errors on every hook
    class BrokenTracer:
        def on_heartbeat_wake_started(self, *args, **kwargs):
            raise RuntimeError("DISK_FULL_ERR")
        def on_heartbeat_wake_completed(self, *args, **kwargs):
            raise RuntimeError("DISK_FULL_ERR")
        def on_heartbeat_wake_failed(self, *args, **kwargs):
            raise RuntimeError("DISK_FULL_ERR")

    monkeypatch.setattr(halo_tracer, "_tracer", BrokenTracer())

    called = False
    def mock_callback():
        nonlocal called
        called = True

    wake = WakeRegistration(
        name="test-fail-open-wake",
        crew_name=SELF_TEST_CREW,
        callback=mock_callback,
    )

    now = datetime.now(pytz.timezone("America/Denver"))
    _fire(wake, now) # Should completely absorb tracer RuntimeError

    assert called is True # Callback must run anyway!
