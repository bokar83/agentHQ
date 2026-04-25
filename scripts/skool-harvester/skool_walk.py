"""
Skool classroom walker. Three operations:

  --list           Show top-level courses in the classroom. Fast, ~10s.
                   Paginates ?p=N. Reports each course's module count from
                   metadata WITHOUT visiting it. Use this when you just want
                   to see what is in the classroom.

  --list --deep    Same plus visit every accessible course detail page to
                   enumerate every lesson. Slow (~minutes for large classrooms).
                   Use only when you want a complete lesson index.

  --new            Deep walk, then print only lessons not yet harvested.
                   Saves the refreshed index.

  --all            Deep walk, then harvest each lesson via skool_harvest.harvest().
                   Skips already-harvested unless --force. Use --max N to cap.

Loads the saved Playwright session at ~/.claude/playwright-state/skool.json.
Run skool_login.py first if Skool has logged you out.

How discovery works:

  1. The classroom root is paginated via ?p=N. Each page has up to 30 courses
     embedded in <script id="__NEXT_DATA__"> as props.pageProps.allCourses.
     We loop pages until allCourses is empty.

  2. Each top-level entry is either:
       - unitType="course" with numModules > 0  -> visit it for lesson list
       - unitType="course" with numModules == 0 -> standalone lesson, can be
         harvested directly via /classroom/<name_slug>
     We treat the SSR payload as the truth.

  3. For nested courses we visit /classroom/<name_slug> and read
     props.pageProps.course.children (recursively expanded). Modules with
     unitType="module" are lessons; "set" entries are folders with their own
     children.

Usage:
    python skool_walk.py <classroom_url> --list
    python skool_walk.py <classroom_url> --new
    python skool_walk.py <classroom_url> --all
    python skool_walk.py <classroom_url> --all --force
    python skool_walk.py <classroom_url> --all --max 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Page, sync_playwright

# Force line-buffered stdout so background runs stream progress live.
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

# Reuse the harvester for individual lessons.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skool_harvest import (  # noqa: E402
    harvest,
    community_from_url,
    WORKSPACE_BASE,
    STATE_PATH,
)


_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


# ---- Page helpers -----------------------------------------------------------

def _get_next_data(page: Page) -> dict | None:
    m = _NEXT_DATA_RE.search(page.content())
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _navigate(page: Page, url: str, settle: float = 2.0) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("load", timeout=30000)
    except Exception:
        pass
    if settle:
        time.sleep(settle)


# ---- Classroom-level discovery (paginated allCourses) ----------------------

def _classroom_base(url: str) -> str:
    """Return the canonical classroom URL (no query, no /<course-slug>)."""
    p = urlparse(url)
    parts = p.path.rstrip("/").split("/")
    # /<community>/classroom/[<course-slug>]
    if "classroom" in parts:
        idx = parts.index("classroom")
        canonical_path = "/".join(parts[: idx + 1])
    else:
        canonical_path = p.path.rstrip("/")
    return f"{p.scheme}://{p.netloc}{canonical_path}"


def _list_top_level(page: Page, classroom_url: str) -> list[dict]:
    """Walk ?p=1, ?p=2, ... until allCourses is empty. Returns flat list."""
    base = _classroom_base(classroom_url)
    out: list[dict] = []
    seen_ids: set[str] = set()
    page_no = 1
    while True:
        url = f"{base}?p={page_no}"
        print(f"[walk] discover page {page_no}: {url}")
        _navigate(page, url, settle=1.5)
        data = _get_next_data(page)
        if not data:
            print(f"[walk] no __NEXT_DATA__ at page {page_no}, stopping")
            break
        all_courses = (
            data.get("props", {}).get("pageProps", {}).get("allCourses") or []
        )
        if not all_courses:
            break
        added = 0
        for c in all_courses:
            cid = c.get("id")
            if not cid or cid in seen_ids:
                continue
            seen_ids.add(cid)
            md = c.get("metadata") or {}
            out.append(
                {
                    "id": cid,
                    "name_slug": c.get("name"),
                    "title": md.get("title") or "(untitled)",
                    "unitType": c.get("unitType"),
                    "numModules": md.get("numModules") or 0,
                    "hasAccess": md.get("hasAccess", 0),
                    "createdAt": c.get("createdAt"),
                    "updatedAt": c.get("updatedAt"),
                    "course_url": f"{base}/{c.get('name')}",
                }
            )
            added += 1
        print(f"[walk] page {page_no}: +{added} courses (total {len(out)})")
        page_no += 1
        if page_no > 50:  # paranoia stop
            print(f"[walk] safety stop at page {page_no}")
            break
    return out


# ---- Course-level discovery (nested modules) -------------------------------

def _flatten_modules(node: dict, parent_path: list[str] | None = None) -> list[dict]:
    """Recurse into course.children -> {course: {...}, children:[...]}.
    Return only unitType=='module' leaves. Each entry includes parent path.
    """
    parent_path = parent_path or []
    out: list[dict] = []
    children = node.get("children") or []
    for ch in children:
        inner = ch.get("course") or {}
        unit_type = inner.get("unitType")
        md = inner.get("metadata") or {}
        title = md.get("title") or "(untitled)"
        if unit_type == "module":
            out.append(
                {
                    "id": inner.get("id"),
                    "name_slug": inner.get("name"),
                    "title": title,
                    "unitType": unit_type,
                    "createdAt": inner.get("createdAt"),
                    "updatedAt": inner.get("updatedAt"),
                    "parent_path": parent_path,
                }
            )
        elif unit_type in ("set", "course"):
            # Recurse; sets can be nested, and their children carry the lessons.
            out.extend(_flatten_modules(ch, parent_path + [title]))
        else:
            # Unknown type. Recurse defensively in case it has children too.
            if ch.get("children"):
                out.extend(_flatten_modules(ch, parent_path + [title]))
    return out


def _expand_course(page: Page, course_url: str, course_name_slug: str) -> list[dict]:
    """Visit a course page and return its module list (lessons)."""
    _navigate(page, course_url, settle=2.5)
    data = _get_next_data(page)
    if not data:
        print(f"[walk] no __NEXT_DATA__ at course {course_url}")
        return []
    course_node = data.get("props", {}).get("pageProps", {}).get("course") or {}
    modules = _flatten_modules(course_node)
    base = _classroom_base(course_url)
    for m in modules:
        m["lesson_url"] = f"{base}/{course_name_slug}?md={m['id']}"
    return modules


# ---- Index management -------------------------------------------------------

def _index_path(community: str) -> Path:
    return WORKSPACE_BASE / community / "_index.json"


def _load_index(community: str) -> dict:
    p = _index_path(community)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"community": community, "courses": [], "lessons": [], "last_walk": None}


def _save_index(community: str, index: dict) -> None:
    p = _index_path(community)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ascii(s: str | None) -> str:
    return ((s or "").encode("ascii", "replace").decode("ascii"))


# ---- Public operations ------------------------------------------------------

def discover(classroom_url: str, expand_courses: bool = True) -> dict:
    """Walk classroom and (optionally) every course detail page.

    expand_courses=False is the fast path: one page load per pagination page,
    no per-course visits. Use it when you just want a top-level summary or
    are checking what is new at the course level.

    expand_courses=True visits every accessible course's detail page to
    enumerate lessons. Required before --all or --new can act on lessons.
    """
    if not STATE_PATH.exists():
        raise RuntimeError(f"no saved session at {STATE_PATH}; run skool_login.py first")
    community = community_from_url(classroom_url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            storage_state=str(STATE_PATH),
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()
        try:
            top = _list_top_level(page, classroom_url)
            lessons: list[dict] = []
            if expand_courses:
                expandable = [c for c in top if c.get("hasAccess") and c.get("numModules", 0) > 0]
                print(f"[walk] expanding {len(expandable)} courses (this is the slow part)...")
                for i, c in enumerate(top, 1):
                    # Standalone lesson: a course with 0 numModules acts as a
                    # direct lesson entry. Treat the course slug as the lesson.
                    if c.get("numModules") == 0:
                        lessons.append(
                            {
                                "id": c["id"],
                                "name_slug": c["name_slug"],
                                "title": c["title"],
                                "unitType": "lesson",
                                "course_id": c["id"],
                                "course_title": c["title"],
                                "parent_path": [],
                                "lesson_url": c["course_url"],
                                "createdAt": c.get("createdAt"),
                                "updatedAt": c.get("updatedAt"),
                            }
                        )
                        continue
                    if not c.get("hasAccess"):
                        continue
                    print(f"[walk] ({i}/{len(top)}) {c['numModules']} modules: {_ascii(c['title'])[:60]}")
                    mods = _expand_course(page, c["course_url"], c["name_slug"])
                    for m in mods:
                        lessons.append(
                            {
                                **m,
                                "course_id": c["id"],
                                "course_title": c["title"],
                            }
                        )
            else:
                # Shallow mode: do not visit course pages. Lessons left empty so
                # callers know they need to re-run with expand_courses=True
                # before harvest. Standalone (single-lesson) courses are still
                # captured as lessons since we already have their URL.
                for c in top:
                    if c.get("numModules") == 0:
                        lessons.append(
                            {
                                "id": c["id"],
                                "name_slug": c["name_slug"],
                                "title": c["title"],
                                "unitType": "lesson",
                                "course_id": c["id"],
                                "course_title": c["title"],
                                "parent_path": [],
                                "lesson_url": c["course_url"],
                                "createdAt": c.get("createdAt"),
                                "updatedAt": c.get("updatedAt"),
                            }
                        )
        finally:
            browser.close()

    # Merge with existing index, preserving harvested_at timestamps.
    # Shallow runs: keep prior lesson rows we did not re-discover, since the
    # shallow walk does not enumerate per-course lessons.
    index = _load_index(community)
    by_lid = {l["id"]: l for l in index.get("lessons", []) if l.get("id")}

    if expand_courses:
        # Deep walk: lessons list IS authoritative. Replace, but preserve
        # harvested_at on the entries we re-saw.
        merged_lessons = []
        for l in lessons:
            prior = by_lid.get(l["id"], {}) if l.get("id") else {}
            merged_lessons.append(
                {
                    **l,
                    "first_seen": prior.get("first_seen") or _now_iso(),
                    "last_seen": _now_iso(),
                    "harvested_at": prior.get("harvested_at"),
                }
            )
    else:
        # Shallow walk: only refresh standalone lessons; keep all prior rows.
        merged_lessons = list(index.get("lessons", []))
        seen_ids = {l["id"] for l in merged_lessons if l.get("id")}
        for l in lessons:
            if l.get("id") not in seen_ids:
                merged_lessons.append(
                    {**l, "first_seen": _now_iso(), "last_seen": _now_iso(), "harvested_at": None}
                )
            else:
                # Update last_seen on the existing row
                for ex in merged_lessons:
                    if ex.get("id") == l.get("id"):
                        ex["last_seen"] = _now_iso()
                        break

    # Courses list is always authoritative on every walk, deep or shallow.
    index["courses"] = top
    index["lessons"] = merged_lessons
    index["last_walk"] = _now_iso()
    index["last_walk_mode"] = "deep" if expand_courses else "shallow"
    _save_index(community, index)
    return index


def _apply_course_filter(
    lessons: list[dict], course_filter: str | None
) -> list[dict]:
    """Keep only lessons whose course_title or own title matches the regex.

    The filter is anchored to the start of the title by default so users can
    pass things like 'R\\d+' and get the R-series only without leaking matches
    from anywhere mid-string. Pass with explicit anchors to override.
    """
    if not course_filter:
        return lessons
    pattern = re.compile(course_filter)
    out = []
    for l in lessons:
        ct = l.get("course_title") or ""
        lt = l.get("title") or ""
        if pattern.search(ct) or pattern.search(lt):
            out.append(l)
    return out


def list_new(classroom_url: str, course_filter: str | None = None) -> dict:
    """Refresh discovery, return ONLY lessons not yet harvested.

    When course_filter is set, also restrict the new-lesson list to titles
    matching the regex (search, not match — pass `^R\\d+` to anchor).
    """
    index = discover(classroom_url, expand_courses=True)
    new_only = [l for l in index["lessons"] if not l.get("harvested_at")]
    new_only = _apply_course_filter(new_only, course_filter)
    return {
        "community": index["community"],
        "total_courses": len(index["courses"]),
        "total_lessons": len(index["lessons"]),
        "new_lessons": new_only,
    }


def harvest_all(
    classroom_url: str,
    force: bool = False,
    max_count: int | None = None,
    course_filter: str | None = None,
) -> dict:
    """List the classroom, harvest every lesson (or only new ones unless --force).

    course_filter is a regex applied to course_title and lesson title; only
    matching lessons are harvested.
    """
    index = discover(classroom_url, expand_courses=True)
    community = index["community"]
    candidates = (
        index["lessons"]
        if force
        else [l for l in index["lessons"] if not l.get("harvested_at")]
    )
    candidates = _apply_course_filter(candidates, course_filter)
    targets = candidates[:max_count] if max_count is not None else candidates
    filt_note = f", course_filter='{course_filter}'" if course_filter else ""
    print(
        f"[walk] harvesting {len(targets)} lessons "
        f"({'all' if force else 'new only'}{', capped at ' + str(max_count) if max_count else ''}{filt_note})"
    )

    results = []
    by_lid = {l["id"]: l for l in index["lessons"] if l.get("id")}
    for i, lesson in enumerate(targets, 1):
        title = _ascii(lesson.get("title", ""))[:60]
        print(f"\n[walk] ({i}/{len(targets)}) {title}")
        try:
            harvest(lesson["lesson_url"], subdir=lesson["id"])
            lesson_in_index = by_lid.get(lesson["id"])
            if lesson_in_index:
                lesson_in_index["harvested_at"] = _now_iso()
            results.append({"id": lesson["id"], "ok": True})
        except Exception as e:
            print(f"[walk] FAILED on {lesson['id']}: {e}")
            results.append({"id": lesson["id"], "ok": False, "error": str(e)})
        _save_index(community, index)

    return {
        "community": community,
        "total_courses": len(index["courses"]),
        "total_lessons": len(index["lessons"]),
        "harvested_count": sum(1 for r in results if r["ok"]),
        "failed_count": sum(1 for r in results if not r["ok"]),
        "results": results,
    }


# ---- CLI --------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("classroom_url", help="https://www.skool.com/<community>/classroom")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="enumerate everything, print summary")
    mode.add_argument("--new", action="store_true", help="list only lessons not yet harvested")
    mode.add_argument("--all", action="store_true", help="enumerate then harvest")
    ap.add_argument("--force", action="store_true", help="re-harvest already-harvested lessons")
    ap.add_argument("--max", type=int, help="cap the number of lessons harvested")
    ap.add_argument("--deep", action="store_true",
                    help="for --list only: also visit every course detail page to enumerate lessons (slow)")
    ap.add_argument("--course-filter", dest="course_filter", default=None,
                    help="regex to restrict --new / --all to matching course/lesson titles "
                         "(e.g. '^R\\\\d+' for the R-series)")
    args = ap.parse_args()

    if args.list:
        # Shallow by default: only paginated classroom (~3 page loads, ~10s).
        # Deep when explicitly requested: also visits each course (1 load per course).
        idx = discover(args.classroom_url, expand_courses=args.deep)
        community = idx["community"]
        total_courses = len(idx["courses"])
        total_lessons = len(idx["lessons"])
        unharvested = sum(1 for l in idx["lessons"] if not l.get("harvested_at"))
        print(f"\n=== {community} ===")
        print(f"  mode:     {'deep' if args.deep else 'shallow (top-level only)'}")
        print(f"  courses:  {total_courses}")
        if args.deep:
            print(f"  lessons:  {total_lessons}  ({unharvested} not yet harvested)")
        print(f"  index:    {_index_path(community)}")

        # Show top courses with module counts so you can see what's there
        top_courses = sorted(idx["courses"], key=lambda c: -(c.get("numModules") or 0))[:15]
        print("\n  top 15 courses by module count:")
        for c in top_courses:
            title = _ascii(c.get("title", ""))[:60]
            access = "    " if c.get("hasAccess") else "[no]"
            print(f"    {access} {c.get('numModules', 0):>3} modules  {title}  ({c.get('name_slug', '')})")

        if args.deep:
            unharvested_list = [l for l in idx["lessons"] if not l.get("harvested_at")][:10]
            if unharvested_list:
                print("\n  next 10 unharvested lessons:")
                for l in unharvested_list:
                    title = _ascii(l.get("title", ""))[:70]
                    print(f"    {l.get('id', '?')[:12]}  {title}")
        else:
            print("\n  (run with --deep to enumerate every lesson, or --new / --all to harvest)")
        return 0

    if args.new:
        summary = list_new(args.classroom_url, course_filter=args.course_filter)
        community = summary["community"]
        new_lessons = summary["new_lessons"]
        print(f"\n=== {community}: {summary['total_courses']} courses, "
              f"{summary['total_lessons']} lessons, {len(new_lessons)} new ===")
        for l in new_lessons:
            print(f"  NEW  {l.get('id', '?')[:12]}  {_ascii(l.get('title', ''))[:70]}")
        if not new_lessons:
            print("  (no new lessons since last walk)")
        return 0

    if args.all:
        summary = harvest_all(
            args.classroom_url,
            force=args.force,
            max_count=args.max,
            course_filter=args.course_filter,
        )
        print(f"\n=== Harvest summary for {summary['community']} ===")
        print(f"  courses:           {summary['total_courses']}")
        print(f"  lessons total:     {summary['total_lessons']}")
        print(f"  harvested this run:{summary['harvested_count']}")
        print(f"  failed:            {summary['failed_count']}")
        return 0 if summary["failed_count"] == 0 else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
