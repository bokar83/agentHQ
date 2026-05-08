"""Tests for _first_name_from_email and _extract_first_name in
skills/outreach/sequence_engine.py.

Lock the gkirz/jsmith/mhall initial+lastname fix (2026-05-07) so future
regressions trigger a test failure instead of bad email drafts.
"""
import sys
from pathlib import Path

# Make skills/outreach importable
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.outreach.sequence_engine import (  # noqa: E402
    _first_name_from_email,
    _extract_first_name,
    _looks_like_initial_plus_lastname,
)


class TestInitialPlusLastnameDetector:
    def test_gkirz_pattern_flagged(self):
        assert _looks_like_initial_plus_lastname("gkirz") is True

    def test_jsmith_pattern_flagged(self):
        assert _looks_like_initial_plus_lastname("jsmith") is True

    def test_mhall_pattern_flagged(self):
        assert _looks_like_initial_plus_lastname("mhall") is True

    def test_lgrow_pattern_flagged(self):
        assert _looks_like_initial_plus_lastname("lgrow") is True

    def test_allowlisted_scott_not_flagged(self):
        assert _looks_like_initial_plus_lastname("scott") is False

    def test_allowlisted_chris_not_flagged(self):
        assert _looks_like_initial_plus_lastname("chris") is False

    def test_allowlisted_brian_not_flagged(self):
        assert _looks_like_initial_plus_lastname("brian") is False

    def test_first_letter_vowel_not_flagged(self):
        assert _looks_like_initial_plus_lastname("andrew") is False

    def test_second_letter_vowel_not_flagged(self):
        assert _looks_like_initial_plus_lastname("paul") is False
        assert _looks_like_initial_plus_lastname("jeff") is False

    def test_too_short_not_flagged(self):
        assert _looks_like_initial_plus_lastname("jo") is False
        assert _looks_like_initial_plus_lastname("jon") is False

    def test_too_long_not_flagged(self):
        assert _looks_like_initial_plus_lastname("mjohnson") is False
        assert _looks_like_initial_plus_lastname("robsnow") is False


class TestFirstNameFromEmail:
    def test_gkirz_returns_low(self):
        assert _first_name_from_email("gkirz@company.com") == ("Gkirz", "low")

    def test_jsmith_returns_low(self):
        assert _first_name_from_email("jsmith@company.com") == ("Jsmith", "low")

    def test_mhall_returns_low(self):
        assert _first_name_from_email("mhall@x.com") == ("Mhall", "low")

    def test_lgrow_returns_low(self):
        assert _first_name_from_email("lgrow@x.com") == ("Lgrow", "low")

    def test_scott_allowlisted_returns_high(self):
        assert _first_name_from_email("scott@commroof.com") == ("Scott", "high")

    def test_chris_allowlisted_returns_high(self):
        assert _first_name_from_email("chris@x.com") == ("Chris", "high")

    def test_brian_allowlisted_returns_high(self):
        assert _first_name_from_email("brian@x.com") == ("Brian", "high")

    def test_dotted_separator_returns_high(self):
        assert _first_name_from_email("john.smith@x.com") == ("John", "high")

    def test_dashed_separator_returns_high(self):
        assert _first_name_from_email("jeff-campbell@x.com") == ("Jeff", "high")

    def test_dr_prefix_stripped_high(self):
        assert _first_name_from_email("drmarcus@x.com") == ("Marcus", "high")

    def test_short_first_name_high(self):
        assert _first_name_from_email("paul@x.com") == ("Paul", "high")
        assert _first_name_from_email("jeff@x.com") == ("Jeff", "high")

    def test_long_no_separator_low(self):
        assert _first_name_from_email("robsnow@x.com") == ("Robsnow", "low")
        assert _first_name_from_email("mjohnson@x.com") == ("Mjohnson", "low")

    def test_role_inbox_returns_blank(self):
        assert _first_name_from_email("info@x.com") == ("", "low")
        assert _first_name_from_email("sales@x.com") == ("", "low")
        assert _first_name_from_email("hello@x.com") == ("", "low")

    def test_single_letter_local_returns_blank(self):
        assert _first_name_from_email("j.smith@x.com") == ("", "low")

    def test_empty_email_returns_blank(self):
        assert _first_name_from_email("") == ("", "low")

    def test_andrew_starts_vowel_high(self):
        assert _first_name_from_email("andrew@x.com") == ("Andrew", "high")


class TestExtractFirstNameFromLead:
    def test_cw_apollo_lead_with_name_high(self):
        lead = {"source": "apollo_us_smb", "name": "John Smith", "email": "gkirz@x.com"}
        name, conf = _extract_first_name(lead)
        assert name == "John"
        assert conf == "high"

    def test_cw_apollo_lead_single_token_name_falls_to_email(self):
        # 1-token "name" doesn't satisfy >=2 tokens in CW path,
        # falls to email parser which catches the gkirz pattern.
        lead = {"source": "apollo_us_smb", "name": "Kirz", "email": "gkirz@x.com"}
        name, conf = _extract_first_name(lead)
        assert conf == "low"

    def test_cw_apollo_lead_no_name_falls_to_email(self):
        # Empty name forces fall-through to email parser.
        lead = {"source": "apollo_us_smb", "name": "", "email": "gkirz@x.com"}
        name, conf = _extract_first_name(lead)
        assert name == "Gkirz"
        assert conf == "low"

    def test_sw_lead_with_business_name_only_uses_email(self):
        lead = {"source": "signal_works", "name": "Acme Plumbing", "email": "gkirz@x.com"}
        name, conf = _extract_first_name(lead)
        assert name == "Gkirz"
        assert conf == "low"  # gkirz pattern flagged

    def test_sw_lead_with_clean_email_high(self):
        lead = {"source": "signal_works", "name": "Acme Plumbing", "email": "scott@acme.com"}
        name, conf = _extract_first_name(lead)
        assert name == "Scott"
        assert conf == "high"

    def test_explicit_first_name_wins(self):
        lead = {"first_name": "Glenn", "source": "apollo_us_smb", "email": "gkirz@x.com"}
        name, conf = _extract_first_name(lead)
        assert name == "Glenn"
        assert conf == "high"


class TestSWEmailBuilderGreeting:
    """Lock the SW path uses confidence-aware greeting (gkirz fix 2026-05-07)."""

    def test_sw_initial_lastname_email_drops_greeting(self):
        from signal_works.email_builder import _opening
        lead = {
            "name": "Acme Plumbing",
            "niche": "plumbing",
            "city": "Salt Lake City",
            "ai_score": 30,
            "owner_name": "",
            "email": "gkirz@acme.com",
        }
        out = _opening(lead)
        # Should open with "Hi," not "Hi Gkirz,"
        assert "Hi Gkirz" not in out
        assert out.startswith("Hi,")

    def test_sw_single_token_owner_drops_greeting(self):
        from signal_works.email_builder import _opening
        lead = {
            "name": "Acme Plumbing",
            "niche": "plumbing",
            "city": "Salt Lake City",
            "ai_score": 30,
            "owner_name": "Kirz",  # single-token surname only
            "email": "gkirz@acme.com",
        }
        out = _opening(lead)
        assert "Hi Kirz" not in out

    def test_sw_full_owner_name_greets(self):
        from signal_works.email_builder import _opening
        lead = {
            "name": "Acme Plumbing",
            "niche": "plumbing",
            "city": "Salt Lake City",
            "ai_score": 30,
            "owner_name": "Glenn Kirz",
            "email": "gkirz@acme.com",
        }
        out = _opening(lead)
        assert "Hi Glenn," in out
