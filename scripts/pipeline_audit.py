"""
scripts/pipeline_audit.py
=========================
SW pipeline health checks. Run on VPS:

  python scripts/pipeline_audit.py --check gmb_score_gate
  python scripts/pipeline_audit.py --check all

Checks:
  gmb_score_gate   Verify no unqualified leads (high review count OR has_website)
                   are enrolled in the active SW sequence.
  sequence_thread  Verify gmb_opener is set on all T1+ SW leads (no null threads).
  decay_candidates Show leads that would be opted out by the next decay run.
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
logger = logging.getLogger("pipeline_audit")

# Thresholds — must match hunter_tool.py constants
GMB_LOW_REVIEW_THRESHOLD = 30
GMB_DECAY_REVIEW_FLOOR = 100
GMB_DECAY_WEBSITE_FLOOR = 30

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"


def check_gmb_score_gate(conn) -> bool:
    """Verify no unqualified leads are in active SW sequence (sequence_touch >= 1).

    Unqualified = review_count >= 100 OR (has_website = TRUE AND review_count >= 30).
    These should have been dropped by score_gmb_lead() before T1 enrollment.
    If any exist, the gate is not working.

    Success criterion (2026-05-28 audit): zero rows returned.
    """
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

    print(f"{FAIL} gmb_score_gate: {len(rows)} unqualified lead(s) found in SW sequence")
    for r in rows:
        print(f"  id={r['id']} name={r['name']!r} city={r['city']} "
              f"reviews={r['review_count']} has_website={r['has_website']} "
              f"touch={r['sequence_touch']} opener={r['gmb_opener']}")
    print("  Fix: set opt_out=TRUE for these leads or investigate why gate did not fire.")
    return False


def check_sequence_thread(conn) -> bool:
    """Verify gmb_opener is set on all SW leads with sequence_touch >= 1.

    Null gmb_opener means the lead enrolled before the opener persistence
    was added (pre-2026-05-09). Those leads will get the default (empty
    signal_notes) branch in T2-T5, which is acceptable — they are not broken,
    just unthreaded. WARN, not FAIL.
    """
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

    total = r["total"]
    missing = r["missing"]
    pct = (missing / total * 100) if total else 0

    if missing == 0:
        print(f"{PASS} sequence_thread: all {total} active SW leads have gmb_opener set")
        return True
    elif pct < 20:
        print(f"{WARN} sequence_thread: {missing}/{total} leads missing gmb_opener "
              f"({pct:.0f}%) — pre-2026-05-09 enrollments, acceptable")
        return True
    else:
        print(f"{FAIL} sequence_thread: {missing}/{total} leads missing gmb_opener "
              f"({pct:.0f}%) — gate may not be writing opener correctly")
        return False


def check_decay_candidates(conn) -> bool:
    """Show leads that would be opted out by next monthly decay run.

    Informational only — always returns True.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as pre_t1,
               (SELECT COUNT(*) FROM leads
                WHERE source LIKE 'signal_works%%'
                  AND (opt_out IS NULL OR opt_out = FALSE)
                  AND sequence_touch > 0
                  AND (review_count >= %s OR (has_website = TRUE AND review_count >= %s))
               ) as mid_sequence
        FROM leads
        WHERE source LIKE 'signal_works%%'
          AND (opt_out IS NULL OR opt_out = FALSE)
          AND (sequence_touch IS NULL OR sequence_touch = 0)
          AND (review_count >= %s OR (has_website = TRUE AND review_count >= %s))
    """, (GMB_DECAY_REVIEW_FLOOR, GMB_DECAY_WEBSITE_FLOOR,
          GMB_DECAY_REVIEW_FLOOR, GMB_DECAY_WEBSITE_FLOOR))
    r = dict(cur.fetchone())
    cur.close()
    print(f"{WARN} decay_candidates: {r['pre_t1']} pre-T1 leads would be opted out, "
          f"{r['mid_sequence']} mid-sequence would be flagged on next decay run (1st of month)")
    return True


def main():
    parser = argparse.ArgumentParser(description="SW pipeline audit")
    parser.add_argument("--check", required=True,
                        choices=["gmb_score_gate", "sequence_thread", "decay_candidates", "all"])
    args = parser.parse_args()

    conn = get_crm_connection()
    results = []

    checks = (["gmb_score_gate", "sequence_thread", "decay_candidates"]
              if args.check == "all" else [args.check])

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
