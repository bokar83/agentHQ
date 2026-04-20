from unittest.mock import patch
import pytest
from skills.inbound_lead.drafter import lint_draft, draft_email
from skills.inbound_lead.schema import DraftedEmail, ResearchBrief


def _brief():
    return ResearchBrief(
        company_domain="acme.com",
        what_they_do="Boutique mid-market consulting.",
        industry_signals=["Mid-market focus"],
        likely_friction=["Margin pressure as they scale delivery"],
        conversation_hooks=["What changed last year?"],
        lens_entry_point="Theory of Constraints",
        sources=["https://acme.com/"],
        research_confidence="medium",
    )


def test_lint_passes_clean_draft():
    email = DraftedEmail(
        subject="Saw your booking",
        body_markdown="Hi Jane, short, calm note with one specific question at the end. Does that sound right?",
    )
    ok, errors = lint_draft(email)
    assert ok
    assert errors == []


def test_lint_blocks_framework_name_toc():
    email = DraftedEmail(
        subject="hi",
        body_markdown="I use Theory of Constraints to find bottlenecks.",
    )
    ok, errors = lint_draft(email)
    assert not ok
    assert any("framework_name" in e for e in errors)


def test_lint_blocks_framework_name_jtbd():
    email = DraftedEmail(
        subject="hi",
        body_markdown="Let me share my Jobs to Be Done framework with you.",
    )
    ok, errors = lint_draft(email)
    assert not ok
    assert any("framework_name" in e for e in errors)


def test_lint_blocks_em_dash():
    email = DraftedEmail(
        subject="hi",
        body_markdown="One thing I noticed \u2014 margin pressure shows up.",
    )
    ok, errors = lint_draft(email)
    assert not ok
    assert "em_dash" in errors


def test_lint_blocks_double_hyphen():
    email = DraftedEmail(
        subject="hi",
        body_markdown="One thing I noticed -- margin pressure shows up.",
    )
    ok, errors = lint_draft(email)
    assert not ok
    assert "em_dash" in errors


def test_lint_blocks_sales_phrase():
    email = DraftedEmail(
        subject="hi",
        body_markdown="Wanted to circle back on your booking and touch base soon.",
    )
    ok, errors = lint_draft(email)
    assert not ok
    assert any("sales_phrase" in e for e in errors)


def test_lint_blocks_too_long_body():
    body = " ".join(["note"] * 200)
    email = DraftedEmail(subject="hi", body_markdown=body)
    ok, errors = lint_draft(email)
    assert not ok
    assert "too_long" in errors


def test_lint_does_not_false_match_lean_inside_clean():
    """'clean' contains the letters 'lean' but must not trigger the Lean framework block."""
    email = DraftedEmail(
        subject="hi",
        body_markdown="A short, clean note with a question for you?",
    )
    ok, errors = lint_draft(email)
    assert ok, f"False positive: {errors}"


def test_dratedemail_caps_subject_at_60():
    """Pydantic enforces the 60-char subject cap at construction time."""
    with pytest.raises(Exception):
        DraftedEmail(subject="x" * 70, body_markdown="b")


def test_draft_email_regenerates_on_lint_fail_then_passes():
    dirty = DraftedEmail(subject="hi", body_markdown="Let me circle back on this.")
    clean = DraftedEmail(subject="hi", body_markdown="Short, clean note with a question?")
    with patch("skills.inbound_lead.drafter._generate_draft") as gen:
        gen.side_effect = [dirty, clean]
        result = draft_email(name="Jane", brief=_brief(), meeting_time=None)
    assert result.status == "clean"
    assert result.email.body_markdown == clean.body_markdown
    assert gen.call_count == 2


def test_draft_email_ships_partial_after_two_lint_fails():
    dirty1 = DraftedEmail(subject="hi", body_markdown="Let me circle back.")
    dirty2 = DraftedEmail(subject="hi", body_markdown="Let me touch base.")
    with patch("skills.inbound_lead.drafter._generate_draft") as gen:
        gen.side_effect = [dirty1, dirty2]
        result = draft_email(name="Jane", brief=_brief(), meeting_time=None)
    assert result.status == "partial"
    assert result.email.body_markdown == dirty2.body_markdown
    assert len(result.lint_errors) > 0
