import re
import os

def sanitize_text(text: str) -> str:
    """
    Redact potential secrets and sensitive data from text before logging.
    """
    if not text:
        return ""
    
    # 1. Redact API keys / Tokens (long alphanumeric strings like OpenAI/OpenRouter keys)
    # Typically 40-50 chars. We look for sk-[a-zA-Z0-9]{32,} or similar.
    # This is a broad regex to catch various token formats.
    token_patterns = [
        r"sk-[a-zA-Z0-9]{32,}",                # OpenAI-style
        r"pk_[a-zA-Z0-9]{32,}",                # Stripe-style
        r"ghp_[a-zA-Z0-9]{36,}",               # GitHub PAT
        r"Bearer\s+[a-zA-Z0-9\-\._~+/]+=*",   # Bearer tokens
    ]
    
    sanitized = text
    for pattern in token_patterns:
        sanitized = re.sub(pattern, "[REDACTED_TOKEN]", sanitized, flags=re.IGNORECASE)
    
    # 2. Redact passwords in connection strings / SMTP
    # e.g., smtp://user:pass@host  # pragma: allowlist secret
    sanitized = re.sub(r":([^:@\s]+)@([a-zA-Z0-9\.-]+)", r":[REDACTED_PASS]@\2", sanitized)  # pragma: allowlist secret
    
    return sanitized

def _query_system() -> str:
    """
    Live system introspection tool.
    """
    import agents as agent_module
    from router import TASK_TYPES
    
    lines = ["=== agentsHQ LIVE SYSTEM STATE ===\n"]

    try:
        builders = [f for f in dir(agent_module) if f.startswith("build_") and f.endswith("_agent")]
        lines.append(f"AGENTS ({len(builders)} registered):")
        for b in sorted(builders):
            name = b.replace("build_", "").replace("_agent", "").replace("_", " ").title()
            lines.append(f"  - {name}")
    except Exception as e:
        lines.append(f"  [Could not load agent list: {e}]")

    try:
        lines.append(f"\nTASK TYPES ({len(TASK_TYPES) - 1} actionable):")
        for key, meta in TASK_TYPES.items():
            if key == "chat": continue
            lines.append(f"  - {key}: {meta['description']}")
    except Exception as e:
        lines.append(f"  [Could not load task types: {e}]")

    return "\n".join(lines)

def _build_summary(task_type: str, full_output: str, files_created: list, execution_time: float) -> str:
    """
    Build a summary message for Telegram.
    """
    label = task_type.replace("_", " ").title()
    lines = [
        f"--- {label} Task Complete ---",
        f"Time: {execution_time:.0f}s",
    ]
    if files_created:
        lines.append(f"Files saved: {', '.join(files_created)}")
    lines.append("")

    MAX_CONTENT = 3700
    if full_output:
        content = full_output.strip()
        if len(content) > MAX_CONTENT:
            content = content[:MAX_CONTENT] + "\n\n[reply 'more' to see the rest]"
        lines.append(content)
    
    return "\n".join(lines)

def _save_overflow_if_needed(session_key: str, full_output: str, task_type: str) -> None:
    """Save overflow to DB if output exceeds one Telegram message."""
    MAX_CONTENT = 3700
    if full_output and len(full_output.strip()) > MAX_CONTENT:
        try:
            from memory import save_overflow
            save_overflow(session_key, full_output.strip(), MAX_CONTENT, task_type)
        except Exception:
            pass

def _extract_file_text(path: str, filename: str) -> str:
    """Extract readable text from an uploaded file."""
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext in (".txt", ".md", ".json", ".py", ".js", ".ts", ".html", ".css", ".yaml", ".yml", ".xml", ".sql"):
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read(50000) or "[File: empty]"
        # ... other formats truncated for brevity in this step
        return f"[File: {filename} ({ext}) — extraction not implemented for this type]"
    except Exception as e:
        return f"[Error extracting {filename}: {e}]"
