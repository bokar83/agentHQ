import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from templates.email import sw_t1


def test_no_website_opener_used_when_flag_true():
    lead = {
        "first_name": "Kurt", "niche": "dental", "city": "Provo, UT",
        "business_name": "Edge Dental", "no_website": True,
    }
    body = sw_t1.build_body(lead)
    assert "no website" in body.lower() or "not on the web" in body.lower() or "no site" in body.lower() or "could not find a website" in body.lower()
    assert "Kurt" in body


def test_default_opener_used_when_no_website_false():
    lead = {
        "first_name": "Kurt", "niche": "dental", "city": "Provo, UT",
        "business_name": "Edge Dental", "no_website": False,
    }
    body = sw_t1.build_body(lead)
    assert "ChatGPT" in body
    assert "Kurt" in body


def test_subject_unchanged():
    assert sw_t1.SUBJECT == "Is your business invisible on ChatGPT?"
