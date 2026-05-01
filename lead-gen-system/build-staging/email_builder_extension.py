"""DRAFT extension to signal_works/email_builder.py.

Pre-staged 2026-04-30. NOT a new file. The function below gets APPENDED to
the bottom of signal_works/email_builder.py during the Friday build. It
reuses every helper already in that file (_subject, _quick_wins_html,
_platform_icons, _bar_width, _score_label, render_html structure).

The only difference from render_html() is the opening + closing paragraphs:
the inbound version says "here is the report you requested" instead of
"I scanned your business," and the CTA is "book a 20-minute Signal Works
call" instead of "reply to me."

NOTE on pyright/IDE warnings: this staging file flags "Could not find name"
warnings for NICHE_CONFIG, DEFAULT_CONFIG, os, _score_label, and
_quick_wins_html. EXPECTED. Those names exist in email_builder.py at the
target append site. The warnings disappear during the Friday build when
the function lands in its real home.
"""

# === BEGIN PASTE-IN APPEND TO signal_works/email_builder.py ============

INBOUND_OPENING = (
    "<p>Hi {first_name},</p>"
    "<p>Here is the AI visibility report you requested for "
    "<strong>{business}</strong> in {city}.</p>"
    "<p>You scored <strong>{score}/100</strong>. "
    "That puts you {score_context}.</p>"
)

INBOUND_CLOSING = (
    "<p>If you want help closing the gap, the next step is a 20-minute "
    "Signal Works call. We will go through the 3 quick wins above on your "
    "actual site, decide which one to fix first, and you leave with a "
    "concrete plan whether you work with us or not.</p>"
    '<p><a href="{calendly_url}" style="display:inline-block;background:#00E5FF;'
    'color:#0B0F1A;text-decoration:none;font-family:Syne,sans-serif;font-weight:700;'
    'font-size:0.85rem;letter-spacing:0.06em;text-transform:uppercase;'
    'padding:14px 28px;border-radius:2px;margin-top:8px;">Book a 20-minute Signal Works call</a></p>'
    "<p style=\"font-size:0.78rem;color:#6b7280;margin-top:18px;\">"
    "If you would rather just take the report and run with it, no problem. "
    "We will be here when you want a conversation."
    "</p>"
)


def _score_context_phrase(score: int) -> str:
    """Plain-English context for the inbound report. Not a value judgement."""
    if score <= 25:
        return "in the 'effectively invisible to AI' band, where most local businesses sit today"
    elif score <= 50:
        return "in the 'partially visible' band, with one or two channels picking you up"
    elif score <= 75:
        return "in the 'discoverable' band, ahead of most of your local competition"
    else:
        return "in the 'AI-recommended' band, which is where you want to stay"


def render_inbound_report_html(lead: dict) -> str:
    """Render an inbound-flavored AI Visibility Report email.

    Reuses every helper from this module. The only differences from
    render_html() are the opening, the score-context phrase, the closing,
    and the absence of the operator-perspective scan-line.

    `lead` shape (set by skills/score_request/runner.py):
      - first_name: str
      - business / name: str  (the business name)
      - email: str
      - city: str
      - niche: str
      - ai_score: int
      - ai_breakdown: dict  (chatgpt, perplexity, robots_ok, maps_present)
      - ai_quick_wins: list[str]
      - website_url: str
      - source_context: 'inbound'  (caller MUST set this)
    """
    if lead.get("source_context") != "inbound":
        raise ValueError(
            "render_inbound_report_html requires lead['source_context']='inbound'. "
            "For outbound cold emails use render_html() instead."
        )

    score = int(lead.get("ai_score") or 0)
    business = lead.get("business") or lead.get("name") or "your business"
    first_name = lead.get("first_name", "there")
    city = lead.get("city", "your city")

    opening = INBOUND_OPENING.format(
        first_name=first_name,
        business=business,
        city=city,
        score=score,
        score_context=_score_context_phrase(score),
    )

    closing = INBOUND_CLOSING.format(
        calendly_url=os.environ.get(
            "SIGNAL_WORKS_CALENDLY",
            "https://calendly.com/boubacarbarry/signal-works-discovery-call",
        ),
    )

    # Reuse the score strip + quick-wins block from render_html() by extracting
    # them into shared internal helpers during the Friday build. For now, the
    # draft assumes a simplified inline structure. The real implementation
    # will share 90 percent of the markup with render_html().
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><title>Your AI Visibility Score</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  background:#f4f4f5;margin:0;padding:28px 16px;color:#1a1a1a;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f4f4f5">
<tr><td align="center">
  <table width="580" cellpadding="0" cellspacing="0" border="0"
    style="max-width:580px;background:#ffffff;border-radius:8px;overflow:hidden;">
    <!-- HEADER + SCORE STRIP (shared with render_html) -->
    <tr><td style="padding:8px 28px;border-bottom:1px solid #f3f4f6;">
      <span style="color:#9ca3af;font-size:11px;font-weight:600;
        letter-spacing:0.07em;text-transform:uppercase;">Signal Works</span>
      <span style="color:#d1d5db;font-size:11px;float:right;">
        AI Visibility Report &middot; {city}</span>
    </td></tr>
    <tr><td style="background:#0F1923;padding:16px 24px;">
      <span style="color:#FFFFFF;font-size:44px;font-weight:900;
        letter-spacing:-2px;">{score}</span><span style="color:#94A3B8;
        font-size:15px;font-weight:600;">/100</span>
      <div style="color:#CBD5E1;font-size:11px;font-weight:700;
        text-transform:uppercase;letter-spacing:0.08em;margin-top:3px;">
        {_score_label(score)}</div>
    </td></tr>
    <!-- BODY -->
    <tr><td style="padding:32px 32px 0 32px;">
      <div style="font-size:17px;line-height:1.8;color:#1a1a1a;">{opening}</div>
      <div class="gaps" style="background:#f9fafb;border-left:3px solid #EF4444;
        border-radius:0 6px 6px 0;padding:14px 18px;margin:18px 0;">
        <strong style="font-size:12px;font-weight:800;text-transform:uppercase;
          letter-spacing:0.07em;color:#EF4444;display:block;margin-bottom:10px;">
          3 things to fix first</strong>
        {_quick_wins_html(lead)}
      </div>
    </td></tr>
    <!-- CLOSING + CTA -->
    <tr><td style="padding:8px 32px 32px 32px;">
      <div style="font-size:17px;line-height:1.8;color:#1a1a1a;">{closing}</div>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
      <div style="font-size:16px;color:#111827;font-weight:700;">Boubacar</div>
      <div style="font-size:13px;color:#9ca3af;margin-top:4px;">
        Signal Works &middot; We make your business the one AI recommends.</div>
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>"""
    return html

# === END PASTE-IN APPEND ===============================================
