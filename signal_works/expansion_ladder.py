"""
signal_works/expansion_ladder.py
================================
Geo-expansion ladder for SW lead harvest. Walked top-to-bottom each day
until the daily target is hit. Tier 1-2 = Utah (target=10), Tier 3+ = wider
geography (target=20).

PAIRS is a flat list of (niche, city, tier, target_for_tier) tuples.
"""
from typing import List, Tuple

# Niches by tier. Tier 1-2 stays narrow (Utah-only). Tier 3+ widens.
_NICHES_TIER_1_2 = [
    "dental", "hvac", "roofing", "plumbing", "chiropractic", "pediatric dentist",
]
_NICHES_TIER_3_4 = _NICHES_TIER_1_2 + ["electrical", "landscaping"]
_NICHES_TIER_5_6 = _NICHES_TIER_3_4 + [
    "auto repair", "veterinary", "physical therapy", "cleaning service",
]

# Cities by tier.
_CITIES_TIER_1 = [
    "Salt Lake City, UT", "Provo, UT", "Ogden, UT", "Sandy, UT",
    "Lehi, UT", "St. George, UT", "West Jordan, UT", "Murray, UT", "Draper, UT",
]
_CITIES_TIER_2 = ["Park City, UT", "Heber, UT", "Bountiful, UT", "Logan, UT", "Cedar City, UT"]
_CITIES_TIER_3 = ["Denver, CO", "Phoenix, AZ", "Las Vegas, NV", "Boise, ID", "Albuquerque, NM"]
_CITIES_TIER_4 = ["Seattle, WA", "Portland, OR", "San Diego, CA", "Reno, NV", "Tucson, AZ"]
_CITIES_TIER_5 = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Atlanta, GA",
    "Dallas, TX", "Miami, FL", "Boston, MA", "Philadelphia, PA", "Washington, DC",
    "Minneapolis, MN", "Detroit, MI", "Tampa, FL", "Charlotte, NC", "Nashville, TN",
]
_CITIES_TIER_6 = ["Toronto, ON", "Vancouver, BC", "Calgary, AB", "Montreal, QC"]


def _build_pairs() -> List[Tuple[str, str, int, int]]:
    out: list[tuple[str, str, int, int]] = []
    for tier, cities, niches, target in [
        (1, _CITIES_TIER_1, _NICHES_TIER_1_2, 10),
        (2, _CITIES_TIER_2, _NICHES_TIER_1_2, 10),
        (3, _CITIES_TIER_3, _NICHES_TIER_3_4, 20),
        (4, _CITIES_TIER_4, _NICHES_TIER_3_4, 20),
        (5, _CITIES_TIER_5, _NICHES_TIER_5_6, 20),
        (6, _CITIES_TIER_6, _NICHES_TIER_5_6, 20),
    ]:
        for city in cities:
            for niche in niches:
                out.append((niche, city, tier, target))
    return out


PAIRS: list[tuple[str, str, int, int]] = _build_pairs()


def target_for_tier(tier: int) -> int:
    """Return daily SW lead target for a given tier."""
    return 10 if tier <= 2 else 20
