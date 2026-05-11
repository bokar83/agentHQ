"""
signal_works/email_gate.py
==========================
Role-mailbox + deliverability hard gate. Two-step filter:

  Step 1 (free, local): drop emails whose local-part matches a known role
         prefix (info, sales, contact, support, dispatcher, etc).
  Step 2 (paid, Hunter Email Verifier API, 1 credit/lookup): drop emails
         that are catch-all (accept_all=true), disposable, gibberish,
         webmail (unless allow_webmail=True), invalid, or score<80 unless
         status=='valid'.

Why this exists:
  Today's SW lead pool is ~20% role mailboxes and today's drafts are ~34%
  role mailboxes. Sending to role mailboxes at scale (50+/day) burns
  sender reputation per Google Postmaster thresholds in 7-14 days. This
  gate MUST run before AUTO_SEND_SW/CW flip to true.

Hunter Email Verifier budget:
  4000 credits/month available, ~134 used this period (99.7% headroom).
  In-run cache by email = same address never re-queried in one process.

Usage:
  from signal_works.email_gate import gate_email, EmailGateDrop

  try:
      gate_email("derek@elevateroofing.com", source="sw_topup")
      # email is safe to use, code continues
  except EmailGateDrop as e:
      logger.info(f"email_gate dropped: {e.reason} -- {e.detail}")
      # caller decides: pick next candidate, skip lead, etc.

Wired into:
  - signal_works/hunter_client.py            (all 3 tiers)
  - signal_works/topup_leads.py:_resolve_email
  - signal_works/topup_cw_leads.py           (Apollo email path)
  - skills/email_enrichment/enrichment_tool.py
  - signal_works/lead_scraper.py             (replaces SKIP_EMAIL_PREFIXES)
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Role prefixes (full set from Ship 2c spec) ──────────────────────
# Trailing digits are stripped before match: info2@ -> info -> matches.
ROLE_PREFIXES: set[str] = {
    "info", "office", "contact", "contactus", "hello", "hi",
    "scheduling", "schedule", "appointments", "booking", "bookings",
    "dispatcher", "dispatch", "frontdesk", "front-desk", "reception",
    "admin", "administration", "administrator", "webmaster", "postmaster",
    "noreply", "no-reply", "donotreply", "do-not-reply", "mailer-daemon",
    "support", "help", "helpdesk", "service", "customerservice", "cs",
    "sales", "marketing", "team", "staff", "hr", "jobs", "careers",
    "billing", "accounts", "accounting", "ap", "ar", "finance",
    "projects", "events", "media", "press", "pr",
    "legal", "compliance", "privacy", "abuse", "security",
    "general", "main", "mail", "email", "inquiries", "enquiries",
}

# Free-webmail providers. We drop these unless caller explicitly passes
# allow_webmail=True (e.g. enrichment paths that target small founder-led
# shops where personal Gmail is sometimes the business inbox).
_WEBMAIL_DOMAINS: set[str] = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "me.com", "live.com", "msn.com", "comcast.net",
    "protonmail.com", "proton.me", "yandex.com", "mail.com", "gmx.com",
    "zoho.com", "fastmail.com", "ymail.com", "rocketmail.com",
}

_TRAILING_DIGIT_RE = re.compile(r"\d+$")

HUNTER_VERIFIER_URL = "https://api.hunter.io/v2/email-verifier"

# In-run verifier cache. Maps email -> (passed, reason, detail).
# Passed=True caches a clean verify; Passed=False caches a drop reason so
# the same address re-queried in one run consumes 0 extra credits.
_VERIFY_CACHE: dict[str, tuple[bool, str, str]] = {}


class EmailGateDrop(Exception):
    """Raised when an email fails the gate. reason is one of:
        role_prefix, accept_all, disposable, webmail, gibberish,
        low_score, invalid, verifier_down
    detail carries the email address and any structured context.
    """

    def __init__(self, reason: str, detail: str = ""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


def reset_verify_cache() -> None:
    """Test hook. Clears the in-run verifier cache."""
    _VERIFY_CACHE.clear()


def _strip_trailing_digits(local: str) -> str:
    return _TRAILING_DIGIT_RE.sub("", local)


def _is_role_prefix(email: str) -> tuple[bool, str]:
    """Return (matches, normalized_local). Strips trailing digits."""
    if "@" not in email:
        return False, ""
    local = email.rsplit("@", 1)[0].lower()
    stripped = _strip_trailing_digits(local)
    return stripped in ROLE_PREFIXES, stripped


def _domain_of(email: str) -> str:
    if "@" not in email:
        return ""
    return email.rsplit("@", 1)[1].lower()


def _hunter_verify(email: str) -> Optional[dict]:
    """Single Hunter Email Verifier call. Returns parsed data dict or
    None on transport error (treated by caller as verifier_down)."""
    api_key = os.environ.get("HUNTER_API_KEY", "")
    if not api_key:
        logger.warning("email_gate: HUNTER_API_KEY not set, verifier skipped")
        return None
    try:
        resp = httpx.get(
            HUNTER_VERIFIER_URL,
            params={"email": email, "api_key": api_key},
            timeout=15,
        )
    except Exception as e:
        logger.warning(f"email_gate: verifier request failed for {email}: {e}")
        return None
    if resp.status_code == 429:
        logger.warning(f"email_gate: 429 rate limited on {email}")
        return None
    if resp.status_code != 200:
        logger.warning(f"email_gate: verifier status {resp.status_code} on {email}")
        return None
    return resp.json().get("data", {})


def _log_drop(reason: str, source: str, detail: str = "") -> None:
    """Best-effort drop logger. Writes one row into pipeline_metrics with
    step='email_gate_drop', reason=<reason>, skipped=1. Never raises.

    Schema reuse: pipeline_metrics has (step, attempted, succeeded,
    skipped, reason). We pack source+detail into reason as
    '<source>:<reason>:<detail>' so downstream SQL can split on ':'.
    """
    try:
        from signal_works.pipeline_metrics import log_step
        packed = f"{source}:{reason}"
        if detail:
            packed = f"{packed}:{detail[:200]}"
        log_step(
            step="email_gate_drop",
            attempted=1,
            succeeded=0,
            skipped=1,
            reason=packed,
        )
    except Exception as e:
        logger.debug(f"email_gate: _log_drop failed: {e}")


def gate_email(
    email: str,
    source: str = "unknown",
    allow_webmail: bool = False,
    skip_verifier: bool = False,
) -> str:
    """Run the two-step gate on `email`. Returns the normalized email on
    success. Raises EmailGateDrop on failure.

    Args:
      email: candidate email address.
      source: metric tag for the drop log (sw_topup, cw_topup,
              enrichment, hunter_tier1, etc).
      allow_webmail: if True, do NOT drop gmail/yahoo/outlook/etc. Used
              by paths where founder-led shops legitimately run on
              personal Gmail.
      skip_verifier: if True, run only the local prefix check (no
              Hunter Email Verifier call). Used by lead_scraper.py
              tight loop where the email is one of many candidates and
              spending a credit per is wasteful -- the gate is re-run
              on the final pick by the harvest path.
    """
    if not email or "@" not in email:
        raise EmailGateDrop("invalid", detail=email or "")

    email = email.strip().lower()

    # ── Step 1: role-prefix local check (free) ─────────────────
    is_role, stripped = _is_role_prefix(email)
    if is_role:
        _log_drop("role_prefix", source, detail=f"{email} (matched={stripped})")
        raise EmailGateDrop("role_prefix", detail=f"{email} (matched={stripped})")

    # Webmail check is free too -- skip Hunter for free providers.
    domain = _domain_of(email)
    if domain in _WEBMAIL_DOMAINS and not allow_webmail:
        _log_drop("webmail", source, detail=email)
        raise EmailGateDrop("webmail", detail=email)

    if skip_verifier:
        return email

    # ── Step 2: Hunter Email Verifier (1 credit, cached per-run) ─
    cached = _VERIFY_CACHE.get(email)
    if cached is not None:
        passed, reason, detail = cached
        if passed:
            return email
        _log_drop(reason, source, detail=detail)
        raise EmailGateDrop(reason, detail=detail)

    data = _hunter_verify(email)
    if data is None:
        # Verifier unreachable. Fail-open with verifier_down so caller
        # can decide whether to use the email or skip. Drop is logged
        # but no cache entry stored -- next call will retry.
        _log_drop("verifier_down", source, detail=email)
        raise EmailGateDrop("verifier_down", detail=email)

    status = (data.get("status") or "").lower()
    score = int(data.get("score") or 0)
    accept_all = bool(data.get("accept_all"))
    disposable = bool(data.get("disposable"))
    gibberish = bool(data.get("gibberish"))
    webmail = bool(data.get("webmail"))
    smtp_check = data.get("smtp_check")

    drop_reason: Optional[str] = None
    drop_detail = f"{email} status={status} score={score}"

    if status == "invalid":
        drop_reason = "invalid"
    elif smtp_check is False:
        drop_reason = "invalid"
        drop_detail += " smtp_check=false"
    elif accept_all:
        drop_reason = "accept_all"
    elif disposable:
        drop_reason = "disposable"
    elif gibberish:
        drop_reason = "gibberish"
    elif webmail and not allow_webmail:
        drop_reason = "webmail"
    elif score < 80 and status != "valid":
        drop_reason = "low_score"

    if drop_reason:
        _VERIFY_CACHE[email] = (False, drop_reason, drop_detail)
        _log_drop(drop_reason, source, detail=drop_detail)
        raise EmailGateDrop(drop_reason, detail=drop_detail)

    _VERIFY_CACHE[email] = (True, "", "")
    return email
