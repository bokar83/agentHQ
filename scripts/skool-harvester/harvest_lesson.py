"""
harvest_lesson.py - Wrapper around skool_harvest.py that ensures:
  1. Output folder is always named by lesson_id (not URL slug)
  2. Downloaded ZIPs are extracted automatically
  3. enriched_text.txt is built from page text + all extracted file contents

Usage:
    python scripts/skool-harvester/harvest_lesson.py <lesson_id> <lesson_url>

Example:
    python scripts/skool-harvester/harvest_lesson.py ef846599e2a34f6394fd493cf4f7e2a7 \
        "https://www.skool.com/robonuggets/classroom/0d3c944a?md=ef846599e2a34f6394fd493cf4f7e2a7"

Batch mode (from review plan):
    python scripts/skool-harvester/harvest_lesson.py --from-plan robonuggets --max 5
"""

import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_BASE = REPO_ROOT / "workspace" / "skool-harvest"

# Max chars per file injected into enriched_text.txt
_MAX_FILE_CHARS = 5000
# Extensions worth reading as text
_TEXT_EXTENSIONS = {".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".env", ".sh"}
# Max total enriched size fed to Mapper
_MAX_ENRICHED_CHARS = 20000


def community_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    return parts[0] if parts and parts[0] else "unknown-community"


def _extract_zips(lesson_dir: Path) -> list[Path]:
    """Extract all ZIPs in downloads/, return list of extracted dirs."""
    downloads = lesson_dir / "downloads"
    extracted_dirs = []
    if not downloads.exists():
        return extracted_dirs
    for zp in downloads.glob("*.zip"):
        out = downloads / ("extracted_" + re.sub(r"[^\w]", "_", zp.stem))
        if not out.exists():
            out.mkdir()
            with zipfile.ZipFile(zp) as z:
                z.extractall(out)
            print(f"  [enrich] extracted {zp.name} -> {out.name}/ ({len(list(out.rglob('*')))} items)")
        extracted_dirs.append(out)
    return extracted_dirs


def _collect_text_files(lesson_dir: Path) -> list[Path]:
    """Find all readable text files in downloads/ (ZIPs extracted, JSONs, MDs)."""
    downloads = lesson_dir / "downloads"
    files = []
    if not downloads.exists():
        return files
    for p in sorted(downloads.rglob("*")):
        if p.is_file() and p.suffix.lower() in _TEXT_EXTENSIONS:
            files.append(p)
    return files


def build_enriched_text(lesson_dir: Path) -> int:
    """Build enriched_text.txt from page text + download contents. Returns total chars."""
    text_path = lesson_dir / "text.txt"
    base_text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""

    _extract_zips(lesson_dir)
    extra_files = _collect_text_files(lesson_dir)

    sections = [base_text]
    remaining = _MAX_ENRICHED_CHARS - len(base_text)

    for fp in extra_files:
        if remaining <= 0:
            break
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if len(content) > _MAX_FILE_CHARS:
            content = content[:_MAX_FILE_CHARS] + "\n... [truncated]"
        chunk = f"\n\n=== FILE: {fp.name} ===\n{content}"
        sections.append(chunk)
        remaining -= len(chunk)

    enriched = "".join(sections)
    (lesson_dir / "enriched_text.txt").write_text(enriched, encoding="utf-8")
    return len(enriched)


def harvest_lesson(lesson_id: str, lesson_url: str) -> bool:
    """Run skool_harvest.py for one lesson, then build enriched_text.txt."""
    import subprocess

    community = community_from_url(lesson_url)
    lesson_dir = WORKSPACE_BASE / community / lesson_id

    print(f"\n[harvest_lesson] {lesson_id[:12]}  {lesson_url[:70]}")

    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "skool_harvest.py"), lesson_url, lesson_id],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"  [harvest_lesson] skool_harvest.py failed (exit {result.returncode})")
        return False

    if lesson_dir.exists():
        n = build_enriched_text(lesson_dir)
        print(f"  [harvest_lesson] enriched_text.txt built: {n} chars")
    else:
        print(f"  [harvest_lesson] WARNING: lesson dir missing after harvest: {lesson_dir}")
        return False

    return True


def harvest_from_plan(community: str, max_count: int | None = None) -> list[str]:
    """Harvest next un-harvested deep lessons from the review plan."""
    plan_path = WORKSPACE_BASE / community / "_review_plan.json"
    if not plan_path.exists():
        print(f"ERROR: {plan_path} missing")
        sys.exit(1)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    entries = plan.get("entries", [])

    targets = [
        e for e in entries
        if e.get("triage_label") == "deep"
        and not e.get("harvested_artifacts_present")
        and e.get("lesson_url")
        and e.get("lesson_id")
    ]

    if max_count is not None:
        targets = targets[:max_count]

    harvested_ids = []
    for e in targets:
        lid = e["lesson_id"]
        url = e["lesson_url"]
        ok = harvest_lesson(lid, url)
        if ok:
            e["harvested_artifacts_present"] = True
            harvested_ids.append(lid)

    if harvested_ids:
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[harvest_from_plan] marked {len(harvested_ids)} lessons as harvested in plan")

    return harvested_ids


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "--from-plan":
        community = argv[2] if len(argv) > 2 else "robonuggets"
        max_count = int(argv[4]) if len(argv) > 4 and argv[3] == "--max" else None
        ids = harvest_from_plan(community, max_count)
        print(f"\nHarvested {len(ids)} lessons: {ids}")
        return 0

    if len(argv) < 3:
        print(__doc__)
        return 1

    lesson_id = argv[1]
    lesson_url = argv[2]
    ok = harvest_lesson(lesson_id, lesson_url)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
