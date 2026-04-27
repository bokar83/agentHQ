"""
model_review_agent.py -- Weekly leGriot model quality review.

Fires every Sunday at 08:00 MT (13:00 UTC) via heartbeat scheduler.

What it does:
  1. Loads the leGriot quality rubric from docs/reference/legriot-quality-rubric.md
     at runtime (not from training data).
  2. Pulls 3 seed posts from the Notion Content Board (Status=Queued or Posted,
     last 14 days).
  3. Runs each seed idea through leGriot social/moderate prompt for each model in
     MODEL_REVIEW_CANDIDATES.
  4. Scores each output against the 5 rubric criteria using a structured LLM scorer.
  5. Computes per-model totals. Checks threshold: challenger must beat incumbent by
     >= 3 points TOTAL across 3 seeds (avg gap >= 1.0 / post) to trigger recommendation.
  6. Writes results to docs/reference/model-review-{YYYY-MM-DD}.md.
  7. If threshold crossed: emits a routing change proposal to approval_queue with
     Approve/Reject buttons. Boubacar approves; the agent NEVER edits ROLE_CAPABILITY.
  8. Sends Telegram summary regardless.

Hard constraints (enforced structurally):
  - This module does NOT import agents.py or autonomy_guard.py.
  - This module does NOT write to autonomy_state.json or any routing config.
  - The only write paths are: docs/reference/, approval_queue.enqueue(), Telegram.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from litellm import completion

logger = logging.getLogger("agentsHQ.model_review_agent")

REPO_ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = REPO_ROOT / "docs" / "reference" / "legriot-quality-rubric.md"
REVIEW_OUTPUT_DIR = REPO_ROOT / "docs" / "reference"

# Current incumbent for social/moderate routing (informational only -- agent does not touch routing).
INCUMBENT_MODEL = "xai/grok-4"

# Models evaluated each Sunday. Add/remove here as the landscape evolves.
MODEL_REVIEW_CANDIDATES: list[str] = [
    "xai/grok-4",
    "anthropic/claude-sonnet-4.6",
    "mistralai/mistral-large-2407",
    "google/gemini-2.5-flash",
]

# Routing change threshold: challenger must beat incumbent by this many points
# TOTAL across all seed posts. Matches legriot-quality-rubric.md spec.
ROUTING_CHANGE_THRESHOLD = 3

# Scoring model: cheap + instruction-following, not the model being evaluated.
SCORER_MODEL = "openrouter/anthropic/claude-haiku-4.5"

LEGRIOT_SYSTEM_PROMPT = """You are leGriot, Boubacar Barry's social media content agent.

Boubacar is the founder of Catalyst Works, a solo AI strategy consulting practice
targeting SMB leadership teams. His methodology is constraint-led. His differentiator
is intellectual honesty.

Voice: direct, specific, earned confidence, occasionally provocative, warm but precise.
Never: "I'm excited to share", "game-changer", "leverage", "synergy", em dashes.

Write ONE LinkedIn post (150-300 words) on the given topic. One post only.
Short punchy lines. End with a question or soft CTA. No hashtags. No em dashes.
Output the post text only -- no preamble, no labels, no metadata."""

SCORER_SYSTEM = """You score social media posts against a quality rubric.
Output ONLY valid JSON. No prose. No explanation outside the JSON object."""


# ---- Notion helpers ----------------------------------------------------------

def _fetch_seed_posts(limit: int = 3) -> list[dict]:
    """Pull recent Queued/Posted content board records as seed ideas.

    Returns list of dicts with keys: title, platform, notion_id.
    Falls back to DEFAULT_SEEDS if Notion is unavailable.
    """
    try:
        from notifier import _notion_client  # type: ignore
    except Exception:
        logger.warning("Notion client unavailable; using default seeds")
        return _default_seeds()

    db_id = os.environ.get("FORGE_CONTENT_DB")
    if not db_id:
        logger.warning("FORGE_CONTENT_DB not set; using default seeds")
        return _default_seeds()

    try:
        from notion_client import NotionClient  # type: ignore
        client = NotionClient()
        results = client.query_database(
            db_id,
            filter_obj={
                "or": [
                    {"property": "Status", "select": {"equals": "Queued"}},
                    {"property": "Status", "select": {"equals": "Posted"}},
                ]
            },
            sorts=[{"property": "Scheduled Date", "direction": "descending"}],
        )
        pages = (results or {}).get("results", [])[:limit]
        seeds = []
        for p in pages:
            props = p.get("properties", {})
            title_prop = props.get("Name", {}).get("title", [])
            title = title_prop[0]["plain_text"] if title_prop else "Untitled"
            platform_prop = props.get("Platform", {}).get("multi_select", [])
            platform = platform_prop[0]["name"] if platform_prop else "LinkedIn"
            seeds.append({"title": title, "platform": platform, "notion_id": p["id"]})
        return seeds if seeds else _default_seeds()
    except Exception as exc:
        logger.warning("Notion seed fetch failed (%s); using defaults", exc)
        return _default_seeds()


def _default_seeds() -> list[dict]:
    return [
        {"title": "The first AI decision you already made without knowing it", "platform": "LinkedIn", "notion_id": None},
        {"title": "Why SMB owners overbuy AI tools and under-implement them", "platform": "LinkedIn", "notion_id": None},
        {"title": "One constraint nobody has named yet", "platform": "X", "notion_id": None},
    ]


# ---- Draft generation --------------------------------------------------------

def _generate_draft(idea: str, platform: str, model_id: str) -> str:
    """Call model_id via litellm to produce one leGriot social post."""
    openrouter_model = model_id if model_id.startswith("openrouter/") else f"openrouter/{model_id}"
    is_anthropic = "anthropic/" in model_id
    extra_body: dict = {}
    if is_anthropic:
        extra_body = {"provider": {"order": ["Anthropic"], "allow_fallbacks": False}}

    try:
        resp = completion(
            model=openrouter_model,
            messages=[
                {"role": "system", "content": LEGRIOT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Topic: {idea}\nPlatform: {platform}"},
            ],
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            api_base="https://openrouter.ai/api/v1",
            max_tokens=600,
            temperature=0.7,
            extra_body=extra_body,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning("Draft generation failed for %s: %s", model_id, exc)
        return f"[GENERATION ERROR: {exc}]"


# ---- Scoring -----------------------------------------------------------------

def _score_draft(draft: str, rubric_text: str) -> dict:
    """Score one draft against the rubric. Returns dict with per-criterion scores + total."""
    scoring_prompt = f"""Score this social media post against the rubric below.
Return ONLY this JSON (no extra text):
{{
  "hook_strength": <1-3>,
  "voice_fidelity": <1-3>,
  "diagnosis_clarity": <1-3>,
  "ai_slop_absence": <1-3>,
  "cta_sharpness": <1-3>,
  "reasoning": "<one sentence per criterion, separated by | >"
}}

RUBRIC:
{rubric_text}

POST TO SCORE:
{draft[:1500]}

Output JSON only."""

    try:
        resp = completion(
            model=SCORER_MODEL,
            messages=[
                {"role": "system", "content": SCORER_SYSTEM},
                {"role": "user", "content": scoring_prompt},
            ],
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            api_base="https://openrouter.ai/api/v1",
            max_tokens=300,
            temperature=0.1,
            extra_body={"provider": {"order": ["Anthropic"], "allow_fallbacks": False}},
        )
        raw = (resp.choices[0].message.content or "").strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            import re
            m = re.search(r"\{[\s\S]*\}", raw)
            data = json.loads(m.group(0)) if m else {}
        total = sum(
            int(data.get(k, 2))
            for k in ("hook_strength", "voice_fidelity", "diagnosis_clarity", "ai_slop_absence", "cta_sharpness")
        )
        data["total"] = total
        return data
    except Exception as exc:
        logger.warning("Scoring failed: %s", exc)
        return {"hook_strength": 2, "voice_fidelity": 2, "diagnosis_clarity": 2,
                "ai_slop_absence": 2, "cta_sharpness": 2, "total": 10, "error": str(exc)}


# ---- Report ------------------------------------------------------------------

def _write_report(date_str: str, results: list[dict], recommendation: Optional[str]) -> Path:
    """Write model-review-{date}.md and return its path."""
    lines = [
        f"# leGriot Model Review -- {date_str}",
        "",
        f"Incumbent: `{INCUMBENT_MODEL}` (social/moderate routing)",
        f"Threshold: challenger must beat incumbent by >= {ROUTING_CHANGE_THRESHOLD} pts total across seeds",
        "",
        "## Results",
        "",
        "| Model | " + " | ".join(f"Seed {i+1}" for i in range(len(results[0]['scores']))) + " | Total |",
        "|-------|" + "|".join("--------" for _ in results[0]['scores']) + "|-------|",
    ]
    for r in results:
        seed_cols = " | ".join(str(s["total"]) for s in r["scores"])
        lines.append(f"| `{r['model']}` | {seed_cols} | **{r['total']}** |")

    lines += ["", "## Recommendation", ""]
    if recommendation:
        lines.append(recommendation)
    else:
        lines.append("No routing change recommended (no challenger cleared the threshold).")

    lines += ["", "## Seed Posts Used", ""]
    for i, r in enumerate(results[:1]):
        for j, s in enumerate(r["scores"]):
            lines.append(f"- Seed {j+1}: see session data")

    lines += ["", "---", f"Generated: {date_str} by model_review_agent.py"]

    path = REVIEW_OUTPUT_DIR / f"model-review-{date_str}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---- Approval queue emit -----------------------------------------------------

def _emit_routing_proposal(winner_model: str, incumbent: str, score_delta: float) -> None:
    """Emit a model routing change proposal to the approval queue."""
    try:
        import approval_queue
        approval_queue.enqueue(
            crew_name="model_review_agent",
            proposal_type="model_routing_change",
            payload={
                "role": "social",
                "complexity": "moderate",
                "current_model": incumbent,
                "proposed_model": winner_model,
                "avg_score_delta_per_post": round(score_delta, 2),
                "total_score_delta": round(score_delta * 3, 1),
                "summary": (
                    f"Weekly review: `{winner_model}` outscored incumbent `{incumbent}` "
                    f"by {score_delta:.1f} pts/post on average across 3 seed posts. "
                    f"Approve to update ROLE_CAPABILITY social/moderate. "
                    f"Reject to keep current routing."
                ),
            },
        )
        logger.info("Routing change proposal queued for %s -> %s", incumbent, winner_model)
    except Exception as exc:
        logger.warning("Failed to enqueue routing proposal: %s", exc)


# ---- Telegram ----------------------------------------------------------------

def _send_telegram_summary(date_str: str, results: list[dict], recommendation: Optional[str], report_path: Path) -> None:
    try:
        from notifier import send_message
        chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
        if not chat_id:
            return
        lines = [f"Model Review {date_str}", ""]
        for r in results:
            marker = " INCUMBENT" if r["model"] == INCUMBENT_MODEL else ""
            lines.append(f"`{r['model']}`{marker}: {r['total']} pts")
        lines.append("")
        lines.append(recommendation or "No routing change recommended.")
        lines.append(f"\nFull report: {report_path.name}")
        send_message(str(chat_id), "\n".join(lines))
    except Exception as exc:
        logger.warning("Telegram summary failed: %s", exc)


# ---- Main tick ---------------------------------------------------------------

def model_review_tick() -> None:
    """Heartbeat callback. Runs every Sunday at 08:00 MT.

    The day-of-week gate is inside this function because heartbeat.register_wake
    only supports at= (daily) or every= (interval) -- no day_of_week param.
    """
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo("America/Denver")
    except Exception:
        import datetime as _dt
        tz = _dt.timezone.utc

    now_local = datetime.now(tz)
    if now_local.weekday() != 6:  # 6 = Sunday
        logger.debug("model_review_tick: not Sunday (%s), skipping", now_local.strftime("%A"))
        return

    date_str = now_local.strftime("%Y-%m-%d")
    logger.info("model_review_tick: starting weekly review for %s", date_str)

    if not os.environ.get("OPENROUTER_API_KEY"):
        logger.warning("model_review_tick: OPENROUTER_API_KEY missing, aborting")
        return

    rubric_text = RUBRIC_PATH.read_text(encoding="utf-8") if RUBRIC_PATH.exists() else ""
    if not rubric_text:
        logger.warning("model_review_tick: rubric not found at %s", RUBRIC_PATH)
        return

    seeds = _fetch_seed_posts(limit=3)
    logger.info("model_review_tick: %d seeds, %d candidates", len(seeds), len(MODEL_REVIEW_CANDIDATES))

    results = []
    for model_id in MODEL_REVIEW_CANDIDATES:
        model_scores = []
        for seed in seeds:
            draft = _generate_draft(seed["title"], seed["platform"], model_id)
            score = _score_draft(draft, rubric_text)
            model_scores.append(score)
        total = sum(s["total"] for s in model_scores)
        results.append({"model": model_id, "scores": model_scores, "total": total})
        logger.info("model_review_tick: %s -> %d pts", model_id, total)

    # Find incumbent and best challenger scores
    incumbent_result = next((r for r in results if r["model"] == INCUMBENT_MODEL), None)
    incumbent_total = incumbent_result["total"] if incumbent_result else 0

    challengers = [r for r in results if r["model"] != INCUMBENT_MODEL]
    best_challenger = max(challengers, key=lambda r: r["total"]) if challengers else None

    recommendation = None
    if best_challenger:
        delta = best_challenger["total"] - incumbent_total
        avg_delta = delta / max(len(seeds), 1)
        if delta >= ROUTING_CHANGE_THRESHOLD:
            recommendation = (
                f"RECOMMENDATION: Switch social/moderate from `{INCUMBENT_MODEL}` to "
                f"`{best_challenger['model']}` (+{delta} pts total, +{avg_delta:.1f} avg/post). "
                f"Proposal sent to approval queue."
            )
            _emit_routing_proposal(best_challenger["model"], INCUMBENT_MODEL, avg_delta)
        else:
            recommendation = (
                f"Best challenger `{best_challenger['model']}` is +{delta} pts total "
                f"(threshold is +{ROUTING_CHANGE_THRESHOLD}). No routing change recommended."
            )

    report_path = _write_report(date_str, results, recommendation)
    _send_telegram_summary(date_str, results, recommendation, report_path)
    logger.info("model_review_tick: complete, report at %s", report_path)
