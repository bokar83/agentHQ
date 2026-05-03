"""
llm_helpers.py - Shared LLM client factory and completion helper.

All OpenRouter / OpenAI-compatible calls in agentsHQ should go through
this module so the client config, model env vars, and default headers
live in exactly one place.

Usage (recommended, DB-driven):
    from llm_helpers import call_llm
    result = call_llm(messages, model=None, model_key="ATLAS_CHAT_MODEL")

Usage (deliberate cost pinning, e.g. validator/classifier roles):
    from llm_helpers import call_llm
    result = call_llm(messages, model="anthropic/claude-haiku-4.5")
"""

import logging
import os

logger = logging.getLogger("agentsHQ.llm_helpers")

_DEFAULT_MODEL = "anthropic/claude-haiku-4.5"

# Sentinel value for the deprecated module-level constants. Any caller still
# passing these as the model arg will produce a loud OpenRouter error rather
# than silently degrading to haiku. Background: 2026-05-02 we shipped a fix
# where chat traffic was silently routing to haiku because the constants below
# were resolved at import time from empty env vars and call sites passed them
# as model=. The DB-driven config layer was bypassed. Loud failure beats
# silent default. See feedback_resolve_model_bypasses_db_when_arg_set.md.
_DEPRECATED_CONST_SENTINEL = "_DEPRECATED_USE_MODEL_KEY_PARAM"

# Deprecated. Pass model=None and model_key="CHAT_MODEL" instead so the DB
# layer is consulted at call time.
CHAT_MODEL: str = _DEPRECATED_CONST_SENTINEL
HELPER_MODEL: str = _DEPRECATED_CONST_SENTINEL
ATLAS_CHAT_MODEL: str = _DEPRECATED_CONST_SENTINEL

CHAT_TEMPERATURE: float = float(os.environ.get("CHAT_TEMPERATURE") or "0.7")
CHAT_SANDBOX: bool = (os.environ.get("CHAT_SANDBOX") or "false").lower() == "true"


def get_openrouter_client():
    """
    Return a configured openai.OpenAI client pointed at OpenRouter.
    Import is lazy so the module can be imported in test contexts without
    requiring openai to be available at module load time.
    """
    import openai

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY env var is not set.")

    return openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://agentshq.catalystworks.com",
            "X-Title": "agentsHQ",
        },
    )


def _resolve_model(model: str | None, key: str = "CHAT_MODEL") -> str:
    """
    Resolve a model slug with priority: explicit arg > DB config > env var > default.
    DB config lookup is non-fatal; falls back to env/default on any error.
    """
    if model:
        return model
    fallback = os.environ.get(key) or _DEFAULT_MODEL
    try:
        from agent_config import get_config
        return get_config(key, default=fallback) or fallback
    except Exception:
        return fallback


def call_llm(
    messages: list,
    model: str | None = None,
    model_key: str = "CHAT_MODEL",
    temperature: float = 0.7,
    tools: list | None = None,
    tool_choice: str = "auto",
    max_tokens: int | None = None,
    response_format: dict | None = None,
):
    """
    Make a single chat completion call via OpenRouter.

    Args:
        messages: OpenAI-format messages list (role/content dicts).
        model: Optional explicit model slug (e.g. "anthropic/claude-haiku-4.5").
               Pass None to consult DB config + env for the role identified by
               model_key. Pinning a literal here is for cost-sensitive validator
               or classifier roles only.
        model_key: agent_config DB key consulted when model=None. Defaults to
                   "CHAT_MODEL". Chat handlers that need the atlas role pass
                   "ATLAS_CHAT_MODEL". Compressor passes "HELPER_MODEL".
        temperature: Sampling temperature (0.0-1.0).
        tools: Optional list of tool defs in OpenAI tool format.
        tool_choice: "auto" | "none" | {"type": "function", ...}
        max_tokens: Optional token ceiling.
        response_format: Optional e.g. {"type": "json_object"}.

    Returns:
        openai ChatCompletion response object. The resolved model name is
        attached to the response as `_resolved_model` for callers that want
        to surface it to the user (UI footer, telemetry, etc.).

    Raises:
        RuntimeError if OPENROUTER_API_KEY is missing or if a deprecated
        sentinel (CHAT_MODEL/ATLAS_CHAT_MODEL/HELPER_MODEL constant) was
        passed as model=. Loud failure prevents the silent-haiku regression
        seen on 2026-05-02.
        openai.APIError on API failures (caller should handle).
    """
    if model == _DEPRECATED_CONST_SENTINEL:
        raise RuntimeError(
            "call_llm received the deprecated CHAT_MODEL/ATLAS_CHAT_MODEL/HELPER_MODEL "
            "constant as model=. These constants are no longer resolved at import time. "
            "Pass model=None plus model_key='CHAT_MODEL' (or 'ATLAS_CHAT_MODEL' / "
            "'HELPER_MODEL') so the agent_config DB layer is consulted at call time. "
            "See feedback_resolve_model_bypasses_db_when_arg_set.md."
        )
    resolved_model = _resolve_model(model, key=model_key)
    client = get_openrouter_client()

    kwargs: dict = {
        "model": resolved_model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if response_format is not None:
        kwargs["response_format"] = response_format

    logger.debug(f"LLM call model={resolved_model} msgs={len(messages)} tools={len(tools or [])}")
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        try:
            from provider_health import record_failure
            from notifier import send_message
            result = record_failure("openrouter")
            if result.get("just_tripped"):
                chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
                if chat_id:
                    send_message(chat_id, (
                        "ATLAS ALERT: OpenRouter circuit tripped\n"
                        "3 failures in the last 5 minutes.\n\n"
                        "Manual switch command (run on your laptop):\n"
                        "  python skills/switch-provider/switch_provider.py therouter --cli claude\n\n"
                        "Restore when fixed:\n"
                        "  python skills/switch-provider/switch_provider.py openrouter --cli claude"
                    ))
        except Exception as _cb_err:
            logger.debug(f"circuit breaker record skipped (non-fatal): {_cb_err}")
        raise

    logger.debug(f"LLM response model={resolved_model} finish={response.choices[0].finish_reason}")

    # Attach the resolved model to the response so callers can surface it to
    # the user (UI footer, telemetry). OpenRouter's response.model is also
    # populated, but we want the slug WE asked for, not whatever provider
    # OpenRouter chose to route through.
    try:
        response._resolved_model = resolved_model
    except (AttributeError, TypeError):
        pass

    # Fire-and-forget ledger insert. The usage_logger queues the generation_id,
    # waits 12s for OpenRouter indexing, then GETs /api/v1/generation for cost
    # + token detail and inserts a row into llm_calls. Without this, chat calls
    # never reach the ledger and the spend dashboard is blind to chat traffic.
    try:
        from usage_logger import log_call, current_call_context
        gen_id = getattr(response, "id", None)
        if gen_id:
            ctx = dict(current_call_context.get() or {})
            ctx.setdefault("model", resolved_model)
            ctx.setdefault("project", "agentsHQ")
            log_call(generation_id=gen_id, metadata=ctx)
    except Exception as _log_e:
        logger.debug(f"usage_logger skipped (non-fatal): {_log_e}")

    return response
