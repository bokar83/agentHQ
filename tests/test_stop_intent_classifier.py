"""Tests for the STOP-intent classifier in scripts/sync_replies_from_gmail.py.

These tests run without any DB or network access. They lock in the
detection patterns that drive email_suppressions writes.

False-positive rule: a body that does NOT contain a STOP signal MUST
return None. False-negative rule: every documented prospect-side
opt-out phrase MUST classify. Both are CAN-SPAM critical.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

# Import directly. The module's top-level imports (httpx, psycopg2) must be
# present in the test env -- they already are because other reply-scanner
# tests share that requirement.
from sync_replies_from_gmail import classify_stop_intent  # noqa: E402


# ─── Positive cases (must classify) ──────────────────────────────────────────

def test_bare_uppercase_stop():
    out = classify_stop_intent("STOP\n\nJordan\nCEO Catalina Capital")
    assert out is not None
    reason, label = out
    assert reason == "reply_stop"
    assert label == "STOP"


def test_unsubscribe_word():
    out = classify_stop_intent("Please unsubscribe me from this list.")
    assert out is not None
    assert out[0] == "reply_unsubscribe"


def test_unsubscribe_capitalized():
    assert classify_stop_intent("Unsubscribe please")[0] == "reply_unsubscribe"


def test_remove_me():
    assert classify_stop_intent("Hi -- please remove me from this list")[0] == "reply_remove"


def test_take_me_off():
    assert classify_stop_intent("Take me off your list please.")[0] == "reply_remove"


def test_stop_emailing():
    assert classify_stop_intent("stop emailing me")[0] == "reply_stop"


def test_do_not_contact():
    assert classify_stop_intent("Do not contact me again.")[0] == "reply_remove"


def test_dont_contact_with_apostrophe():
    assert classify_stop_intent("Don't email me.")[0] == "reply_remove"


def test_dont_contact_no_apostrophe():
    assert classify_stop_intent("Dont contact me.")[0] == "reply_remove"


def test_opt_out_phrase():
    assert classify_stop_intent("I want to opt out.")[0] == "reply_remove"


def test_opt_dash_out():
    assert classify_stop_intent("Please opt-out.")[0] == "reply_remove"


# ─── Negative cases (must NOT classify) ──────────────────────────────────────

def test_lowercase_stop_in_sentence_not_classified():
    # 'stop' (lowercase, mid-sentence) is too noisy. Only \bSTOP\b uppercase
    # matches the bare 'STOP' rule. This protects against false positives in
    # sentences like 'will not stop me from working with you'.
    assert classify_stop_intent("This will not stop me from buying.") is None


def test_long_friendly_reply_no_stop():
    body = (
        "Hi Boubacar, thanks for reaching out. I'd love to chat next week. "
        "Can you send your Calendly link? Best, Jordan"
    )
    assert classify_stop_intent(body) is None


def test_empty_body():
    assert classify_stop_intent("") is None


def test_none_body_safe():
    # None should not crash; should return None
    assert classify_stop_intent(None) is None  # type: ignore[arg-type]


def test_only_first_1000_chars_scanned():
    # STOP that lives deep in a quoted thread (e.g. our own outbound copy)
    # MUST NOT trigger suppression. Build a body where 'STOP' only appears
    # at position 1500 -- the classifier should miss it on purpose.
    padding = "x" * 1500
    body = padding + "\nSTOP\n"
    assert classify_stop_intent(body) is None


def test_stop_at_top_of_reply_classified_even_with_long_tail():
    body = "STOP\n" + ("more text " * 500)
    out = classify_stop_intent(body)
    assert out is not None
    assert out[0] == "reply_stop"


# ─── Real-world fixture: Jordan Harbertson 2026-05-14 ─────────────────────────

def test_real_jordan_harbertson_reply():
    """Reproduces the actual body that arrived 2026-05-14 06:59 MDT.
    Suppression must fire on this exact text. If it ever fails we have a
    CAN-SPAM regression."""
    body = (
        "STOP Jordan Harbertson CEO & President Catalina Capital "
        "> On May 13, 2026, at 11:27 AM, Boubacar Barry "
        "<boubacar@catalystworks.consulting> wrote: > > Hi Jordan, > > Sent you"
    )
    out = classify_stop_intent(body)
    assert out is not None
    reason, label = out
    assert reason == "reply_stop"
    assert label == "STOP"
