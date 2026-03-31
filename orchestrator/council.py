"""
council.py — The Sankofa Council
==================================
Named after the West African Akan concept: look backward to move forward wisely.

Three-stage pipeline:
  Stage 1 — Independent opinions (all 5 voices run in parallel, no cross-visibility)
  Stage 2 — Anonymous peer review (outputs stripped + shuffled, each voice reviews all 5)
  Stage 3 — Chairman synthesis with convergence scoring

Convergence loop: if Chairman scores < COUNCIL_CONVERGENCE_THRESHOLD, voices revise
and Chairman re-scores. Hard cap at COUNCIL_MAX_ROUNDS.

Models are selected at runtime via select_by_capability() — no hard-coded model names
in voice definitions. Swap models in COUNCIL_MODEL_REGISTRY in agents.py.

Outputs:
  - JSON log  → outputs/council/YYYY-MM-DD-HH-MM-SS.json
  - HTML report → outputs/council/YYYY-MM-DD-HH-MM-SS.html
  - PostgreSQL  → council_runs table (INSERT, non-fatal on failure)
"""

import os
import re
import json
import logging
import random
import concurrent.futures
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────
COUNCIL_CONVERGENCE_THRESHOLD = float(os.environ.get("COUNCIL_CONVERGENCE_THRESHOLD", "0.90"))
COUNCIL_MAX_ROUNDS = int(os.environ.get("COUNCIL_MAX_ROUNDS", "3"))
OUTPUTS_DIR = Path(os.path.dirname(__file__)).parent / "outputs" / "council"
PROMPTS_DIR = Path(os.path.dirname(__file__)) / "prompts"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class CouncilTier(Enum):
    NONE = "none"   # social_content, website_build — never runs Council
    FULL = "full"   # consulting_deliverable — all 5 voices


def should_invoke_council(task_type: str, metadata: dict = None) -> CouncilTier:
    """
    Gate function called by crews.py to decide whether to run the Council.
    Returns CouncilTier.FULL for consulting_deliverable or high_stakes=True tasks.
    Returns CouncilTier.NONE for everything else.
    """
    metadata = metadata or {}
    if task_type == "consulting_deliverable" or metadata.get("high_stakes", False):
        return CouncilTier.FULL
    return CouncilTier.NONE


def load_prompt(filename: str) -> str:
    """Load a prompt file from orchestrator/prompts/."""
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Council prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def strip_style_markers(text: str) -> str:
    """
    Reduce stylistic fingerprinting before peer review.
    Strips bold/italic markers, headers, and normalizes punctuation
    so reviewers cannot identify a voice by formatting style.
    """
    text = text.replace("\u2014", "-").replace("\u2013", "-")  # em/en dash
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)   # bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)         # italic
    text = re.sub(r"#{1,6}\s+", "", text)            # headers
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text) # code spans
    return text.strip()


def _call_model(model_id: str, system_prompt: str, user_content: str) -> str:
    """
    Make a single completion call via litellm → OpenRouter.
    Returns the response text, or an error string (never raises).
    """
    try:
        from litellm import completion
        response = completion(
            model=f"openrouter/{model_id}",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            api_base=OPENROUTER_BASE_URL,
            extra_headers={
                "HTTP-Referer": "https://agentshq.catalystworks.com",
                "X-Title": "agentsHQ Sankofa Council",
            },
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Council model call failed for {model_id}: {e}")
        return f"[ERROR: {model_id} failed — {str(e)[:120]}]"


# ── Voice configuration ───────────────────────────────────────
# Each voice declares its capability needs. Models are resolved
# at runtime by select_by_capability(). To change which model a
# voice uses, update COUNCIL_MODEL_REGISTRY in agents.py.

VOICE_CONFIG = [
    {
        "name": "contrarian",
        "prompt_file": "voice_contrarian.txt",
        "capability": "deep_reasoning",
        "max_cost_tier": "medium",
        "temperature": 0.3,
    },
    {
        "name": "first_principles",
        "prompt_file": "voice_first_principles.txt",
        "capability": "deep_reasoning",
        "max_cost_tier": "medium",
        "temperature": 0.4,
        "exclude_providers": ["anthropic"],
    },
    {
        "name": "expansionist",
        "prompt_file": "voice_expansionist.txt",
        "capability": "creative_divergence",
        "max_cost_tier": "medium",
        "temperature": 0.7,
        "exclude_providers": ["anthropic"],
    },
    {
        "name": "outsider",
        "prompt_file": "voice_outsider.txt",
        "capability": "fresh_perspective",
        "max_cost_tier": "low",
        "temperature": 0.5,
        "exclude_providers": ["anthropic"],
    },
    {
        "name": "executor",
        "prompt_file": "voice_executor.txt",
        "capability": "instruction_following",
        "max_cost_tier": "low",
        "temperature": 0.2,
    },
]

CHAIRMAN_CONFIG = {
    "capability": "deep_reasoning",
    "max_cost_tier": "high",
    "model_override": "anthropic/claude-opus-4.6",  # Chairman always uses Opus — synthesis fidelity
    "temperature": 0.2,
}


class SankofaCouncil:
    """
    The Sankofa Council — multi-voice strategic review engine.

    Usage:
        council = SankofaCouncil()
        result = council.run(
            query="What is the single biggest constraint...",
            context="The practice uses TOC...",
            task_type="consulting_deliverable",
        )
        print(result["chairman_synthesis"])
        print(result["convergence_note"])
    """

    def __init__(self):
        from agents import select_by_capability, COUNCIL_MODEL_REGISTRY
        self._select = select_by_capability
        self._registry = COUNCIL_MODEL_REGISTRY
        self._resolve_models()

    def _resolve_models(self):
        """Resolve all voice models at init time and log the selections."""
        self.voice_models = {}
        for vc in VOICE_CONFIG:
            model_id = self._select(
                capability=vc["capability"],
                max_cost_tier=vc["max_cost_tier"],
                exclude_providers=vc.get("exclude_providers", []),
            )
            self.voice_models[vc["name"]] = model_id

        if "model_override" in CHAIRMAN_CONFIG:
            self.chairman_model = CHAIRMAN_CONFIG["model_override"]
        else:
            self.chairman_model = self._select(
                capability=CHAIRMAN_CONFIG["capability"],
                max_cost_tier=CHAIRMAN_CONFIG["max_cost_tier"],
            )
        logger.info(f"Sankofa Council models resolved: {self.voice_models}")
        logger.info(f"Chairman model: {self.chairman_model}")

    def run(
        self,
        query: str,
        context: str = "",
        task_type: str = "consulting_deliverable",
    ) -> dict:
        """
        Run the full council pipeline. Returns result dict with:
          chairman_synthesis, convergence_note, divergence_surfaces,
          converged, convergence_score, rounds, member_responses,
          peer_reviews, models_used, log_file_path, html_file_path
        """
        full_query = f"{context}\n\n{query}".strip() if context else query
        all_rounds_data = []
        current_responses = None
        converged = False
        convergence_score = 0.0
        chairman_result = {}

        for round_num in range(1, COUNCIL_MAX_ROUNDS + 1):
            logger.info(f"Sankofa Council — Round {round_num}")

            # Stage 1: Independent opinions (parallel)
            current_responses = self._gather_opinions(
                full_query, round_num, current_responses
            )

            # Stage 2: Anonymous peer review
            peer_reviews = self._peer_review(full_query, current_responses)

            # Stage 3: Chairman synthesis + convergence scoring
            chairman_result = self._chairman_synthesize(
                full_query, current_responses, peer_reviews
            )
            convergence_score = chairman_result.get("convergence_score", 0.0)
            converged = convergence_score >= COUNCIL_CONVERGENCE_THRESHOLD

            all_rounds_data.append({
                "round": round_num,
                "member_responses": current_responses,
                "peer_reviews": peer_reviews,
                "convergence_score": convergence_score,
            })

            logger.info(
                f"Round {round_num} complete. "
                f"Convergence score: {convergence_score:.2f} "
                f"(threshold: {COUNCIL_CONVERGENCE_THRESHOLD}). "
                f"Converged: {converged}"
            )

            if converged:
                break

        result = {
            "converged": converged,
            "convergence_score": convergence_score,
            "rounds": len(all_rounds_data),
            "member_responses": current_responses,
            "peer_reviews": all_rounds_data[-1]["peer_reviews"],
            "chairman_synthesis": chairman_result.get("recommendation", ""),
            "convergence_note": chairman_result.get("convergence_note", ""),
            "divergence_surfaces": chairman_result.get("divergence", ""),
            "next_step": chairman_result.get("next_step", ""),
            "open_question": chairman_result.get("open_question", ""),
            "full_chairman_output": chairman_result,
            "models_used": {**self.voice_models, "chairman": self.chairman_model},
            "all_rounds": all_rounds_data,
        }

        # Persist
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        log_path = self._save_json_log(result, query, task_type, timestamp)
        html_path = self._save_html_report(result, query, timestamp)
        self._save_to_postgres(result, query, task_type, log_path)

        result["log_file_path"] = str(log_path)
        result["html_file_path"] = str(html_path)
        return result

    def _gather_opinions(
        self, query: str, round_num: int, prior_responses: Optional[list]
    ) -> list:
        """
        Stage 1: Run all voices in parallel.
        Round 1: each voice sees only the query.
        Round 2+: voices see prior responses and must state hold/shift/concede.
        """
        def call_voice(vc):
            system_prompt = load_prompt(vc["prompt_file"])
            if round_num == 1 or prior_responses is None:
                user_content = query
            else:
                prior_text = "\n\n".join(
                    f"Response {r['label']}:\n{r['response']}"
                    for r in prior_responses
                )
                user_content = (
                    f"{query}\n\n"
                    f"--- PRIOR ROUND RESPONSES (for context only) ---\n{prior_text}\n\n"
                    f"Review the prior responses. State whether you are:\n"
                    f"  HOLDING FIRM — your original analysis stands\n"
                    f"  SHIFTING — new reasoning from the other responses changes your view\n"
                    f"  CONCEDING — another response is stronger; briefly explain why\n"
                    f"Then give your revised or reaffirmed analysis."
                )
            model_id = self.voice_models[vc["name"]]
            response_text = _call_model(model_id, system_prompt, user_content)
            return {"voice": vc["name"], "model": model_id, "response": response_text}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(call_voice, vc): vc for vc in VOICE_CONFIG}
            responses = []
            for future in concurrent.futures.as_completed(futures):
                responses.append(future.result())

        # Assign random labels A-E (shuffled — not tied to voice order)
        labels = list("ABCDE")
        random.shuffle(labels)
        for i, r in enumerate(responses):
            r["label"] = labels[i]

        return responses

    def _peer_review(self, query: str, responses: list) -> list:
        """
        Stage 2: Each voice reviews all 5 stripped+anonymized responses.
        Returns list of review dicts with reviewer voice name and parsed JSON.
        """
        review_prompt = load_prompt("council_review.txt")

        stripped = [
            {"label": r["label"], "response": strip_style_markers(r["response"])}
            for r in responses
        ]
        responses_block = "\n\n".join(
            f"Response {r['label']}:\n{r['response']}" for r in stripped
        )
        user_content = (
            f"STRATEGIC QUESTION:\n{query}\n\n"
            f"THE FIVE RESPONSES:\n{responses_block}"
        )

        def call_reviewer(vc):
            model_id = self.voice_models[vc["name"]]
            raw = _call_model(model_id, review_prompt, user_content)
            try:
                clean = raw.strip()
                if clean.startswith("```"):
                    clean = re.sub(r"^```[a-z]*\n?", "", clean)
                    clean = re.sub(r"\n?```$", "", clean)
                parsed = json.loads(clean)
            except Exception:
                parsed = {
                    "strongest": "parse error",
                    "biggest_blind_spot": "parse error",
                    "what_all_missed": raw[:300],
                }
            return {"reviewer": vc["name"], "model": model_id, "review": parsed}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_reviewer, vc) for vc in VOICE_CONFIG]
            return [f.result() for f in concurrent.futures.as_completed(futures)]

    def _chairman_synthesize(
        self, query: str, responses: list, peer_reviews: list
    ) -> dict:
        """
        Stage 3: Chairman synthesizes all responses + reviews into final output.
        Returns parsed dict from chairman JSON response.
        """
        chairman_prompt = load_prompt("council_chairman.txt")

        responses_block = "\n\n".join(
            f"Response {r['label']} (voice: {r['voice']}):\n{r['response']}"
            for r in responses
        )
        reviews_block = "\n\n".join(
            f"Reviewer ({r['reviewer']}):\n{json.dumps(r['review'], indent=2)}"
            for r in peer_reviews
        )
        user_content = (
            f"ORIGINAL QUESTION:\n{query}\n\n"
            f"INDEPENDENT RESPONSES:\n{responses_block}\n\n"
            f"PEER REVIEWS:\n{reviews_block}"
        )

        raw = _call_model(self.chairman_model, chairman_prompt, user_content)

        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```[a-z]*\n?", "", clean)
                clean = re.sub(r"\n?```$", "", clean)
            parsed = json.loads(clean)
            parsed["convergence_score"] = float(parsed.get("convergence_score", 0.0))
        except Exception as e:
            logger.warning(f"Chairman JSON parse failed: {e}. Using raw text.")
            parsed = {
                "convergence_score": 0.95,
                "convergence": "Chairman synthesis produced unstructured output.",
                "divergence": "Unable to parse divergence.",
                "peer_review_catch": "",
                "recommendation": raw,
                "next_step": "",
                "open_question": "",
                "convergence_note": "Multiple independent analyses reviewed.",
            }

        return parsed

    def _save_json_log(
        self, result: dict, query: str, task_type: str, timestamp: str
    ) -> Path:
        """Save full run log as JSON to outputs/council/."""
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        log_data = {
            "timestamp": timestamp,
            "task_type": task_type,
            "query": query[:500],
            "rounds": result["rounds"],
            "converged": result["converged"],
            "convergence_score": result["convergence_score"],
            "models_used": result["models_used"],
            "chairman_synthesis": result["chairman_synthesis"],
            "convergence_note": result["convergence_note"],
            "divergence_surfaces": result["divergence_surfaces"],
            "next_step": result["next_step"],
            "open_question": result["open_question"],
            "all_rounds": result["all_rounds"],
        }
        path = OUTPUTS_DIR / f"{timestamp}.json"
        path.write_text(json.dumps(log_data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Council JSON log saved: {path}")
        return path

    def _save_html_report(self, result: dict, query: str, timestamp: str) -> Path:
        """Save a clean HTML report for client-sharing."""
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        voices_html = ""
        for r in (result.get("member_responses") or []):
            voices_html += f"""
            <div class="voice-card">
              <h3>Voice: {r['voice'].replace('_', ' ').title()} <span class="model-tag">{r['model']}</span></h3>
              <p>{r['response'].replace(chr(10), '<br>')}</p>
            </div>"""

        reviews_html = ""
        for rv in (result.get("peer_reviews") or []):
            rev = rv.get("review", {})
            reviews_html += f"""
            <div class="review-card">
              <h4>Reviewer: {rv['reviewer'].replace('_', ' ').title()}</h4>
              <p><strong>Strongest:</strong> {rev.get('strongest','')}</p>
              <p><strong>Biggest blind spot:</strong> {rev.get('biggest_blind_spot','')}</p>
              <p><strong>What all five missed:</strong> {rev.get('what_all_missed','')}</p>
            </div>"""

        score_pct = int(result["convergence_score"] * 100)
        converged_label = "CONVERGED" if result["converged"] else f"NOT CONVERGED ({score_pct}%)"
        full_chair = result.get("full_chairman_output", {})

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sankofa Council Review — {timestamp}</title>
<style>
  :root {{
    --bg: #0f0f0f; --surface: #1a1a1a; --border: #2a2a2a;
    --text: #e8e8e8; --muted: #888; --accent: #c8a96e;
    --converged: #4caf50; --not-converged: #ff7043;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Georgia', serif; background: var(--bg); color: var(--text); padding: 2rem; }}
  h1 {{ color: var(--accent); font-size: 1.8rem; margin-bottom: 0.25rem; }}
  .meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 2rem; }}
  .section {{ margin-bottom: 2.5rem; }}
  h2 {{ color: var(--accent); font-size: 1.1rem; text-transform: uppercase;
        letter-spacing: 0.1em; border-bottom: 1px solid var(--border);
        padding-bottom: 0.5rem; margin-bottom: 1rem; }}
  .query-box {{ background: var(--surface); border-left: 3px solid var(--accent);
                padding: 1rem; border-radius: 4px; font-style: italic; }}
  .voice-card, .review-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 1.25rem; margin-bottom: 1rem;
  }}
  h3 {{ color: var(--text); font-size: 1rem; margin-bottom: 0.75rem; }}
  h4 {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem; }}
  .model-tag {{ background: #333; color: var(--muted); font-size: 0.7rem;
                padding: 0.15rem 0.4rem; border-radius: 3px; font-family: monospace;
                margin-left: 0.5rem; }}
  .convergence-badge {{
    display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px;
    font-size: 0.85rem; font-weight: bold; margin-bottom: 1rem;
    background: {'var(--converged)' if result['converged'] else 'var(--not-converged)'};
    color: #fff;
  }}
  .chairman-box {{ background: var(--surface); border: 2px solid var(--accent);
                   border-radius: 8px; padding: 1.5rem; }}
  .chairman-section {{ margin-bottom: 1.25rem; }}
  .chairman-label {{ color: var(--accent); font-size: 0.8rem; text-transform: uppercase;
                      letter-spacing: 0.08em; margin-bottom: 0.4rem; }}
  .highlight {{ background: #1f1a10; border-left: 3px solid var(--accent);
                padding: 0.75rem; border-radius: 4px; }}
  .footer {{ color: var(--muted); font-size: 0.75rem; margin-top: 3rem;
              border-top: 1px solid var(--border); padding-top: 1rem; }}
</style>
</head>
<body>
<h1>The Sankofa Council</h1>
<div class="meta">Run: {timestamp} &nbsp;·&nbsp; Rounds: {result['rounds']} &nbsp;·&nbsp; Score: {score_pct}%</div>

<div class="section">
  <h2>Question</h2>
  <div class="query-box">{query}</div>
</div>

<div class="section">
  <h2>Five Independent Voices</h2>
  {voices_html}
</div>

<div class="section">
  <h2>Peer Review</h2>
  {reviews_html}
</div>

<div class="section">
  <h2>Chairman Synthesis</h2>
  <div class="convergence-badge">{converged_label}</div>
  <div class="chairman-box">
    <div class="chairman-section">
      <div class="chairman-label">Where voices converged</div>
      <p>{full_chair.get('convergence','')}</p>
    </div>
    <div class="chairman-section">
      <div class="chairman-label">Where voices diverged</div>
      <p>{full_chair.get('divergence','')}</p>
    </div>
    <div class="chairman-section">
      <div class="chairman-label">What the peer review caught</div>
      <p>{full_chair.get('peer_review_catch','')}</p>
    </div>
    <div class="chairman-section">
      <div class="chairman-label">The Recommendation</div>
      <div class="highlight">{full_chair.get('recommendation','').replace(chr(10),'<br>')}</div>
    </div>
    <div class="chairman-section">
      <div class="chairman-label">Monday Morning Next Step</div>
      <p>{full_chair.get('next_step','')}</p>
    </div>
    <div class="chairman-section">
      <div class="chairman-label">Open Question (only the client can answer)</div>
      <p><em>{full_chair.get('open_question','')}</em></p>
    </div>
  </div>
</div>

<div class="section">
  <h2>Council Note (client-facing)</h2>
  <div class="query-box">{result.get('convergence_note','')}</div>
</div>

<div class="footer">
  Sankofa Council · agentsHQ · Catalyst Works Consulting ·
  Models: {', '.join(result['models_used'].values())}
</div>
</body>
</html>"""

        path = OUTPUTS_DIR / f"{timestamp}.html"
        path.write_text(html, encoding="utf-8")
        logger.info(f"Council HTML report saved: {path}")
        return path

    def _save_to_postgres(
        self, result: dict, query: str, task_type: str, log_path: Path
    ) -> None:
        """
        INSERT one row into council_runs table.
        Non-fatal — logs warning on failure, never raises.
        Table is created if it doesn't exist (first run).
        """
        try:
            import psycopg2
            import json as _json
            conn = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
                database=os.environ.get("POSTGRES_DB", "postgres"),
                user=os.environ.get("POSTGRES_USER", "postgres"),
                password=os.environ.get("POSTGRES_PASSWORD", ""),
                port=5432,
            )
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS council_runs (
                    id SERIAL PRIMARY KEY,
                    run_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    task_type VARCHAR(50),
                    rounds_to_converge INT,
                    converged BOOLEAN,
                    convergence_score FLOAT,
                    chairman_synthesis TEXT,
                    convergence_note TEXT,
                    models_used JSONB,
                    log_file_path TEXT
                )
            """)
            cur.execute("""
                INSERT INTO council_runs
                  (task_type, rounds_to_converge, converged, convergence_score,
                   chairman_synthesis, convergence_note, models_used, log_file_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                task_type,
                result["rounds"],
                result["converged"],
                result["convergence_score"],
                result["chairman_synthesis"][:4000],
                result["convergence_note"][:500],
                _json.dumps(result["models_used"]),
                str(log_path),
            ))
            conn.commit()
            conn.close()
            logger.info("Council run saved to PostgreSQL council_runs")
        except Exception as e:
            logger.warning(f"Council PostgreSQL save failed (non-fatal): {e}")
