"""
harvest_reviewer.py - Two-agent (Mapper + Decision) reviewer for harvested
Skool lessons.

Reads:
  - workspace/skool-harvest/<community>/_review_plan.json (from harvest_triage)
  - workspace/skool-harvest/<community>/<lesson_id>/* (harvested artifacts)
  - docs/agentsHQ_inventory.json (from inventory_snapshot)

For each lesson with triage_label == "deep":
  1. Mapper agent: produces a structured map of overlap, new capability,
     tools, and required translations to our stack.
  2. Decision rule: rule-based first (cheap), LLM tiebreaker only on borderline.

After all per-lesson verdicts are collected, an optional Council pass runs
ONCE on the consolidated batch.

Outputs:
  - workspace/skool-harvest/<community>/_reviews/<batch_id>.json (full data)
  - One row per "deep" lesson written to the Notion "Harvested Recommendations" DB
    (data source set in NOTION_HARVESTED_RECS_DATA_SOURCE_ID).

Models:
  - Mapper:    openrouter/anthropic/claude-haiku-4.5  (cheap, fast)
  - Decision:  openrouter/anthropic/claude-haiku-4.5  (only when rule fallback fires)
  - Council:   handled by orchestrator.council on a single consolidated prompt

Cost target: ~$0.005-$0.01 per lesson, ~$0.05 for one Council pass per batch.

Usage:
    from orchestrator.harvest_reviewer import review_batch
    review_batch("robonuggets", batch_size=5, run_council=True)

CLI:
    python orchestrator/harvest_reviewer.py robonuggets --max 5
    python orchestrator/harvest_reviewer.py robonuggets --max 5 --no-council
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from litellm import completion

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_BASE = REPO_ROOT / "workspace" / "skool-harvest"
INVENTORY_JSON = REPO_ROOT / "docs" / "agentsHQ_inventory.json"

# Models. Switch to claude-sonnet-4.6 if the Mapper output ever feels shallow.
MAPPER_MODEL = "anthropic/claude-haiku-4.5"
DECISION_MODEL = "anthropic/claude-haiku-4.5"


# ---- LLM call --------------------------------------------------------------

def _llm(model_id: str, system_prompt: str, user_content: str, max_tokens: int = 1500) -> str:
    """Single completion via litellm -> OpenRouter, mirroring council._call_model."""
    extra_body = {}
    if "anthropic/" in model_id:
        extra_body = {"provider": {"order": ["Anthropic"], "allow_fallbacks": False}}
    is_anthropic = "anthropic/" in model_id
    if is_anthropic:
        system_msg = {
            "role": "system",
            "content": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    else:
        system_msg = {"role": "system", "content": system_prompt}

    response = completion(
        model=f"openrouter/{model_id}",
        messages=[
            system_msg,
            {"role": "user", "content": user_content},
        ],
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        api_base="https://openrouter.ai/api/v1",
        max_tokens=max_tokens,
        temperature=0.2,
        extra_body=extra_body,
        metadata={"caller": "harvest_reviewer"},
    )
    return response.choices[0].message.content or ""


# ---- Prompts ---------------------------------------------------------------

_MAPPER_SYSTEM = """You are the agentsHQ harvest reviewer's Mapper.

agentsHQ is a personal automation system. The owner Boubacar follows two HARD
rules when adopting external content:

1. n8n is a LAST RESORT. The default for any new automation is an agentsHQ
   skill (in skills/) or a CrewAI crew (in orchestrator/). Only fall back to
   n8n when the workload genuinely cannot be done in-process.

2. EXISTING STACK FIRST. Translate every recommended tool to our equivalent
   before considering adoption. Stack defaults:
     - database / records hub  -> Supabase (Postgres). NEVER Airtable.
     - source of truth (content, leads, projects) -> Notion. Never Google Sheets.
     - web scraping -> Firecrawl (3 tools). Apify only for purpose-built
       platform actors (Reddit, IG, TikTok). No other scrapers.
     - image / video -> Kie AI (skills/kie_media). Other vendors only as
       fallbacks in the same router.
     - automation -> CrewAI crews + agentsHQ skills first; n8n last resort.
     - browser automation -> Playwright Python with saved storage_state.
     - hosting -> Vercel (apps), Hostinger (sites). Never Modal unless
       genuinely 24/7 serverless with no other home.

You will receive:
  - A summary of one Skool lesson (title, course, text, downloads, tools).
  - A condensed snapshot of the agentsHQ inventory (skills + orchestrator
    modules with one-line purposes).

Your job is to produce a STRUCTURED MAP. Do not editorialize. Output JSON
EXACTLY in this shape, no extra keys:

{
  "summary_one_line": "...",
  "existing_overlap": [
    {"path": "skills/<slug>/ or orchestrator/<file>.py", "overlap_kind": "covers | adjacent | conflicts", "note": "..."}
  ],
  "new_capability": "<one sentence describing what this lesson would add to agentsHQ if adopted, or 'none'>",
  "tools_used_by_lesson": ["n8n", "apify", "blotato", ...],
  "required_translations": [
    {"from": "Airtable", "to": "Notion + Supabase", "why": "..."}
  ],
  "risks_or_blockers": ["..."],
  "suggested_target_path_if_adopted": "skills/<new-slug>/ | orchestrator/<file>.py | docs/reference/<file>.md | none",
  "lift_hours_estimate": <float>,
  "verdict_hint": "Take | Take with translation | Reference only | Skip"
}

Be precise. Cite real paths from the inventory you receive. If you do not see
a clear inventory match, set existing_overlap to []. Do not invent files.
"""


_DECISION_SYSTEM = """You are the harvest reviewer's Decision agent.

You will receive a Mapper output (JSON) plus the same lesson summary. The
Mapper proposed a verdict_hint. Default to the Mapper's verdict_hint unless
one of these specific override conditions fires:

OVERRIDE TO "Reference only":
- Lesson uses ONLY n8n as the entire automation, with no clean translation
  to a CrewAI crew or skill. (n8n is last resort.)
- Lesson uses Airtable, Google Sheets, or Modal centrally AND the Mapper's
  required_translations is empty OR the translation is unclear.
- new_capability is "none" AND existing_overlap is dominated by "covers".

OVERRIDE TO "Skip":
- existing_overlap shows "covers" for the entire capability AND
  new_capability is "none". (We already have this.)

OVERRIDE TO "Take" (no translation needed):
- Mapper hint is "Take" AND tools_used_by_lesson contains nothing forbidden
  by our rules.

CRITICAL: Lift hours alone never block adoption. A 16-hour lesson is fine if
it is splittable into ~4 small pieces (multiple skills + a tool + a doc),
which is common when adopting an entire agent template. Read the Mapper's
existing_overlap and required_translations: if they show 3+ distinct items,
treat the lesson as splittable and KEEP the Mapper's verdict (typically
"Take with translation"). Only large monolithic adoptions with no clean
split fall to "Reference only" purely on size.

Output JSON EXACTLY in this shape, no extra keys:

{
  "verdict": "Take | Take with translation | Reference only | Skip",
  "target_path": "<copy from mapper, or 'none'>",
  "lift_hours": <float>,
  "reasoning": "<2-4 sentence justification grounded in the rules above>"
}
"""


# ---- Inputs ----------------------------------------------------------------

def _load_inventory() -> dict:
    if not INVENTORY_JSON.exists():
        raise FileNotFoundError(
            f"{INVENTORY_JSON} missing -- run scripts/inventory_snapshot.py first"
        )
    return json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))


def _condense_inventory(inv: dict) -> str:
    """Reduce the full inventory to a compact prompt block."""
    lines: list[str] = []
    lines.append("== agentsHQ Skills ==")
    for s in inv.get("skills", []):
        desc = (s.get("description") or "")[:160]
        lines.append(f"- {s['slug']}: {desc}")
    lines.append("")
    lines.append("== agentsHQ Orchestrator Modules ==")
    for m in inv.get("orchestrator_modules", []):
        purpose = (m.get("purpose") or "")[:120]
        tools = ", ".join((m.get("tool_classes") or [])[:4])
        bundles = ", ".join((m.get("tool_bundles") or [])[:3])
        extras = []
        if tools:
            extras.append(f"tool_classes=[{tools}]")
        if bundles:
            extras.append(f"bundles=[{bundles}]")
        suffix = f"  ({'; '.join(extras)})" if extras else ""
        lines.append(f"- {m['file']}: {purpose}{suffix}")
    lines.append("")
    keys = inv.get("env_keys") or []
    if keys:
        lines.append("== Notable env keys ==")
        lines.append(", ".join(keys[:60]))
    return "\n".join(lines)


def _load_review_plan(community: str) -> dict:
    p = WORKSPACE_BASE / community / "_review_plan.json"
    if not p.exists():
        raise FileNotFoundError(
            f"{p} missing -- run python orchestrator/harvest_triage.py {community}"
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _load_lesson_artifacts(community: str, lesson_id: str) -> dict:
    d = WORKSPACE_BASE / community / lesson_id
    out: dict = {"text": "", "summary": {}, "downloads": [], "attachments_meta": []}
    if not d.exists():
        return out
    if (d / "summary.json").exists():
        try:
            out["summary"] = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        except Exception:
            pass
    if (d / "text.txt").exists():
        out["text"] = (d / "text.txt").read_text(encoding="utf-8", errors="replace")
    if (d / "attachments_meta.json").exists():
        try:
            out["attachments_meta"] = json.loads((d / "attachments_meta.json").read_text(encoding="utf-8"))
        except Exception:
            pass
    if (d / "downloads").exists():
        out["downloads"] = sorted(p.name for p in (d / "downloads").iterdir() if p.is_file())
    return out


# ---- Mapper + Decision -----------------------------------------------------

def _mapper_user_content(plan_entry: dict, artifacts: dict, inventory_block: str) -> str:
    text = (artifacts.get("text") or "")[:6000]
    summary = artifacts.get("summary") or {}
    parts = [
        "== Lesson summary ==",
        f"title: {plan_entry.get('title')}",
        f"course: {plan_entry.get('course_title')}",
        f"lesson_id: {plan_entry.get('lesson_id')}",
        f"url: {plan_entry.get('lesson_url')}",
        f"downloads: {plan_entry.get('downloads')}",
        f"summary_metrics: {json.dumps(summary)[:500]}",
        f"tools_detected_by_triage: {plan_entry.get('tools_mentioned')}",
        "",
        "== Lesson text (first 6000 chars) ==",
        text,
        "",
        inventory_block,
        "",
        "Now produce the JSON map.",
    ]
    return "\n".join(parts)


def _decision_user_content(plan_entry: dict, mapper_output: dict) -> str:
    return (
        "Lesson title: " + (plan_entry.get("title") or "") + "\n"
        "Lesson course: " + (plan_entry.get("course_title") or "") + "\n"
        "Mapper output (JSON):\n" + json.dumps(mapper_output, indent=2)
        + "\n\nNow produce the decision JSON."
    )


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def _parse_json_lenient(raw: str) -> dict:
    """LLM output sometimes has prose around the JSON. Pull the first {...} block."""
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK_RE.search(raw)
    if not m:
        return {"_parse_error": "no JSON object found", "_raw": raw[:500]}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw": raw[:500]}


def review_lesson(community: str, plan_entry: dict, inventory_block: str) -> dict:
    """Run Mapper + Decision on one lesson; return a verdict dict."""
    lesson_id = plan_entry["lesson_id"]
    artifacts = _load_lesson_artifacts(community, lesson_id)

    mapper_user = _mapper_user_content(plan_entry, artifacts, inventory_block)
    mapper_raw = _llm(MAPPER_MODEL, _MAPPER_SYSTEM, mapper_user, max_tokens=1800)
    mapper_out = _parse_json_lenient(mapper_raw)

    decision_user = _decision_user_content(plan_entry, mapper_out)
    decision_raw = _llm(DECISION_MODEL, _DECISION_SYSTEM, decision_user, max_tokens=600)
    decision_out = _parse_json_lenient(decision_raw)

    verdict = {
        "lesson_id": lesson_id,
        "title": plan_entry.get("title"),
        "course_title": plan_entry.get("course_title"),
        "lesson_url": plan_entry.get("lesson_url"),
        "downloads": plan_entry.get("downloads", []),
        "tools_mentioned": list(set(
            (plan_entry.get("tools_mentioned") or [])
            + (mapper_out.get("tools_used_by_lesson") or [])
        )),
        "mapper": mapper_out,
        "decision": decision_out,
        "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return verdict


# ---- Batch + Council -------------------------------------------------------

def _batch_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _select_targets(plan: dict, max_count: int | None) -> list[dict]:
    deep = [
        e for e in plan.get("entries", [])
        if e.get("triage_label") == "deep"
        and e.get("harvested_artifacts_present")
    ]
    if max_count is not None:
        return deep[:max_count]
    return deep


_COUNCIL_FRAMING = """
A reviewer crew has scored {n} harvested Skool lessons against the agentsHQ
inventory. Verdicts are one of: Take, Take with translation, Reference only,
Skip. Your job is to stress-test the consolidated set of recommendations,
not each lesson individually.

Look for:
- Recommendations that pretend to add capability we already have
- Translations that introduce hidden costs
- "Take" verdicts that should have been "Reference only" given our roadmap
- Patterns: are we systematically over- or under-adopting? What did the
  reviewer miss as a class?
- The single highest-leverage Take in this batch
- The single Take we should reverse to Skip

Return a short critique (under 600 words) ranked by impact.

Below is the consolidated batch:

{verdicts_json}
"""


def run_council_on_batch(verdicts: list[dict]) -> str | None:
    if not verdicts:
        return None
    try:
        from council import SankofaCouncil  # type: ignore
    except Exception as e:
        logger.warning(f"council import failed: {e}")
        return None
    try:
        compact = []
        for v in verdicts:
            d = v.get("decision") or {}
            m = v.get("mapper") or {}
            compact.append({
                "lesson_id": v["lesson_id"],
                "title": v.get("title"),
                "verdict": d.get("verdict"),
                "target_path": d.get("target_path"),
                "lift_hours": d.get("lift_hours"),
                "reasoning": d.get("reasoning"),
                "tools": v.get("tools_mentioned"),
                "translations": m.get("required_translations"),
                "new_capability": m.get("new_capability"),
            })
        prompt = _COUNCIL_FRAMING.format(
            n=len(compact),
            verdicts_json=json.dumps(compact, indent=2, ensure_ascii=False),
        )
        c = SankofaCouncil()
        result = c.run(query=prompt)
        # Extract chairman synthesis as the headline summary
        synth = (result or {}).get("chairman_synthesis") or ""
        return synth or json.dumps(result, indent=2)[:6000]
    except Exception as e:
        logger.exception("council run failed")
        return f"council error: {e}"


# ---- Notion writer ---------------------------------------------------------

def _write_to_notion(community: str, batch_id: str, verdicts: list[dict]) -> dict:
    """Create one row per verdict in the Harvested Recommendations DB.
    Soft-fails if the Notion MCP is not available; logs and returns counts.
    """
    data_source_id = os.environ.get("NOTION_HARVESTED_RECS_DATA_SOURCE_ID")
    if not data_source_id:
        return {"written": 0, "skipped": len(verdicts), "reason": "NOTION_HARVESTED_RECS_DATA_SOURCE_ID not set"}
    # The actual write is done from the agent / Claude Code session that has
    # the Notion MCP loaded; this module just emits a JSON payload that
    # caller code (or Claude Code) sends.
    payload = {
        "data_source_id": data_source_id,
        "batch_id": batch_id,
        "rows": [_to_notion_row(community, batch_id, v) for v in verdicts],
    }
    out = WORKSPACE_BASE / community / "_reviews" / f"{batch_id}.notion-payload.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"written": 0, "queued": len(payload["rows"]), "payload_path": str(out)}


def _to_notion_row(community: str, batch_id: str, verdict: dict) -> dict:
    d = verdict.get("decision") or {}
    m = verdict.get("mapper") or {}
    tools = verdict.get("tools_mentioned") or []
    translations = m.get("required_translations") or []
    translation_str = "; ".join(
        f"{t.get('from')} -> {t.get('to')}" for t in translations if isinstance(t, dict)
    )
    return {
        "Title": (verdict.get("title") or "")[:200],
        "Lesson ID": verdict.get("lesson_id"),
        "Community": community,
        "Course": verdict.get("course_title"),
        "Verdict": d.get("verdict") or "Pending",
        "Target Path": d.get("target_path") or "",
        "Lift Hours": d.get("lift_hours"),
        "Reasoning": (d.get("reasoning") or "")[:1800],
        "Council Notes": "",
        "Status": "Proposed",
        "Source URL": verdict.get("lesson_url"),
        "Reviewed At": verdict.get("reviewed_at"),
        "Batch": batch_id,
        "Tools Mentioned": tools,
        "Translation Applied": translation_str,
    }


# ---- Public entry ----------------------------------------------------------

def review_batch(community: str, max_count: int | None = None, run_council: bool = True) -> dict:
    inv = _load_inventory()
    inv_block = _condense_inventory(inv)
    plan = _load_review_plan(community)
    targets = _select_targets(plan, max_count)
    if not targets:
        print(f"[reviewer] no harvested+deep lessons to review for {community}")
        return {"community": community, "verdicts": [], "council_notes": None}

    print(f"[reviewer] reviewing {len(targets)} lessons "
          f"(inventory: {len(inv['skills'])} skills + {len(inv['orchestrator_modules'])} modules)")
    verdicts = []
    for i, e in enumerate(targets, 1):
        title = (e.get("title") or "")[:60]
        title = title.encode("ascii", "replace").decode("ascii")
        print(f"[reviewer] ({i}/{len(targets)}) {e['lesson_id'][:12]}  {title}")
        try:
            v = review_lesson(community, e, inv_block)
            verdicts.append(v)
        except Exception as ex:
            logger.exception("reviewer failed on %s", e.get("lesson_id"))
            verdicts.append({
                "lesson_id": e["lesson_id"],
                "title": e.get("title"),
                "error": str(ex),
            })

    bid = _batch_id()
    out_dir = WORKSPACE_BASE / community / "_reviews"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{bid}.json").write_text(
        json.dumps({"community": community, "batch_id": bid, "verdicts": verdicts},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    council_notes = None
    if run_council:
        print(f"[reviewer] running Council on consolidated batch ({len(verdicts)} verdicts)")
        council_notes = run_council_on_batch(verdicts)
        if council_notes:
            (out_dir / f"{bid}.council.md").write_text(council_notes, encoding="utf-8")

    notion_summary = _write_to_notion(community, bid, verdicts)

    print(f"\n[reviewer] batch {bid} complete")
    print(f"  verdicts: {len(verdicts)}")
    print(f"  json:     {out_dir / (bid + '.json')}")
    print(f"  notion:   {notion_summary}")
    if council_notes:
        print(f"  council:  {out_dir / (bid + '.council.md')}")
    return {
        "community": community,
        "batch_id": bid,
        "verdicts": verdicts,
        "council_notes": council_notes,
        "notion_summary": notion_summary,
    }


# ---- CLI -------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="harvest-reviewer batch runner")
    ap.add_argument("community")
    ap.add_argument("--max", type=int, default=None)
    ap.add_argument("--no-council", action="store_true", help="skip the Council pass")
    args = ap.parse_args(argv[1:])
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    review_batch(args.community, max_count=args.max, run_council=not args.no_council)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
