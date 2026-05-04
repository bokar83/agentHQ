"""
signal_works/studio_web_scorer.py
==================================
Pre-filter for Studio Apollo candidates: score website quality BEFORE
spending reveal credits. High-need prospects (no site, broken site, old
site) get priority. Low-need (fast modern site) get deprioritized.

Scoring (0 = modern/healthy, higher = more opportunity):
  +3  no website at all
  +2  site returns non-200 or times out
  +2  site is on Wix / Squarespace / Weebly (often poor SEO)
  +1  copyright year <= current_year - 2 (site not recently updated)
  +1  page load > 3s (slow site)
  +1  no HTTPS
  +1  no contact info found in homepage text
  -1  site has structured data / schema.org markup (already optimized)

A score >= 2 is a "high-need" prospect worth revealing.
Score 0-1 is deprioritized (they may not need help).

Uses only HEAD + lightweight GET — no Firecrawl credits spent here.
Firecrawl is reserved for email extraction after scoring.
"""

import os
import re
import time
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

_TIMEOUT = 6  # seconds per request
_BUILDER_PATTERNS = re.compile(
    r"wix\.com|wixsite\.com|squarespace\.com|weebly\.com|godaddysites\.com"
    r"|strikingly\.com|jimdo\.com|webflow\.io|myshopify\.com",
    re.IGNORECASE,
)
_COPYRIGHT_YEAR = re.compile(r"copyright\s*[©&copy;]*\s*(\d{4})", re.IGNORECASE)
_SCHEMA_ORG = re.compile(r'schema\.org|application/ld\+json', re.IGNORECASE)
_CONTACT_SIGNALS = re.compile(
    r'contact|email|phone|call us|reach us|get in touch|book|schedule|reserve',
    re.IGNORECASE,
)

CURRENT_YEAR = datetime.now().year
MIN_SCORE = 2  # prospects below this are deprioritized


def score_website(url: str) -> dict:
    """
    Score a website for opportunity. Returns:
      {"score": int, "reason": str, "url": str, "reachable": bool}

    Score >= MIN_SCORE = high-need, worth revealing email for.
    """
    if not url:
        return {"score": 3, "reason": "no_website", "url": url, "reachable": False}

    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    score = 0
    reasons = []

    # Builder domain check (fast, no request needed)
    if _BUILDER_PATTERNS.search(url):
        score += 2
        reasons.append("builder_platform")

    # No HTTPS
    if url.startswith("http://"):
        score += 1
        reasons.append("no_https")

    # Try to fetch the homepage
    try:
        t0 = time.time()
        resp = requests.get(
            url,
            timeout=_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; site-quality-check/1.0)"},
            stream=True,
        )
        elapsed = time.time() - t0

        # Read just the first 32KB — enough for signals
        content = b""
        for chunk in resp.iter_content(1024 * 32):
            content = chunk
            break
        text = content.decode("utf-8", errors="ignore")

        if resp.status_code >= 400:
            score += 2
            reasons.append(f"http_{resp.status_code}")
        else:
            # Slow load
            if elapsed > 3.0:
                score += 1
                reasons.append(f"slow_{elapsed:.1f}s")

            # Old copyright year
            for m in _COPYRIGHT_YEAR.finditer(text):
                year = int(m.group(1))
                if year <= CURRENT_YEAR - 2:
                    score += 1
                    reasons.append(f"old_copyright_{year}")
                break  # first match only

            # No contact signals
            if not _CONTACT_SIGNALS.search(text):
                score += 1
                reasons.append("no_contact_signals")

            # Has schema.org (already somewhat optimized — deduct)
            if _SCHEMA_ORG.search(text):
                score -= 1
                reasons.append("has_schema_org")

        reachable = resp.status_code < 400

    except requests.exceptions.SSLError:
        score += 1
        reasons.append("ssl_error")
        reachable = False
    except requests.exceptions.ConnectionError:
        score += 2
        reasons.append("connection_error")
        reachable = False
    except requests.exceptions.Timeout:
        score += 2
        reasons.append("timeout")
        reachable = False
    except Exception as e:
        score += 1
        reasons.append(f"fetch_error")
        reachable = False
        logger.debug(f"score_website error for {url}: {e}")

    return {
        "score": score,
        "reason": ",".join(reasons) if reasons else "ok",
        "url": url,
        "reachable": reachable,
    }


def filter_studio_candidates(people: list[dict], min_score: int = MIN_SCORE) -> list[dict]:
    """
    Given a list of Apollo people dicts, score each one's website and
    return them sorted by opportunity score (highest first).

    People with no website_url on the Apollo record are scored as
    high-need automatically (score=3). People whose site scores below
    min_score are moved to the back of the list (still included — not
    dropped — so we never leave the harvest empty-handed).

    Each person dict gets a 'web_score' and 'web_reason' key added.
    """
    scored = []
    for person in people:
        org = person.get("organization") or {}
        website = org.get("website_url") or org.get("primary_domain") or ""

        if website and not website.startswith("http"):
            website = "https://" + website

        result = score_website(website)
        person["web_score"] = result["score"]
        person["web_reason"] = result["reason"]
        scored.append(person)
        logger.debug(
            f"  web_score={result['score']} ({result['reason']}) "
            f"for {org.get('name','?')} @ {website or 'NO SITE'}"
        )

    # Sort: high score first (most opportunity), then alphabetical by company
    scored.sort(key=lambda p: (-p["web_score"], (p.get("organization") or {}).get("name", "")))

    high = sum(1 for p in scored if p["web_score"] >= min_score)
    logger.info(f"  web_scorer: {high}/{len(scored)} candidates are high-need (score>={min_score})")
    return scored
