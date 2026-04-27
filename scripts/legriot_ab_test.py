"""
legriot_ab_test.py -- Blind A/B model comparison for leGriot social/moderate routing.

Usage:
    python scripts/legriot_ab_test.py                   # run all 3 seeds, 3 models
    python scripts/legriot_ab_test.py --ideas "idea 1" "idea 2"   # custom seeds
    python scripts/legriot_ab_test.py --reveal workspace/ab-test-2026-04-26/  # show mapping

Decision rule (from legriot-quality-rubric.md):
    A model must outscore the incumbent by >= 3 points TOTAL across 3 seed posts
    (average gap >= 1.0 per post) to warrant a routing change recommendation.
    Less than that = no routing change.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
ORCH_DIR = REPO_ROOT / "orchestrator"
if str(ORCH_DIR) not in sys.path:
    sys.path.insert(0, str(ORCH_DIR))

# ---- Constants ---------------------------------------------------------------

# Models to test. Labels are assigned at runtime (shuffled so A/B/C != fixed model).
# incumbent is the current social/moderate routing target.
# COUNCIL_MODEL_REGISTRY keys (exact slugs -- verified against agents.py)
INCUMBENT_MODEL = "x-ai/grok-4"

CANDIDATE_MODELS = [
    "x-ai/grok-4",
    "anthropic/claude-sonnet-4.6",
    "mistralai/mistral-large-2512",
]

# Label order is always A, B, C. Mapping is written to .reveal/ only.
LABELS = ["A", "B", "C"]

DEFAULT_SEED_IDEAS = [
    (
        "The first AI decision you already made without knowing it",
        "LinkedIn",
    ),
    (
        "Why SMB owners overbuy AI tools and under-implement them",
        "LinkedIn",
    ),
    (
        "One constraint nobody has named yet",
        "X",
    ),
]

RUBRIC_PATH = REPO_ROOT / "docs" / "reference" / "legriot-quality-rubric.md"

SCORING_SHEET_TEMPLATE = """\
# leGriot A/B Scoring Sheet
Date: {date}
Session: {session_dir}

**STOP: Do NOT open .reveal/ until all scores are complete.**

Score each post 1-3 on each criterion. Total out of 15.
Criteria: Hook Strength | Voice Fidelity | Diagnosis Clarity | AI Slop Absence | CTA Sharpness

Decision rule: a model must outscore the incumbent by >= 3 points TOTAL
across all seed posts (average gap >= 1.0 per post) to warrant a routing
change. Less than that = no routing change warranted.

---

## Rubric Reference

{rubric_text}

---

## Scoring Grid

{scoring_grid}

---

## Totals (fill after scoring)

| Label | Total / {max_score} | Notes |
|-------|---------------------|-------|
{totals_rows}

Routing change warranted? (incumbent must be beaten by >= 3 pts total):
[ ] Yes -- winner: ___  [ ] No routing change

Run `python scripts/legriot_ab_test.py --reveal {session_dir}` to see model mapping.
"""


# ---- Core functions ----------------------------------------------------------

def _resolve_openrouter_id(model_id: str) -> str:
    """Prepend openrouter/ if not already present."""
    if model_id.startswith("openrouter/"):
        return model_id
    return f"openrouter/{model_id}"


def _run_legriot_for_model(idea: str, platform: str, model_id: str) -> str:
    """
    Run leGriot social crew with the given model patched in for social/moderate.

    Patches agents.select_llm so build_social_media_agent() gets the target model
    without modifying any routing config. The patch is scoped to this call only.

    Uses get_llm() to build the LLM object so the openrouter/ prefix and
    provider routing (Anthropic lock-in for Claude models) are handled correctly.
    """
    from agents import get_llm

    forced_llm = get_llm(model_id, temperature=0.7)

    # Capture the real function BEFORE patching so the closure doesn't recurse.
    import agents as _agents_mod
    _real_select_llm = _agents_mod.select_llm

    def _patched_select_llm(agent_role: str, task_complexity: str = "moderate", temperature: float = None):
        if agent_role == "social":
            return forced_llm
        return _real_select_llm(agent_role, task_complexity, temperature)

    request = f"Write a single {platform} post on this topic for Boubacar's audience: {idea}. One post only, no variations."

    with patch("agents.select_llm", side_effect=_patched_select_llm):
        from crews import build_social_crew
        crew = build_social_crew(request)
        result = crew.kickoff()

    raw = getattr(result, "raw", None)
    # Grok-4 can return a list of function-call objects instead of a string
    # when the model uses tool format unexpectedly. Normalize to string.
    if not isinstance(raw, str):
        if isinstance(raw, list):
            parts = []
            for item in raw:
                text = getattr(item, "content", None) or getattr(item, "text", None) or str(item)
                if text:
                    parts.append(str(text))
            raw = "\n".join(parts) if parts else str(result)
        else:
            raw = str(result) if raw is None else str(raw)
    # Extract DELIVERABLE block if present (QA agent output format)
    if "DELIVERABLE:" in raw:
        raw = raw.split("DELIVERABLE:", 1)[1].strip()
    return raw.strip()


def _build_scoring_grid(ideas: list[tuple[str, str]], labels: list[str]) -> str:
    rows = []
    for i, (idea, platform) in enumerate(ideas, 1):
        for label in labels:
            rows.append(
                f"### Idea {i} ({platform}): {idea[:60]}\n"
                f"**Post {label}** (file: idea-{i}-{label}.md)\n\n"
                "| Criterion | Score (1-3) | Notes |\n"
                "|-----------|-------------|-------|\n"
                "| Hook Strength | | |\n"
                "| Voice Fidelity | | |\n"
                "| Diagnosis Clarity | | |\n"
                "| AI Slop Absence | | |\n"
                "| CTA Sharpness | | |\n"
                f"**Subtotal {label}:** ___ / 15\n"
            )
        rows.append("---\n")
    return "\n".join(rows)


def _build_totals_rows(labels: list[str]) -> str:
    return "\n".join(f"| {l} | ___ | |" for l in labels)


def run_ab_test(
    ideas: Optional[list[tuple[str, str]]] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    ideas = ideas or DEFAULT_SEED_IDEAS
    if len(CANDIDATE_MODELS) != len(LABELS):
        raise ValueError("CANDIDATE_MODELS and LABELS must have the same length")

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if output_dir is None:
        output_dir = REPO_ROOT / "workspace" / f"ab-test-{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)

    reveal_dir = output_dir / ".reveal"
    reveal_dir.mkdir(exist_ok=True)

    # Assign labels -> models (stable order, not shuffled -- same run = same mapping)
    label_to_model = {label: model for label, model in zip(LABELS, CANDIDATE_MODELS)}
    model_to_label = {v: k for k, v in label_to_model.items()}

    # Write reveal mapping (kept in .reveal/ -- scorer must NOT open until done)
    reveal_path = reveal_dir / "model-map.json"
    reveal_path.write_text(
        json.dumps({"label_to_model": label_to_model, "incumbent": INCUMBENT_MODEL}, indent=2),
        encoding="utf-8",
    )

    rubric_text = RUBRIC_PATH.read_text(encoding="utf-8") if RUBRIC_PATH.exists() else "(rubric not found)"

    print(f"[ab-test] Session: {output_dir}")
    print(f"[ab-test] {len(ideas)} ideas x {len(CANDIDATE_MODELS)} models = {len(ideas) * len(CANDIDATE_MODELS)} drafts")
    print("[ab-test] Model mapping written to .reveal/ -- do not open until scoring complete")

    for i, (idea, platform) in enumerate(ideas, 1):
        for label, model_id in label_to_model.items():
            out_path = output_dir / f"idea-{i}-{label}.md"
            if out_path.exists():
                print(f"[ab-test] SKIP idea-{i}-{label}.md already exists (idempotent re-run)")
                continue
            print(f"[ab-test] Generating idea-{i}-{label}.md ({model_id})...")
            try:
                draft = _run_legriot_for_model(idea, platform, model_id)
                out_path.write_text(draft, encoding="utf-8")
                print(f"[ab-test] Written: {out_path.name} ({len(draft)} chars)")
            except Exception as exc:
                error_text = f"[GENERATION ERROR for idea {i} label {label}]\n{exc}"
                out_path.write_text(error_text, encoding="utf-8")
                print(f"[ab-test] ERROR on idea-{i}-{label}: {exc}")

    # Build scoring sheet
    grid = _build_scoring_grid(ideas, LABELS)
    totals = _build_totals_rows(LABELS)
    max_score = len(ideas) * 15
    sheet = SCORING_SHEET_TEMPLATE.format(
        date=date_str,
        session_dir=str(output_dir),
        rubric_text=rubric_text,
        scoring_grid=grid,
        max_score=max_score,
        totals_rows=totals,
    )
    sheet_path = output_dir / "scoring-sheet.md"
    if not sheet_path.exists():
        sheet_path.write_text(sheet, encoding="utf-8")
        print(f"[ab-test] Scoring sheet: {sheet_path}")

    print(f"\n[ab-test] Done. Score posts in {output_dir}/scoring-sheet.md")
    print(f"[ab-test] Then run: python scripts/legriot_ab_test.py --reveal {output_dir}")
    return output_dir


def reveal(session_dir: Path) -> None:
    reveal_path = session_dir / ".reveal" / "model-map.json"
    if not reveal_path.exists():
        print(f"[reveal] No model map found at {reveal_path}")
        return
    data = json.loads(reveal_path.read_text(encoding="utf-8"))
    label_to_model = data["label_to_model"]
    incumbent = data.get("incumbent", INCUMBENT_MODEL)

    print("\n=== leGriot A/B Reveal ===")
    print(f"Incumbent (current routing): {incumbent}\n")
    for label, model in label_to_model.items():
        marker = " <-- INCUMBENT" if model == incumbent else ""
        print(f"  Label {label} = {model}{marker}")

    print("\nDecision rule: winner must beat incumbent by >= 3 pts total across seed posts.")
    print("If no model clears +3 over incumbent, routing stays on current model.\n")


# ---- CLI ---------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="leGriot A/B blind model comparison")
    ap.add_argument("--ideas", nargs="+", help="Custom seed ideas (pairs: 'idea' 'platform')")
    ap.add_argument("--reveal", metavar="SESSION_DIR", help="Reveal model mapping after scoring")
    ap.add_argument("--out", metavar="DIR", help="Output directory (default: workspace/ab-test-DATE)")
    args = ap.parse_args(argv[1:])

    if args.reveal:
        reveal(Path(args.reveal))
        return 0

    ideas = None
    if args.ideas:
        if len(args.ideas) % 2 != 0:
            print("--ideas requires pairs: 'idea text' 'platform' ...")
            return 1
        ideas = [(args.ideas[i], args.ideas[i + 1]) for i in range(0, len(args.ideas), 2)]

    out = Path(args.out) if args.out else None
    run_ab_test(ideas=ideas, output_dir=out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
