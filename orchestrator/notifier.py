"""
notifier.py — All Telegram Bot API calls for agentsHQ.
No other file sends Telegram messages.

Env vars required:
  ORCHESTRATOR_TELEGRAM_BOT_TOKEN  — bot token for Agents HQ (Primary)
  TELEGRAM_CHAT_ID                 — user's chat ID for Agents HQ
  REMOAT_TELEGRAM_BOT_TOKEN       — bot token for Remoat (Mirror)
  REMOAT_TELEGRAM_CHAT_ID         — user's chat ID for Remoat
"""
import os
import random
import logging
import requests
import smtplib
import sys
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("agentsHQ.notifier")

# Telegram config (Agents HQ Bot)
ORCHESTRATOR_BOT_TOKEN = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{ORCHESTRATOR_BOT_TOKEN}" if ORCHESTRATOR_BOT_TOKEN else ""

# SMTP config (Placeholder - user needs to set these in .env)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
REPORT_EMAILS = [
    os.environ.get("REPORT_EMAIL", "bokar83@gmail.com"),
    "boubacarbusiness@gmail.com",
    "catalystworks.ai@gmail.com"
]

# Remoat Config (Remote IDE Bridge)
REMOAT_BOT_TOKEN = os.environ.get("REMOAT_TELEGRAM_BOT_TOKEN", "")
REMOAT_CHAT_ID = os.environ.get("REMOAT_TELEGRAM_CHAT_ID", "")
REMOAT_API_BASE = f"https://api.telegram.org/bot{REMOAT_BOT_TOKEN}" if REMOAT_BOT_TOKEN else ""

TASK_TYPE_LABELS = {
    "research_report":        "Research Agent is on the case",
    "consulting_deliverable": "Consulting Agent is building your deliverable",
    "website_build":          "Web Builder Agent is coding your site",
    "3d_website_build":       "3D Web Builder Agent is on it",
    "app_build":              "App Builder Agent is on it",
    "code_task":              "Code Agent is writing your solution",
    "general_writing":        "Writing Agent is crafting your document",
    "social_content":         "Social Agent is creating your content",
    "linkedin_x_campaign":    "Social Agent is building your LinkedIn/X campaign",
    "notion_overhaul":        "Notion Agent is redesigning your workspace",
    "agent_creation":         "Agent Creator is drafting the spec",
    "voice_polishing":        "Voice Polisher is humanising your text",
    "hunter_task":            "Growth Hunter is prospecting for leads",
    "crm_outreach":           "Outreach Agent is drafting your cold emails",
    "enrich_leads":           "Enrichment Agent is filling in missing data",
    "mark_outreach_sent":     "CRM Agent is updating your lead statuses",
    "prompt_engineering":     "Prompt Engineer is rewriting your prompt",
    "news_brief":             "News Agent is scanning the headlines",
    "gws_task":               "Google Workspace Agent is on it",
    "notion_capture":         "Ideas Agent is capturing your thought in Notion",
    "memory_capture":         "Got it — saving to memory",
    "agent_team":             "The full team is on it",
    "chat":                   "...",
    "unknown":                "Agents are on it",
    "content_review":         "Content Reviewer is checking your posts",
    "content_push_to_drive":  "Pushing approved posts to Google Drive",
    "forge_kpi_refresh":      "Running Forge KPI refresh",
    "doc_routing":            "Document Routing Agent is classifying your file",
}

TASK_TYPE_CREWS = {
    "research_report":        "Researcher + Copywriter",
    "consulting_deliverable": "Consulting Agent + Planner",
    "website_build":          "Web Builder + QA Agent",
    "3d_website_build":       "3D Web Builder + QA Agent",
    "app_build":              "App Builder + QA Agent",
    "code_task":              "Code Agent + QA Agent",
    "general_writing":        "Writer + QA Agent",
    "social_content":         "Social Media Agent",
    "linkedin_x_campaign":    "Social Media Agent (LinkedIn + X)",
    "notion_overhaul":        "Notion Agent + Planner",
    "agent_creation":         "Agent Creator + Planner",
    "voice_polishing":        "Voice Polisher",
    "hunter_task":            "Growth Hunter + Researcher",
    "crm_outreach":           "Outreach Agent (direct Supabase + Gmail)",
    "enrich_leads":           "Enrichment Agent (Prospeo + web scrape)",
    "mark_outreach_sent":     "CRM Agent (direct Supabase)",
    "prompt_engineering":     "Prompt Engineer",
    "news_brief":             "News Agent + Researcher",
    "gws_task":               "Google Workspace Agent",
    "notion_capture":         "Ideas Curator (Notion write/read)",
    "agent_team":             "Full multi-agent team",
    "unknown":                "Orchestrator (improvising)",
    "content_review":         "Content Reviewer (voice + quality gate)",
    "content_push_to_drive":  "Drive Publisher (Notion + Google Drive)",
    "forge_kpi_refresh":      "KPI Engine (direct Python)",
}

SIMPSONS_QUOTES = [
    "It's taking forever... or is it just me? — Homer",
    "I am so smart! S-M-R-T. The agents are proving it right now. — Homer",
    "Mmm... deep research... — Homer",
    "Trying is the first step towards failure. Good thing your agents don't try — they DO. — Homer",
    "Don't have a cow — still chewing on it. — Bart",
    "Excellent... the plan is proceeding. — Mr. Burns",
    "In this house, we obey the laws of thermodynamics. Processing takes time. — Homer",
    "This is the greatest thing I've ever been asked to do. — Homer",
    "Why do they call it a shortcut when it never is? — Homer",
    "This better be worth it... it will be. — Homer",
    "I'm not normally a praying man, but if you're up there... speed up the agents. — Homer",
    "The key to happiness is not to ask questions. Also: wait for the ping. — Homer",
    "Remember: an idiot is anyone slower than me. These agents are not idiots. — Homer",
    "I've learned that life is one crushing defeat after another — until the deliverable arrives. — Homer",
    "Every time I try to leave, something pulls me back. Just like this research task. — Homer",
    "Ahhh, the agents are thinking. There's nothing more satisfying... except nachos. — Homer",
    "I can't promise I'll try, but I'll try to try. The agents promised more. — Homer",
    "Facts are meaningless. You can use facts to prove anything that's even remotely true. Like: your task is almost done. — Homer",
    "To alcohol! The cause of, and solution to, all of life's problems. To agents! — Homer",
    "The problem with being right is that nobody believes you until it's too late. Check back in 5 minutes. — Homer",
]

_last_quote_index: int = -1


def send_message(chat_id: str, text: str) -> None:
    """Send a plain text message to a Telegram chat. Truncates at 4096 chars."""
    # Mirror all outgoing orchestrator messages to Remoat for remote tracking
    log_for_remoat(text)
    
    if not ORCHESTRATOR_BOT_TOKEN or not chat_id:
        print("ERROR: ORCHESTRATOR_TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env", file=sys.stderr)
        return
    if len(text) > 4096:
        text = text[:4090] + "\n[...]"
    try:
        resp = requests.post(
            f"{TELEGRAM_API_BASE}/sendMessage",
            json={"chat_id": str(chat_id), "text": text},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(f"Telegram sendMessage returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Telegram sendMessage failed: {e}")

def log_for_remoat(message: str, category: str = "NOTIFICATION"):
    """
    Standardized log format for Remoat to capture and forward to Telegram.
    category: NOTIFICATION | APPROVAL | PROGRESS | ERROR | ANALYSIS
    """
    # 1. Print to stdout for terminal capture (The primary Remoat bridge)
    print(f"\n[REMOAT:{category}] {message}")
    sys.stdout.flush()
    
    # 2. Direct Mirror (If tokens are initialized)
    if REMOAT_API_BASE and REMOAT_CHAT_ID:
        try:
            # Handle long messages by truncating/splitting
            clean_text = f"[{category}] {message}"
            if len(clean_text) > 4096:
                clean_text = clean_text[:4090] + "..."
                
            requests.post(
                f"{REMOAT_API_BASE}/sendMessage",
                json={"chat_id": str(REMOAT_CHAT_ID), "text": clean_text},
                timeout=5
            )
        except Exception:
            pass # Non-blocking for local dev

def push_commentary(text: str, category: str = "ANALYSIS"):
    """
    Force-pushes a coordinator insight directly to the user's phone.
    Use this to bypass Remoat's 'Thought' buffering for complex tasks.
    """
    log_for_remoat(text, category=category)


def _generate_task_interpretation(task_text: str, task_type: str) -> str:
    """
    Use Haiku to generate a one-line plain-English description of what the
    agents are about to do. Falls back to a generic label on any failure.
    """
    try:
        import openai as _openai
        client = _openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://agentshq.catalystworks.com",
                "X-Title": "agentsHQ Briefing"
            }
        )
        prompt = (
            f"You are summarising what an AI agent system is about to do for a user.\n"
            f"Task type: {task_type}\n"
            f"User request: {task_text}\n\n"
            f"Write ONE sentence (max 20 words) describing the specific action the agents "
            f"will take. Be concrete — mention the subject matter. No preamble, no quotes."
        )
        resp = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=60,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Briefing interpretation failed (non-fatal): {e}")
        return TASK_TYPE_LABELS.get(task_type, TASK_TYPE_LABELS["unknown"])


def send_briefing(chat_id: str, task_type: str, task_text: str) -> None:
    """
    Send a rich acknowledgement after classification.
    Fires within a few seconds of receiving the task and tells the user:
    - What was understood (task type)
    - Which crew is running
    - One-line plain-English interpretation of the specific task
    """
    if task_type == "chat":
        return  # no briefing for chat — response is fast enough

    crew = TASK_TYPE_CREWS.get(task_type, "Agents")
    interpretation = _generate_task_interpretation(task_text, task_type)

    lines = [
        f"On it.",
        f"",
        f"Task: {task_type.replace('_', ' ').title()}",
        f"Crew: {crew}",
        f"Plan: {interpretation}",
        f"",
        f"Will ping you when done.",
    ]
    send_message(chat_id, "\n".join(lines))


def send_progress_ping(chat_id: str) -> None:
    """Send a random Simpsons quote. Never repeats the same one consecutively."""
    global _last_quote_index
    available = [i for i in range(len(SIMPSONS_QUOTES)) if i != _last_quote_index]
    idx = random.choice(available)
    _last_quote_index = idx
    send_message(chat_id, SIMPSONS_QUOTES[idx])


def send_result(chat_id: str, summary: str, drive_url: str = None, github_url: str = None) -> None:
    """Send the final result to Telegram. Always includes Drive link if available."""
    parts = [summary]
    if drive_url or github_url:
        parts.append("")
        parts.append("--- Saved to ---")
        if drive_url:
            parts.append(f"Drive: {drive_url}")
        if github_url:
            parts.append(f"GitHub: {github_url}")
    send_message(chat_id, "\n".join(parts))


def _parse_hunter_report_to_html(leads_output: str, _scoreboard: str, today: str, enrich_result: dict = None) -> str:
    """
    Convert the Growth Hunter markdown report into a clean HTML email.
    Parses the structured sections from leads_output and renders them as styled HTML.
    """
    import re

    # ── colour tokens ──────────────────────────────────────────────────────────
    BRAND_DARK   = "#0A0A0A"
    BRAND_ACCENT = "#2563EB"   # blue — Catalyst Works primary
    BRAND_GREEN  = "#16A34A"
    BRAND_RED    = "#DC2626"
    BRAND_AMBER  = "#D97706"
    HEADER_BG    = "#0F172A"   # near-black navy
    CARD_BG      = "#F8FAFC"
    BORDER       = "#E2E8F0"
    TEXT_MUTED   = "#64748B"

    # ── section extraction helpers ─────────────────────────────────────────────
    def extract_section(text: str, header: str) -> str:
        """Pull everything between two ### headings."""
        pattern = rf"###[^\n]*{re.escape(header)}[^\n]*\n(.*?)(?=\n###|\Z)"
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def parse_md_table(block: str) -> list[dict]:
        """Return list-of-dicts from a markdown table block."""
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        table_lines = [l for l in lines if l.startswith("|")]
        if len(table_lines) < 3:
            return []
        headers = [h.strip() for h in table_lines[0].strip("|").split("|")]
        rows = []
        for row in table_lines[2:]:          # skip separator line
            cells = [c.strip() for c in row.strip("|").split("|")]
            rows.append(dict(zip(headers, cells)))
        return rows

    def clean(text: str) -> str:
        """Strip markdown bold/italic/code markers and trailing commas."""
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*",     r"\1", text)
        text = re.sub(r"`(.+?)`",       r"\1", text)
        return text.strip().strip(",")

    def status_badge(val: str) -> str:
        val = clean(val)
        color = BRAND_GREEN if "✅" in val or "Goal Hit" in val or "Saved" in val else \
                BRAND_AMBER if "⏳" in val or "Pending" in val else \
                BRAND_RED   if "⚡" in val or "Needs" in val else TEXT_MUTED
        return (f'<span style="background:{color};color:#fff;padding:2px 8px;'
                f'border-radius:4px;font-size:12px;font-weight:600;">{val}</span>')

    # ── parse sections ─────────────────────────────────────────────────────────
    pipeline_rows  = parse_md_table(extract_section(leads_output, "PIPELINE METRICS"))
    industry_rows  = parse_md_table(extract_section(leads_output, "LEADS BY INDUSTRY"))
    priority_rows  = parse_md_table(extract_section(leads_output, "TOP PRIORITY LEADS"))

    # ── patch pipeline table: replace "Leads With Email" row with enrichment truth ──
    enrich = enrich_result or {}
    if enrich and pipeline_rows:
        emails_found = enrich.get("emails_found", 0)
        processed    = enrich.get("processed", 0)
        for row in pipeline_rows:
            metric_key = next((k for k in row if "email" in k.lower()), None)
            if metric_key and "email" in clean(row.get(metric_key, "")).lower() or \
               any("email" in clean(v).lower() for v in row.values()):
                # Find the value and status columns
                keys = list(row.keys())
                if len(keys) >= 2:
                    row[keys[1]] = f"{emails_found} / {processed}"
                if len(keys) >= 3:
                    row[keys[2]] = "✅ Enrichment ran" if emails_found > 0 else "⚠️ No emails found after enrichment"
                break

    action_block   = extract_section(leads_output, "ACTION ITEMS")
    action_items   = re.findall(r"\*\*(\d+\.[^*]+)\*\*,?\s*(.+?)(?=\n>|\Z)", action_block, re.DOTALL)
    action_items   = [(clean(title), re.sub(r"\s+", " ", clean(body_text)))
                      for title, body_text in action_items]

    health_block   = extract_section(leads_output, "SCOREBOARD HEALTH CHECK")

    # ── helper: render a generic table ────────────────────────────────────────
    def table_html(rows: list[dict], special_col: str = None) -> str:
        if not rows:
            return "<p style='color:#94A3B8;font-size:13px;'>No data available.</p>"
        headers = list(rows[0].keys())
        th_cells = "".join(
            f'<th style="text-align:left;padding:10px 14px;font-size:12px;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:.05em;'
            f'color:{TEXT_MUTED};border-bottom:2px solid {BORDER};">{h}</th>'
            for h in headers
        )
        body_rows = ""
        for i, row in enumerate(rows):
            bg = "#fff" if i % 2 == 0 else CARD_BG
            cells = ""
            for h, v in row.items():
                v = clean(v)
                if h == special_col:
                    content = status_badge(v)
                elif "TOTAL" in v.upper() or h == "#":
                    content = f'<strong>{v}</strong>'
                else:
                    content = v
                cells += (f'<td style="padding:10px 14px;font-size:14px;'
                           f'color:{BRAND_DARK};border-bottom:1px solid {BORDER};">'
                           f'{content}</td>')
            body_rows += f'<tr style="background:{bg};">{cells}</tr>'
        return (f'<table style="width:100%;border-collapse:collapse;border-radius:8px;'
                f'overflow:hidden;border:1px solid {BORDER};">'
                f'<thead><tr>{th_cells}</tr></thead>'
                f'<tbody>{body_rows}</tbody></table>')

    # ── section card wrapper ───────────────────────────────────────────────────
    def section(icon: str, title: str, content: str) -> str:
        return (
            f'<div style="margin-bottom:28px;">'
            f'  <h2 style="font-size:16px;font-weight:700;color:{BRAND_DARK};'
            f'      margin:0 0 14px 0;padding-bottom:8px;'
            f'      border-bottom:2px solid {BRAND_ACCENT};">'
            f'    {icon} {title}'
            f'  </h2>'
            f'  {content}'
            f'</div>'
        )

    # ── action items HTML ──────────────────────────────────────────────────────
    if action_items:
        action_html = '<ol style="margin:0;padding-left:20px;">'
        for title, body_text in action_items:
            action_html += (
                f'<li style="margin-bottom:10px;font-size:14px;color:{BRAND_DARK};">'
                f'<strong style="color:{BRAND_ACCENT};">{title}</strong> — {body_text}'
                f'</li>'
            )
        action_html += '</ol>'
    else:
        action_html = f'<p style="color:{TEXT_MUTED};font-size:13px;">No action items parsed.</p>'

    # ── override Email Coverage using enrichment data if available ───────────────
    enrich = enrich_result or {}
    emails_found  = enrich.get("emails_found", 0)
    total_leads   = enrich.get("processed", 0)

    # ── health check bars ──────────────────────────────────────────────────────
    health_lines = [l.strip() for l in health_block.splitlines() if l.strip() and l.strip() not in ("```",)]
    health_html  = ""
    for line in health_lines:
        # Rewrite Email Coverage line using real enrichment numbers
        if enrich and re.search(r"email coverage", line, re.IGNORECASE):
            if total_leads > 0:
                pct = int(emails_found / total_leads * 100)
            else:
                pct = 0
            bar_color = BRAND_GREEN if emails_found > 0 else BRAND_RED
            circle    = "🟢" if emails_found > 0 else "🔴"
            label = (
                f"{circle} Email Coverage {pct}%, "
                f"{emails_found}/{total_leads} leads have emails after enrichment pass"
                + ("" if emails_found > 0 else "; Hunter.io + Apollo returned no matches, enrichment skill ran")
            )
            health_html += (
                f'<div style="margin-bottom:10px;">'
                f'  <div style="font-size:13px;color:{BRAND_DARK};margin-bottom:4px;">{label}</div>'
                f'  <div style="background:{BORDER};border-radius:4px;height:8px;width:100%;">'
                f'    <div style="background:{bar_color};height:8px;border-radius:4px;'
                f'         width:{pct}%;transition:width .3s;"></div>'
                f'  </div>'
                f'</div>'
            )
            continue

        # detect colour: green circle → green, red circle → red, money bag → amber
        if "🟢" in line:
            bar_color = BRAND_GREEN
        elif "🔴" in line:
            bar_color = BRAND_RED
        elif "💰" in line:
            bar_color = BRAND_AMBER
        else:
            bar_color = TEXT_MUTED

        # extract percentage if present
        pct_match = re.search(r"(\d+)%", line)
        pct = int(pct_match.group(1)) if pct_match else 0

        # clean label: remove block chars, keep meaningful text
        label = re.sub(r"[█░]+", "", line).strip()
        label = re.sub(r"\s{2,}", " ", label)

        health_html += (
            f'<div style="margin-bottom:10px;">'
            f'  <div style="font-size:13px;color:{BRAND_DARK};margin-bottom:4px;">{label}</div>'
            f'  <div style="background:{BORDER};border-radius:4px;height:8px;width:100%;">'
            f'    <div style="background:{bar_color};height:8px;border-radius:4px;'
            f'         width:{pct}%;transition:width .3s;"></div>'
            f'  </div>'
            f'</div>'
        )

    # ── priority medals map ────────────────────────────────────────────────────
    medal_colors = {"🥇": "#F59E0B", "🥈": "#94A3B8", "🥉": "#B45309", "🏅": BRAND_ACCENT}

    def priority_table_html() -> str:
        if not priority_rows:
            return "<p style='color:#94A3B8;'>No priority leads found.</p>"
        rows_html = ""
        for i, row in enumerate(priority_rows):
            bg = "#fff" if i % 2 == 0 else CARD_BG
            name_raw = clean(row.get("Name", ""))
            medal    = next((m for m in medal_colors if m in name_raw), "")
            name     = name_raw.replace(medal, "").strip()
            color    = medal_colors.get(medal, BRAND_ACCENT)
            email    = clean(row.get("Email", "Not revealed"))
            
            rows_html += (
                f'<tr style="background:{bg};">'
                f'  <td style="padding:10px 14px;width:36px;font-size:18px;">{medal}</td>'
                f'  <td style="padding:10px 14px;font-size:14px;font-weight:600;color:{color};">{name}</td>'
                f'  <td style="padding:10px 14px;font-size:14px;color:{BRAND_DARK};">{clean(row.get("Company",""))}</td>'
                f'  <td style="padding:10px 14px;font-size:13px;color:{BRAND_ACCENT};font-family:monospace;">{email}</td>'
                f'  <td style="padding:10px 14px;font-size:13px;color:{TEXT_MUTED};">{clean(row.get("Industry",""))}</td>'
                f'  <td style="padding:10px 14px;font-size:13px;color:{BRAND_DARK};">{clean(row.get("Why Priority",""))}</td>'
                f'</tr>'
            )
        return (
            f'<table style="width:100%;border-collapse:collapse;border-radius:8px;'
            f'overflow:hidden;border:1px solid {BORDER};">'
            f'<thead><tr>'
            f'<th style="padding:10px 14px;font-size:12px;font-weight:700;text-transform:uppercase;'
            f'color:{TEXT_MUTED};border-bottom:2px solid {BORDER};text-align:left;width:36px;"></th>'
            f'<th style="padding:10px 14px;font-size:12px;font-weight:700;text-transform:uppercase;'
            f'color:{TEXT_MUTED};border-bottom:2px solid {BORDER};text-align:left;">Name</th>'
            f'<th style="padding:10px 14px;font-size:12px;font-weight:700;text-transform:uppercase;'
            f'color:{TEXT_MUTED};border-bottom:2px solid {BORDER};text-align:left;">Company</th>'
            f'<th style="padding:10px 14px;font-size:12px;font-weight:700;text-transform:uppercase;'
            f'color:{TEXT_MUTED};border-bottom:2px solid {BORDER};text-align:left;">Email</th>'
            f'<th style="padding:10px 14px;font-size:12px;font-weight:700;text-transform:uppercase;'
            f'color:{TEXT_MUTED};border-bottom:2px solid {BORDER};text-align:left;">Industry</th>'
            f'<th style="padding:10px 14px;font-size:12px;font-weight:700;text-transform:uppercase;'
            f'color:{TEXT_MUTED};border-bottom:2px solid {BORDER};text-align:left;">Why Priority</th>'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table>'
        )

    # ── assemble full HTML ─────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Daily Lead Report — {today}</title>
</head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" style="width:100%;background:#F1F5F9;padding:32px 0;">
    <tr>
      <td align="center">
        <table role="presentation" style="width:100%;max-width:680px;">

          <!-- HEADER -->
          <tr>
            <td style="background:{HEADER_BG};border-radius:12px 12px 0 0;padding:32px 36px;">
              <p style="margin:0 0 4px 0;font-size:11px;font-weight:700;letter-spacing:.15em;
                         text-transform:uppercase;color:#94A3B8;">CATALYST WORKS CONSULTING</p>
              <h1 style="margin:0;font-size:26px;font-weight:800;color:#fff;line-height:1.2;">
                📊 Growth Hunter
              </h1>
              <p style="margin:6px 0 0;font-size:14px;color:#94A3B8;">
                Daily Prospecting Report &mdash; {today}
              </p>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="background:#fff;padding:32px 36px;border:1px solid {BORDER};border-top:none;">

              {section("🎯", "Pipeline Metrics", table_html(pipeline_rows, special_col="Status"))}
              {section("🏭", "Leads by Industry", table_html(industry_rows))}
              {section("🔥", "Top Priority Leads for Outreach Today", priority_table_html())}
              {section("⚡", "Action Items", action_html)}
              {section("💡", "Scoreboard Health Check", health_html)}

            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:{CARD_BG};border:1px solid {BORDER};border-top:none;
                       border-radius:0 0 12px 12px;padding:20px 36px;">
              <p style="margin:0;font-size:12px;color:{TEXT_MUTED};text-align:center;">
                📌 Report generated by <strong>Growth Hunter</strong> | Catalyst Works Consulting | {today}
              </p>
              <p style="margin:6px 0 0;font-size:12px;color:{TEXT_MUTED};text-align:center;">
                Sent automatically by agentsHQ &mdash; Reply here or message
                <a href="https://t.me/agentsHQ4Bou_bot" style="color:{BRAND_ACCENT};">@agentsHQ4Bou_bot</a>
                on Telegram to act on any lead.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return html


def _format_health_check_html(status: str, report_text: str, date: str) -> str:
    """
    Render the weekly health check report as a branded HTML email.
    Uses the same Catalyst Works colour tokens as the Hunter report.

    status     — "GREEN", "YELLOW", or "RED"
    report_text — full Markdown report body
    date        — display date string e.g. "2026-04-07"
    """
    import html as html_lib
    import re

    # ── colour tokens (match Hunter report exactly) ───────────────────────────
    BRAND_DARK   = "#0A0A0A"
    BRAND_ACCENT = "#2563EB"
    BRAND_GREEN  = "#16A34A"
    BRAND_RED    = "#DC2626"
    BRAND_AMBER  = "#D97706"
    HEADER_BG    = "#0F172A"
    CARD_BG      = "#F8FAFC"
    BORDER       = "#E2E8F0"
    TEXT_MUTED   = "#64748B"

    STATUS_COLOR = {
        "GREEN":  BRAND_GREEN,
        "YELLOW": BRAND_AMBER,
        "RED":    BRAND_RED,
    }.get(status.upper(), TEXT_MUTED)

    STATUS_EMOJI = {"GREEN": "✅", "YELLOW": "⚠️", "RED": "🔴"}.get(status.upper(), "ℹ️")

    # ── convert Markdown to simple HTML ──────────────────────────────────────
    def md_to_html(text: str) -> str:
        """Minimal Markdown → HTML: headings, bold, bullets, horizontal rules."""
        lines = text.split("\n")
        out = []
        in_list = False
        for line in lines:
            # Escape HTML special chars first
            safe = html_lib.escape(line)
            # Headings
            if safe.startswith("### "):
                if in_list: out.append("</ul>"); in_list = False
                out.append(f'<h3 style="font-size:14px;font-weight:700;color:{BRAND_ACCENT};margin:16px 0 6px 0;">{safe[4:]}</h3>')
            elif safe.startswith("## "):
                if in_list: out.append("</ul>"); in_list = False
                out.append(f'<h2 style="font-size:16px;font-weight:700;color:{BRAND_DARK};margin:20px 0 8px 0;padding-bottom:6px;border-bottom:2px solid {BRAND_ACCENT};">{safe[3:]}</h2>')
            elif safe.startswith("# "):
                if in_list: out.append("</ul>"); in_list = False
                out.append(f'<h1 style="font-size:20px;font-weight:800;color:{BRAND_DARK};margin:0 0 16px 0;">{safe[2:]}</h1>')
            # Horizontal rule
            elif safe.strip() in ("---", "***", "___"):
                if in_list: out.append("</ul>"); in_list = False
                out.append(f'<hr style="border:none;border-top:1px solid {BORDER};margin:20px 0;">')
            # Bullet list items
            elif re.match(r"^[-*] ", safe) or re.match(r"^\d+\. ", safe) or re.match(r"^  [-*] ", safe):
                if not in_list: out.append(f'<ul style="margin:0 0 12px 0;padding-left:20px;">'); in_list = True
                item = re.sub(r"^[-*\d.]+\s+", "", safe).strip()
                # Bold inside bullets
                item = re.sub(r"\*\*(.+?)\*\*", r'<strong>\1</strong>', item)
                item = re.sub(r"`(.+?)`", r'<code style="background:#F1F5F9;padding:1px 4px;border-radius:3px;font-size:12px;">\1</code>', item)
                out.append(f'<li style="margin-bottom:6px;font-size:14px;color:{BRAND_DARK};line-height:1.5;">{item}</li>')
            # Blank line closes list
            elif safe.strip() == "":
                if in_list: out.append("</ul>"); in_list = False
                out.append('<br>')
            # Normal paragraph
            else:
                if in_list: out.append("</ul>"); in_list = False
                p = re.sub(r"\*\*(.+?)\*\*", r'<strong>\1</strong>', safe)
                p = re.sub(r"`(.+?)`", r'<code style="background:#F1F5F9;padding:1px 4px;border-radius:3px;font-size:12px;">\1</code>', p)
                out.append(f'<p style="margin:0 0 10px 0;font-size:14px;color:{BRAND_DARK};line-height:1.6;">{p}</p>')
        if in_list:
            out.append("</ul>")
        return "\n".join(out)

    report_html = md_to_html(report_text)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>agentsHQ Weekly Health Check — {html_lib.escape(date)}</title>
</head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" style="width:100%;background:#F1F5F9;padding:32px 0;">
    <tr>
      <td align="center">
        <table role="presentation" style="width:100%;max-width:680px;">

          <!-- HEADER -->
          <tr>
            <td style="background:{HEADER_BG};border-radius:12px 12px 0 0;padding:32px 36px;">
              <p style="margin:0 0 4px 0;font-size:11px;font-weight:700;letter-spacing:.15em;
                         text-transform:uppercase;color:#94A3B8;">CATALYST WORKS CONSULTING</p>
              <h1 style="margin:0;font-size:26px;font-weight:800;color:#fff;line-height:1.2;">
                🛡️ agentsHQ Weekly Health Check
              </h1>
              <p style="margin:6px 0 0;font-size:14px;color:#94A3B8;">
                Automated code quality report &mdash; {html_lib.escape(date)}
              </p>
            </td>
          </tr>

          <!-- STATUS BANNER -->
          <tr>
            <td style="background:{STATUS_COLOR};padding:16px 36px;">
              <p style="margin:0;font-size:18px;font-weight:800;color:#fff;letter-spacing:.02em;">
                {STATUS_EMOJI} Status: {html_lib.escape(status.upper())}
              </p>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="background:#fff;padding:32px 36px;border:1px solid {BORDER};border-top:none;">
              {report_html}
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:{CARD_BG};border:1px solid {BORDER};border-top:none;
                       border-radius:0 0 12px 12px;padding:20px 36px;">
              <p style="margin:0;font-size:12px;color:{TEXT_MUTED};text-align:center;">
                📌 Generated automatically by <strong>agentsHQ Weekly Health Check</strong> | Catalyst Works Consulting | {html_lib.escape(date)}
              </p>
              <p style="margin:6px 0 0;font-size:12px;color:{TEXT_MUTED};text-align:center;">
                Report also committed to
                <a href="https://github.com/bokar83/agentHQ/tree/main/outputs/health_checks"
                   style="color:{BRAND_ACCENT};">GitHub → outputs/health_checks/</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_health_check_report(status: str, report_text: str, date: str) -> bool:
    """
    Email the weekly health check report to all three Catalyst Works addresses.
    Called by the /internal/health-report webhook after each scheduled run.

    status      — "GREEN", "YELLOW", or "RED"
    report_text — full Markdown report from the remote agent
    date        — date string e.g. "2026-04-07"
    """
    subject = f"agentsHQ Weekly Health Check — {status.upper()} — {date}"
    html_body = _format_health_check_html(status, report_text, date)
    to_addresses = [
        "bokar83@gmail.com",
        "boubacarbusiness@gmail.com",
        "catalystworks.ai@gmail.com",
    ]
    return send_email(subject, html_body, to_addresses=to_addresses, html=True)


def send_hunter_report(leads_output: str, scoreboard: str = "", enrich_result: dict = None) -> bool:
    """
    Email the daily hunter results to Boubacar.
    Called automatically after every hunter_crew run.
    enrich_result: optional dict from enrich_missing_emails() with emails_found, processed, etc.
    """
    from datetime import date
    today = date.today().strftime("%B %d, %Y")
    subject = f"Daily Lead Report — {today}"

    html_body = _parse_hunter_report_to_html(leads_output, scoreboard, today, enrich_result=enrich_result or {})
    return send_email(subject, html_body, html=True)


def send_email(subject: str, body: str, to_addresses: list = None, html: bool = False) -> bool:
    """
    Send an email report.
    Requires SMTP_USER and SMTP_PASS in .env.
    Pass html=True to send as HTML; defaults to plain text.
    """
    if not SMTP_USER or not SMTP_PASS:
        logger.warning("SMTP credentials not set — skipping send_email")
        return False

    targets = to_addresses or REPORT_EMAILS

    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = SMTP_USER
        msg['To'] = ", ".join(targets)
        msg['Subject'] = subject

        if html:
            # Attach plain-text fallback first, then HTML (RFC 2046 — last wins)
            plain = "Daily Lead Report from Growth Hunter. Please view in an HTML-capable email client."
            msg.attach(MIMEText(plain, 'plain'))
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info(f"Email report sent successfully to {len(targets)} addresses.")
        return True
    except Exception as e:
        logger.error(f"Email delivery failed: {e}")
        return False


def send_doc_routing_alert(filename: str, alert_type: str, details: dict) -> None:
    """
    Send a Telegram alert for document routing events.

    alert_type values:
      "confirm"    -- ready to file, needs operator confirmation
      "review"     -- low confidence, routed to review queue
      "unreadable" -- file could not be extracted
      "error"      -- classification failed after retry
    """
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not chat_id:
        logger.warning("TELEGRAM_CHAT_ID not set -- cannot send doc routing alert")
        return

    if alert_type == "confirm":
        msg = (
            f"Ready to file\n\n"
            f"Original: {filename}\n"
            f"Renamed: {details.get('standardized_filename', '')}\n"
            f"Domain: {details.get('domain', '')}\n"
            f"Project: {details.get('project_id', '')} | {details.get('topic_or_client', '')}\n"
            f"Doc type: {details.get('doc_type', '')}\n"
            f"Folder: {details.get('target_folder_path', '')}\n"
            f"Notebook: {details.get('notebook_assignment', '')}\n"
            f"Confidence: {details.get('confidence', '')} ({details.get('confidence_score', '')})\n"
            f"Note: {details.get('routing_notes', '')}\n\n"
            f"Reply: confirm | edit [field]:[value] to correct | new [name] new project | flag"
        )
    elif alert_type == "review":
        msg = (
            f"Low confidence: {filename}\n"
            f"Suggestion: {details.get('target_folder_path', '00_Review_Queue/')}\n"
            f"Notebook: {details.get('notebook_assignment', 'Unassigned')}\n"
            f"Confidence: {details.get('confidence_score', 0)}\n"
            f"Reason: {details.get('routing_notes', '')}\n\n"
            f"Reply: confirm to accept, edit [field]:[value] to correct, flag to reject."
        )
    elif alert_type == "unreadable":
        msg = (
            f"Unreadable file: {filename}. Moved to Review Queue.\n"
            f"Check for scanned PDF or unsupported format."
        )
    elif alert_type == "error":
        msg = f"Classification failed for {filename}. Routed to Review Queue."
    else:
        msg = f"Doc routing event [{alert_type}]: {filename}"

    send_message(chat_id, msg)
