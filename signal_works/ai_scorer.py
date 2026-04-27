"""
signal_works/ai_scorer.py
Generates an AI Visibility Score (0-100) for a local business.

Scoring breakdown:
  +25  Business mentioned in ChatGPT answer for "[niche] in [city]"
  +25  Business mentioned in Perplexity answer for "[niche] in [city]"
  +25  robots.txt allows GPTBot AND PerplexityBot (no blocking)
  +25  Bing Places listing is claimed and populated

Honest caveat: measures infrastructure readiness + known citation sources.
Does NOT guarantee future AI appearances. Defensible because it measures fixable things.
"""
import os
import re
import logging
import requests
from urllib.parse import urlparse
from openai import OpenAI

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")


def _query_chatgpt(business_name: str, niche: str, city: str) -> bool:
    """Ask ChatGPT 'best [niche] in [city]'. Returns True if business_name appears."""
    try:
        queries = [
            f"best {niche} in {city}",
            f"top {niche} near {city}",
        ]
        for q in queries:
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful local search assistant. Answer concisely."},
                    {"role": "user", "content": q},
                ],
                max_tokens=300,
            )
            answer = resp.choices[0].message.content or ""
            if business_name.lower() in answer.lower():
                return True
        return False
    except Exception as exc:
        logger.warning(f"_query_chatgpt failed: {exc}")
        return False


def _query_perplexity(business_name: str, niche: str, city: str) -> bool:
    """Ask Perplexity 'best [niche] in [city]'. Returns True if business_name appears."""
    if not PERPLEXITY_API_KEY:
        logger.warning("PERPLEXITY_API_KEY not set -- skipping Perplexity check, scoring 0")
        return False
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [{"role": "user", "content": f"best {niche} in {city}"}],
            "max_tokens": 400,
        }
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"]
        return business_name.lower() in answer.lower()
    except Exception as exc:
        logger.warning(f"_query_perplexity failed: {exc}")
        return False


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
        blocked_bots = ["gptbot", "perplexitybot", "claudebot", "ccbot"]
        for bot in blocked_bots:
            pattern = rf"user-agent:\s*{bot}.*?disallow:\s*/(?:\s|$)"
            if re.search(pattern, text, re.DOTALL | re.IGNORECASE):
                return False
        return True
    except Exception as exc:
        logger.warning(f"_check_robots_txt failed for {website_url}: {exc}")
        return False


def _check_bing_places(business_name: str, city: str) -> bool:
    """Returns True if business has a Bing Places listing."""
    bing_key = os.environ.get("BING_SEARCH_API_KEY", "")
    if not bing_key:
        logger.warning("BING_SEARCH_API_KEY not set -- skipping Bing check, scoring 0")
        return False
    try:
        headers = {"Ocp-Apim-Subscription-Key": bing_key}
        params = {"q": f"{business_name} {city} site:bing.com/maps", "count": 3}
        resp = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers=headers,
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        web_pages = data.get("webPages", {}).get("value", [])
        return any(
            "bing.com/maps" in r.get("url", "") or business_name.lower() in r.get("name", "").lower()
            for r in web_pages
        )
    except Exception as exc:
        logger.warning(f"_check_bing_places failed: {exc}")
        return False


def score_business(
    business_name: str,
    city: str,
    niche: str,
    website_url: str = "",
) -> dict:
    """Generate AI Visibility Score (0-100) for a business."""
    chatgpt_hit = _query_chatgpt(business_name, niche, city)
    perplexity_hit = _query_perplexity(business_name, niche, city)
    robots_ok = _check_robots_txt(website_url)
    bing_listed = _check_bing_places(business_name, city)

    score = (
        (25 if chatgpt_hit else 0) +
        (25 if perplexity_hit else 0) +
        (25 if robots_ok else 0) +
        (25 if bing_listed else 0)
    )

    quick_wins = []
    if not robots_ok:
        quick_wins.append("Fix robots.txt -- AI crawlers (GPTBot, PerplexityBot) are currently blocked. This makes you invisible to ChatGPT and Perplexity.")
    if not bing_listed:
        quick_wins.append("Claim your Bing Places listing -- ChatGPT uses Bing to find local businesses. Unclaimed = invisible to ChatGPT.")
    if not chatgpt_hit and not perplexity_hit:
        quick_wins.append("Build topical authority content -- answer the exact questions your customers are asking AI tools about your service in your city.")

    return {
        "score": score,
        "breakdown": {
            "chatgpt": chatgpt_hit,
            "perplexity": perplexity_hit,
            "robots_ok": robots_ok,
            "bing_listed": bing_listed,
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
