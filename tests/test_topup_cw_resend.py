import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signal_works.topup_cw_leads import topup_cw_leads
from signal_works.email_gate import reset_verify_cache


def setup_function():
    reset_verify_cache()


def _passthrough_gate(email, source="unknown", allow_webmail=False, skip_verifier=False):
    """Stub for signal_works.topup_cw_leads.gate_email — Ship 2c gate is
    exercised directly in tests/test_email_gate.py. These tests focus on
    hybrid fresh+resend flow and should not hit the live Hunter Email
    Verifier."""
    return email


def test_hybrid_uses_5_fresh_5_resend():
    fake_resends = [
        {"apollo_id": f"old_{i}", "email": f"resend{i}@biz.com", "name": f"Person {i}"}
        for i in range(5)
    ]
    fake_fresh = [
        {"id": f"new_{i}", "email": f"fresh{i}@biz.com", "name": f"Fresh {i}"}
        for i in range(5)
    ]
    with patch("signal_works.topup_cw_leads.get_resend_queue", return_value=fake_resends), \
         patch("signal_works.topup_cw_leads.harvest_leads", return_value=fake_fresh) as mock_harvest, \
         patch("signal_works.topup_cw_leads.gate_email", side_effect=_passthrough_gate), \
         patch("signal_works.topup_cw_leads._save_cw_lead", return_value=True), \
         patch("signal_works.topup_cw_leads._count_ready_cw_leads", return_value=0), \
         patch("signal_works.topup_cw_leads._is_duplicate", return_value=False), \
         patch("signal_works.topup_cw_leads.get_crm_connection") as mock_conn, \
         patch("signal_works.topup_cw_leads.ensure_leads_columns"):
        # Mock connection just needs to support .close()
        mock_conn.return_value = MagicMock()
        n = topup_cw_leads(minimum=10, dry_run=True)
    assert n == 10
    # harvest_leads should be called for the 5 fresh slots
    assert mock_harvest.call_count == 1
    args, kwargs = mock_harvest.call_args
    target = kwargs.get("target", args[1] if len(args) > 1 else None)
    assert target == 5


def test_resend_short_falls_back_to_apollo_topup():
    """When resend queue returns <5, the gap is filled by extra Apollo fresh."""
    with patch("signal_works.topup_cw_leads.get_resend_queue", return_value=[]), \
         patch("signal_works.topup_cw_leads.harvest_leads") as mock_harvest, \
         patch("signal_works.topup_cw_leads.gate_email", side_effect=_passthrough_gate), \
         patch("signal_works.topup_cw_leads._save_cw_lead", return_value=True), \
         patch("signal_works.topup_cw_leads._count_ready_cw_leads", return_value=0), \
         patch("signal_works.topup_cw_leads._is_duplicate", return_value=False), \
         patch("signal_works.topup_cw_leads.get_crm_connection") as mock_conn, \
         patch("signal_works.topup_cw_leads.ensure_leads_columns"):
        mock_conn.return_value = MagicMock()
        # First call returns 5 fresh; second call (top-up for the gap) returns 5 more
        mock_harvest.side_effect = [
            [{"id": f"new_{i}", "email": f"f{i}@biz.com", "name": f"F{i}"} for i in range(5)],
            [{"id": f"top_{i}", "email": f"t{i}@biz.com", "name": f"T{i}"} for i in range(5)],
        ]
        n = topup_cw_leads(minimum=10, dry_run=True)
    assert n == 10
    assert mock_harvest.call_count == 2
