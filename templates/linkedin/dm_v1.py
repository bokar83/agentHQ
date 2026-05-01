"""
templates/linkedin/dm_v1.py
============================
SINGLE SOURCE OF TRUTH for the LinkedIn cold DM.

Used by skills.linkedin_mvm.generate_dms to produce personalized DMs from a
target_list.csv. Mirrors the cold_outreach.py pattern.

TO UPDATE THE TEMPLATE: edit this file only.
  - Change DM_BODY or BUMP_BODY as needed.
  - Do NOT change the variable names -- everything imports by name.
  - Do NOT copy this text into any other file, crew, or agent prompt.

Version history:
  v1.0 (2026-04-30) - First version. Asset-first opener, no agenda. 20-min CTA.
                      Bump after 7 days. One bump only.
  v1.1 (2026-04-30) - Removed "3 biggest" -> "biggest". Matches About + Featured
                      copy. Honest at any number, scales across firm size.
  v1.2 (2026-04-30) - Added CONNECTION_NOTE_BODY (300 char cap) for Path A
                      mechanic: connection request with note on Day 1, full
                      DM after accept. See memory: reference_linkedin_dm_mechanics.
  v1.3 (2026-04-30) - Sankofa + ctq-social pass. CONNECTION_NOTE_BODY
                      reframed (relational only, no offer pre-pitch). DM_BODY
                      now acknowledges the accept, opens with a NEW scene
                      (not the repeated hook), and closes with a dual CTA
                      (call OR Field Guide). BUMP_BODY mirrors the dual CTA.
                      Five warmth edits applied to land closer to Boubacar
                      voice (less consultant-y, more operator-to-operator).
"""

# Sent AFTER the prospect accepts the connection request. Acknowledges the
# accept, pivots to a NEW scene (not the connection-note hook reused), names
# the offer, and closes with a dual CTA (call OR Field Guide).
#
# Variables expected by formatter:
#   {first_name} - prospect first name only
#   {calendly_url} - the AI Governance Assessment Call URL.
DM_BODY = """Hi {first_name}, thanks for the connect.

Most of the firms I talk to find their first real AI exposure inside a tool they have used for years. Some vendor amendment that arrived on a Friday afternoon. Some default toggle on a feature flag. Some admin panel nobody has logged into in six months. The CRM, the email platform, the practice management suite. The exposure is real and almost nobody has it on paper.

If this is something you are actually wrestling with, I run a free 20-minute AI Governance Assessment Call. We walk your stack and I tell you what I am seeing. No pitch.

If you would rather just read the frame I use, I can send the AI Governance Field Guide. Forty pages, no opt-in form, no follow-up. Reply with "guide" and I will send it over.

Calendly if the call works: {calendly_url}

Boubacar"""


# Sent on Day 1 as the LinkedIn connection-request note (Path A mechanic).
# LinkedIn caps connection notes at 300 characters.
#
# v1.3: relational-only copy. No offer pre-pitch. The connection note's job
# is to earn the accept, not sell the call. The call gets named in DM_BODY
# AFTER acceptance. Cuts "free 20-min" / "no pitch" / "open to a chat" - those
# all telegraph the funnel before the relationship exists.
#
# Variables expected:
#   {first_name} - prospect first name only
#   {hook}       - one-sentence personalization, will be auto-trimmed if too long
CONNECTION_NOTE_BODY = """Hi {first_name},

{hook}

That gap is where most of the work lives. The Utah professional services bench is small enough that we should probably know each other.

Boubacar"""


def render_connection_note(first_name: str, hook: str, max_chars: int = 300) -> str:
    """Render the LinkedIn connection-request note (300 char hard cap).

    LinkedIn truncates anything over 300 characters in the invite note. We
    auto-trim the hook to make the full note fit. Returns a string guaranteed
    to be under max_chars (default 300).
    """
    name = first_name.strip()
    hook_clean = hook.strip()

    # First try: render with the full hook.
    note = CONNECTION_NOTE_BODY.format(first_name=name, hook=hook_clean)
    if len(note) <= max_chars:
        return note

    # Compute fixed-content length (everything except the hook).
    fixed_template = CONNECTION_NOTE_BODY.format(first_name=name, hook="__HOOK__")
    fixed_len = len(fixed_template) - len("__HOOK__")
    available = max_chars - fixed_len

    # Trim the hook on a word boundary, drop trailing punctuation, add ellipsis.
    if available <= 0:
        # Fallback: hook drops entirely.
        return CONNECTION_NOTE_BODY.format(first_name=name, hook="").rstrip()[:max_chars]

    if len(hook_clean) <= available:
        return CONNECTION_NOTE_BODY.format(first_name=name, hook=hook_clean)

    trimmed = hook_clean[: available - 1].rsplit(" ", 1)[0].rstrip(",.;:")
    return CONNECTION_NOTE_BODY.format(first_name=name, hook=trimmed)


# Sent ~7 days after DM_BODY if no reply. Mirrors the dual CTA from DM_BODY
# so the prospect still has the lower-friction option.
# Same variables.
BUMP_BODY = """Hi {first_name},

Bumping this in case it got buried.

If the call still works, here is the link: {calendly_url}

If you would rather just have the Field Guide, reply with "guide" and I will send it.

If neither, no worries. File me away.

Boubacar"""


# Default Calendly URL: AI Governance Assessment Call (20 min) -- created
# 2026-04-30 via PAT API. URI:
# https://api.calendly.com/event_types/93058142-11b5-48ed-857d-75365aa94af4
# Override via env var CALENDLY_AI_GOVERNANCE_URL if needed.
import os as _os
DEFAULT_CALENDLY_URL = _os.environ.get(
    "CALENDLY_AI_GOVERNANCE_URL",
    "https://calendly.com/boubacarbarry/ai-governance-assessment-call",
)


def render_dm(first_name: str, hook: str, calendly_url: str = DEFAULT_CALENDLY_URL) -> str:
    """Render the cold DM with personalization."""
    return DM_BODY.format(
        first_name=first_name.strip(),
        hook=hook.strip(),
        calendly_url=calendly_url.strip(),
    )


def render_bump(first_name: str, calendly_url: str = DEFAULT_CALENDLY_URL) -> str:
    """Render the 7-day bump."""
    return BUMP_BODY.format(
        first_name=first_name.strip(),
        calendly_url=calendly_url.strip(),
    )
