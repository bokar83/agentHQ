"""
halo_tracer.py — CrewAI -> HALO-compatible OTel JSONL trace writer.

Subscribes to CrewAI's event bus and writes one JSONL span per event
to a local file in the inference.net OTel format that HALO Engine reads.

Activation: set HALO_TRACING_ENABLED=true in .env.
Output path: HALO_TRACES_PATH (default: /app/data/halo_traces.jsonl).

The file is append-only. To start a fresh diagnostic pass, delete it
or move it aside before re-running the harness. Parallel container runs
each write to the same file (append is atomic on Linux); or set
HALO_TRACES_PATH to a per-run path.

Usage (from app.py startup, behind env gate):
    from halo_tracer import maybe_install_halo_tracer
    maybe_install_halo_tracer()

HALO loop (once >=50 traces collected):
    pip install halo-engine
    halo /app/data/halo_traces.jsonl \
        --prompt "What are the most common failure modes across failed traces?" \
        --model gpt-4.1-2025-04-14 --max-turns 15
"""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("agentsHQ.halo_tracer")

_DEFAULT_PATH = "/app/data/halo_traces.jsonl"
_PROJECT_ID = "agentshq-atlas"
_SERVICE_NAME = "orc-crewai"
_SCHEMA_VERSION = 1


def _now_iso() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}000Z"


def _safe_str(v: Any, limit: int = 2000) -> str | None:
    if v is None:
        return None
    s = v if isinstance(v, str) else json.dumps(v, default=str, separators=(",", ":"))
    return s[:limit] if len(s) > limit else s


def _build_span(
    *,
    span_id: str,
    trace_id: str,
    parent_span_id: str,
    name: str,
    start_time: str,
    end_time: str,
    status_code: str,
    status_message: str,
    observation_kind: str,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    attrs = {k: v for k, v in attributes.items() if v is not None}
    attrs.update({
        "inference.export.schema_version": _SCHEMA_VERSION,
        "inference.project_id": _PROJECT_ID,
        "inference.observation_kind": observation_kind,
    })
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "trace_state": "",
        "name": name,
        "kind": "SPAN_KIND_INTERNAL",
        "start_time": start_time,
        "end_time": end_time,
        "status": {"code": status_code, "message": status_message},
        "resource": {"attributes": {"service.name": _SERVICE_NAME}},
        "scope": {"name": "crewai", "version": ""},
        "attributes": attrs,
    }


class HaloTracer:
    """Writes HALO-compatible JSONL spans from CrewAI events."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._fh = open(path, mode="a", encoding="utf-8")
        # Maps crew_name -> trace_id so all events in a crew run share one trace.
        self._crew_traces: dict[str, str] = {}
        # Maps call_id -> (span_id, start_time, trace_id) for LLM spans.
        self._llm_spans: dict[str, tuple[str, str, str]] = {}
        # Maps (tool_name, agent_role) -> (span_id, start_time, trace_id).
        self._tool_spans: dict[str, tuple[str, str, str]] = {}
        logger.info(f"[halo_tracer] writing traces to {path}")

    def _write(self, span: dict[str, Any]) -> None:
        line = json.dumps(span, separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            self._fh.write(line + "\n")
            self._fh.flush()

    def _trace_for_crew(self, crew_name: str | None) -> str:
        key = crew_name or "unknown"
        if key not in self._crew_traces:
            self._crew_traces[key] = str(uuid.uuid4()).replace("-", "")
        return self._crew_traces[key]

    # ------------------------------------------------------------------
    # Crew-level events
    # ------------------------------------------------------------------

    def on_crew_kickoff_started(self, crew_name: str | None, ts: str) -> None:
        tid = self._trace_for_crew(crew_name)
        span = _build_span(
            span_id=str(uuid.uuid4()).replace("-", ""),
            trace_id=tid,
            parent_span_id="",
            name=f"crew.kickoff.{crew_name or 'unknown'}",
            start_time=ts,
            end_time=ts,
            status_code="STATUS_CODE_OK",
            status_message="",
            observation_kind="AGENT",
            attributes={"agent.name": crew_name or "unknown", "crew.name": crew_name},
        )
        self._write(span)

    def on_crew_kickoff_completed(self, crew_name: str | None, ts: str) -> None:
        # Reset trace so next run gets a fresh trace_id.
        self._crew_traces.pop(crew_name or "unknown", None)

    def on_crew_kickoff_failed(self, crew_name: str | None, error: str, ts: str) -> None:
        tid = self._trace_for_crew(crew_name)
        span = _build_span(
            span_id=str(uuid.uuid4()).replace("-", ""),
            trace_id=tid,
            parent_span_id="",
            name=f"crew.kickoff_failed.{crew_name or 'unknown'}",
            start_time=ts,
            end_time=ts,
            status_code="STATUS_CODE_ERROR",
            status_message=error[:500] if error else "",
            observation_kind="AGENT",
            attributes={"agent.name": crew_name or "unknown", "error.message": error},
        )
        self._write(span)
        self._crew_traces.pop(crew_name or "unknown", None)

    # ------------------------------------------------------------------
    # LLM events
    # ------------------------------------------------------------------

    def on_llm_call_started(
        self, call_id: str, model: str | None, crew_name: str | None, agent_role: str | None, ts: str
    ) -> None:
        tid = self._trace_for_crew(crew_name)
        sid = str(uuid.uuid4()).replace("-", "")
        self._llm_spans[call_id] = (sid, ts, tid)
        span = _build_span(
            span_id=sid,
            trace_id=tid,
            parent_span_id="",
            name=f"llm.call.{model or 'unknown'}",
            start_time=ts,
            end_time=ts,
            status_code="STATUS_CODE_OK",
            status_message="",
            observation_kind="LLM",
            attributes={
                "llm.model_name": model,
                "llm.provider": "openrouter",
                "inference.agent_name": agent_role,
                "inference.llm.model_name": model,
            },
        )
        self._write(span)

    def on_llm_call_completed(
        self,
        call_id: str,
        model: str | None,
        usage: dict[str, Any] | None,
        crew_name: str | None,
        agent_role: str | None,
        ts: str,
    ) -> None:
        cached = self._llm_spans.pop(call_id, None)
        tid = cached[2] if cached else self._trace_for_crew(crew_name)
        start = cached[1] if cached else ts
        sid = cached[0] if cached else str(uuid.uuid4()).replace("-", "")
        in_tok = None
        out_tok = None
        if usage:
            in_tok = usage.get("prompt_tokens") or usage.get("input_tokens")
            out_tok = usage.get("completion_tokens") or usage.get("output_tokens")
        span = _build_span(
            span_id=sid,
            trace_id=tid,
            parent_span_id="",
            name=f"llm.completed.{model or 'unknown'}",
            start_time=start,
            end_time=ts,
            status_code="STATUS_CODE_OK",
            status_message="",
            observation_kind="LLM",
            attributes={
                "llm.model_name": model,
                "llm.provider": "openrouter",
                "llm.token_count.prompt": in_tok,
                "llm.token_count.completion": out_tok,
                "inference.agent_name": agent_role,
                "inference.llm.model_name": model,
                "inference.llm.input_tokens": in_tok,
                "inference.llm.output_tokens": out_tok,
            },
        )
        self._write(span)

    def on_llm_call_failed(
        self, call_id: str, error: str, model: str | None, crew_name: str | None, ts: str
    ) -> None:
        cached = self._llm_spans.pop(call_id, None)
        tid = cached[2] if cached else self._trace_for_crew(crew_name)
        start = cached[1] if cached else ts
        sid = cached[0] if cached else str(uuid.uuid4()).replace("-", "")
        span = _build_span(
            span_id=sid,
            trace_id=tid,
            parent_span_id="",
            name=f"llm.failed.{model or 'unknown'}",
            start_time=start,
            end_time=ts,
            status_code="STATUS_CODE_ERROR",
            status_message=error[:500] if error else "",
            observation_kind="LLM",
            attributes={
                "llm.model_name": model,
                "error.message": error,
                "inference.llm.model_name": model,
            },
        )
        self._write(span)

    # ------------------------------------------------------------------
    # Tool events
    # ------------------------------------------------------------------

    def on_tool_started(
        self,
        tool_name: str,
        tool_args: Any,
        agent_role: str | None,
        crew_name: str | None,
        task_name: str | None,
        ts: str,
    ) -> None:
        tid = self._trace_for_crew(crew_name)
        sid = str(uuid.uuid4()).replace("-", "")
        key = f"{tool_name}:{agent_role}"
        self._tool_spans[key] = (sid, ts, tid)
        span = _build_span(
            span_id=sid,
            trace_id=tid,
            parent_span_id="",
            name=f"tool.{tool_name}",
            start_time=ts,
            end_time=ts,
            status_code="STATUS_CODE_OK",
            status_message="",
            observation_kind="TOOL",
            attributes={
                "tool.name": tool_name,
                "input.value": _safe_str(tool_args),
                "inference.agent_name": agent_role,
                "task.name": task_name,
            },
        )
        self._write(span)

    def on_tool_finished(
        self,
        tool_name: str,
        output: Any,
        agent_role: str | None,
        crew_name: str | None,
        task_name: str | None,
        ts: str,
    ) -> None:
        key = f"{tool_name}:{agent_role}"
        cached = self._tool_spans.pop(key, None)
        tid = cached[2] if cached else self._trace_for_crew(crew_name)
        start = cached[1] if cached else ts
        sid = cached[0] if cached else str(uuid.uuid4()).replace("-", "")
        span = _build_span(
            span_id=sid,
            trace_id=tid,
            parent_span_id="",
            name=f"tool.{tool_name}",
            start_time=start,
            end_time=ts,
            status_code="STATUS_CODE_OK",
            status_message="",
            observation_kind="TOOL",
            attributes={
                "tool.name": tool_name,
                "output.value": _safe_str(output),
                "inference.agent_name": agent_role,
                "task.name": task_name,
            },
        )
        self._write(span)

    def on_tool_error(
        self,
        tool_name: str,
        error: Any,
        agent_role: str | None,
        crew_name: str | None,
        task_name: str | None,
        ts: str,
    ) -> None:
        key = f"{tool_name}:{agent_role}"
        cached = self._tool_spans.pop(key, None)
        tid = cached[2] if cached else self._trace_for_crew(crew_name)
        start = cached[1] if cached else ts
        sid = cached[0] if cached else str(uuid.uuid4()).replace("-", "")
        span = _build_span(
            span_id=sid,
            trace_id=tid,
            parent_span_id="",
            name=f"tool.{tool_name}",
            start_time=start,
            end_time=ts,
            status_code="STATUS_CODE_ERROR",
            status_message=_safe_str(error, 500) or "",
            observation_kind="TOOL",
            attributes={
                "tool.name": tool_name,
                "error.message": _safe_str(error),
                "inference.agent_name": agent_role,
                "task.name": task_name,
            },
        )
        self._write(span)

    def shutdown(self) -> None:
        with self._lock:
            try:
                self._fh.flush()
                self._fh.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Event listener wiring
# ---------------------------------------------------------------------------

class HaloTracerListener:
    """Minimal CrewAI event listener that delegates to HaloTracer."""

    def __init__(self, tracer: HaloTracer) -> None:
        self._tracer = tracer
        self._setup()

    def _ts(self, event: Any) -> str:
        ts = getattr(event, "timestamp", None)
        if ts is None:
            return _now_iso()
        if isinstance(ts, str):
            return ts
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond:06d}000Z"
        return _now_iso()

    def _setup(self) -> None:
        try:
            from crewai.events.event_bus import crewai_event_bus
            from crewai.events.types.crew_events import (
                CrewKickoffStartedEvent,
                CrewKickoffCompletedEvent,
                CrewKickoffFailedEvent,
            )
            from crewai.events.types.llm_events import (
                LLMCallStartedEvent,
                LLMCallCompletedEvent,
                LLMCallFailedEvent,
            )
            from crewai.events.types.tool_usage_events import (
                ToolUsageStartedEvent,
                ToolUsageFinishedEvent,
                ToolUsageErrorEvent,
            )
            t = self._tracer

            @crewai_event_bus.on(CrewKickoffStartedEvent)
            def _crew_start(source: Any, event: CrewKickoffStartedEvent) -> None:
                t.on_crew_kickoff_started(event.crew_name, self._ts(event))

            @crewai_event_bus.on(CrewKickoffCompletedEvent)
            def _crew_done(source: Any, event: CrewKickoffCompletedEvent) -> None:
                t.on_crew_kickoff_completed(event.crew_name, self._ts(event))

            @crewai_event_bus.on(CrewKickoffFailedEvent)
            def _crew_fail(source: Any, event: CrewKickoffFailedEvent) -> None:
                t.on_crew_kickoff_failed(event.crew_name, getattr(event, "error", ""), self._ts(event))

            @crewai_event_bus.on(LLMCallStartedEvent)
            def _llm_start(source: Any, event: LLMCallStartedEvent) -> None:
                t.on_llm_call_started(
                    event.call_id,
                    event.model,
                    getattr(event, "crew_name", None),
                    getattr(event, "agent_role", None),
                    self._ts(event),
                )

            @crewai_event_bus.on(LLMCallCompletedEvent)
            def _llm_done(source: Any, event: LLMCallCompletedEvent) -> None:
                t.on_llm_call_completed(
                    event.call_id,
                    event.model,
                    event.usage,
                    getattr(event, "crew_name", None),
                    getattr(event, "agent_role", None),
                    self._ts(event),
                )

            @crewai_event_bus.on(LLMCallFailedEvent)
            def _llm_fail(source: Any, event: LLMCallFailedEvent) -> None:
                t.on_llm_call_failed(
                    event.call_id,
                    event.error,
                    event.model,
                    getattr(event, "crew_name", None),
                    self._ts(event),
                )

            @crewai_event_bus.on(ToolUsageStartedEvent)
            def _tool_start(source: Any, event: ToolUsageStartedEvent) -> None:
                t.on_tool_started(
                    event.tool_name,
                    event.tool_args,
                    event.agent_role,
                    getattr(event, "crew_name", None),
                    event.task_name,
                    self._ts(event),
                )

            @crewai_event_bus.on(ToolUsageFinishedEvent)
            def _tool_done(source: Any, event: ToolUsageFinishedEvent) -> None:
                t.on_tool_finished(
                    event.tool_name,
                    event.output,
                    event.agent_role,
                    getattr(event, "crew_name", None),
                    event.task_name,
                    self._ts(event),
                )

            @crewai_event_bus.on(ToolUsageErrorEvent)
            def _tool_err(source: Any, event: ToolUsageErrorEvent) -> None:
                t.on_tool_error(
                    event.tool_name,
                    event.error,
                    event.agent_role,
                    getattr(event, "crew_name", None),
                    event.task_name,
                    self._ts(event),
                )

            logger.info("[halo_tracer] event listeners registered (crew/llm/tool)")

        except Exception as e:
            logger.warning(f"[halo_tracer] listener setup failed (non-fatal): {e}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_tracer: HaloTracer | None = None


def maybe_install_halo_tracer() -> None:
    """Install HaloTracer if HALO_TRACING_ENABLED=true. Call once at startup."""
    global _tracer
    if os.environ.get("HALO_TRACING_ENABLED", "false").lower() != "true":
        return
    path = os.environ.get("HALO_TRACES_PATH", _DEFAULT_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _tracer = HaloTracer(path)
    HaloTracerListener(_tracer)
    logger.info(f"[halo_tracer] ACTIVE — traces -> {path}")
