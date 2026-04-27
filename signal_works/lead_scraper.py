"""
signal_works/lead_scraper.py
Scrapes Google Maps for local businesses matching Signal Works criteria.
Uses SerpAPI (free tier) or direct HTTP to maps.google.com search.
Falls back to a manual CSV input mode if API unavailable.
"""
import os
import logging
import requests
from orchestrator.db import upsert_signal_works_lead

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")


def _fetch_maps_results(query: str, location: str, limit: int = 20) -> list[dict]:
    """
    Fetch Google Maps business listings.
    Tries SerpAPI local_results first; falls back to returning empty list
    with a warning so the caller can use manual CSV mode.
    """
    if not SERPAPI_KEY:
        logger.warning("SERPAPI_KEY not set. Returning empty list -- use manual CSV mode.")
        return []
    try:
        params = {
            "engine": "google_maps",
            "q": f"{query} in {location}",
            "hl": "en",
            "api_key": SERPAPI_KEY,
            "num": limit,
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for biz in data.get("local_results", [])[:limit]:
            results.append({
                "name": biz.get("title", ""),
                "phone": biz.get("phone", ""),
                "website": biz.get("website", ""),
                "rating": biz.get("rating", 0.0),
                "review_count": biz.get("reviews", 0),
                "maps_url": biz.get("place_id_search", biz.get("link", "")),
                "address": biz.get("address", ""),
            })
        return results
    except Exception as exc:
        logger.warning(f"SerpAPI fetch failed: {exc}. Use manual CSV mode.")
        return []


def scrape_google_maps_leads(
    niche: str,
    city: str,
    min_reviews: int = 20,
    max_reviews: int = 100,
    limit: int = 25,
    save_to_supabase: bool = True,
) -> list[dict]:
    """
    Scrape Google Maps for businesses in niche + city matching review criteria.
    Filters: min_reviews <= review_count <= max_reviews.
    Tags each lead with niche + city for Signal Works.
    Optionally upserts to Supabase.
    Returns list of enriched lead dicts.
    """
    raw = _fetch_maps_results(f"{niche}", city, limit=limit * 2)
    leads = []
    for biz in raw:
        rc = biz.get("review_count", 0)
        if rc < min_reviews or rc > max_reviews:
            continue
        lead = {
            "name": biz["name"],
            "email": "",
            "phone": biz.get("phone", ""),
            "website_url": biz.get("website", ""),
            "review_count": rc,
            "google_maps_url": biz.get("maps_url", ""),
            "niche": niche,
            "city": city,
            "ai_score": 0,
        }
        leads.append(lead)
        if save_to_supabase and lead["email"]:
            try:
                upsert_signal_works_lead(lead)
            except Exception as exc:
                logger.warning(f"Could not save lead to Supabase (continuing): {exc}")
    logger.info(f"scrape_google_maps_leads: {len(leads)} qualifying leads for '{niche}' in {city}")
    return leads[:limit]


def load_leads_from_csv(csv_path: str, niche: str, city: str) -> list[dict]:
    """
    Manual fallback: load leads from a CSV file.
    Expected columns: name, email, phone, website_url, review_count
    Used when SerpAPI key is unavailable or for hand-curated lists.
    """
    import csv
    leads = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = {
                "name": row.get("name", ""),
                "email": row.get("email", ""),
                "phone": row.get("phone", ""),
                "website_url": row.get("website_url", row.get("website", "")),
                "review_count": int(row.get("review_count", 0)),
                "google_maps_url": row.get("google_maps_url", ""),
                "niche": niche,
                "city": city,
                "ai_score": 0,
            }
            leads.append(lead)
            if lead["email"]:
                try:
                    upsert_signal_works_lead(lead)
                except Exception as exc:
                    logger.warning(f"Could not save lead to Supabase (continuing): {exc}")
    logger.info(f"load_leads_from_csv: loaded {len(leads)} leads from {csv_path}")
    return leads
