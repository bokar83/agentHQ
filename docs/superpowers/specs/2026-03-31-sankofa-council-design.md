# The Sankofa Council — Design Spec
**Date:** 2026-03-31  
**Status:** Approved for implementation  
**Author:** Boubacar Barry / Claude Code

---

## What We're Building

A strategic multi-voice review layer for agentsHQ called **The Sankofa Council** — named after the West African Akan concept of looking backward to move forward wisely. When activated, five independent analytical voices examine a consulting question from distinct perspectives, review each other's work anonymously, and iterate toward convergence before a Chairman synthesizes the final output.

The Council activates on `consulting_deliverable` tasks and any task flagged `high_stakes: true`. It never runs on social content, website builds, or routine writing.

---

## Why We're Building It

A single model, no matter how well-prompted, has one reasoning path. For TOC diagnostics and client strategy work, a missed reframe or unchallenged assumption doesn't just weaken a deliverable — it can send a client in the wrong direction. The Council is insurance against *confident wrongness*, which is the most dangerous kind of output.

The virtual test (retention/turnover scenario) confirmed the Council surfaces things a single agent misses:
- Manager clustering as the real locus of mid-level departures
- The distinction between *how many* people left vs *who specifically* left
- The CEO-as-constraint reframe — the sharpest diagnostic line came from the Outsider's cold read

---

## The Five Voices + Chairman

Each voice is a fixed analytical *posture*, not a fixed model. Models rotate underneath via capability-based selection.

| Voice | Job | What It Catches |
|-------|-----|-----------------|
| **The Contrarian** | Find the fatal flaw. Assume failure. | Hidden risks, optimistic assumptions, "sounds good" traps |
| **The First Principles Thinker** | Strip assumptions. Reframe from zero. | Wrong variable optimization, inherited framing nobody questioned |
| **The Expansionist** | Hunt for upside being missed. | Thinking-too-small blind spots, adjacent opportunities |
| **The Outsider** | Zero context. Respond to what's literally there. | Curse of knowledge, invisible assumptions |
| **The Executor** | What happens Monday morning? | Brilliant plans with no execution path |
| **The Chairman** | Synthesize. Surface convergence AND divergence. | Produces final deliverable — separate invocation, not a council member |

---

## Architecture

### Three Stages Per Run

```
Stage 1 — Independent Opinions (parallel, no cross-visibility)
  All 5 voices answer the query simultaneously.
  No voice sees any other voice's output.

Stage 2 — Anonymous Peer Review
  Outputs stripped of stylistic markers (em-dashes, bold, headers).
  Labeled A-E randomly (shuffled each run — not tied to voice identity).
  Each voice reviews all 5 outputs and answers:
    1. Which response is strongest and why?
    2. Which has the biggest blind spot?
    3. What did ALL FIVE miss? (most important question)

Stage 3 — Chairman Synthesis
  Separate model invocation — Chairman is NOT a council member.
  Receives: original query + all 5 responses + all 5 peer reviews.
  Scores convergence. If ≥ threshold → synthesize and ship.
  If below threshold → trigger next round (max 3 rounds).
  Surfaces divergence explicitly — never hides it.
```

### Convergence Loop

```python
COUNCIL_CONVERGENCE_THRESHOLD = 0.90  # configurable
COUNCIL_MAX_ROUNDS = 3                 # hard cap — no infinite loops
```

- Round 1: All voices give independent opinions
- Round 2 (if needed): Each voice reads Round 1 outputs + peer reviews, revises position — must state whether holding firm, shifting, or conceding and why
- Round 3 (if needed): Only divergent voices re-argue
- If not converged after Round 3: Chairman surfaces the tension explicitly. Persistent disagreement is a signal, not a failure.

Convergence scoring: Chairman evaluates whether key recommendations align on critical variables — not whether all prose is similar.

---

## Dynamic Model Selection (No Hard-Coded Models)

### The Problem With Hard-Coding
The LLM landscape changes weekly. Hard-coding `claude-opus-4.6` to The Contrarian means we're frozen in time. As better/cheaper models emerge, we want automatic access to them without touching Council code.

### The Solution: Capability-Based Selection

Each voice declares *what it needs*, not *which model*. A `select_by_capability()` function resolves that to the current best-fit model from the live registry.

**Capability tags** (each model in registry gets these):

```python
CAPABILITIES = {
    "deep_reasoning",      # sustained analytical depth, multi-step logic
    "creative_divergence", # generates non-obvious angles, lateral thinking
    "fast",                # low latency, high throughput
    "cost_efficient",      # low cost per token
    "long_context",        # handles 200K+ tokens reliably
    "instruction_following", # precise adherence to structured output formats
    "fresh_perspective",   # different training distribution from Anthropic models
}
```

**Voice capability requirements:**

| Voice | Primary Capability | Cost Tier |
|-------|-------------------|-----------|
| Contrarian | `deep_reasoning` | medium |
| First Principles | `deep_reasoning` | medium |
| Expansionist | `creative_divergence` | low-medium |
| Outsider | `fresh_perspective` | low (intentionally lightweight) |
| Executor | `instruction_following` | medium |
| Chairman | `deep_reasoning` + `instruction_following` | high |

**Current registry (pulled from OpenRouter 2026-03-31):**

```python
MODEL_REGISTRY = {
    # ── Anthropic ─────────────────────────────────────────────────
    "anthropic/claude-opus-4.6": {
        "capabilities": ["deep_reasoning", "long_context", "instruction_following"],
        "cost_tier": "high",
        "input_per_mtok": 5.00,
        "output_per_mtok": 25.00,
        "context_k": 1000,
        "notes": "Best for Chairman synthesis and deep diagnostic work. 1M context."
    },
    "anthropic/claude-sonnet-4.6": {
        "capabilities": ["deep_reasoning", "instruction_following", "long_context"],
        "cost_tier": "medium",
        "input_per_mtok": 3.00,
        "output_per_mtok": 15.00,
        "context_k": 1000,
        "notes": "Frontier Sonnet. Strong reasoning + agents. Default workhorse."
    },
    "anthropic/claude-haiku-4.5": {
        "capabilities": ["fast", "cost_efficient", "instruction_following"],
        "cost_tier": "low",
        "input_per_mtok": 1.00,
        "output_per_mtok": 5.00,
        "context_k": 200,
        "notes": "Fast, cheap. Good for Outsider voice — simulates naive reader."
    },
    # ── Google ────────────────────────────────────────────────────
    "google/gemini-3.1-pro-preview": {
        "capabilities": ["deep_reasoning", "long_context", "fresh_perspective"],
        "cost_tier": "medium-high",
        "input_per_mtok": 2.00,
        "output_per_mtok": 12.00,
        "context_k": 1048,
        "notes": "Google frontier. Different training distribution = genuine divergence from Claude."
    },
    "google/gemini-2.5-pro": {
        "capabilities": ["deep_reasoning", "long_context", "fresh_perspective"],
        "cost_tier": "medium",
        "input_per_mtok": 1.25,
        "output_per_mtok": 10.00,
        "context_k": 1048,
        "notes": "Strong reasoning. Good value vs Gemini 3.1 Pro if cost is a factor."
    },
    "google/gemini-2.5-flash": {
        "capabilities": ["fast", "cost_efficient", "fresh_perspective"],
        "cost_tier": "low",
        "input_per_mtok": 0.30,
        "output_per_mtok": 2.50,
        "context_k": 1048,
        "notes": "Fast Google model. Good Outsider voice — different perspective, low cost."
    },
    # ── OpenAI ────────────────────────────────────────────────────
    "openai/gpt-5.1": {
        "capabilities": ["deep_reasoning", "long_context", "fresh_perspective", "instruction_following"],
        "cost_tier": "medium",
        "input_per_mtok": 1.25,
        "output_per_mtok": 10.00,
        "context_k": 400,
        "notes": "OpenAI frontier. Genuinely different training. Strong for Expansionist."
    },
    "openai/gpt-4.1": {
        "capabilities": ["deep_reasoning", "instruction_following", "long_context"],
        "cost_tier": "medium",
        "input_per_mtok": 2.00,
        "output_per_mtok": 8.00,
        "context_k": 1047,
        "notes": "GPT-4.1 with 1M context. Reliable instruction following."
    },
    "openai/o4-mini": {
        "capabilities": ["deep_reasoning", "cost_efficient"],
        "cost_tier": "low-medium",
        "input_per_mtok": 1.10,
        "output_per_mtok": 4.40,
        "context_k": 200,
        "notes": "OpenAI reasoning model. Strong analytical depth at reasonable cost."
    },
    # ── DeepSeek ──────────────────────────────────────────────────
    "deepseek/deepseek-r1-0528": {
        "capabilities": ["deep_reasoning", "cost_efficient", "fresh_perspective"],
        "cost_tier": "very_low",
        "input_per_mtok": 0.45,
        "output_per_mtok": 2.15,
        "context_k": 163,
        "notes": "DeepSeek R1 reasoning model. Exceptional value. Good Contrarian — will find flaws."
    },
    "deepseek/deepseek-v3.2": {
        "capabilities": ["cost_efficient", "instruction_following", "fresh_perspective"],
        "cost_tier": "very_low",
        "input_per_mtok": 0.26,
        "output_per_mtok": 0.38,
        "context_k": 163,
        "notes": "Extremely cheap. Different architecture. Good Outsider or Executor at low cost."
    },
    # ── xAI ───────────────────────────────────────────────────────
    "x-ai/grok-4": {
        "capabilities": ["deep_reasoning", "fresh_perspective", "creative_divergence"],
        "cost_tier": "medium",
        "input_per_mtok": 3.00,
        "output_per_mtok": 15.00,
        "context_k": 256,
        "notes": "Grok 4. Different perspective, known for unconventional takes. Good Expansionist."
    },
    # ── Mistral ───────────────────────────────────────────────────
    "mistralai/mistral-large-2512": {
        "capabilities": ["instruction_following", "cost_efficient", "fresh_perspective"],
        "cost_tier": "low",
        "input_per_mtok": 0.50,
        "output_per_mtok": 1.50,
        "context_k": 262,
        "notes": "Good value. European training data distribution. Solid Executor voice."
    },
    # ── Qwen ──────────────────────────────────────────────────────
    "qwen/qwen3-235b-a22b-2507": {
        "capabilities": ["deep_reasoning", "cost_efficient", "fresh_perspective"],
        "cost_tier": "very_low",
        "input_per_mtok": 0.071,
        "output_per_mtok": 0.10,
        "context_k": 262,
        "notes": "235B MoE. Exceptional capability-to-cost ratio. Diverse training."
    },
}
```

**Selection logic for council (Phase 1 defaults):**

| Voice | Default Model | Rationale |
|-------|--------------|-----------|
| Contrarian | `deepseek/deepseek-r1-0528` | R1 reasoning finds real flaws cheaply |
| First Principles | `anthropic/claude-sonnet-4.6` | Our best reframing model |
| Expansionist | `openai/gpt-5.1` or `x-ai/grok-4` | Different training → genuinely different upside |
| Outsider | `google/gemini-2.5-flash` | Cheap, fast, different provider = genuine outsider |
| Executor | `mistralai/mistral-large-2512` | Good instruction following, cost-efficient |
| Chairman | `anthropic/claude-opus-4.6` | Synthesis + voice fidelity — must be our best |

---

## File Structure

All files within the existing project layout. Nothing on C: drive. Nothing outside `d:\Ai_Sandbox\agentsHQ\`.

```
orchestrator/
├── agents.py         ← ADD: build_council_voice_agent(), build_chairman_agent()
├── crews.py          ← MODIFY: build_consulting_crew() wraps SankofaCouncil
├── router.py         ← MODIFY: high_stakes metadata extraction
├── council.py        ← NEW: SankofaCouncil class, CouncilTier enum,
│                            select_by_capability(), convergence loop,
│                            strip_style_markers(), JSON log writer
└── prompts/          ← NEW DIRECTORY (inside orchestrator/)
    ├── voice_contrarian.txt
    ├── voice_first_principles.txt
    ├── voice_expansionist.txt
    ├── voice_outsider.txt
    ├── voice_executor.txt
    ├── council_review.txt
    └── council_chairman.txt

outputs/
└── council/          ← NEW DIRECTORY: JSON run logs + HTML reports

skills/
└── council/          ← NEW: "council this" Claude Code skill
    └── council.md

tests/
└── test_council.py   ← NEW: end-to-end test using retention scenario
```

---

## Data Persistence

### JSON run log (outputs/council/YYYY-MM-DD-HH-MM-SS.json)
```json
{
  "timestamp": "2026-03-31T14:23:00",
  "task_type": "consulting_deliverable",
  "query": "...",
  "rounds": 2,
  "converged": true,
  "convergence_score": 0.92,
  "member_responses": [...],
  "peer_reviews": [...],
  "chairman_synthesis": "...",
  "convergence_note": "...",
  "divergence_surfaces": "...",
  "models_used": {...},
  "tokens_used": {...},
  "estimated_cost_usd": 0.00
}
```

### PostgreSQL (existing connection)
One INSERT per council run into `council_runs` table:
```sql
CREATE TABLE council_runs (
  id SERIAL PRIMARY KEY,
  run_timestamp TIMESTAMPTZ,
  task_type VARCHAR(50),
  rounds_to_converge INT,
  converged BOOLEAN,
  convergence_score FLOAT,
  chairman_synthesis TEXT,
  convergence_note TEXT,
  models_used JSONB,
  tokens_used JSONB,
  estimated_cost_usd FLOAT,
  log_file_path TEXT
);
```

### HTML report (outputs/council/YYYY-MM-DD-HH-MM-SS.html)
Clean visual artifact showing: each voice's position, peer review findings, convergence score, Chairman synthesis, open question. Suitable for sharing with a client as a "Sankofa Council Review" deliverable artifact.

---

## Integration into build_consulting_crew()

Current flow:
```
planner → researcher → consultant → qa
```

New flow when Council is active:
```
planner → researcher → [SankofaCouncil runs on research brief] → qa reviews Chairman output
```

The QA agent reviews the Chairman's synthesis exactly as it currently reviews the consultant's output. The consulting agent's direct path remains available — Council wraps it, doesn't replace it. If council fails or errors, fallback to single consulting agent.

---

## Incremental Build Order (Phase 1)

Build and test locally. Push to GitHub. VPS pulls from GitHub. Never edit files directly on VPS.

```
Step 1: orchestrator/prompts/ — all 7 prompt files
Step 2: orchestrator/council.py — SankofaCouncil class (Contrarian only first)
Step 3: orchestrator/agents.py — voice agent factories
Step 4: tests/test_council.py — run on retention scenario before wiring to crew
Step 5: orchestrator/crews.py — integrate into build_consulting_crew()
Step 6: orchestrator/router.py — high_stakes metadata flag
Step 7: outputs/council/ directory + HTML report output
Step 8: PostgreSQL council_runs table + INSERT logic
Step 9: Add remaining 4 voices + full peer review + convergence loop
Step 10: skills/council/council.md — "council this" CLI skill
Step 11: AGENTS.md — register The Sankofa Council
Step 12: git push → VPS git pull
```

Test after Step 4 (single Contrarian). Test again after Step 9 (full council). Only push to VPS after Step 9 tests pass locally.

---

## Phase 2 (After 10 Real Runs)

- Add `thought_leadership` task type to router with MINI council (Contrarian + First Principles only)
- Automated MODEL_REGISTRY refresh: weekly cron job pulls `/api/v1/models` from OpenRouter, updates pricing + adds new models, flags deprecated ones — **HIGH PRIORITY** task for the backlog
- Evaluate which voices add most value based on peer review data — consider dropping redundant voice
- Surface "Where the Council disagreed" as a named section in consulting deliverables
- Token/cost tracking dashboard from PostgreSQL data

---

## Cost Reference (Phase 1 defaults, 2026-03-31 pricing)

| Tier | Round | Est. Cost |
|------|-------|-----------|
| FULL council, 1 round | 5 voices + 5 reviews + 1 chairman | ~$0.80–$2.50 |
| FULL council, 2 rounds | convergence required | ~$1.60–$5.00 |
| FULL council, 3 rounds | max iteration | ~$2.40–$7.50 |

These are dramatically cheaper than Claude Chat's original "$18-25 per run" estimate because we use a mixed model pool (DeepSeek R1 + Gemini Flash + Mistral Large) instead of 3x Opus.

---

## Client-Facing Language

> "This recommendation was developed through the Sankofa Council process — five independent analytical perspectives examined the question without visibility into each other's reasoning, reviewed each other's work anonymously, and iterated toward alignment before a Chairman synthesized the final output. This is equivalent to having three to five senior advisors work a problem independently before a lead partner writes the final recommendation."

---

## What We Are NOT Building (This Phase)

- No Swarms dependency
- No `thought_leadership` task type yet — needs real usage data first
- No public API for Council (internal only)
- No streaming output — batch run, final output delivered complete
