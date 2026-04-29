import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.expansion_ladder import PAIRS, target_for_tier


def test_ladder_starts_at_tier_1():
    assert PAIRS[0][2] == 1


def test_ladder_walks_in_ascending_tier_order():
    tiers = [p[2] for p in PAIRS]
    assert tiers == sorted(tiers)


def test_target_for_tier_utah_is_10():
    assert target_for_tier(1) == 10
    assert target_for_tier(2) == 10


def test_target_for_tier_outside_utah_is_20():
    assert target_for_tier(3) == 20
    assert target_for_tier(6) == 20


def test_ladder_has_no_duplicate_pairs():
    seen = set()
    for niche, city, tier, _ in PAIRS:
        key = (niche, city)
        assert key not in seen, f"duplicate pair: {key}"
        seen.add(key)


def test_ladder_has_at_least_300_pairs():
    """6 tiers, multiple cities and niches each. At-least bound, not exact."""
    assert len(PAIRS) >= 300
