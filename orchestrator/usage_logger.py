"""
usage_logger.py — Per-call LLM ledger
======================================
Logs every OpenRouter completion to the `llm_calls` table in local Postgres.

Design:
  - Fire-and-forget from any thread (CrewAI runs in worker threads via asyncio.to_thread)
  - Background daemon thread drains a queue.Queue, polls OpenRouter /api/v1/generation,
    inserts one row per call
  - Never raises. Never blocks the calling thread. Failures log a warning and drop.

Usage:
    from usage_logger import log_call
    log_call(generation_id="gen-abc123", metadata={
        "project": "agentsHQ",
        "agent_name": "hunter",
        "task_type": "outreach",
        "crew_name": "hunter_crew",
        "session_key": "tg-12345",
        "council_run_id": None,
        "model": "anthropic/claude-sonnet-4.6",
    })

Context propagation:
    The orchestrator sets `current_call_context` (a contextvars.ContextVar)
    before crew.kickoff(). The LLM wrapper reads it and merges it into metadata.
"""

import os
import time
import queue
import logging
import threading
import contextvars
from typing import Optional

logger = logging.getLogger("agentsHQ.usage_logger")

# ── Public context var (set by orchestrator before crew.kickoff) ──
# Keys: project, task_type, crew_name, session_key, council_run_id
current_call_context: contextvars.ContextVar[dict] = contextvars.ContextVar(
    "llm_call_context", default={}
)

# ── Queue + worker ────────────────────────────────────────────────
_QUEUE: "queue.Queue[tuple[str, dict]]" = queue.Queue(maxsize=10_000)
_WORKER_STARTED = False
_WORKER_LOCK = threading.Lock()
_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_GENERATION_DELAY_S = 12.0  # OpenRouter indexing delay before /generation is queryable


def log_call(generation_id: Optional[str], metadata: dict) -> None:
    """
    Fire-and-forget. Safe to call from any thread, sync or async.
    Drops silently if generation_id is missing or queue is full.
    """
    if not generation_id:
        return
    _ensure_worker()
    try:
        _QUEUE.put_nowait((generation_id, dict(metadata)))
    except queue.Full:
        logger.warning("usage_logger queue full, dropping call %s", generation_id)


def _ensure_worker() -> None:
    """Lazy-start the background worker thread on first call."""
    global _WORKER_STARTED
    if _WORKER_STARTED:
        return
    with _WORKER_LOCK:
        if _WORKER_STARTED:
            return
        t = threading.Thread(target=_worker_loop, name="usage_logger", daemon=True)
        t.start()
        _WORKER_STARTED = True
        logger.info("usage_logger worker thread started")


def _worker_loop() -> None:
    """Drain the queue. One row per generation_id."""
    import httpx
    import psycopg2
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set, usage_logger will skip OpenRouter polls")

    while True:
        try:
            generation_id, metadata = _QUEUE.get()
        except Exception:
            time.sleep(1)
            continue

        try:
            time.sleep(_GENERATION_DELAY_S)
            data = _fetch_generation(generation_id, api_key)
            _insert_row(generation_id, metadata, data)
        except Exception as e:
            logger.warning("usage_logger failed for %s: %s", generation_id, e)


def _fetch_generation(generation_id: str, api_key: str) -> dict:
    """
    GET /api/v1/generation?id=<id>. Returns dict with usage details, or {}.
    OpenRouter occasionally returns 404 if the row hasn't indexed yet -- one retry.
    """
    if not api_key:
        return {}
    import httpx

    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{_OPENROUTER_BASE}/generation"
    for attempt in range(2):
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(url, params={"id": generation_id}, headers=headers)
            if r.status_code == 200:
                return r.json().get("data", {}) or {}
            if r.status_code == 404 and attempt == 0:
                time.sleep(2)
                continue
            logger.warning(
                "OpenRouter /generation returned %s for %s",
                r.status_code, generation_id,
            )
            return {}
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
                continue
            logger.warning("OpenRouter /generation fetch failed for %s: %s", generation_id, e)
            return {}
    return {}


def _insert_row(generation_id: str, metadata: dict, data: dict) -> None:
    """INSERT one row into llm_calls. Non-fatal on failure."""
    import psycopg2
    from db import get_local_connection

    # OpenRouter generation response shape (subset we use):
    #   tokens_prompt, tokens_completion
    #   native_tokens_prompt, native_tokens_completion
    #   native_tokens_cached  (cache READ on Anthropic)
    #   total_cost (USD)
    #   latency
    #   model, finish_reason
    tokens_prompt = int(data.get("tokens_prompt") or data.get("native_tokens_prompt") or 0)
    tokens_completion = int(
        data.get("tokens_completion") or data.get("native_tokens_completion") or 0
    )
    tokens_cached_read = int(data.get("native_tokens_cached") or 0)
    tokens_cached_write = int(
        data.get("native_tokens_cache_write")
        or data.get("cache_creation_input_tokens")
        or 0
    )
    cost_usd = float(data.get("total_cost") or 0.0)
    latency_ms = int(data.get("latency") or 0) or None
    finish_reason = data.get("finish_reason") or data.get("native_finish_reason")
    model = data.get("model") or metadata.get("model") or "unknown"

    sql = """
        INSERT INTO llm_calls (
            generation_id, project, agent_name, task_type, crew_name,
            session_key, council_run_id, model,
            tokens_prompt, tokens_completion,
            tokens_cached_read, tokens_cached_write,
            cost_usd, latency_ms, finish_reason, error
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (generation_id) DO NOTHING
    """
    params = (
        generation_id,
        metadata.get("project"),
        metadata.get("agent_name"),
        metadata.get("task_type"),
        metadata.get("crew_name"),
        metadata.get("session_key"),
        metadata.get("council_run_id"),
        model,
        tokens_prompt,
        tokens_completion,
        tokens_cached_read,
        tokens_cached_write,
        cost_usd,
        latency_ms,
        finish_reason,
        None,
    )

    conn = None
    try:
        conn = get_local_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning("usage_logger insert failed for %s: %s", generation_id, e)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# Anthropic list price per 1M tokens (USD). Used when logging direct Anthropic
# SDK calls (research_engine), which don't hit OpenRouter and can't be priced via
# /api/v1/generation. Update when Anthropic changes pricing.
_ANTHROPIC_PRICING = {
    "claude-opus-4-1":    {"in": 15.00, "out": 75.00, "cache_read": 1.50,  "cache_write": 18.75},
    "claude-opus-4":      {"in": 15.00, "out": 75.00, "cache_read": 1.50,  "cache_write": 18.75},
    "claude-sonnet-4-5":  {"in":  3.00, "out": 15.00, "cache_read": 0.30,  "cache_write":  3.75},
    "claude-sonnet-4":    {"in":  3.00, "out": 15.00, "cache_read": 0.30,  "cache_write":  3.75},
    "claude-haiku-4-5":   {"in":  1.00, "out":  5.00, "cache_read": 0.10,  "cache_write":  1.25},
}


def log_anthropic_call(response, metadata: dict) -> None:
    """Log a direct Anthropic SDK response to the llm_calls table.

    Unlike log_call(), this writes synchronously with pricing computed locally
    from response.usage. Use for research_engine and any other direct-SDK caller
    that bypasses OpenRouter.
    """
    try:
        gen_id = getattr(response, "id", None)
        if not gen_id:
            return
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        tokens_in = int(getattr(usage, "input_tokens", 0) or 0)
        tokens_out = int(getattr(usage, "output_tokens", 0) or 0)
        tokens_cache_read = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        tokens_cache_write = int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
        model_full = getattr(response, "model", "") or metadata.get("model") or "unknown"

        price = None
        for key, p in _ANTHROPIC_PRICING.items():
            if key in model_full:
                price = p
                break
        if price:
            cost_usd = (
                tokens_in * price["in"]
                + tokens_out * price["out"]
                + tokens_cache_read * price["cache_read"]
                + tokens_cache_write * price["cache_write"]
            ) / 1_000_000.0
        else:
            cost_usd = 0.0

        data = {
            "tokens_prompt": tokens_in,
            "tokens_completion": tokens_out,
            "native_tokens_cached": tokens_cache_read,
            "native_tokens_cache_write": tokens_cache_write,
            "total_cost": cost_usd,
            "model": model_full,
            "finish_reason": getattr(response, "stop_reason", None),
        }
        _ensure_worker()
        _insert_row(gen_id, metadata, data)
    except Exception as e:
        logger.warning("log_anthropic_call failed: %s", e)


def merge_context(extra: Optional[dict] = None) -> dict:
    """
    Read current_call_context and merge with extra fields.
    Used by callers that have additional metadata (agent_name, model) to add.
    """
    base = dict(current_call_context.get() or {})
    if extra:
        base.update({k: v for k, v in extra.items() if v is not None})
    return base


# ── litellm global callback ───────────────────────────────────────
# Registered once at orchestrator startup. Fires on every litellm.completion
# that succeeds, regardless of whether the caller is CrewAI, council.py, or
# a direct script. One-line wiring captures the whole system.

try:
    from litellm.integrations.custom_logger import CustomLogger as _LiteLLMCustomLogger
except Exception:  # pragma: no cover - litellm always installed in our stack
    _LiteLLMCustomLogger = object


class _LiteLLMLogger(_LiteLLMCustomLogger):
    """
    litellm CustomLogger hook. Captures response.id and queues it for the
    background worker to enrich via OpenRouter /generation.

    Must subclass litellm.integrations.custom_logger.CustomLogger -- litellm
    routes events through that base class only.
    """
    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            gen_id = None
            if hasattr(response_obj, "id"):
                gen_id = response_obj.id
            elif isinstance(response_obj, dict):
                gen_id = response_obj.get("id")
            if not gen_id:
                return

            # Caller metadata (project, task_type, crew_name, session_key, council_run_id)
            ctx = dict(current_call_context.get() or {})

            # litellm passes the full model_call_details dict as kwargs.
            # Explicit `metadata={...}` param lands at kwargs["metadata"] or
            # kwargs["litellm_params"]["metadata"].
            meta = {}
            if isinstance(kwargs, dict):
                meta = kwargs.get("metadata") or {}
                if not meta:
                    lp = kwargs.get("litellm_params") or {}
                    if isinstance(lp, dict):
                        meta = lp.get("metadata") or {}
            meta = meta if isinstance(meta, dict) else {}

            # Explicit call metadata wins over contextvar.
            merged = {**ctx, **{k: v for k, v in meta.items() if v is not None}}
            model = kwargs.get("model") if isinstance(kwargs, dict) else None
            if model:
                merged["model"] = model

            log_call(gen_id, merged)
        except Exception as e:
            logger.debug("litellm callback failed: %s", e)

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        # Failures don't have generation_ids to enrich. Skip.
        pass

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        self.log_success_event(kwargs, response_obj, start_time, end_time)

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        pass


_LITELLM_REGISTERED = False


def install_litellm_callback() -> None:
    """Register the global litellm CustomLogger callback. Idempotent.

    Council calls go through litellm.completion directly, so the standard
    callback path works for them. CrewAI's LLM.set_callbacks overwrites
    litellm.callbacks on every Crew init, so this won't catch CrewAI calls
    -- that's by design (CrewAI calls aren't logged in Phase 1).
    """
    global _LITELLM_REGISTERED
    if _LITELLM_REGISTERED:
        return
    try:
        import litellm
        cb = _LiteLLMLogger()
        if cb not in litellm.callbacks:
            litellm.callbacks.append(cb)
        _LITELLM_REGISTERED = True
        logger.info("usage_logger: litellm callback installed (council path)")
    except Exception as e:
        logger.warning("usage_logger: failed to install litellm callback: %s", e)
