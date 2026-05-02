"""Notion Task Audit harvester.

Walks markdown feeders, extracts atomic tasks, classifies each, upserts to Notion.

Usage:
    python scripts/notion_task_audit.py --dry-run
    python scripts/notion_task_audit.py
    python scripts/notion_task_audit.py --mode=sweep --window=14d

See docs/superpowers/specs/2026-05-01-notion-task-audit-design.md for the design.
"""
from __future__ import annotations

import argparse
import json as _json
import os
import re
import sys
import time as _time
from datetime import date, timedelta
from pathlib import Path
from datetime import date, timedelta

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_NOTION_TASK_DB_ID = "249bcf1a302980739c26c61cad212477"
DEFAULT_LLM_MODEL = "anthropic/claude-haiku-4-5"
HARD_LLM_CALL_CAP = 500
HARD_LIVE_ROW_CAP = 300
NOTION_VERSION = "2022-06-28"
FEEDER_GLOBS = (
    "docs/roadmap/*.md",
    "docs/superpowers/plans/*.md",
    "docs/superpowers/specs/*.md",
    "docs/handoff/*.md",
)
_HEADER_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$")
_SHIPPED_RE = re.compile(r"\b(SHIPPED|DONE|shipped|✅)\b")
_INPROGRESS_RE = re.compile(r"\b(IN PROGRESS|QUEUED|NOT STARTED|IN FLIGHT|🟡|⏳)\b", re.IGNORECASE)
EXTRACT_PROMPT = """\
Given this milestone or block from a markdown doc, extract atomic tasks.

A task is action-verb-led work bite of <= 8 hours, OR <= 10% of the parent
milestone's expected duration, whichever is smaller. Anything bigger gets
split.

Return a JSON ARRAY (no prose) of objects with these keys:
- title: action verb first, no fluff (e.g. "Add LinkedIn polling cron")
- completion_criteria: one sentence, verifiable. It must be obvious whether
  the task is done by comparing output with the criterion.
- estimated_hours: number (1, 2, 4, 8 max)
- source_section: the heading where this came from

Special rules:
- If the milestone is already shipped (you'll see SHIPPED, ✅, DONE markers),
  return one task per shipped sub-deliverable, with completion_criteria
  starting "Already shipped: ".
- If the block has no actionable work (just a status snapshot, table of
  contents, etc.), return [].
- If the block describes a future milestone with a trigger date in the future,
  return tasks but mark estimated_hours conservatively.

UNIT TITLE: {title}
STATUS MARKER: {status_marker}
SOURCE: {source_path}

BODY:
{body}

Return only the JSON array. No prose.
"""
GEM_PROMPT = """\
Given this task and source context, decide:
- Is this idea still sound, or stale/superseded?
- If sound, is there any chance it is *better than or complementary to*
  current active work?

Return ONLY one JSON object (no prose) with two keys:
- verdict: one of "live" | "gem" | "archive"
  - "live"   : sound, fits in active work as-is
  - "gem"    : sound AND possibly better than current approach (worth a fresh look)
  - "archive": stale, superseded, or no longer relevant
- reason: one sentence (max 25 words) explaining the verdict.

TASK TITLE: {title}
COMPLETION CRITERION: {completion_criteria}
SOURCE: {source_path}
SOURCE SECTION: {source_section}
SOURCE STATUS: {source_status_marker}
"""
_DATE_RE = re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b")
_PUNCT_RE = re.compile(r"[^\w\s]")
_ROADMAP_PRIORITY = {"harvest.md": 0, "atlas.md": 1, "studio.md": 2, "echo.md": 3}


def _notion_headers() -> dict:
    token = os.environ.get("NOTION_SECRET")
    if not token:
        raise RuntimeError("NOTION_SECRET not in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def ensure_schema(database_id: str) -> dict:
    """Add Source + Completion Criteria fields to the Tasks DB if missing.

    Idempotent: if both already exist, returns without writing.
    Returns the final list of property names.
    """
    headers = _notion_headers()
    r = httpx.get(
        f"https://api.notion.com/v1/databases/{database_id}",
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    existing = r.json()
    props = existing.get("properties", {})

    needed = {}
    if "Source" not in props:
        needed["Source"] = {"rich_text": {}}
    if "Completion Criteria" not in props:
        needed["Completion Criteria"] = {"rich_text": {}}

    if not needed:
        return {"unchanged": True, "properties": list(props.keys())}

    patch_body = {"properties": needed}
    r = httpx.patch(
        f"https://api.notion.com/v1/databases/{database_id}",
        headers=headers,
        json=patch_body,
        timeout=15,
    )
    r.raise_for_status()
    return {"unchanged": False, "added": list(needed.keys())}


def walk_feeders(repo_root: Path, mode: str = "full", window_days: int = 14) -> list[Path]:
    """Return list of feeder markdown files.

    mode='full': all files matching FEEDER_GLOBS.
    mode='sweep': only files modified within window_days.
    """
    out: list[Path] = []
    cutoff = _time.time() - (window_days * 86400) if mode == "sweep" else None
    for pattern in FEEDER_GLOBS:
        for path in sorted((repo_root).glob(pattern)):
            if cutoff is not None:
                if path.stat().st_mtime < cutoff:
                    continue
            out.append(path)
    return out


def extract_units(path: Path) -> list[dict]:
    """Split a markdown file into milestone-or-block units.

    A unit is a heading (## / ### / ####) plus the body text up to the next
    same-or-higher-level heading. Each unit gets a 'status_marker' if a
    recognized marker appears in the heading or first 30 lines of body.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    units: list[dict] = []
    current: dict | None = None

    for idx, line in enumerate(lines):
        m = _HEADER_RE.match(line)
        if m:
            if current is not None:
                units.append(current)
            current = {
                "title": m.group(2).strip(),
                "level": len(m.group(1)),
                "body": "",
                "line_no": idx + 1,
                "status_marker": "",
                "source_path": str(path),
            }
            continue
        if current is not None:
            current["body"] += line + "\n"

    if current is not None:
        units.append(current)

    # Tag each unit with a status marker
    for u in units:
        head = u["title"]
        body_head = u["body"][:2000]
        if _SHIPPED_RE.search(head) or _SHIPPED_RE.search(body_head):
            u["status_marker"] = "SHIPPED"
        elif _INPROGRESS_RE.search(head) or _INPROGRESS_RE.search(body_head):
            u["status_marker"] = "IN_PROGRESS"

    return units


def extract_tasks_from_unit(unit: dict, model: str = DEFAULT_LLM_MODEL) -> list[dict]:
    """Call OpenRouter Haiku to extract atomic tasks from a unit. Returns list."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not in environment.")

    body_truncated = unit["body"][:6000]
    prompt = EXTRACT_PROMPT.format(
        title=unit["title"],
        status_marker=unit.get("status_marker", ""),
        source_path=unit["source_path"],
        body=body_truncated,
    )

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    r = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()

    # Tolerate code-fence wrapping
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].lstrip()
        # Remove trailing fence
        content = content.rsplit("```", 1)[0].strip() if "```" in content else content

    try:
        raw = _json.loads(content) if content else []
    except _json.JSONDecodeError:
        return []

    if not isinstance(raw, list):
        return []

    tasks: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict) or not entry.get("title"):
            continue
        tasks.append({
            "title": entry["title"].strip(),
            "completion_criteria": entry.get("completion_criteria", "").strip(),
            "estimated_hours": entry.get("estimated_hours", 0),
            "source_section": entry.get("source_section", unit["title"]),
            "source_path": unit["source_path"],
            "source_status_marker": unit.get("status_marker", ""),
        })
    return tasks


def classify_task(task: dict, file_mtime_days_ago: int) -> dict:
    """Apply Section 5.1 classification rules. Returns task with 'disposition' set.

    Disposition is one of: Shipped, Live, Archived, GoldenGem, NeedsReview.
    GoldenGem is only set later by gem_check_task() (second LLM pass).
    """
    marker = (task.get("source_status_marker") or "").upper()
    crit = (task.get("completion_criteria") or "").lower()

    if marker == "SHIPPED" or "already shipped" in crit:
        return {**task, "disposition": "Shipped"}

    if marker == "IN_PROGRESS":
        return {**task, "disposition": "Live"}

    src = task.get("source_path", "").replace("\\", "/")
    is_plan_or_spec = ("superpowers/plans/" in src) or ("superpowers/specs/" in src)
    if is_plan_or_spec:
        return {**task, "disposition": "Archived"}

    if "docs/handoff/" in src and file_mtime_days_ago >= 14:
        return {**task, "disposition": "Archived"}

    if file_mtime_days_ago >= 60:
        return {**task, "disposition": "Archived"}

    # Recent file, no status marker, no completion criterion: review
    if not task.get("completion_criteria") and task.get("estimated_hours", 0) == 0:
        return {**task, "disposition": "NeedsReview"}

    return {**task, "disposition": "Live"}


def gem_check_task(task: dict, model: str = DEFAULT_LLM_MODEL) -> dict:
    """Run second LLM pass to flag Golden Gems vs archive vs keep-as-Live."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not in environment.")

    prompt = GEM_PROMPT.format(
        title=task["title"],
        completion_criteria=task.get("completion_criteria", ""),
        source_path=task["source_path"],
        source_section=task.get("source_section", ""),
        source_status_marker=task.get("source_status_marker", ""),
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    r = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].lstrip()
        if "```" in content:
            content = content.rsplit("```", 1)[0].strip()
    try:
        obj = _json.loads(content) if content else {}
    except _json.JSONDecodeError:
        obj = {}

    verdict = obj.get("verdict", "live").lower()
    reason = obj.get("reason", "")

    if verdict == "gem":
        return {**task, "disposition": "GoldenGem", "gem_reason": reason}
    if verdict == "archive":
        return {**task, "disposition": "Archived", "gem_reason": reason}
    return {**task, "disposition": "Live", "gem_reason": reason}


def _normalize_title(title: str) -> str:
    s = _DATE_RE.sub("", title or "")
    s = _PUNCT_RE.sub(" ", s)
    s = " ".join(s.lower().split())
    return s


def dedupe(tasks: list[dict]) -> list[dict]:
    """Group tasks by normalized title. Keep the newest by source_mtime.

    The kept entry's source_path is updated to a semicolon-joined string
    of every original source_path that mapped to the same normalized title.
    """
    groups: dict[str, list[dict]] = {}
    for t in tasks:
        key = _normalize_title(t.get("title", ""))
        groups.setdefault(key, []).append(t)

    out: list[dict] = []
    for _, members in groups.items():
        members_sorted = sorted(
            members,
            key=lambda m: m.get("source_mtime", 0),
            reverse=True,
        )
        winner = dict(members_sorted[0])
        all_paths = []
        for m in members_sorted:
            p = m.get("source_path", "")
            if p and p not in all_paths:
                all_paths.append(p)
        winner["source_path"] = "; ".join(all_paths)
        out.append(winner)
    return out


def _due_within(task: dict, today: date, days: int) -> bool:
    raw = task.get("due_date")
    if not raw:
        return False
    try:
        d = date.fromisoformat(raw)
    except ValueError:
        return False
    return today <= d <= today + timedelta(days=days)


def _roadmap_rank(task: dict) -> int:
    src = task.get("source_path", "")
    for name, rank in _ROADMAP_PRIORITY.items():
        if name in src:
            return rank
    return 99


def pick_p0(live_tasks: list[dict], today: date | None = None) -> dict | None:
    """Pick exactly one P0 from Live tasks. See spec section 5.2 for rule."""
    today = today or date.today()
    if not live_tasks:
        return None

    only_live = [t for t in live_tasks if t.get("disposition") == "Live"]
    if not only_live:
        return None

    # Rule 1: Revenue + due within 7d, soonest first
    rule1 = [t for t in only_live if t.get("category") == "Revenue" and _due_within(t, today, 7)]
    if rule1:
        return min(rule1, key=lambda t: t.get("due_date", "9999-99-99"))

    # Rule 2: source roadmap rank, then highest revenue impact
    rule2 = [
        t for t in only_live
        if _roadmap_rank(t) < 99 and t.get("category") == "Revenue"
    ]
    if rule2:
        return min(rule2, key=lambda t: (_roadmap_rank(t), t.get("due_date", "9999-99-99")))

    # Rule 3: soonest-due High priority
    rule3 = [t for t in only_live if t.get("priority") == "High"]
    if rule3:
        return min(rule3, key=lambda t: t.get("due_date", "9999-99-99"))

    # Rule 4: anything with NN2: Revenue Movement, soonest due
    rule4 = [t for t in only_live if "NN2" in (t.get("non_negotiables") or "")]
    if rule4:
        return min(rule4, key=lambda t: t.get("due_date", "9999-99-99"))

    # Fallback: first live task by due date
    return min(only_live, key=lambda t: t.get("due_date", "9999-99-99"))

_ROADMAP_PRIORITY = {"harvest.md": 0, "atlas.md": 1, "studio.md": 2, "echo.md": 3}


def _due_within(task: dict, today, days: int) -> bool:
    raw = task.get("due_date")
    if not raw:
        return False
    try:
        d = date.fromisoformat(raw)
    except ValueError:
        return False
    return today <= d <= today + timedelta(days=days)


def _roadmap_rank(task: dict) -> int:
    src = task.get("source_path", "")
    for name, rank in _ROADMAP_PRIORITY.items():
        if name in src:
            return rank
    return 99


def pick_p0(live_tasks: list, today=None):
    """Pick exactly one P0 from Live tasks. See spec section 5.2."""
    today = today or date.today()
    if not live_tasks:
        return None
    only_live = [t for t in live_tasks if t.get("disposition") == "Live"]
    if not only_live:
        return None
    rule1 = [t for t in only_live if t.get("category") == "Revenue" and _due_within(t, today, 7)]
    if rule1:
        return min(rule1, key=lambda t: t.get("due_date", "9999-99-99"))
    in_progress = [t for t in only_live if (t.get("source_status_marker") or "").upper() == "IN_PROGRESS"]
    if in_progress:
        rule2 = sorted(in_progress, key=lambda t: (_roadmap_rank(t), t.get("due_date", "9999-99-99")))
        if _roadmap_rank(rule2[0]) < 99:
            return rule2[0]
    rule3 = [t for t in only_live if t.get("priority") == "High"]
    if rule3:
        return min(rule3, key=lambda t: t.get("due_date", "9999-99-99"))
    rule4 = [t for t in only_live if "NN2" in (t.get("non_negotiables") or "")]
    if rule4:
        return min(rule4, key=lambda t: t.get("due_date", "9999-99-99"))
    return min(only_live, key=lambda t: t.get("due_date", "9999-99-99"))


_DISPOSITION_TO_STATUS = {"Live": "Not Started", "Shipped": "Done", "GoldenGem": "Not Started"}


def _build_notion_props(task: dict) -> dict:
    """Build a Notion properties payload for create or update."""
    props: dict = {}
    title = task["title"]
    notes = task.get("notes", "")
    if task.get("disposition") == "GoldenGem":
        gem_reason = task.get("gem_reason", "")
        notes = f"\U0001f50d GOLDEN GEM: {gem_reason} {notes}".strip()
    props["Task"] = {"title": [{"text": {"content": title}}]}
    status = _DISPOSITION_TO_STATUS.get(task.get("disposition", "Live"), "Not Started")
    props["Status"] = {"select": {"name": status}}
    if task.get("category"):
        props["Category"] = {"select": {"name": task["category"]}}
    if task.get("priority"):
        props["Priority"] = {"select": {"name": task["priority"]}}
    if task.get("source_path"):
        props["Source"] = {"rich_text": [{"text": {"content": task["source_path"][:1900]}}]}
    if task.get("completion_criteria"):
        props["Completion Criteria"] = {"rich_text": [{"text": {"content": task["completion_criteria"][:1900]}}]}
    if notes:
        props["Notes"] = {"rich_text": [{"text": {"content": notes[:1900]}}]}
    if task.get("disposition") == "Shipped":
        outcome = f"shipped {task.get('shipped_date', '2026-05-01')}"
        props["Outcome"] = {"rich_text": [{"text": {"content": outcome}}]}
    if task.get("is_p0"):
        props["P0"] = {"checkbox": True}
    props["Owner"] = {"multi_select": [{"name": "Boubacar"}]}
    return props


def _query_existing(database_id: str, title: str):
    """Find a row by exact title match. Returns the page object or None."""
    headers = _notion_headers()
    payload = {"filter": {"property": "Task", "title": {"equals": title}}, "page_size": 5}
    r = httpx.post(f"https://api.notion.com/v1/databases/{database_id}/query", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None


def upsert_task(database_id: str, task: dict) -> str:
    """Create or update a Notion page for this task. Returns 'created'/'updated'/'skipped'."""
    existing = _query_existing(database_id, task["title"])
    headers = _notion_headers()
    props = _build_notion_props(task)
    if existing is None:
        payload = {"parent": {"database_id": database_id}, "properties": props}
        r = httpx.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return "created"
    existing_status = ""
    sel = existing.get("properties", {}).get("Status", {}).get("select")
    if sel:
        existing_status = sel.get("name", "")
    if existing_status == "Done":
        return "skipped"
    update_props = {k: v for k, v in props.items() if k in {"Source", "Completion Criteria", "Notes", "P0"}}
    page_id = existing["id"]
    r = httpx.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, json={"properties": update_props}, timeout=30)
    r.raise_for_status()
    return "updated"


def write_archived_md(path: Path, archived: list, run_date: str) -> None:
    lines = [f"# Archived items, audit {run_date}", "", "| Title | Source | Why archived |", "| --- | --- | --- |"]
    for t in archived:
        title = t.get("title", "").replace("|", "\\|")
        src = t.get("source_path", "").replace("|", "\\|")
        why = (t.get("gem_reason") or "Old, no status, untouched > 60 days").replace("|", "\\|")
        lines.append(f"| {title} | {src} | {why} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_needs_review_md(path: Path, items: list, run_date: str) -> None:
    lines = [
        f"# Needs review, audit {run_date}",
        "",
        "Items the classifier could not place confidently. Decide row by row.",
        "",
        "| Title | Source | Completion criterion (if any) |",
        "| --- | --- | --- |",
    ]
    for t in items:
        title = t.get("title", "").replace("|", "\\|")
        src = t.get("source_path", "").replace("|", "\\|")
        crit = (t.get("completion_criteria") or "").replace("|", "\\|")
        lines.append(f"| {title} | {src} | {crit} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary_md(path: Path, summary: dict, run_date: str) -> None:
    p0 = summary.get("p0") or {}
    lines = [
        f"# Audit summary, {run_date}",
        "",
        "## Counts",
        "",
        f"- Live: {summary.get('live', 0)}",
        f"- Shipped: {summary.get('shipped', 0)}",
        f"- Golden Gems: {summary.get('gems', 0)}",
        f"- Archived: {summary.get('archived', 0)}",
        f"- Needs review: {summary.get('needs_review', 0)}",
        "",
        "## P0 (the dictator at the top of the board)",
        "",
        f"**{p0.get('title', '(none)')}**",
        f"Source: {p0.get('source_path', '')}",
        "",
        "## Golden Gems",
        "",
    ]
    for g in summary.get("gems_list", []):
        lines.append(f"- **{g.get('title', '')}** ({g.get('source_path', '')}): {g.get('gem_reason', '')}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Notion Task Audit harvester")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to Notion or audit files; print what would happen.",
    )
    parser.add_argument(
        "--stages",
        default="all",
        help="Comma-separated stages to run: walk,extract,classify,dedupe,upsert,write. Default: all.",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "sweep"],
        default="full",
        help="full = full archaeology pass. sweep = bi-monthly maintenance over a recent window.",
    )
    parser.add_argument(
        "--window",
        default="14d",
        help="For --mode=sweep, only include feeders modified within this window. Default 14d.",
    )
    return parser.parse_args(argv)


def _stages_from_arg(arg: str) -> set:
    if arg == "all":
        return {"walk", "extract", "classify", "dedupe", "upsert", "write"}
    return {s.strip() for s in arg.split(",") if s.strip()}


def main(argv: list | None = None) -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    args = parse_args(argv)
    stages = _stages_from_arg(args.stages)
    repo = REPO_ROOT
    db_id = os.environ.get("NOTION_TASK_DB_ID", DEFAULT_NOTION_TASK_DB_ID)
    audits_dir = repo / "docs" / "audits"
    audits_dir.mkdir(parents=True, exist_ok=True)
    run_date = "2026-05-01"

    print(f"notion_task_audit: mode={args.mode} stages={sorted(stages)} dry_run={args.dry_run}")

    files = walk_feeders(
        repo,
        mode=args.mode,
        window_days=int(args.window.rstrip("d")) if args.window.endswith("d") else 14,
    )
    print(f"  walk: {len(files)} feeder files")
    if "extract" not in stages:
        return 0

    units: list = []
    for f in files:
        units.extend(extract_units(f))
    print(f"  extract: {len(units)} units")

    if args.dry_run:
        units = units[:5]
        print(f"  dry-run: capped to {len(units)} units")

    tasks: list = []
    llm_calls = 0
    for u in units:
        if llm_calls >= HARD_LLM_CALL_CAP:
            print(f"  [STOP] LLM call cap {HARD_LLM_CALL_CAP} reached.")
            break
        try:
            extracted = extract_tasks_from_unit(u)
            llm_calls += 1
        except Exception as e:
            print(f"  extract error on {u['source_path']}: {e}")
            continue
        try:
            mtime = (repo / u["source_path"]).stat().st_mtime if isinstance(u["source_path"], str) and (repo / u["source_path"]).exists() else _time.time()
        except Exception:
            mtime = _time.time()
        for t in extracted:
            t["source_mtime"] = mtime
            tasks.append(t)
    print(f"  tasks extracted: {len(tasks)} (llm calls: {llm_calls})")

    if "classify" not in stages:
        return 0

    classified: list = []
    today_ts = _time.time()
    for t in tasks:
        try:
            mtime_days = int((today_ts - t.get("source_mtime", today_ts)) / 86400)
        except Exception:
            mtime_days = 0
        ct = classify_task(t, file_mtime_days_ago=mtime_days)
        classified.append(ct)

    gem_candidates_idx = {
        i for i, t in enumerate(classified)
        if t["disposition"] == "Live" and (today_ts - t.get("source_mtime", today_ts)) > 21 * 86400
    }
    final: list = []
    for i, t in enumerate(classified):
        if i in gem_candidates_idx and llm_calls < HARD_LLM_CALL_CAP:
            try:
                t = gem_check_task(t)
                llm_calls += 1
            except Exception as e:
                print(f"  gem error on {t['title']}: {e}")
        final.append(t)
    print(
        f"  classified: live={sum(1 for t in final if t['disposition']=='Live')} "
        f"shipped={sum(1 for t in final if t['disposition']=='Shipped')} "
        f"gems={sum(1 for t in final if t['disposition']=='GoldenGem')} "
        f"archived={sum(1 for t in final if t['disposition']=='Archived')} "
        f"needs_review={sum(1 for t in final if t['disposition']=='NeedsReview')}"
    )

    if "dedupe" not in stages:
        return 0

    deduped = dedupe(final)
    print(f"  deduped: {len(deduped)}")

    live_only = [t for t in deduped if t["disposition"] == "Live"]
    if len(live_only) > HARD_LIVE_ROW_CAP:
        print(f"  [STOP] live row count {len(live_only)} > cap {HARD_LIVE_ROW_CAP}. Re-scope per spec.")
        return 2

    today = date.today()
    p0 = pick_p0(live_only, today=today)
    if p0 is not None:
        for t in deduped:
            if t["title"] == p0["title"] and t["source_path"] == p0["source_path"]:
                t["is_p0"] = True

    if "upsert" not in stages:
        if args.dry_run:
            print(f"  [DRY] would upsert {len([t for t in deduped if t['disposition'] in {'Live','Shipped','GoldenGem'}])} tasks")
            print(f"  [DRY] P0 candidate: {p0['title'] if p0 else '(none)'}")
        return 0

    if not args.dry_run:
        ensure_schema(db_id)
        actions = {"created": 0, "updated": 0, "skipped": 0}
        for t in deduped:
            if t["disposition"] not in {"Live", "Shipped", "GoldenGem"}:
                continue
            try:
                a = upsert_task(db_id, t)
                actions[a] = actions.get(a, 0) + 1
            except Exception as e:
                print(f"  upsert error on {t['title']}: {e}")
        print(f"  upsert: {actions}")
    else:
        print(f"  [DRY] would call upsert for {sum(1 for t in deduped if t['disposition'] in {'Live','Shipped','GoldenGem'})} tasks")
        print(f"  [DRY] P0 candidate: {p0['title'] if p0 else '(none)'}")

    if "write" not in stages:
        return 0

    archived_items = [t for t in deduped if t["disposition"] == "Archived"]
    needs = [t for t in deduped if t["disposition"] == "NeedsReview"]
    gems = [t for t in deduped if t["disposition"] == "GoldenGem"]
    summary = {
        "live": sum(1 for t in deduped if t["disposition"] == "Live"),
        "shipped": sum(1 for t in deduped if t["disposition"] == "Shipped"),
        "gems": len(gems),
        "archived": len(archived_items),
        "needs_review": len(needs),
        "p0": p0,
        "gems_list": gems,
    }
    if not args.dry_run:
        write_archived_md(audits_dir / f"{run_date}-archived.md", archived_items, run_date)
        write_needs_review_md(audits_dir / f"{run_date}-needs-review.md", needs, run_date)
        write_summary_md(audits_dir / f"{run_date}-summary.md", summary, run_date)
        print(f"  wrote 3 audit files in {audits_dir}")
    else:
        print(f"  [DRY] would write 3 audit files in {audits_dir}")
        print(
            f"  [DRY] summary: {summary['live']} live / {summary['shipped']} shipped / "
            f"{summary['gems']} gems / {summary['archived']} archived / {summary['needs_review']} review"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
