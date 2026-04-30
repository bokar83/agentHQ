"""
llm_helpers.py - Shared LLM client factory and completion helper.

All OpenRouter / OpenAI-compatible calls in agentsHQ should go through
this module so the client config, model env vars, and default headers
live in exactly one place.

Usage:
    from llm_helpers import call_llm, CHAT_MODEL, HELPER_MODEL

    result = call_llm(messages, model=CHAT_MODEL, temperature=0.7)
    reply = result.choices[0].message.content
"""

import logging
import os

logger = logging.getLogger("agentsHQ.llm_helpers")

# Model env vars - override per-call via the model= param.
# `os.environ.get(KEY) or DEFAULT` (not `os.environ.get(KEY, DEFAULT)`) so that
# empty strings from docker-compose `${VAR}` substitution fall back to the
# default instead of being passed through as model="".
_DEFAULT_MODEL = "anthropic/claude-haiku-4.5"
CHAT_MODEL: str = os.environ.get("CHAT_MODEL") or _DEFAULT_MODEL
HELPER_MODEL: str = os.environ.get("HELPER_MODEL") or _DEFAULT_MODEL
ATLAS_CHAT_MODEL: str = os.environ.get("ATLAS_CHAT_MODEL") or _DEFAULT_MODEL
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
    try:
        from agent_config import get_config
        return get_config(key, default=CHAT_MODEL) or CHAT_MODEL
    except Exception:
        return os.environ.get(key, CHAT_MODEL)


def call_llm(
    messages: list,
    model: str | None = None,
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
        model: Model slug, e.g. "anthropic/claude-haiku-4.5". Defaults to
               the DB-overridable CHAT_MODEL config key.
        temperature: Sampling temperature (0.0-1.0).
        tools: Optional list of tool defs in OpenAI tool format.
        tool_choice: "auto" | "none" | {"type": "function", ...}
        max_tokens: Optional token ceiling.
        response_format: Optional e.g. {"type": "json_object"}.

    Returns:
        openai ChatCompletion response object.

    Raises:
        RuntimeError if OPENROUTER_API_KEY is missing.
        openai.APIError on API failures (caller should handle).
    """
    resolved_model = _resolve_model(model)
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
    response = client.chat.completions.create(**kwargs)
    logger.debug(f"LLM response model={resolved_model} finish={response.choices[0].finish_reason}")
    return response
