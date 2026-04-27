"""
signal_works/ai_scorer.py
Generates an AI Visibility Score (0-100) for a local business.

Scoring breakdown:
  +25  Business mentioned when OpenRouter (via GPT-4o-mini) answers "[niche] in [city]"
  +25  Business mentioned when OpenRouter (via perplexity/sonar) answers "[niche] in [city]"
  +25  robots.txt allows GPTBot AND PerplexityBot (no blocking)
  +25  Business appears in SerpAPI Google Maps results for niche + city

All LLM calls go through OpenRouter (OPENROUTER_API_KEY already in .env).
SerpAPI (SERPER_API_KEY already in .env) replaces the Bing Places API.

Honest caveat: measures infrastructure readiness + known citation sources.
Does NOT guarantee future AI appearances. Defensible because it measures fixable things.
"""
import os
import re
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def _openrouter_chat(model: str, messages: list[dict], max_tokens: int = 400) -> str:
    """Send a chat request to OpenRouter. Returns response text or empty string."""
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set -- cannot query AI models")
        return ""
    try:
        resp = requests.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://signalworks.ai",
                "X-Title": "Signal Works AI Scorer",
            },
            json={"model": model, "messages": messages, "max_tokens": max_tokens},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"] or ""
    except Exception as exc:
        logger.warning(f"OpenRouter call failed ({model}): {exc}")
        return ""


def _query_chatgpt(business_name: str, niche: str, city: str) -> bool:
    """Ask GPT-4o-mini via OpenRouter. Returns True if business_name appears."""
    queries = [f"best {niche} in {city}", f"top {niche} near {city}"]
    for q in queries:
        answer = _openrouter_chat(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful local search assistant. Answer concisely."},
                {"role": "user", "content": q},
            ],
        )
        if answer and business_name.lower() in answer.lower():
            return True
    return False


def _query_perplexity(business_name: str, niche: str, city: str) -> bool:
    """Ask Perplexity Sonar via OpenRouter. Returns True if business_name appears."""
    answer = _openrouter_chat(
        model="perplexity/sonar",
        messages=[{"role": "user", "content": f"best {niche} in {city}"}],
    )
    return bool(answer and business_name.lower() in answer.lower())


def _check_robots_txt(website_url: str) -> bool:
    """Returns True if AI crawlers are NOT blocked in robots.txt."""
    if not website_url:
        return False
    try:
        parsed = urlparse(website_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        resp = requests.get(robots_url, timeout=10)
        if resp.status_code == 404:
            return True
        text = resp.text.lower()
        for bot in ["gptbot", "perplexitybot", "claudebot", "ccbot"]:
            pattern = rf"user-agent:\s*{bot}.*?disallow:\s*/(?:\s|$)"
            if re.search(pattern, text, re.DOTALL | re.IGNORECASE):
                return False
        return True
    except Exception as exc:
        logger.warning(f"_check_robots_txt failed for {website_url}: {exc}")
        return False


def _check_serp_presence(business_name: str, niche: str, city: str) -> bool:
    """
    Uses SerpAPI (SERPER_API_KEY) to check if business appears in Google Maps
    results for niche + city. A Maps presence = higher chance of AI citation.
    """
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not set -- skipping Maps presence check, scoring 0")
        return False
    try:
        resp = requests.post(
            "https://google.serper.dev/maps",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": f"{niche} in {city}", "num": 10},
            timeout=15,
        )
        resp.raise_for_status()
        places = resp.json().get("places", [])
        name_lower = business_name.lower()
        return any(name_lower in p.get("title", "").lower() for p in places)
    except Exception as exc:
        logger.warning(f"_check_serp_presence failed: {exc}")
        return False


def score_business(
    business_name: str,
    city: str,
    niche: str,
    website_url: str = "",
) -> dict:
    """
    Generate AI Visibility Score (0-100) for a business.
    Returns: {score, breakdown, quick_wins, business_name, city, niche}
    """
    chatgpt_hit = _query_chatgpt(business_name, niche, city)
    perplexity_hit = _query_perplexity(business_name, niche, city)
    robots_ok = _check_robots_txt(website_url)
    maps_present = _check_serp_presence(business_name, niche, city)

    score = (
        (25 if chatgpt_hit else 0) +
        (25 if perplexity_hit else 0) +
        (25 if robots_ok else 0) +
        (25 if maps_present else 0)
    )

    quick_wins = []
    if not robots_ok:
        quick_wins.append("Fix robots.txt: AI crawlers (GPTBot, PerplexityBot) are currently blocked, making you invisible to ChatGPT and Perplexity.")
    if not maps_present:
        quick_wins.append("Strengthen your Google Maps presence and claim Bing Places: AI tools use Maps data to find and cite local businesses.")
    if not chatgpt_hit and not perplexity_hit:
        quick_wins.append("Build topical authority content: answer the exact questions your customers ask AI tools about your service in your city.")

    return {
        "score": score,
        "breakdown": {
            "chatgpt": chatgpt_hit,
            "perplexity": perplexity_hit,
            "robots_ok": robots_ok,
            "maps_present": maps_present,
        },
        "quick_wins": quick_wins,
        "business_name": business_name,
        "city": city,
        "niche": niche,
    }


def score_leads_batch(leads: list[dict]) -> list[dict]:
    """Score a list of leads in sequence. Updates ai_score in each lead dict."""
    for lead in leads:
        result = score_business(
            lead["name"], lead["city"], lead["niche"], lead.get("website_url", "")
        )
        lead["ai_score"] = result["score"]
        lead["ai_breakdown"] = result["breakdown"]
        lead["ai_quick_wins"] = result["quick_wins"]
        logger.info(f"Scored {lead['name']}: {result['score']}/100")
    return leads
