"""
signal_works/email_builder.py
Builds personalized HTML cold emails and creates Gmail drafts via GWS CLI.
From: boubacar@catalystworks.consulting
"""
import os
import json
import base64
import logging
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)

SENDER = "boubacar@catalystworks.consulting"
CALENDLY_URL = os.environ.get(
    "SIGNAL_WORKS_CALENDLY",
    "https://calendly.com/boubacarbarry/signal-works-discovery-call",
)

# Drive video URLs per niche (share links from Drive upload step)
DRIVE_VIDEO_URLS = {
    "roofer": os.environ.get(
        "SIGNAL_WORKS_VIDEO_ROOFER",
        "https://drive.google.com/file/d/1aancESOfki8e2n7nWX4DwDogt-1ru6Sm/view",
    ),
    "roofing": os.environ.get(
        "SIGNAL_WORKS_VIDEO_ROOFER",
        "https://drive.google.com/file/d/1aancESOfki8e2n7nWX4DwDogt-1ru6Sm/view",
    ),
    "pediatric dentist": os.environ.get(
        "SIGNAL_WORKS_VIDEO_DENTAL",
        "https://drive.google.com/file/d/1rtZKnVQJI9XtXcxnocJN8CZX9HhqN3o0/view",
    ),
    "dentist": os.environ.get(
        "SIGNAL_WORKS_VIDEO_DENTAL",
        "https://drive.google.com/file/d/1rtZKnVQJI9XtXcxnocJN8CZX9HhqN3o0/view",
    ),
    "hvac": os.environ.get(
        "SIGNAL_WORKS_VIDEO_HVAC",
        "https://drive.google.com/file/d/1aancESOfki8e2n7nWX4DwDogt-1ru6Sm/view",  # replace when HVAC reel is uploaded
    ),
}
DEFAULT_VIDEO_URL = DRIVE_VIDEO_URLS["roofer"]

# Niche config: accent color + video label text
NICHE_CONFIG = {
    "roofer":            {"accent": "#F4600C", "label": "roofer"},
    "roofing":           {"accent": "#F4600C", "label": "roofer"},
    "pediatric dentist": {"accent": "#F5C842", "label": "pediatric dentist"},
    "dentist":           {"accent": "#F5C842", "label": "pediatric dentist"},
    "hvac":              {"accent": "#E8A020", "label": "HVAC company"},
}
DEFAULT_CONFIG = {"accent": "#F4600C", "label": "local business"}

TEMPLATE_PATH = Path(__file__).parent / "templates" / "cold_email.html"


# ── No-website detection ─────────────────────────────────────────────────────

def _has_no_website(lead: dict) -> bool:
    """True when the lead has no website at all (not just a bad one)."""
    website = (lead.get("website_url") or "").strip()
    has_website = lead.get("has_website")
    if has_website is False:
        return True
    if not website:
        return True
    return False


# ── Subject line by niche ─────────────────────────────────────────────────────

def _subject(lead: dict) -> str:
    name = lead.get("name", "your business")
    score = lead.get("ai_score", 0)
    niche = (lead.get("niche") or "").lower()

    if _has_no_website(lead):
        return f"{name} has no website -- and AI can't find you at all"

    if "dentist" in niche:
        return f"ChatGPT doesn't know {name} exists (AI score: {score}/100)"
    elif "roofer" in niche or "roofing" in niche:
        return f"ChatGPT doesn't know {name} exists (your AI score: {score}/100)"
    elif "hvac" in niche:
        return f"Homeowners can't find {name} on ChatGPT (AI score: {score}/100)"
    return f"Your AI visibility score: {score}/100 -- {name} isn't showing up in ChatGPT"


# ── Quick wins HTML ───────────────────────────────────────────────────────────

def _quick_wins_html(lead: dict) -> str:
    if _has_no_website(lead):
        wins = [
            "Build a website. AI tools can only cite businesses with a web presence. Without one, you are invisible.",
            "Claim your Google Business Profile and Bing Places listing now -- free, 30 minutes, immediate visibility lift.",
            "Once your site is live, add structured data and AI-optimized content. That is what gets you cited in ChatGPT.",
        ]
        rows = ""
        for win in wins:
            rows += f'<p>&#9679; {win}</p>\n'
        return rows

    wins = lead.get("ai_quick_wins") or []
    if isinstance(wins, str):
        raw = wins.strip()
        # Handle PostgreSQL set literal: {"item1","item2"} or {item1,item2}
        if raw.startswith("{") and raw.endswith("}"):
            inner = raw[1:-1]
            wins = [w.strip().strip('"') for w in inner.split('","') if w.strip().strip('"')]
            if len(wins) == 1:
                wins = [w.strip().strip('"') for w in inner.split(",") if w.strip().strip('"')]
        else:
            wins = [w.strip() for w in raw.split("|") if w.strip()]
    if not wins:
        wins = [
            "Fix robots.txt so AI crawlers (GPTBot, PerplexityBot) can index you. 10-minute fix.",
            "Claim your Bing Places listing. ChatGPT uses Bing to find local businesses. 20-minute fix.",
            "Add structured data to your site. AI tools skip businesses with no schema markup.",
        ]
    rows = ""
    for win in wins[:3]:
        rows += f'<p>&#9679; {win}</p>\n'
    return rows


# ── Platform indicators (colorblind-safe: symbol + color) ────────────────────

def _platform_icons(lead: dict) -> str:
    breakdown = lead.get("ai_breakdown") or {}
    if isinstance(breakdown, str):
        try:
            breakdown = json.loads(breakdown)
        except Exception:
            breakdown = {}

    # Map breakdown keys to display names (score > 0 = pass)
    checks = [
        ("chatgpt",    breakdown.get("chatgpt_visibility", 0)),
        ("perplexity", breakdown.get("perplexity_signal", 0)),
        ("robots",     breakdown.get("robots_txt", 0)),
        ("bing",       breakdown.get("bing_places", 0)),
    ]
    labels = {
        "chatgpt":    "ChatGPT",
        "perplexity": "Perplexity",
        "robots":     "Crawlers",
        "bing":       "Bing",
    }

    cells = ""
    for key, score in checks:
        if score > 0:
            circle = (
                '<div style="width:18px;height:18px;background:#22C55E;border-radius:50%;'
                'margin:0 auto 3px auto;color:#fff;font-size:11px;font-weight:900;'
                'line-height:18px;text-align:center;">&#10003;</div>'
            )
        else:
            circle = (
                '<div style="width:18px;height:18px;background:#EF4444;border-radius:50%;'
                'margin:0 auto 3px auto;color:#fff;font-size:11px;font-weight:900;'
                'line-height:18px;text-align:center;">&#10005;</div>'
            )
        cells += (
            f'<td style="text-align:center;padding:0 6px;">'
            f'{circle}'
            f'<div style="font-size:10px;color:#CBD5E1;font-weight:600;">{labels[key]}</div>'
            f'</td>\n'
        )
    return cells


# ── Score bar width ───────────────────────────────────────────────────────────

def _bar_width(score: int) -> str:
    pct = max(2, min(100, score))
    return f"{pct}%"


# ── Score context label ───────────────────────────────────────────────────────

def _score_label(score: int, no_website: bool = False) -> str:
    if no_website:
        return "No web presence -- invisible to AI"
    if score <= 20:
        return "Critical -- not visible to AI"
    elif score <= 50:
        return "Below average -- partially visible"
    return "Moderate -- room to improve"


# ── Opening body paragraph by niche ──────────────────────────────────────────

def _opening(lead: dict) -> str:
    name = lead.get("name", "your business")
    niche_raw = (lead.get("niche") or "local business").lower()
    city = lead.get("city", "your city")
    score = lead.get("ai_score", 0)
    owner = lead.get("owner_name") or ""
    greeting = f"Hi {owner}," if owner and owner.lower() not in ("", "there") else "Hi,"

    if _has_no_website(lead):
        # No-website variant: different angle entirely
        if "dentist" in niche_raw:
            problem = f"I tried to find {name} online. I couldn't. No website, no AI presence -- parents asking ChatGPT for a pediatric dentist in {city} will never land on you."
        elif "roofer" in niche_raw or "roofing" in niche_raw:
            problem = f"I tried to find {name} online. I couldn't. No website, no AI presence -- homeowners asking ChatGPT for a roofer in {city} will never find you."
        elif "hvac" in niche_raw:
            problem = f"I tried to find {name} online. I couldn't. No website, no AI presence -- homeowners asking ChatGPT for emergency HVAC help in {city} will never call you."
        else:
            problem = f"I tried to find {name} online. I couldn't. Without a web presence, AI tools have nothing to cite -- and you stay invisible."
        scan_line = f"That is fixable. I put together a quick demo showing what {name} could look like with a site built for AI visibility from day one."
        return f"{greeting}\n{problem}\n{scan_line}"

    if "dentist" in niche_raw:
        problem = f"Right now, a parent in {city} is asking ChatGPT for a pediatric dentist. They are getting a name. It is not yours."
        scan_line = f"I ran {name} through an AI visibility scan. You scored {score}/100."
    elif "roofer" in niche_raw or "roofing" in niche_raw:
        problem = f"Right now, someone in {city} is asking ChatGPT for a roofer. They are getting a name. It is not yours."
        scan_line = f"I ran {name} through an AI visibility scan. You scored {score}/100."
    elif "hvac" in niche_raw:
        problem = f"Right now, a homeowner in {city} is asking ChatGPT for emergency HVAC help. They are getting a name. It is not yours."
        scan_line = f"I ran {name} through an AI visibility scan. You scored {score}/100."
    else:
        problem = f"Right now, someone in {city} is searching for a {niche_raw}. AI tools are pointing them elsewhere."
        scan_line = f"I ran {name} through an AI visibility scan. You scored {score}/100."

    return f"{greeting}\n{problem}\n{scan_line}"


# ── Closing paragraph by niche ────────────────────────────────────────────────

def _closing(lead: dict) -> str:
    niche_raw = (lead.get("niche") or "local business").lower()
    city = lead.get("city", "your city")
    if "dentist" in niche_raw:
        label = "pediatric dentists"
    elif "roofer" in niche_raw or "roofing" in niche_raw:
        label = "roofers"
    elif "hvac" in niche_raw:
        label = "HVAC companies"
    else:
        label = "local businesses"

    if _has_no_website(lead):
        return (
            f"I build AI-visible websites for {label} in {city} -- sites that rank in ChatGPT and Google AI "
            "from day one, not as an afterthought.\n"
            "If you want to see what that looks like for your business, 20 minutes is enough:"
        )
    return (
        f"I help {label} in {city} become the business AI recommends -- "
        "through website optimization, structured data, and content that AI tools actually read and cite.\n"
        "If the gap is real to you, let's talk. 20 minutes, no pitch:"
    )


# ── Render full HTML email ────────────────────────────────────────────────────

def render_html(lead: dict) -> str:
    niche = (lead.get("niche") or "").lower()
    cfg = NICHE_CONFIG.get(niche, DEFAULT_CONFIG)
    score = int(lead.get("ai_score") or 0)
    name = lead.get("name", "your business")
    video_url = lead.get("video_url") or DRIVE_VIDEO_URLS.get(niche, DEFAULT_VIDEO_URL)
    city = lead.get("city", "Salt Lake City")
    no_website = _has_no_website(lead)

    opening_lines = _opening(lead).split("\n")
    greeting = opening_lines[0]
    para1 = opening_lines[1] if len(opening_lines) > 1 else ""
    para2 = opening_lines[2] if len(opening_lines) > 2 else ""
    closing_paras = _closing(lead).split("\n")
    close1 = closing_paras[0] if closing_paras else ""
    close2 = closing_paras[1] if len(closing_paras) > 1 else ""

    html = f"""<!--
  ACCESSIBILITY RULE (enforced permanently):
  Never use color as the sole signal. Always pair color with shape or text.
  - Status indicators: X symbol for fail, checkmark for pass -- never dots only
  - Red text labels are OK when the WORD carries the meaning (e.g. "CRITICAL")
  - Score bars always have a text label below (Critical / Below Average / Good)
  - Affects ~8% of men who are red-green colorblind
-->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your AI Visibility Score</title>
<style>
  body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
  table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
  img {{ border: 0; display: block; }}
  body {{ margin: 0; padding: 0; background-color: #f4f4f5;
         font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }}
  .body-text {{ font-size: 17px; line-height: 1.8; color: #1a1a1a; }}
  .body-text p {{ margin: 0 0 14px 0; }}
  .gaps {{ background: #f9fafb; border-left: 3px solid #EF4444; border-radius: 0 6px 6px 0;
          padding: 14px 18px; margin: 18px 0; }}
  .gaps p {{ margin: 0 0 8px 0; font-size: 16px; color: #1f2937; line-height: 1.7; }}
  .gaps p:last-child {{ margin-bottom: 0; }}
  .gaps strong {{ font-size: 12px; font-weight: 800; text-transform: uppercase;
                  letter-spacing: 0.07em; color: #EF4444; display: block; margin-bottom: 10px; }}
  a {{ color: inherit; }}
  .body-text a {{ color: #1a1a1a; text-decoration: none; }}
  .footer {{ background: #f9fafb; padding: 14px 28px; font-size: 11px; color: #9ca3af;
             border-top: 1px solid #e5e7eb; }}
</style>
</head>
<body>
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f4f4f5">
<tr><td align="center" style="padding: 28px 16px;">
<table width="580" cellpadding="0" cellspacing="0" border="0"
       style="max-width:580px; background:#ffffff; border-radius:8px; overflow:hidden;">

  <!-- MINIMAL HEADER -->
  <tr>
    <td style="padding: 8px 28px; border-bottom: 1px solid #f3f4f6;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
        <td><span style="color:#9ca3af;font-size:11px;font-weight:600;
                         letter-spacing:0.07em;text-transform:uppercase;">Signal Works</span></td>
        <td align="right"><span style="color:#d1d5db;font-size:11px;">AI Visibility Report &middot; {city}, UT</span></td>
      </tr></table>
    </td>
  </tr>

  <!-- SCORE STRIP -->
  <tr>
    <td style="background:#0F1923;padding:16px 24px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr valign="middle">
          <!-- Left: score number -->
          <td style="width:110px;">
            <div style="line-height:1;">
              <span style="color:#FFFFFF;font-size:44px;font-weight:900;letter-spacing:-2px;">{score}</span><span style="color:#94A3B8;font-size:15px;font-weight:600;">/100</span>
            </div>
            <div style="color:#CBD5E1;font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.08em;margin-top:3px;">AI Visibility</div>
          </td>
          <!-- Middle: business name + bar -->
          <td style="padding:0 14px;">
            <div style="color:#F1F5F9;font-size:14px;font-weight:700;margin-bottom:6px;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:220px;">{name}</div>
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr><td style="background:#1E293B;border-radius:3px;height:5px;padding:0;">
                <table cellpadding="0" cellspacing="0" border="0" style="width:{_bar_width(score)};">
                  <tr><td style="background:#EF4444;border-radius:3px;height:5px;
                                 line-height:5px;font-size:1px;">&nbsp;</td></tr>
                </table>
              </td></tr>
            </table>
            <div style="color:#EF4444;font-size:11px;font-weight:700;margin-top:5px;
                        text-transform:uppercase;letter-spacing:0.06em;">{_score_label(score, no_website)}</div>
          </td>
          <!-- Right: platform indicators -->
          <td align="right" style="white-space:nowrap;vertical-align:middle;">
            <table cellpadding="0" cellspacing="0" border="0">
              <tr>
                {_platform_icons(lead)}
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- BODY -->
  <tr>
    <td style="padding:32px 32px 0 32px;">
      <div class="body-text" style="color:#1a1a1a;">
        <p>{greeting}</p>
        <p>{para1}</p>
        {"" if no_website else f"<p>{para2} Here is what that means:</p>"}
      </div>
      <div class="gaps">
        <strong>{"3 things keeping you invisible" if no_website else "3 gaps costing you leads today"}</strong>
        {_quick_wins_html(lead)}
      </div>
      <div class="body-text" style="color:#1a1a1a;">
        <p>I put together a 20-second video showing what {name} could look like {"built for AI from day one" if no_website else "when this is fixed"}.</p>
      </div>
    </td>
  </tr>

  <!-- VIDEO BLOCK -->
  <tr>
    <td style="padding:14px 32px;">
      <a href="{video_url}" style="display:block;text-decoration:none;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="background:linear-gradient(135deg,#111111 0%,#1a0d04 100%);border-radius:8px;">
          <tr><td align="center" valign="middle" style="padding:32px 24px;">
            <table width="52" height="52" cellpadding="0" cellspacing="0" border="0"
                   style="background:rgba(244,96,12,0.15);border:2px solid {cfg['accent']};
                          border-radius:50%;margin:0 auto 10px auto;">
              <tr><td align="center" valign="middle">
                <div style="width:0;height:0;border-top:9px solid transparent;
                            border-bottom:9px solid transparent;
                            border-left:16px solid {cfg['accent']};margin-left:4px;"></div>
              </td></tr>
            </table>
            <p style="color:#ffffff;font-size:14px;font-weight:700;margin:0 0 4px 0;">Watch: {name} -- AI-visible</p>
            <p style="color:#6b7280;font-size:11px;margin:0;">20 seconds &middot; no sound required</p>
          </td></tr>
        </table>
      </a>
    </td>
  </tr>

  <!-- CLOSE + CTA -->
  <tr>
    <td style="padding:8px 32px 32px 32px;">
      <div class="body-text" style="color:#1a1a1a;">
        <p>{close1}</p>
        <p>{close2}</p>
      </div>
      <table cellpadding="0" cellspacing="0" border="0" style="margin:4px 0 24px 0;">
        <tr><td>
          <a href="{CALENDLY_URL}"
             style="display:inline-block;background:#EF4444;color:#ffffff;text-decoration:none;
                    font-size:17px;font-weight:700;padding:14px 32px;border-radius:6px;">
            Book a Free Visibility Check
          </a>
        </td></tr>
      </table>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
      <div style="font-size:16px;color:#111827;font-weight:700;">Boubacar</div>
      <div style="font-size:13px;color:#9ca3af;margin-top:4px;">Signal Works &middot; We make your business the one AI recommends.</div>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td class="footer">
      <p style="margin:0 0 3px 0;">You are receiving this because I ran a public AI visibility scan on local {cfg['label']} businesses in {city}.</p>
      <p style="margin:0;">To unsubscribe, reply "unsubscribe" and I will remove you immediately.</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return html


# ── GWS CLI helper ────────────────────────────────────────────────────────────

def _gws_env() -> dict:
    import platform
    env = {**os.environ}
    if platform.system() != "Windows":
        # Inside Docker container -- point to mounted secrets
        env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = os.environ.get(
            "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE",
            "/app/secrets/gws-oauth-credentials.json",
        )
        env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] = "file"
        env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = os.environ.get(
            "GOOGLE_WORKSPACE_CLI_CONFIG_DIR",
            "/app/.config/gws",
        )
    # On Windows, gws uses C:/Users/<user>/.config/gws by default -- no override needed
    return env


def create_gmail_draft(lead: dict) -> str:
    """Create a Gmail draft for this lead. Returns the Gmail draft ID.

    On Windows: writes the payload to a temp file and calls gws via PowerShell
    (single-quote params bypass the JSON escaping issue in subprocess->shell).
    On Linux/Docker: calls gws directly with shell=False.
    """
    import platform
    import tempfile

    subject = _subject(lead)
    html_body = render_html(lead)

    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER
    msg["To"] = lead["email"]
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8").rstrip("=\n")
    draft_payload = json.dumps({"message": {"raw": raw}})

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    tmp.write(draft_payload)
    tmp.close()
    tmp_path = tmp.name

    try:
        if platform.system() == "Windows":
            # PowerShell single-quote params avoids JSON key quoting issues.
            # Read the temp file and pipe to gws stdin via PS pipeline.
            safe_path = tmp_path.replace("\\", "/")
            ps_script = (
                f"Get-Content -Raw -Encoding UTF8 '{safe_path}'"
                " | gws gmail users drafts create"
                " --params '{\"userId\":\"me\"}'"
                " --json -"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                env=_gws_env(),
                timeout=30,
            )
        else:
            with open(tmp_path, "r", encoding="utf-8") as f:
                json_content = f.read()
            result = subprocess.run(
                [
                    "gws", "gmail", "users", "drafts", "create",
                    "--params", json.dumps({"userId": "me"}),
                    "--json", json_content,
                ],
                capture_output=True,
                text=True,
                env=_gws_env(),
                timeout=30,
            )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error")[:300]
        raise RuntimeError(f"Gmail draft create failed: {err}")

    try:
        data = json.loads(result.stdout)
        draft_id = data.get("id", "")
        logger.info(f"Draft created for {lead['name']} <{lead['email']}> | draft_id={draft_id}")
        return draft_id
    except json.JSONDecodeError:
        raise RuntimeError(f"Unexpected gws response: {result.stdout[:200]}")
