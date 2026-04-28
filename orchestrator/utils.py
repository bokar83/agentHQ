"""
utils.py - Small helpers shared across modules.

Owns:
- sanitize_text: redact secrets before logging (imported by notifier).
- _query_system: live system introspection for the chat 'query_system' tool.
- _build_summary / _save_overflow_if_needed: result summary helpers.
- _extract_file_text: extract readable text from uploaded files (basic types).
"""
import os
import re


def sanitize_text(text: str) -> str:
    """
    Redact potential secrets and sensitive data from text before logging.
    """
    if not text:
        return ""

    token_patterns = [
        r"sk-[a-zA-Z0-9]{32,}",              # OpenAI-style
        r"pk_[a-zA-Z0-9]{32,}",              # Stripe-style
        r"ghp_[a-zA-Z0-9]{36,}",             # GitHub PAT
        r"Bearer\s+[a-zA-Z0-9\-\._~+/]+=*",  # Bearer tokens
    ]
    sanitized = text
    for pattern in token_patterns:
        sanitized = re.sub(pattern, "[REDACTED_TOKEN]", sanitized, flags=re.IGNORECASE)

    # Passwords in connection strings / SMTP
    sanitized = re.sub(r":([^:@\s]+)@([a-zA-Z0-9\.-]+)", r":[REDACTED_PASS]@\2", sanitized)  # pragma: allowlist secret

    return sanitized


def _query_system() -> str:
    """
    Live system introspection tool. Called by the chat LLM when the user
    asks about agents, task types, system config, or capabilities.
    Always returns accurate data from the running modules - never stale.
    """
    lines = ["=== agentsHQ LIVE SYSTEM STATE ===\n"]

    # Agent registry - read from agents.py builder functions
    try:
        import agents as agent_module
        builders = [f for f in dir(agent_module) if f.startswith("build_") and f.endswith("_agent")]
        lines.append(f"AGENTS ({len(builders)} registered):")
        agent_descriptions = {
            "build_planner_agent":       "Plans and structures every task before execution",
            "build_researcher_agent":    "Finds and synthesizes information using web search",
            "build_copywriter_agent":    "Writes reports, articles, documents, and long-form copy",
            "build_social_media_agent":  "Creates posts and content in Boubacar's voice (X, LinkedIn, etc.)",
            "build_consulting_agent":    "Produces frameworks, proposals, diagnostics, strategy briefs",
            "build_web_builder_agent":   "Builds complete single-file HTML/CSS/JS websites",
            "build_app_builder_agent":   "Builds interactive web applications",
            "build_code_agent":          "Writes, debugs, and explains code in any language",
            "build_qa_agent":            "Reviews all deliverables, fixes issues, ensures professional quality",
            "build_orchestrator_agent":  "Handles unknown/ambiguous requests, escalates or improvises",
            "build_agent_creator_agent": "Designs specs for new specialist agents when a gap is identified",
        }
        for b in sorted(builders):
            name = b.replace("build_", "").replace("_agent", "").replace("_", " ").title()
            desc = agent_descriptions.get(b, "Specialist agent")
            lines.append(f"  - {name}: {desc}")
    except Exception as e:
        lines.append(f"  [Could not load agent list: {e}]")

    # Task types - read live from router
    try:
        from router import TASK_TYPES
        lines.append(f"\nTASK TYPES ({len(TASK_TYPES) - 1} actionable):")
        for key, meta in TASK_TYPES.items():
            if key == "chat":
                continue
            lines.append(f"  - {key}: {meta['description']}")
            lines.append(f"    trigger keywords: {', '.join(meta.get('keywords', [])[:5])}")
    except Exception as e:
        lines.append(f"  [Could not load task types: {e}]")

    # Approval queue — live pending items
    try:
        import approval_queue as aq
        pending = aq.list_pending()
        if pending:
            lines.append(f"\nAPPROVAL QUEUE ({len(pending)} pending):")
            for item in pending[:10]:
                crew = item.crew_name if hasattr(item, "crew_name") else item.get("crew_name", "?")
                ptype = item.proposal_type if hasattr(item, "proposal_type") else item.get("proposal_type", "?")
                item_id = item.id if hasattr(item, "id") else item.get("id", "?")
                payload = item.payload if hasattr(item, "payload") else item.get("payload", {})
                title = ""
                if isinstance(payload, dict):
                    title = payload.get("title") or payload.get("subject") or payload.get("task") or ""
                lines.append(f"  [{item_id}] {crew} / {ptype}" + (f" — {title[:80]}" if title else ""))
        else:
            lines.append("\nAPPROVAL QUEUE: empty (no pending items)")
    except Exception as e:
        lines.append(f"\nAPPROVAL QUEUE: [could not fetch: {e}]")

    # Recent outputs
    try:
        output_dir = os.environ.get("AGENTS_OUTPUT_DIR", "/app/outputs")
        if os.path.exists(output_dir):
            files = sorted(
                [f for f in os.listdir(output_dir) if not os.path.isdir(os.path.join(output_dir, f))],
                key=lambda f: os.path.getmtime(os.path.join(output_dir, f)),
                reverse=True,
            )[:10]
            if files:
                lines.append(f"\nRECENT OUTPUT FILES (last 10 in {output_dir}):")
                for f in files:
                    lines.append(f"  - {f}")
            else:
                lines.append(f"\nOUTPUT DIRECTORY: {output_dir} (empty)")
    except Exception:
        pass

    # Infrastructure
    _vps_ip = os.environ.get("VPS_IP", "(unset)")
    lines.append("\nINFRASTRUCTURE:")
    lines.append(f"  VPS: {_vps_ip} (orchestrator on port 8000, localhost-only since 2026-04-22)")
    lines.append("  Public URL: https://agentshq.boubacarbarry.com/chat (browser) + /api/orc (API)")
    lines.append("  Telegram bot: @agentsHQ4Bou_bot")
    lines.append("  n8n: https://n8n.srv1040886.hstgr.cloud")
    lines.append("  GitHub: https://github.com/bokar83/agentHQ")
    lines.append("  Memory: Qdrant (vector) + PostgreSQL (conversation history)")

    return "\n".join(lines)


def _build_summary(task_type: str, full_output: str, files_created: list, execution_time: float) -> str:
    """Build a summary message for Telegram."""
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
    """
    Extract readable text from an uploaded file for injection into a task prompt.
    Supports PDF, DOCX, plain text formats. Returns a placeholder string for
    unsupported types.
    """
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".pdf":
            try:
                import pdfplumber
                pages = []
                with pdfplumber.open(path) as pdf:
                    for p in pdf.pages[:20]:
                        t = p.extract_text()
                        if t:
                            pages.append(t)
                return "\n\n".join(pages) or "[PDF: no extractable text]"
            except ImportError:
                return "[PDF: pdfplumber not installed]"

        if ext in (".docx", ".doc"):
            try:
                import docx
                doc = docx.Document(path)
                return "\n".join(p.text for p in doc.paragraphs if p.text) or "[DOCX: no text extracted]"
            except ImportError:
                return "[DOCX: python-docx not installed]"

        if ext in (".txt", ".md", ".json", ".py", ".js", ".ts", ".html", ".css", ".yaml", ".yml", ".xml", ".sql", ".csv", ".tsv"):
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read(50000) or "[File: empty]"

        return f"[File: {filename} ({ext}), extraction not implemented for this type]"
    except Exception as e:
        return f"[Error extracting {filename}: {e}]"
