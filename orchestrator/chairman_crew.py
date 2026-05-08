"""
chairman_crew.py - M5 L5 Learning Loop.

Weekly oversight crew (Monday 06:00 MT). Reads approval_queue outcomes for
griot proposals, identifies rejection patterns and scoring drift, proposes
mutations to SCORING_WEIGHTS via approval_queue, and applies approved
mutations to agent_config.

Mutation targets (all read/written via agent_config key GRIOT_<UPPER>):
  - total_score_weight, next_arc_bonus, topic_overlap_penalty,
    recent_arc_phase_penalty, RECENCY_WINDOW_DAYS, ARC_PHASE_WINDOW_DAYS

Safety:
  - Non-fatal on <7 outcomes: logs and skips without writing to approval_queue
  - One open proposal per target field at a time (dedup by field + status=pending)
  - Max 1000 tokens per Sonnet call
  - apply_mutation() is called by handlers_approvals on chairman-mutation approval
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime

import pytz

logger = logging.getLogger("agentsHQ.chairman_crew")

TIMEZONE = os.environ.get("HEARTBEAT_TIMEZONE", "America/Denver")

MIN_OUTCOMES = 7
LOOKBACK_DAYS = 14
DRIFT_THRESHOLD = 0.15
MAX_TOKENS = 1000

TUNABLE_FIELDS = (
    "total_score_weight",
    "next_arc_bonus",
    "topic_overlap_penalty",
    "recent_arc_phase_penalty",
)


# =============================================================================
# Data fetch
# =============================================================================

def fetch_outcomes(days: int = LOOKBACK_DAYS) -> list[dict]:
    """Query approval_queue for griot proposals decided in the last N days.

    Returns list of {topic, score, outcome, rejection_reason, platform, arc_phase}.
    Queries approval_queue directly because boubacar_feedback_tag lives there,
    not in content_approvals.
    """
    from memory import _pg_conn
    conn = _pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                payload->>'title'               AS title,
                payload->>'score'               AS score,
                payload->>'platform'            AS platform,
                payload->>'arc_phase'           AS arc_phase,
                payload->'topic'                AS topic_json,
                status,
                boubacar_feedback_tag,
                ts_decided
            FROM approval_queue
            WHERE crew_name = 'griot'
              AND status IN ('approved', 'rejected', 'edited')
              AND ts_decided > NOW() - INTERVAL '%s days'
            ORDER BY ts_decided DESC
            """,
            (days,),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    results = []
    for r in rows:
        title, score_raw, platform, arc_phase, topic_json, status, feedback_tag, ts_decided = r
        try:
            score = float(score_raw) if score_raw else None
        except (ValueError, TypeError):
            score = None
        try:
            topic = json.loads(topic_json) if topic_json else []
        except (ValueError, TypeError):
            topic = []
        results.append({
            "title": title or "",
            "score": score,
            "platform": platform or "",
            "arc_phase": arc_phase or "",
            "topic": topic if isinstance(topic, list) else [],
            "outcome": status,
            "rejection_reason": feedback_tag or "",
            "ts_decided": ts_decided.isoformat() if ts_decided else "",
        })
    return results


# =============================================================================
# Pattern analysis
# =============================================================================

def analyse_patterns(outcomes: list[dict]) -> dict:
    """Group outcomes by rejection_reason, compute approval rate, flag drift.

    Returns analysis dict passed to propose_mutations().
    """
    total = len(outcomes)
    approved = sum(1 for o in outcomes if o["outcome"] in ("approved", "edited"))
    rejected = sum(1 for o in outcomes if o["outcome"] == "rejected")
    approval_rate = approved / total if total else 0.0

    rejection_counts: dict[str, int] = {}
    for o in outcomes:
        reason = o["rejection_reason"] or "none"
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

    scores_approved = [o["score"] for o in outcomes if o["outcome"] in ("approved", "edited") and o["score"] is not None]
    scores_rejected = [o["score"] for o in outcomes if o["outcome"] == "rejected" and o["score"] is not None]
    avg_score_approved = sum(scores_approved) / len(scores_approved) if scores_approved else None
    avg_score_rejected = sum(scores_rejected) / len(scores_rejected) if scores_rejected else None

    platform_rates: dict[str, dict] = {}
    for o in outcomes:
        pf = o["platform"] or "unknown"
        bucket = platform_rates.setdefault(pf, {"approved": 0, "rejected": 0})
        if o["outcome"] in ("approved", "edited"):
            bucket["approved"] += 1
        elif o["outcome"] == "rejected":
            bucket["rejected"] += 1

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "approval_rate": round(approval_rate, 3),
        "rejection_counts": rejection_counts,
        "avg_score_approved": avg_score_approved,
        "avg_score_rejected": avg_score_rejected,
        "platform_rates": platform_rates,
        "drift_threshold": DRIFT_THRESHOLD,
    }


# =============================================================================
# Current weight snapshot
# =============================================================================

def _current_weights() -> dict:
    """Read current effective values for all tunable fields via agent_config."""
    from griot import SCORING_WEIGHTS
    defaults = dict(SCORING_WEIGHTS)

    try:
        from agent_config import get_config
        for field in TUNABLE_FIELDS:
            override = get_config(f"GRIOT_{field.upper()}")
            if override is not None:
                try:
                    defaults[field] = float(override)
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        logger.warning(f"chairman: _current_weights agent_config lookup failed ({e})")
    return defaults


# =============================================================================
# Sonnet mutation proposal
# =============================================================================

def propose_mutations(analysis: dict) -> list[dict]:
    """Call Sonnet to propose scoring weight mutations based on pattern analysis.

    Returns list of {target, field, current, proposed, rationale}.
    target is always "weight" (prompt mutations out of scope for M5).
    """
    from llm_helpers import call_llm

    current_weights = _current_weights()

    prompt = (
        "You are the Chairman Crew for an AI content orchestration system. "
        "Your job is to propose changes to scoring weights that determine which "
        "content posts get selected for review.\n\n"
        "CURRENT SCORING WEIGHTS:\n"
        + json.dumps(current_weights, indent=2)
        + "\n\nAPPROVAL OUTCOME ANALYSIS (last 14 days):\n"
        + json.dumps(analysis, indent=2)
        + "\n\nWeight definitions:\n"
        "- total_score_weight: multiplier on Notion Total Score (0..50)\n"
        "- next_arc_bonus: points added when post matches next unused arc priority\n"
        "- topic_overlap_penalty: points subtracted when post topics overlap recent posts\n"
        "- recent_arc_phase_penalty: points subtracted when same arc phase fired recently\n"
        "- RECENCY_WINDOW_DAYS: how far back 'recent' posts count for overlap math\n"
        "- ARC_PHASE_WINDOW_DAYS: how far back arc phase penalty applies\n\n"
        "Based on the analysis, propose specific weight changes that would improve "
        "approval rates. Only propose changes where there is clear evidence in the data. "
        "If approval rate is above 70% and no single rejection reason dominates, "
        "return an empty list.\n\n"
        "Respond with a JSON array only, no other text. Each item:\n"
        '{"field": "<field_name>", "current": <number>, "proposed": <number>, "rationale": "<one sentence, no em dashes>"}\n\n'
        "Maximum 3 proposals. Only include fields from: "
        + ", ".join(TUNABLE_FIELDS)
    )

    try:
        resp = call_llm(
            messages=[{"role": "user", "content": prompt}],
            model="anthropic/claude-sonnet-4-6",
            temperature=0.3,
            max_tokens=MAX_TOKENS,
        )
        raw = resp.choices[0].message.content.strip()
        mutations = json.loads(raw)
        if not isinstance(mutations, list):
            logger.warning(f"chairman: Sonnet returned non-list: {raw[:200]}")
            return []
        validated = []
        for m in mutations:
            if not all(k in m for k in ("field", "current", "proposed", "rationale")):
                continue
            if m["field"] not in TUNABLE_FIELDS:
                continue
            validated.append({
                "target": "weight",
                "field": m["field"],
                "current": float(m["current"]),
                "proposed": float(m["proposed"]),
                "rationale": str(m["rationale"]).replace("—", "-").replace("–", "-"),
            })
        return validated
    except json.JSONDecodeError as e:
        logger.error(f"chairman: Sonnet response not valid JSON ({e})")
        return []
    except Exception as e:
        logger.error(f"chairman: propose_mutations failed ({e})")
        return []


# =============================================================================
# Dedup check
# =============================================================================

def _field_already_queued(field: str) -> bool:
    """Return True if a chairman-mutation proposal for this field is already pending."""
    from memory import _pg_conn
    conn = _pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM approval_queue
            WHERE crew_name = 'chairman'
              AND proposal_type = 'weight-mutation'
              AND payload->>'field' = %s
              AND status = 'pending'
            LIMIT 1
            """,
            (field,),
        )
        row = cur.fetchone()
        cur.close()
        return row is not None
    except Exception as e:
        logger.warning(f"chairman: dedup check for {field} failed ({e}); assuming not queued")
        return False
    finally:
        conn.close()


# =============================================================================
# Enqueue proposals
# =============================================================================

def enqueue_proposals(mutations: list[dict]) -> list[int]:
    """Enqueue approved mutation proposals to approval_queue.

    Skips any field that already has a pending chairman-mutation proposal.
    Returns list of enqueued queue row IDs.
    """
    from approval_queue import enqueue

    enqueued_ids = []
    for m in mutations:
        field = m["field"]
        if _field_already_queued(field):
            logger.info(f"chairman: skipping {field} -- already has pending proposal")
            continue
        payload = {
            "field": field,
            "current": m["current"],
            "proposed": m["proposed"],
            "rationale": m["rationale"],
            "target": "weight",
            "note": "Approve to apply weight change. Enhance button does not apply to weight proposals.",
        }
        try:
            row = enqueue(
                crew_name="chairman",
                proposal_type="weight-mutation",
                payload=payload,
                outcome_id=None,
            )
            enqueued_ids.append(row.id)
            logger.info(f"chairman: enqueued weight-mutation #{row.id} for {field}: {m['current']} -> {m['proposed']}")
        except Exception as e:
            logger.error(f"chairman: enqueue failed for {field}: {e}")
    return enqueued_ids


# =============================================================================
# Apply mutation (called by handlers_approvals on chairman-mutation approval)
# =============================================================================

def apply_mutation(queue_row_id: int, payload: dict) -> bool:
    """Write an approved weight mutation to agent_config.

    Called by handlers_approvals when Boubacar approves a chairman-mutation row.
    Returns True on success.
    """
    field = payload.get("field")
    proposed = payload.get("proposed")
    if not field or proposed is None:
        logger.error(f"chairman: apply_mutation #{queue_row_id} missing field or proposed value")
        return False
    if field not in TUNABLE_FIELDS:
        logger.error(f"chairman: apply_mutation #{queue_row_id} unknown field {field!r}")
        return False
    try:
        from agent_config import set_config
        key = f"GRIOT_{field.upper()}"
        ok = set_config(key, str(proposed), note=f"Set by chairman queue #{queue_row_id}")
        if ok:
            logger.info(f"chairman: applied {key}={proposed} (queue #{queue_row_id})")
        else:
            logger.warning(f"chairman: set_config returned False for {key}")
        return ok
    except Exception as e:
        logger.error(f"chairman: apply_mutation failed ({e})")
        return False


# =============================================================================
# Weekly tick
# =============================================================================

def chairman_weekly_tick() -> None:
    """Heartbeat callback. Fires daily at 06:00 MT; gates internally to Monday only."""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    if now.weekday() != 0:
        logger.debug(f"chairman_weekly: skipping on {now.strftime('%A')}")
        return

    logger.info(f"chairman_weekly: start at {now.isoformat()}")

    outcomes = fetch_outcomes(days=LOOKBACK_DAYS)
    if len(outcomes) < MIN_OUTCOMES:
        logger.info(f"chairman_weekly: insufficient data ({len(outcomes)} outcomes, need {MIN_OUTCOMES}), skip")
        return

    analysis = analyse_patterns(outcomes)
    logger.info(
        f"chairman_weekly: analysis complete -- "
        f"total={analysis['total']} approval_rate={analysis['approval_rate']:.0%} "
        f"top_rejection={max(analysis['rejection_counts'], key=analysis['rejection_counts'].get, default='none')}"
    )

    mutations = propose_mutations(analysis)
    if not mutations:
        logger.info("chairman_weekly: Sonnet proposed no mutations")
        return

    ids = enqueue_proposals(mutations)
    logger.info(f"chairman_weekly: done -- enqueued {len(ids)} proposal(s): {ids}")
