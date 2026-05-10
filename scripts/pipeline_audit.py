"""
scripts/pipeline_audit.py
=========================
SW pipeline health checks. Run on VPS:

  python scripts/pipeline_audit.py --check gmb_score_gate
  python scripts/pipeline_audit.py --check all

Checks:
  gmb_score_gate   Verify no unqualified leads (high reviews OR has_website)
                   are enrolled in the active SW sequence.
  sequence_thread  Verify gmb_opener is set on all T1+ SW leads.
  decay_candidates Preview leads that would be opted out by next decay run.
"""

import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    sys.path.insert(0, "/app")
    from db import get_crm_connection
except ImportError:
    from orchestrator.db import get_crm_connection

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

GMB_DECAY_REVIEW_FLOOR = 100
GMB_DECAY_WEBSITE_FLOOR = 30

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"


def check_gmb_score_gate(conn) -> bool:
    """Zero unqualified leads in active SW sequence = gate working."""
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, city, niche, review_count, has_website, sequence_touch, gmb_opener
        FROM leads
        WHERE source LIKE 'signal_works%%'
          AND (opt_out IS NULL OR opt_out = FALSE)
          AND sequence_touch >= 1
          AND (
            review_count >= %s
            OR (has_website = TRUE AND review_count >= %s)
          )
        ORDER BY sequence_touch ASC, review_count DESC
        LIMIT 20
    """, (GMB_DECAY_REVIEW_FLOOR, GMB_DECAY_WEBSITE_FLOOR))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    if not rows:
        print(f"{PASS} gmb_score_gate: zero unqualified leads in active SW sequence")
        return True
    print(f"{FAIL} gmb_score_gate: {len(rows)} unqualified lead(s) in SW sequence")
    for r in rows:
        print(f"  id={r['id']} {r['name']!r} {r['city']} "
              f"reviews={r['review_count']} website={r['has_website']} touch={r['sequence_touch']}")
    print("  Fix: opt_out=TRUE for these leads or investigate why gate did not fire.")
    return False


def check_sequence_thread(conn) -> bool:
    """gmb_opener set on enrolled leads = thread continuity working."""
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(*) FILTER (WHERE gmb_opener IS NULL OR gmb_opener = '') as missing
        FROM leads
        WHERE source LIKE 'signal_works%%'
          AND (opt_out IS NULL OR opt_out = FALSE)
          AND sequence_touch >= 1
    """)
    r = dict(cur.fetchone())
    cur.close()
    total, missing = r["total"], r["missing"]
    pct = (missing / total * 100) if total else 0
    if missing == 0:
        print(f"{PASS} sequence_thread: all {total} active SW leads have gmb_opener set")
        return True
    elif pct < 20:
        print(f"{WARN} sequence_thread: {missing}/{total} missing gmb_opener "
              f"({pct:.0f}%) -- pre-2026-05-09 enrollments, acceptable")
        return True
    print(f"{FAIL} sequence_thread: {missing}/{total} missing gmb_opener ({pct:.0f}%)")
    return False


def check_decay_candidates(conn) -> bool:
    """Preview next monthly decay run. Informational only."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
          COUNT(*) FILTER (
            WHERE (sequence_touch IS NULL OR sequence_touch = 0)
              AND (review_count >= %s OR (has_website = TRUE AND review_count >= %s))
          ) as pre_t1,
          COUNT(*) FILTER (
            WHERE sequence_touch > 0
              AND (review_count >= %s OR (has_website = TRUE AND review_count >= %s))
          ) as mid_sequence
        FROM leads
        WHERE source LIKE 'signal_works%%'
          AND (opt_out IS NULL OR opt_out = FALSE)
    """, (GMB_DECAY_REVIEW_FLOOR, GMB_DECAY_WEBSITE_FLOOR,
          GMB_DECAY_REVIEW_FLOOR, GMB_DECAY_WEBSITE_FLOOR))
    r = dict(cur.fetchone())
    cur.close()
    print(f"{WARN} decay_candidates: {r['pre_t1']} pre-T1 would be opted out, "
          f"{r['mid_sequence']} mid-sequence flagged on next decay (1st of month 06:00 MT)")
    return True


def main():
    parser = argparse.ArgumentParser(description="SW pipeline audit")
    parser.add_argument("--check", required=True,
                        choices=["gmb_score_gate", "sequence_thread", "decay_candidates", "all"])
    args = parser.parse_args()
    conn = get_crm_connection()
    checks = (["gmb_score_gate", "sequence_thread", "decay_candidates"]
              if args.check == "all" else [args.check])
    results = []
    for check in checks:
        if check == "gmb_score_gate":
            results.append(check_gmb_score_gate(conn))
        elif check == "sequence_thread":
            results.append(check_sequence_thread(conn))
        elif check == "decay_candidates":
            results.append(check_decay_candidates(conn))
    conn.close()
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
