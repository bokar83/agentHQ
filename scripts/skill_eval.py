#!/usr/bin/env python3
"""
skill_eval.py — routing eval runner for agentsHQ skills

For each {intent, expected} row in a skill's routing-eval.jsonl:
  - checks whether the skill's SKILL.md description trigger phrases match the intent
  - tallies pass/fail
  - exits 0 if pass rate >= threshold, 1 if below

Usage:
    python scripts/skill_eval.py skills/openspace_skill [--threshold 0.8]
    python scripts/skill_eval.py skills/openspace_skill --json

Exit codes:
    0  pass rate >= threshold (gate: proceed)
    1  pass rate < threshold  (gate: reject)
    2  eval file missing or malformed (gate: warn, do not block)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_THRESHOLD = 0.8


def _load_skill_triggers(skill_dir: Path) -> list[str]:
    """Extract trigger phrases from SKILL.md description frontmatter.

    Handles both inline descriptions and YAML block scalars (> and |).
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return []
    text = skill_md.read_text(encoding="utf-8")

    # Find description: value — may be inline or a block scalar (> or |)
    m = re.search(r"^description:\s*(.*)$", text, re.MULTILINE)
    if not m:
        return []

    first_line = m.group(1).strip()
    if first_line in (">", "|", "|-", ">-"):
        # Block scalar: collect indented lines that follow until next key or end of frontmatter
        block_start = m.end()
        block_lines = []
        for line in text[block_start:].splitlines():
            if re.match(r"^\S", line) or line.strip() == "---":
                break
            block_lines.append(line.strip())
        desc = " ".join(block_lines)
    else:
        desc = first_line

    # Unescape and strip outer YAML quotes so inner trigger phrases are extractable
    if desc.startswith('"') and desc.endswith('"'):
        desc = desc[1:-1].replace('\\"', '"')

    # Extract quoted trigger phrases if present
    quoted = re.findall(r'"([^"]+)"', desc)
    if quoted:
        return [t.lower().strip() for t in quoted]
    # Fall back: split on commas, periods, semicolons
    parts = re.split(r"[,;.]+", desc)
    return [p.lower().strip() for p in parts if p.strip()]


def _intent_matches(intent: str, triggers: list[str]) -> bool:
    intent_lower = intent.lower()
    return any(t and t in intent_lower for t in triggers)


def _load_eval_rows(skill_dir: Path) -> list[dict]:
    eval_file = skill_dir / "routing-eval.jsonl"
    if not eval_file.exists():
        return []
    rows = []
    for i, line in enumerate(eval_file.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"[skill_eval] WARN: line {i} malformed ({exc})", file=sys.stderr)
            continue
        if "intent" not in row or "expected" not in row:
            print(f"[skill_eval] WARN: line {i} missing intent/expected — skipped", file=sys.stderr)
            continue
        rows.append(row)
    return rows


def _normalize(name: str) -> str:
    # Strip namespace prefix (e.g. "ckm:brand" → "brand", "vercel-react-best-practices" stays)
    name = name.split(":")[-1]
    return name.lower().replace("-", "_").replace(" ", "_")


def eval_skill(skill_dir: Path, threshold: float) -> dict:
    skill_name = skill_dir.name
    skill_id = _normalize(skill_name)
    triggers = _load_skill_triggers(skill_dir)
    rows = _load_eval_rows(skill_dir)

    if not rows:
        return {
            "skill": skill_name,
            "status": "NO_EVAL",
            "message": "routing-eval.jsonl missing or empty",
            "pass_rate": None,
            "exit_code": 2,
        }

    results = []
    for row in rows:
        intent = row["intent"]
        expected_skill = row["expected"]
        should_match = _normalize(expected_skill) == skill_id
        did_match = _intent_matches(intent, triggers)

        # true positive: should match + did match
        # true negative: should not match + did not match
        correct = (should_match == did_match)
        results.append({
            "intent": intent,
            "expected": expected_skill,
            "should_match": should_match,
            "did_match": did_match,
            "correct": correct,
        })

    passed = sum(1 for r in results if r["correct"])
    total = len(results)
    pass_rate = passed / total if total else 0.0
    ok = pass_rate >= threshold

    return {
        "skill": skill_name,
        "status": "PASS" if ok else "FAIL",
        "pass_rate": pass_rate,
        "passed": passed,
        "total": total,
        "threshold": threshold,
        "rows": results,
        "exit_code": 0 if ok else 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill routing eval runner")
    parser.add_argument("skill_dir", help="Path to skill directory (e.g. skills/openspace_skill)")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Min pass rate to exit 0 (default {DEFAULT_THRESHOLD})")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Output JSON (for gate_poll integration)")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    if not skill_dir.is_absolute():
        skill_dir = REPO_ROOT / skill_dir
    if not skill_dir.exists():
        print(f"[skill_eval] ERROR: {skill_dir} not found", file=sys.stderr)
        return 2

    result = eval_skill(skill_dir, args.threshold)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        rate_str = f"{result['pass_rate']:.0%}" if result["pass_rate"] is not None else "n/a"
        print(f"[skill_eval] {result['skill']} — {result['status']} {rate_str} "
              f"({result.get('passed', '?')}/{result.get('total', '?')}) "
              f"threshold={args.threshold:.0%}")
        if result["status"] == "FAIL":
            for r in result.get("rows", []):
                if not r["correct"]:
                    tag = "FP" if (r["did_match"] and not r["should_match"]) else "FN"
                    print(f"  [{tag}] intent='{r['intent']}' expected={r['expected']} matched={r['did_match']}")
        if result["status"] == "NO_EVAL":
            print(f"  {result['message']}")

    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
