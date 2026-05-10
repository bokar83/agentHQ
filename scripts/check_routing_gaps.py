#!/usr/bin/env python3
"""Routing gap detector for agentsHQ skills.

Implements the Layer A structural check from gbrain's check-resolvable pattern
(garrytan/gbrain src/core/check-resolvable.ts absorbed 2026-05-09, compass M2.5).

Reads:
  - docs/SKILLS_INDEX.md  — registered skills + trigger phrases in descriptions
  - skills/<name>/routing-eval.jsonl  — per-skill fixture files (paraphrased intents)

Checks:
  1. Unreachable  — skill dir exists but has no SKILLS_INDEX.md entry
  2. MECE overlap — two skills whose trigger phrases both match the same fixture intent
  3. MECE gap     — fixture intent matches zero trigger phrases (routing dead zone)
  4. Fixture miss — fixture intent says it should route to skill X but Layer A says Y
  5. Stub sentinel — SKILL.md still contains placeholder text
  6. Tautology    — fixture intent IS a trigger phrase verbatim (invalid test)

Exit code 0 = CLEAN (or only warnings). Exit code 1 = at least one ERROR.

Usage:
    python scripts/check_routing_gaps.py [--strict] [--fix-stubs]
    --strict: treat OVERLAP/GAP/MISS as errors (default: warnings)
    --fix-stubs: list stub files, don't auto-fix
"""
from __future__ import annotations

import json
import re
import sys
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
INDEX_PATH = REPO_ROOT / "docs" / "SKILLS_INDEX.md"

# Sentinels that indicate an unreplaced template — must be whole-word / phrase,
# not substrings that appear legitimately in skill content.
# "PLACEHOLDER" excluded: skills use {{PLACEHOLDER}} as template variable names.
# "TODO" excluded: appears legitimately in skill instructions.
STUB_SENTINELS = ["your description here", "your skill name here", "INSERT SKILL NAME"]

# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SkillEntry:
    slug: str
    dir_path: Path
    description: str
    triggers: list[str] = field(default_factory=list)


@dataclass
class Fixture:
    skill_slug: str
    intent: str
    expected_slug: str  # which skill this intent should route to


@dataclass
class Finding:
    level: str   # ERROR | WARN | INFO
    check: str
    skill: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.check} | {self.skill} | {self.message}"


# ─────────────────────────────────────────────────────────────────────────────
# Parsers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lower-case, collapse whitespace, strip punctuation for fuzzy match."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_skills_index() -> dict[str, SkillEntry]:
    """Parse SKILLS_INDEX.md into slug -> SkillEntry.

    Extracts trigger hints from the description text — looks for patterns like
    'Triggers on "X", "Y"' or 'Trigger when user says "X"'.
    """
    entries: dict[str, SkillEntry] = {}
    if not INDEX_PATH.is_file():
        print(f"ERROR: {INDEX_PATH} not found", file=sys.stderr)
        sys.exit(1)

    text = INDEX_PATH.read_text(encoding="utf-8")
    # Each line: - `slug` (`skills/dir/`): description
    pattern = re.compile(r"^-\s+`([^`]+)`\s+\(`([^`]+)`\):\s+(.+)$", re.MULTILINE)
    for m in pattern.finditer(text):
        slug, dir_rel, description = m.group(1), m.group(2), m.group(3)
        dir_path = REPO_ROOT / dir_rel.rstrip("/")

        # Extract trigger phrases from description.
        # Strategy 1: quoted strings after "Triggers on" / "Trigger when" / "Use when"
        # Strategy 2: ALL quoted strings anywhere in the description (catches skills
        #             that list examples inline like 'say "build a site"')
        # Strategy 3: action keywords from description body (fallback for no quotes)
        triggers: list[str] = []
        trigger_pattern = re.compile(r'"([^"]{3,80})"')

        # Strategy 1: preferred — quoted phrases near trigger declaration
        trigger_section = re.search(
            r'[Tt]riggers?\s+(?:on|when|with)[^.]*\.?(.{0,500})', description
        )
        if trigger_section:
            for phrase_match in trigger_pattern.finditer(trigger_section.group(0)):
                phrase = phrase_match.group(1).strip()
                if phrase and not phrase.startswith("http"):
                    triggers.append(phrase)

        # Strategy 2: all quoted strings in description (if strategy 1 gave nothing)
        if not triggers:
            for phrase_match in trigger_pattern.finditer(description):
                phrase = phrase_match.group(1).strip()
                if phrase and not phrase.startswith("http") and len(phrase.split()) <= 8:
                    triggers.append(phrase)
                if len(triggers) >= 6:
                    break

        entries[slug] = SkillEntry(
            slug=slug,
            dir_path=dir_path,
            description=description,
            triggers=triggers,
        )
    return entries


def load_fixtures(skills: dict[str, SkillEntry]) -> list[Fixture]:
    """Load routing-eval.jsonl fixtures from each skill dir.

    Format per line: {"intent": "...", "expected": "skill-slug"}
    """
    fixtures: list[Fixture] = []
    for slug, entry in skills.items():
        fixture_file = entry.dir_path / "routing-eval.jsonl"
        if not fixture_file.is_file():
            continue
        for line_no, line in enumerate(fixture_file.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                obj = json.loads(line)
                intent = obj.get("intent", "").strip()
                expected = obj.get("expected", slug).strip()
                if intent:
                    fixtures.append(Fixture(skill_slug=slug, intent=intent, expected_slug=expected))
            except json.JSONDecodeError as e:
                print(f"WARN: {fixture_file.relative_to(REPO_ROOT)}:{line_no}: bad JSON: {e}")
    return fixtures


def iter_skill_dirs() -> Iterator[Path]:
    """Yield skill dirs that have a SKILL.md (skip submodules + nested clones)."""
    gitmodules = REPO_ROOT / ".gitmodules"
    submodule_paths: set[str] = set()
    if gitmodules.is_file():
        for line in gitmodules.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("path"):
                _, _, val = line.partition("=")
                val = val.strip()
                if val:
                    submodule_paths.add(val.replace("\\", "/"))

    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir():
            continue
        rel = d.relative_to(REPO_ROOT).as_posix()
        if rel in submodule_paths:
            continue
        git_marker = d / ".git"
        if git_marker.is_file() or git_marker.is_dir():
            continue
        if (d / "SKILL.md").is_file():
            yield d


# ─────────────────────────────────────────────────────────────────────────────
# Checks
# ─────────────────────────────────────────────────────────────────────────────

def check_unreachable(skills: dict[str, SkillEntry]) -> list[Finding]:
    """Skills with a dir + SKILL.md but no SKILLS_INDEX.md entry."""
    findings = []
    indexed_dirs = {str(e.dir_path).replace("\\", "/").rstrip("/") for e in skills.values()}
    for skill_dir in iter_skill_dirs():
        dir_str = str(skill_dir).replace("\\", "/").rstrip("/")
        if dir_str not in indexed_dirs:
            findings.append(Finding(
                level="ERROR",
                check="unreachable",
                skill=skill_dir.name,
                message=f"skill dir exists but has no SKILLS_INDEX.md entry — LLM cannot route to it",
            ))
    return findings


def check_stubs(skills: dict[str, SkillEntry]) -> list[Finding]:
    """SKILL.md files containing unreplaced placeholder sentinel text."""
    findings = []
    for slug, entry in skills.items():
        skill_file = entry.dir_path / "SKILL.md"
        if not skill_file.is_file():
            continue
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        for sentinel in STUB_SENTINELS:
            if sentinel.lower() in text.lower():
                findings.append(Finding(
                    level="WARN",
                    check="stub-sentinel",
                    skill=slug,
                    message=f"SKILL.md contains placeholder text: {sentinel!r}",
                ))
                break
    return findings


def check_tautology(fixtures: list[Fixture], skills: dict[str, SkillEntry]) -> list[Finding]:
    """Fixture intent IS a trigger phrase verbatim — invalid test (tautology)."""
    findings = []
    for fx in fixtures:
        entry = skills.get(fx.skill_slug)
        if not entry:
            continue
        norm_intent = _normalize(fx.intent)
        for trigger in entry.triggers:
            if _normalize(trigger) == norm_intent:
                findings.append(Finding(
                    level="WARN",
                    check="tautology",
                    skill=fx.skill_slug,
                    message=f"fixture intent {fx.intent!r} is verbatim trigger phrase — paraphrase it",
                ))
    return findings


def _intent_matches_skill(intent_norm: str, entry: SkillEntry) -> bool:
    """Layer A: does a normalized intent substring-match any trigger phrase?

    Only uses trigger phrases — not description keywords. Description fallback
    was too noisy (many skills share generic words like 'build', 'skill', 'content').
    Skills with no trigger phrases registered will never match — that's intentional:
    it surfaces them as gaps during fixture checks.
    """
    for trigger in entry.triggers:
        trigger_norm = _normalize(trigger)
        if trigger_norm and (trigger_norm in intent_norm or intent_norm in trigger_norm):
            return True
    return False


def check_fixtures(
    fixtures: list[Fixture],
    skills: dict[str, SkillEntry],
    strict: bool,
) -> list[Finding]:
    """Check each fixture intent against Layer A routing."""
    findings = []
    level = "ERROR" if strict else "WARN"

    for fx in fixtures:
        norm_intent = _normalize(fx.intent)
        matched_slugs = [
            slug for slug, entry in skills.items()
            if _intent_matches_skill(norm_intent, entry)
        ]

        # GAP: intent routes to nothing
        if not matched_slugs:
            findings.append(Finding(
                level=level,
                check="gap",
                skill=fx.skill_slug,
                message=f"intent {fx.intent!r} matches no skill — routing dead zone",
            ))
            continue

        # OVERLAP: intent routes to multiple skills
        if len(matched_slugs) > 1:
            findings.append(Finding(
                level=level,
                check="overlap",
                skill=fx.skill_slug,
                message=f"intent {fx.intent!r} matches {len(matched_slugs)} skills: {matched_slugs}",
            ))

        # MISS: intent doesn't route to expected skill
        if fx.expected_slug not in matched_slugs:
            findings.append(Finding(
                level=level,
                check="fixture-miss",
                skill=fx.skill_slug,
                message=(
                    f"intent {fx.intent!r} expected -> {fx.expected_slug!r} "
                    f"but Layer A matched: {matched_slugs or ['nothing']}"
                ),
            ))

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Check agentsHQ skill routing gaps")
    parser.add_argument("--strict", action="store_true", help="treat OVERLAP/GAP/MISS as errors")
    parser.add_argument("--coverage", action="store_true", help="show fixture coverage stats")
    args = parser.parse_args()

    skills = load_skills_index()
    fixtures = load_fixtures(skills)

    all_findings: list[Finding] = []
    all_findings += check_unreachable(skills)
    all_findings += check_stubs(skills)
    all_findings += check_tautology(fixtures, skills)
    all_findings += check_fixtures(fixtures, skills, strict=args.strict)

    errors = [f for f in all_findings if f.level == "ERROR"]
    warns  = [f for f in all_findings if f.level == "WARN"]

    if all_findings:
        for f in sorted(all_findings, key=lambda x: (x.level, x.check, x.skill)):
            print(f)
    else:
        print("CLEAN — no routing gaps found")

    if args.coverage:
        skills_with_fixtures = {fx.skill_slug for fx in fixtures}
        total = len(skills)
        covered = len(skills_with_fixtures)
        pct = covered / total * 100 if total else 0
        print(f"\nCoverage: {covered}/{total} skills have routing fixtures ({pct:.0f}%)")
        missing = sorted(set(skills) - skills_with_fixtures)
        if missing:
            print(f"Skills without fixtures ({len(missing)}): {', '.join(missing[:10])}" +
                  (" ..." if len(missing) > 10 else ""))

    if errors:
        print(f"\n{len(errors)} error(s), {len(warns)} warning(s). Fix errors before committing.")
        return 1
    if warns:
        print(f"\n0 errors, {len(warns)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
