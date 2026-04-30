import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skills.apollo_skill.apollo_client import find_owner_by_company, CW_ICP_WIDENED


def test_cw_icp_widened_includes_vp_seniority():
    assert "vp" in CW_ICP_WIDENED["person_seniorities"]


def test_cw_icp_widened_employees_up_to_200():
    assert "1,200" in CW_ICP_WIDENED["organization_num_employees_ranges"]


def test_cw_icp_widened_includes_park_city():
    assert any("Park City" in loc for loc in CW_ICP_WIDENED["person_locations"])


def test_find_owner_by_company_returns_email_on_match():
    with patch("skills.apollo_skill.apollo_client.httpx.post") as mock_post:
        mock_post.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: {"organization": {"primary_domain": "edgeeyewear.com"}},
            ),
            MagicMock(
                status_code=200,
                json=lambda: {"person": {"email": "kurt@edgeeyewear.com", "name": "Kurt Daems"}},
            ),
        ]
        # raise_for_status on MagicMock is a no-op (200), but in case the implementation
        # calls .raise_for_status(), MagicMock handles it gracefully.
        result = find_owner_by_company("Edge Eyewear", "Salt Lake City, UT")
    assert result == {
        "domain": "edgeeyewear.com",
        "email": "kurt@edgeeyewear.com",
        "name": "Kurt Daems",
    }


def test_find_owner_by_company_returns_domain_only_when_no_owner():
    """When enrich finds domain but ALL match attempts return no owner, caller can pass domain to Hunter."""
    with patch("skills.apollo_skill.apollo_client.httpx.post") as mock_post:
        # First call: organizations/enrich returns domain
        # Subsequent calls (one per owner title attempt): all return no person
        responses = [
            MagicMock(
                status_code=200,
                json=lambda: {"organization": {"primary_domain": "smallbiz.com"}},
            )
        ]
        # Add 5 "no person" responses, one for each owner title (Owner, Founder, CEO, President, Operator)
        for _ in range(5):
            responses.append(MagicMock(status_code=200, json=lambda: {"person": None}))
        mock_post.side_effect = responses
        result = find_owner_by_company("Small Biz", "Provo, UT")
    assert result == {"domain": "smallbiz.com", "email": None, "name": None}


def test_find_owner_by_company_returns_none_when_enrich_misses():
    with patch("skills.apollo_skill.apollo_client.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"organization": None},
        )
        result = find_owner_by_company("Nonexistent Biz", "Provo, UT")
    assert result is None
