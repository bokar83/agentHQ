"""
skills/transcript-style-dna/extract.py

Reverse-engineer a voice fingerprint from N reference texts.
Output: JSON style profile + a single personalized opener line.

Usage:
    python -m skills.transcript-style-dna.extract \
        --refs ref1.txt ref2.txt ref3.txt \
        --target-context "Salt Lake City roofer named Acme Roofing" \
        --out workspace/style-dna/acme.json
"""
import argparse
import json
import statistics
import sys
import re
from pathlib import Path

# Resolve repo root and add to sys.path so we can import orchestrator.llm_helpers
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Container vs dev import compatibility. The orc-crewai container flattens
# orchestrator/* to /app, so "from orchestrator.llm_helpers" fails there;
# the bare module name does. Local dev keeps the orchestrator package layout.
try:
    from orchestrator.llm_helpers import call_llm
except ModuleNotFoundError:
    sys.path.insert(0, "/app")
    from llm_helpers import call_llm

EXTRACTOR_MODEL = "anthropic/claude-sonnet-4.6"

SYSTEM_PROMPT = """You are a voice-fingerprint extractor. You read N reference texts written by or about a single person/business and return a strict JSON profile of their voice.

You also produce ONE personalized opener line written in THEIR voice that references one concrete thing from the references. The opener is for a cold outreach email or a discovery-call prep brief. It must sound like THEM, not like the sender.

Rules:
- Output JSON only, no prose, no markdown fences.
- Quote concrete details from the references in `vocabulary_markers` and `signature_moves`.
- The opener line is one sentence, max 25 words, written in second person if outreach (sender to prospect) or first person observation if prep brief. Decide from the target_context.
- Never invent facts not in the references. If references are sparse, say so in `confidence` and keep the opener generic-but-on-voice.
- ABSOLUTE BAN: no em-dashes (U+2014) and no en-dashes (U+2013) anywhere in any output field. Use a period, comma, semicolon, parentheses, or two hyphens (--) instead. This is a hard rule.
"""


def _strip_dashes(s: str) -> str:
    """Remove em-dashes and en-dashes from any string. Belt-and-suspenders against the ban."""
    if not isinstance(s, str):
        return s
    return s.replace("\u2014", ", ").replace("\u2013", ", ")


def _scrub(obj):
    """Recursively strip em/en-dashes from all string values in the profile."""
    if isinstance(obj, str):
        return _strip_dashes(obj)
    if isinstance(obj, list):
        return [_scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()}
    return obj

OUTPUT_SCHEMA = {
    "avg_sentence_length": "number, words per sentence",
    "sentence_length_distribution": {"p25": "number", "p50": "number", "p75": "number"},
    "hook_patterns": ["one or more of: question, stat, anecdote, contrarian, command, observation"],
    "vocabulary_markers": ["3-7 distinctive words/phrases that recur, drawn from the references"],
    "tone_signals": ["one or more of: formal, casual, urgent, reflective, confrontational, warm, technical, plainspoken"],
    "cadence": "one of: punchy, flowing, mixed",
    "signature_moves": ["1-3 recurring rhetorical devices observed"],
    "confidence": "one of: high, medium, low (based on reference quantity and consistency)",
    "opener_line": "single personalized first line in their voice, ≤25 words",
}


def _measure_lengths(texts: list[str]) -> dict:
    """Cheap deterministic sentence-length stats from raw text. The LLM will refine but this is a fact baseline."""
    sentences = []
    for t in texts:
        for s in re.split(r"[.!?]+\s+", t):
            s = s.strip()
            if s and len(s.split()) > 2:
                sentences.append(len(s.split()))
    if not sentences:
        return {"avg": 0, "p25": 0, "p50": 0, "p75": 0, "n": 0}
    sentences.sort()
    return {
        "avg": round(statistics.mean(sentences), 1),
        "p25": sentences[len(sentences) // 4],
        "p50": sentences[len(sentences) // 2],
        "p75": sentences[(len(sentences) * 3) // 4],
        "n": len(sentences),
    }


def extract(refs: list[str], target_context: str) -> dict:
    """Extract style profile + opener line from N reference texts."""
    if not refs:
        raise ValueError("at least one reference text required")

    measured = _measure_lengths(refs)

    refs_block = "\n\n===REF===\n\n".join(refs)
    user_msg = f"""TARGET CONTEXT
{target_context}

DETERMINISTIC MEASUREMENTS (use these as ground truth for sentence length; do not contradict)
{json.dumps(measured)}

REFERENCE TEXTS ({len(refs)} total)
{refs_block}

OUTPUT SCHEMA
{json.dumps(OUTPUT_SCHEMA, indent=2)}

Return JSON only."""

    response = call_llm(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        model=EXTRACTOR_MODEL,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    # Strip code fences if the model wraps anyway
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    profile = json.loads(raw)
    profile = _scrub(profile)
    profile["_measured"] = measured
    profile["_target_context"] = _strip_dashes(target_context)
    profile["_n_refs"] = len(refs)
    return profile


def main():
    ap = argparse.ArgumentParser(description="Extract voice fingerprint from N reference texts.")
    ap.add_argument("--refs", nargs="+", required=True, help="paths to reference text files")
    ap.add_argument("--target-context", required=True, help="who this profile is for, e.g. 'Salt Lake City roofer named Acme'")
    ap.add_argument("--out", required=True, help="output JSON path")
    args = ap.parse_args()

    refs = []
    for p in args.refs:
        path = Path(p)
        if not path.exists():
            print(f"ERROR: {p} not found", file=sys.stderr)
            sys.exit(1)
        refs.append(path.read_text(encoding="utf-8"))

    profile = extract(refs, args.target_context)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"OK: wrote {out_path}")
    print(f"Opener: {profile.get('opener_line', '(none)')}")
    print(f"Confidence: {profile.get('confidence', '(unknown)')}")


if __name__ == "__main__":
    main()
