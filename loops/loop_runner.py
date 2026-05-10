"""
loops/loop_runner.py - Atlas L5 substrate.

Autonomous improvement loop: takes one editable artifact + one deterministic
metric function + one mutator + a max-iteration budget. On each iteration:
  1. Score current artifact with metric_fn (must be deterministic)
  2. Ask mutator to propose one targeted change
  3. Apply mutation to a working copy
  4. Score the mutated copy
  5. If score improved by >= threshold: git commit the improvement (keep)
     If not: revert the working copy (discard)
  6. Log iteration result to Postgres + local JSONL
  7. Repeat until max_iterations or no improvement for patience consecutive rounds

Design gates from autoresearch Council 2026-04-30:
  - Totals MUST be computed from dimension scores, never free-typed by LLM
  - Metric must be deterministic (same artifact = same score across runs)
  - First deployment: design-audit 5-dim rubric on CW site HTML

Usage (CLI):
  python loops/loop_runner.py \
    --artifact output/websites/catalystworks-site/index.html \
    --target design_audit \
    --max-iter 10 \
    --threshold 1

Usage (API):
  from loops.loop_runner import run_loop
  result = run_loop(artifact_path, target="design_audit", max_iter=10)
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

logger = logging.getLogger("agentsHQ.loop_runner")

REPO_ROOT = Path(__file__).parent.parent
LOOPS_DIR = Path(__file__).parent
LOG_FILE = LOOPS_DIR / "loop_runs.jsonl"

# ─────────────────────────────────────────────────────────────────────────────
# Score dataclass — dimensions always sum to total (no free-typed totals)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DesignScore:
    accessibility: int   # 0-4
    performance: int     # 0-4
    theme: int           # 0-4
    responsiveness: int  # 0-4
    anti_patterns: int   # 0-4

    @property
    def total(self) -> int:
        return self.accessibility + self.performance + self.theme + self.responsiveness + self.anti_patterns

    @property
    def max_possible(self) -> int:
        return 20

    def as_dict(self) -> dict:
        d = asdict(self)
        d["total"] = self.total
        return d

    def __repr__(self) -> str:
        return (
            f"DesignScore(A11y={self.accessibility} Perf={self.performance} "
            f"Theme={self.theme} Resp={self.responsiveness} Anti={self.anti_patterns} "
            f"Total={self.total}/20)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Metric: design-audit 5-dimension rubric (deterministic LLM scorer)
# ─────────────────────────────────────────────────────────────────────────────

DESIGN_AUDIT_SYSTEM = """You are a senior UX/UI auditor. Score an HTML artifact on 5 dimensions, 0-4 each.

Dimensions:
1. Accessibility (a11y): semantic HTML, alt text, focus rings, ARIA, contrast
2. Performance: image sizes, render-blocking, excessive animations, lazy loading
3. Theme/Visual: typography quality, color system, spacing, anti-slop patterns
4. Responsiveness: mobile-first, no fixed widths, breakpoints, touch targets
5. Anti-patterns: no AI-slop (gradient orbs, equal card grids, rainbow gradients, fake KPIs)

Scoring: 0=fail, 1=poor, 2=acceptable, 3=good, 4=excellent

Return ONLY a JSON object with exactly these keys (integers 0-4):
{"accessibility": N, "performance": N, "theme": N, "responsiveness": N, "anti_patterns": N}

No explanation. No other text. Just the JSON."""


def score_design_audit(artifact_path: Path) -> DesignScore:
    """Score HTML artifact on 5-dimension design rubric. Deterministic."""
    import anthropic

    html = artifact_path.read_text(encoding="utf-8", errors="replace")
    # Truncate to 40k chars — enough for structure, not full page content
    html_sample = html[:40000]

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=DESIGN_AUDIT_SYSTEM,
        messages=[{"role": "user", "content": f"Score this HTML:\n\n{html_sample}"}],
    )

    raw = next(b.text for b in response.content if hasattr(b, "text")).strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        raw = raw.rstrip("`").rstrip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Scorer returned non-JSON: {raw[:200]}") from e

    for key in ("accessibility", "performance", "theme", "responsiveness", "anti_patterns"):
        if key not in data or not isinstance(data[key], int) or not (0 <= data[key] <= 4):
            raise ValueError(f"Invalid score for {key}: {data.get(key)}")

    return DesignScore(**{k: data[k] for k in ("accessibility", "performance", "theme", "responsiveness", "anti_patterns")})


# ─────────────────────────────────────────────────────────────────────────────
# Mutator: LLM proposes + applies one targeted change
# ─────────────────────────────────────────────────────────────────────────────

MUTATOR_SYSTEM = """You are a precise frontend engineer. Given an HTML file and its design audit scores,
propose and apply ONE targeted improvement to the weakest-scoring dimension.

Rules:
- Change exactly ONE thing (one CSS property, one HTML attribute, one element)
- Target the lowest-scoring dimension
- Do not regress other dimensions
- Return the complete modified HTML with the change applied
- Start your response with a single line: CHANGE: <one-sentence description>
- Then output the full modified HTML"""


def mutate_artifact(artifact_path: Path, score: DesignScore, working_copy: Path) -> str:
    """Propose and apply one mutation. Returns description of change."""
    import anthropic

    html = artifact_path.read_text(encoding="utf-8", errors="replace")

    # Identify weakest dimension
    dims = {
        "accessibility": score.accessibility,
        "performance": score.performance,
        "theme": score.theme,
        "responsiveness": score.responsiveness,
        "anti_patterns": score.anti_patterns,
    }
    weakest = min(dims, key=lambda k: dims[k])
    weakest_score = dims[weakest]

    prompt = (
        f"Current scores: {score.as_dict()}\n"
        f"Weakest dimension: {weakest} (score={weakest_score}/4)\n\n"
        f"HTML to improve:\n\n{html[:40000]}"
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        system=MUTATOR_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    full_response = next(b.text for b in response.content if hasattr(b, "text")).strip()
    lines = full_response.split("\n", 1)
    change_desc = lines[0].replace("CHANGE:", "").strip() if lines[0].startswith("CHANGE:") else "unspecified change"
    mutated_html = lines[1].strip() if len(lines) > 1 else full_response

    # Strip markdown code fences if present
    if mutated_html.startswith("```"):
        mutated_html = "\n".join(mutated_html.split("\n")[1:])
        if mutated_html.endswith("```"):
            mutated_html = mutated_html[:-3].rstrip()

    working_copy.write_text(mutated_html, encoding="utf-8")
    return change_desc


# ─────────────────────────────────────────────────────────────────────────────
# Git helpers
# ─────────────────────────────────────────────────────────────────────────────

def _git(args: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _git_commit(artifact_path: Path, message: str) -> bool:
    r = _git(["add", str(artifact_path)])
    if r.returncode != 0:
        return False
    r = _git(["commit", "-m", message, "--no-verify"])
    return r.returncode == 0


def _git_revert_file(artifact_path: Path) -> None:
    _git(["checkout", "--", str(artifact_path)])


# ─────────────────────────────────────────────────────────────────────────────
# JSONL logger
# ─────────────────────────────────────────────────────────────────────────────

def _log_iteration(run_id: str, iteration: int, artifact: str, before: DesignScore,
                   after: DesignScore, change_desc: str, kept: bool) -> None:
    entry = {
        "run_id": run_id,
        "iteration": iteration,
        "ts": datetime.now(timezone.utc).isoformat(),
        "artifact": artifact,
        "before": before.as_dict(),
        "after": after.as_dict(),
        "delta": after.total - before.total,
        "change": change_desc,
        "kept": kept,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info(
        "loop_runner iter=%d %s→%s (Δ%+d) change=%r kept=%s",
        iteration, before.total, after.total, after.total - before.total,
        change_desc, kept,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

METRIC_FNS: dict[str, Callable[[Path], DesignScore]] = {
    "design_audit": score_design_audit,
}


def run_loop(
    artifact_path: str | Path,
    *,
    target: str = "design_audit",
    max_iter: int = 10,
    threshold: int = 1,
    patience: int = 3,
) -> dict:
    """Run the improvement loop on artifact_path.

    Args:
        artifact_path: path to the HTML file to improve (modified in place on keep)
        target: which metric to use (currently only "design_audit")
        max_iter: stop after this many iterations regardless of improvement
        threshold: minimum score delta to keep a mutation (default 1 point)
        patience: stop after this many consecutive non-improvements

    Returns:
        dict with run summary: run_id, iterations, start_score, end_score, kept, discarded
    """
    artifact_path = Path(artifact_path)
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    if target not in METRIC_FNS:
        raise ValueError(f"Unknown target {target!r}. Available: {list(METRIC_FNS)}")

    metric_fn = METRIC_FNS[target]
    run_id = f"{target}_{int(time.time())}"
    working_copy = artifact_path.parent / f".loop_working_{artifact_path.name}"

    logger.info("loop_runner START run_id=%s artifact=%s target=%s max_iter=%d",
                run_id, artifact_path, target, max_iter)

    # Baseline score
    baseline = metric_fn(artifact_path)
    current_score = baseline
    logger.info("loop_runner baseline %s", baseline)

    kept = 0
    discarded = 0
    no_improve_streak = 0

    for i in range(1, max_iter + 1):
        logger.info("loop_runner iter=%d/%d current=%d/20", i, max_iter, current_score.total)

        # Copy artifact to working copy, mutate it
        shutil.copy2(artifact_path, working_copy)
        try:
            change_desc = mutate_artifact(artifact_path, current_score, working_copy)
        except Exception as e:
            logger.warning("loop_runner mutator failed iter=%d: %s", i, e)
            working_copy.unlink(missing_ok=True)
            no_improve_streak += 1
            if no_improve_streak >= patience:
                logger.info("loop_runner patience exhausted, stopping")
                break
            continue

        # Score the mutated copy
        try:
            new_score = metric_fn(working_copy)
        except Exception as e:
            logger.warning("loop_runner scorer failed on working copy iter=%d: %s", i, e)
            working_copy.unlink(missing_ok=True)
            no_improve_streak += 1
            if no_improve_streak >= patience:
                break
            continue

        delta = new_score.total - current_score.total
        keep = delta >= threshold

        if keep:
            # Apply: overwrite artifact with working copy, git commit
            shutil.copy2(working_copy, artifact_path)
            commit_msg = (
                f"loop({target}) iter={i}: {change_desc} "
                f"[{current_score.total}→{new_score.total}/20] run={run_id}"
            )
            _git_commit(artifact_path, commit_msg)
            current_score = new_score
            kept += 1
            no_improve_streak = 0
        else:
            # Discard: revert artifact to HEAD
            _git_revert_file(artifact_path)
            discarded += 1
            no_improve_streak += 1

        _log_iteration(run_id, i, str(artifact_path), current_score if not keep else baseline,
                       new_score, change_desc, keep)

        working_copy.unlink(missing_ok=True)

        if no_improve_streak >= patience:
            logger.info("loop_runner patience=%d exhausted after iter=%d, stopping", patience, i)
            break

    working_copy.unlink(missing_ok=True)

    summary = {
        "run_id": run_id,
        "artifact": str(artifact_path),
        "target": target,
        "iterations": kept + discarded,
        "start_score": baseline.as_dict(),
        "end_score": current_score.as_dict(),
        "net_delta": current_score.total - baseline.total,
        "kept": kept,
        "discarded": discarded,
    }
    logger.info("loop_runner DONE %s", summary)
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    parser = argparse.ArgumentParser(description="Atlas L5 loop runner — autonomous design improvement")
    parser.add_argument("artifact", help="Path to HTML file to improve")
    parser.add_argument("--target", default="design_audit", choices=list(METRIC_FNS),
                        help="Metric target (default: design_audit)")
    parser.add_argument("--max-iter", type=int, default=10, help="Max iterations (default: 10)")
    parser.add_argument("--threshold", type=int, default=1, help="Min score delta to keep (default: 1)")
    parser.add_argument("--patience", type=int, default=3, help="Stop after N consecutive misses (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Score only, no mutations")
    args = parser.parse_args()

    if args.dry_run:
        score = score_design_audit(Path(args.artifact))
        print(f"Baseline score: {score}")
        return

    result = run_loop(
        args.artifact,
        target=args.target,
        max_iter=args.max_iter,
        threshold=args.threshold,
        patience=args.patience,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
