"""
harvest_triage.py - Pure-heuristic filter over a community's harvested lessons.

Reads workspace/skool-harvest/<community>/_index.json plus each harvested
lesson directory and labels every entry as one of:

  - "deep"       : send to the deep reviewer (full LLM pass)
  - "skip"       : auto-skip; matches admin/affiliate/welcome noise
  - "reference"  : keep in record but do not propose adoption (videos with
                   no downloads and no R-prefix; might be worth reading)

No LLM calls. The point is to cut review cost ~10x by removing obvious
non-candidates before any reviewer agent runs.

The output is the harvest_review_plan: a JSON file at
workspace/skool-harvest/<community>/_review_plan.json with one entry per
lesson plus its triage label and the reason.

Usage:
    python orchestrator/harvest_triage.py <community>

Or import:
    from orchestrator.harvest_triage import build_review_plan
    plan = build_review_plan("robonuggets")
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_BASE = REPO_ROOT / "workspace" / "skool-harvest"


# ---- Heuristic rules -------------------------------------------------------

# Title patterns that mean "definitely skip" (admin, navigation, affiliate, etc.)
_SKIP_PATTERNS = [
    r"^Welcome\b",
    r"^Where (?:are|do|to)\b",
    r"^What(?:'?s| are) (?:this|the discussion|the events)\b",
    r"^How to level up\b",
    r"^Download the Skool app\b",
    r"^Get the annual plan\b",
    r"^Affiliates\b",
    r"^Bonuses?\b",
    r"^Bonus (?:Lesson|content)\b",
    r"^\d+(?:\?\?|\W{0,3})\s+(?:Where|What|How|Why)\b",  # "1?? Where are...", "2 What are..."
    r"(?:^|\W{0,3})What(?:'?s)? (?:this|that|the discussion)\b",  # "What's this section?"
    r"^Where to get help\b",
    r"^Get RUBRIC\b",  # in-community tooling, not adoption candidate
    r"^Month \d+ Rewards?\b",
    r"^Level \d+ Rewards?\b",
]

# Title patterns that strongly signal "review deeply"
_DEEP_HINTS = [
    r"^R\d+\b",                 # R-series tutorials (R1, R57, etc.)
    r"\bn8n\b",
    r"\bAI Agent\b",
    r"\bMCP\b",
    r"\bAntigravity\b",
    r"\bclaude code\b",
    r"\bblueprint\b",
    r"\btemplate\b",
    r"\bworkflow\b",
    r"\bautomation\b",
]

# Tools to surface when seen anywhere in the lesson text. Used to populate
# Notion's "Tools Mentioned" multi-select. Order matters for `re.findall`.
TOOL_KEYWORDS: dict[str, list[str]] = {
    "n8n":           [r"\bn8n\b"],
    "apify":         [r"\bapify\b"],
    "blotato":       [r"\bblotato\b"],
    "kie":           [r"\bkie\.ai\b", r"\bkie ai\b"],
    "airtable":      [r"\bairtable\b"],
    "google_sheets": [r"\bgoogle sheets\b", r"\bgsheet"],
    "modal":         [r"\bmodal\.com\b", r"\bmodal labs\b"],
    "gemini":        [r"\bgemini\b", r"\bgoogle ai studio\b", r"\bnano banana\b", r"\bveo 3"],
    "notion":        [r"\bnotion\b"],
    "supabase":      [r"\bsupabase\b"],
    "firecrawl":     [r"\bfirecrawl\b"],
    "crewai":        [r"\bcrewai\b", r"\bcrew ai\b"],
    "antigravity":   [r"\bantigravity\b"],
    "claude_code":   [r"\bclaude code\b", r"\bclaude\.ai/code\b"],
}


# ---- Helpers ---------------------------------------------------------------

def _index_path(community: str) -> Path:
    return WORKSPACE_BASE / community / "_index.json"


def _lesson_dir(community: str, lesson_id: str) -> Path:
    return WORKSPACE_BASE / community / lesson_id


def _read_index(community: str) -> dict:
    p = _index_path(community)
    if not p.exists():
        raise FileNotFoundError(f"index not found: {p} -- run skool_walk --list --deep first")
    return json.loads(p.read_text(encoding="utf-8"))


def _read_lesson_artifacts(d: Path) -> dict:
    """Pull the small files the triage uses; tolerate missing pieces."""
    out: dict = {"present": False, "text": "", "summary": {}, "downloads": [], "attachments_meta": []}
    if not d.exists():
        return out
    out["present"] = True
    summary_path = d / "summary.json"
    if summary_path.exists():
        try:
            out["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    text_path = d / "text.txt"
    if text_path.exists():
        try:
            out["text"] = text_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    am = d / "attachments_meta.json"
    if am.exists():
        try:
            out["attachments_meta"] = json.loads(am.read_text(encoding="utf-8"))
        except Exception:
            pass
    dl_dir = d / "downloads"
    if dl_dir.exists():
        out["downloads"] = sorted(p.name for p in dl_dir.iterdir() if p.is_file())
    return out


def _matches_any(patterns: list[str], text: str) -> str | None:
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return p
    return None


def _detect_tools(text: str) -> list[str]:
    found = []
    for tool, patterns in TOOL_KEYWORDS.items():
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                found.append(tool)
                break
    return found


# ---- Triage core -----------------------------------------------------------

def triage_lesson(lesson: dict, artifacts: dict) -> dict:
    """Return a dict with label + reason + observed signals.

    The label is decided by:
    1. Skip-pattern match on title -> skip.
    2. Has any download in downloads/ -> deep (real artifact present).
    3. Title hits a deep-hint pattern -> deep.
    4. Has video/iframe but no download and no deep hint -> reference.
    5. Default -> deep (when in doubt, review).
    """
    title = (lesson.get("title") or "").strip()
    course_title = (lesson.get("course_title") or "").strip()

    skip_hit = _matches_any(_SKIP_PATTERNS, title) or _matches_any(_SKIP_PATTERNS, course_title)
    if skip_hit:
        return {
            "label": "skip",
            "reason": f"title matches skip pattern: {skip_hit!r}",
            "tools": [],
        }

    has_download = bool(artifacts.get("downloads"))
    if has_download:
        text = artifacts.get("text") or ""
        return {
            "label": "deep",
            "reason": f"has {len(artifacts['downloads'])} downloaded artifact(s)",
            "tools": _detect_tools(title + " " + text),
        }

    deep_hit = _matches_any(_DEEP_HINTS, title) or _matches_any(_DEEP_HINTS, course_title)
    if deep_hit:
        text = artifacts.get("text") or ""
        return {
            "label": "deep",
            "reason": f"title matches deep-hint pattern: {deep_hit!r}",
            "tools": _detect_tools(title + " " + text),
        }

    summary = artifacts.get("summary") or {}
    iframes = summary.get("iframes", 0)
    videos = summary.get("videos", 0)
    if (iframes or videos) and not has_download:
        return {
            "label": "reference",
            "reason": "video / iframe content with no downloadable artifact",
            "tools": _detect_tools((artifacts.get("text") or "")),
        }

    text = artifacts.get("text") or ""
    return {
        "label": "deep",
        "reason": "no skip pattern matched; default to review",
        "tools": _detect_tools(title + " " + text),
    }


def build_review_plan(community: str) -> dict:
    index = _read_index(community)
    lessons = index.get("lessons", [])
    plan_entries = []
    counts = {"deep": 0, "skip": 0, "reference": 0, "harvested": 0, "unharvested": 0}
    for lesson in lessons:
        lid = lesson.get("id")
        if not lid:
            continue
        artifacts = _read_lesson_artifacts(_lesson_dir(community, lid))
        if artifacts["present"]:
            counts["harvested"] += 1
        else:
            counts["unharvested"] += 1
        triage = triage_lesson(lesson, artifacts)
        counts[triage["label"]] += 1
        plan_entries.append(
            {
                "lesson_id": lid,
                "title": lesson.get("title"),
                "course_title": lesson.get("course_title"),
                "lesson_url": lesson.get("lesson_url"),
                "harvested_at": lesson.get("harvested_at"),
                "harvested_artifacts_present": artifacts["present"],
                "downloads": artifacts.get("downloads", []),
                "triage_label": triage["label"],
                "triage_reason": triage["reason"],
                "tools_mentioned": triage["tools"],
            }
        )

    plan = {
        "community": community,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totals": {
            "lessons": len(plan_entries),
            "deep": counts["deep"],
            "skip": counts["skip"],
            "reference": counts["reference"],
            "harvested": counts["harvested"],
            "unharvested": counts["unharvested"],
        },
        "entries": plan_entries,
    }

    out_path = WORKSPACE_BASE / community / "_review_plan.json"
    out_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return plan


# ---- CLI -------------------------------------------------------------------

def _ascii(s: str | None) -> str:
    return ((s or "").encode("ascii", "replace").decode("ascii"))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python orchestrator/harvest_triage.py <community>")
        return 2
    community = argv[1]
    plan = build_review_plan(community)
    t = plan["totals"]
    print(f"\n=== triage: {community} ===")
    print(f"  lessons indexed:   {t['lessons']}")
    print(f"  deep candidates:   {t['deep']}")
    print(f"  reference only:    {t['reference']}")
    print(f"  auto-skip:         {t['skip']}")
    print(f"  already harvested: {t['harvested']}  (rest pending: {t['unharvested']})")
    print()
    deep_only = [e for e in plan["entries"] if e["triage_label"] == "deep"][:15]
    if deep_only:
        print("  next 15 deep candidates:")
        for e in deep_only:
            t_ = _ascii(e.get("title", ""))[:60]
            print(f"    {e['lesson_id'][:12]}  {t_}  ({e['triage_reason']})")
    print(f"\nWrote {WORKSPACE_BASE / community / '_review_plan.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
