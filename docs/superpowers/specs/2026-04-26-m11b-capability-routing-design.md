---
title: M11b: Capability-Based Model Routing
date: 2026-04-26
status: approved
council: passed (Sankofa Council + code expert review, 2026-04-26)
branch: feat/m11b-capability-routing
---

## Problem

`select_llm()` in `agents.py` routes every crew agent through a `ROLE_MODEL` dict that maps `(role, complexity)` to one of four hardcoded Anthropic model aliases (`claude-haiku`, `claude-sonnet`, `claude-opus`, `gemini-flash`). This means:

- 22 crew agents are permanently locked to Anthropic (or one Google model) regardless of task fit
- A better model for coding (o4-mini), social voice (grok-4), or cheap planning (DeepSeek-v3) is never used
- Adding a new model to `COUNCIL_MODEL_REGISTRY` has zero effect on crew agents
- `select_by_capability()` already exists and is battle-tested by the Sankofa Council: it is just not wired to crews

There are also two pre-existing bugs this milestone fixes as a side effect:
1. `("voice", "simple")` and `("voice", "moderate")` are missing from `ROLE_MODEL` AND `ROLE_TEMPERATURE`, causing silent fallback to `claude-sonnet` at `temperature=0.3` for those call sites
2. `skill_builder` and `orchestrator/simple` entries are absent from `ROLE_MODEL`, same fallback risk

---

## Goal

Replace `ROLE_MODEL` with `ROLE_CAPABILITY`: a dict that maps `(role, complexity)` to `(primary_capability, max_cost_tier)`. Rewrite `select_llm()` body to call `select_by_capability()`. The 22 call sites do not change: signature is preserved.

After M11b, adding any new model to `COUNCIL_MODEL_REGISTRY` automatically makes it eligible for crew agent routing with zero further code changes.

---

## What Does NOT Change

- `select_llm(role, complexity, temperature)` signature: identical, 22 call sites are passive
- `ROLE_TEMPERATURE` dict: untouched, same temperature defaults per role
- `MODEL_REGISTRY` (the 4 flat aliases): NOT deprecated; 9 hardcoded `get_llm()` calls in `crews.py` remain intentional overrides and still use it
- `select_by_capability()` internals: already works, no changes
- `COUNCIL_MODEL_REGISTRY`: no new models added in this milestone
- All other files: `crews.py`, `engine.py`, `worker.py`, `router.py`, `app.py`, all tests except the new select_llm test

---

## ROLE_CAPABILITY Dict Design

One primary capability per role. Secondary capabilities noted in comments only: `select_by_capability()` accepts a single string. `ROLE_TEMPERATURE` is preserved exactly as-is alongside this dict.

```python
# Maps (role, complexity) -> (primary_capability, max_cost_tier)
# select_by_capability() picks the lowest-cost model within the ceiling
# that has the primary_capability tag. Relaxes cost upward if no match.
#
# Secondary capabilities are noted as comments -- they informed the choice
# but are NOT passed to select_by_capability() (single-string API).
#
# creative_divergence fallback: roles mapped to creative_divergence also
# accept fresh_perspective as a fallback in the event grok-4 is excluded.
# Document this here; the fallback fires automatically via cost relaxation
# since grok-4 is the only creative_divergence model and is always returned
# when available.

ROLE_CAPABILITY = {
    # Orchestrator: needs sustained multi-step logic
    ("orchestrator", "simple"):    ("instruction_following", "low"),
    ("orchestrator", "moderate"):  ("deep_reasoning", "medium"),
    ("orchestrator", "complex"):   ("deep_reasoning", "medium"),

    # Planner: structured output, does not need frontier reasoning
    ("planner", "simple"):         ("instruction_following", "low"),
    ("planner", "moderate"):       ("instruction_following", "low"),
    ("planner", "complex"):        ("instruction_following", "low-medium"),

    # Researcher: synthesis over long documents; fresh_perspective is a bonus
    ("researcher", "simple"):      ("instruction_following", "low"),
    ("researcher", "moderate"):    ("deep_reasoning", "medium"),
    ("researcher", "complex"):     ("deep_reasoning", "medium"),

    # Writer: moderate = structured; complex = creative angles
    ("writer", "simple"):          ("instruction_following", "low"),
    ("writer", "moderate"):        ("instruction_following", "low-medium"),
    ("writer", "complex"):         ("creative_divergence", "low-medium"),  # grok-4

    # Coder: multi-step logic is primary; instruction_following is secondary
    ("coder", "simple"):           ("instruction_following", "low"),
    ("coder", "moderate"):         ("deep_reasoning", "medium"),
    ("coder", "complex"):          ("deep_reasoning", "medium"),

    # Social: unconventional angles for hooks; grok-4 is the right fit
    ("social", "simple"):          ("instruction_following", "low"),
    ("social", "moderate"):        ("creative_divergence", "low-medium"),  # grok-4
    ("social", "complex"):         ("creative_divergence", "low-medium"),  # grok-4

    # QA: fast + precise; instruction_following is the primary signal
    ("qa", "simple"):              ("instruction_following", "low"),
    ("qa", "moderate"):            ("instruction_following", "low"),
    ("qa", "complex"):             ("instruction_following", "low-medium"),

    # Voice: precise adherence to style/persona constraints
    ("voice", "simple"):           ("instruction_following", "low-medium"),  # was missing
    ("voice", "moderate"):         ("instruction_following", "low-medium"),  # was missing
    ("voice", "complex"):          ("instruction_following", "low-medium"),

    # Hunter: tool-use loop; speed matters
    ("hunter", "simple"):          ("fast", "low"),
    ("hunter", "moderate"):        ("instruction_following", "low"),
    ("hunter", "complex"):         ("instruction_following", "low-medium"),

    # Consultant: substantive analysis, long context
    ("consultant", "simple"):      ("instruction_following", "low"),
    ("consultant", "moderate"):    ("deep_reasoning", "medium"),
    ("consultant", "complex"):     ("deep_reasoning", "medium"),

    # Skill builder: structured output, cheap is fine
    ("skill_builder", "simple"):   ("instruction_following", "low"),
    ("skill_builder", "moderate"): ("instruction_following", "low"),
    ("skill_builder", "complex"):  ("instruction_following", "low-medium"),
}
```

---

## New `select_llm()` Body

The function signature does not change. Only the body changes. The `ROLE_TEMPERATURE` lookup is preserved exactly.

```python
# Known capability tags -- validated at module import time
_VALID_CAPABILITIES = frozenset({
    "deep_reasoning",
    "creative_divergence",
    "fast",
    "cost_efficient",
    "long_context",
    "instruction_following",
    "fresh_perspective",
})

def _validate_role_capability_dict() -> None:
    """Raise ValueError at import time if any capability tag is misspelled."""
    for key, (cap, _tier) in ROLE_CAPABILITY.items():
        if cap not in _VALID_CAPABILITIES:
            raise ValueError(
                f"ROLE_CAPABILITY[{key!r}] has unknown capability {cap!r}. "
                f"Valid: {sorted(_VALID_CAPABILITIES)}"
            )

_validate_role_capability_dict()  # runs once at module import


def select_llm(
    agent_role: str,
    task_complexity: str = "moderate",
    temperature: float = None,
) -> LLM:
    """
    Select the best available LLM for a crew agent role + complexity.

    Routing priority: ROLE_CAPABILITY -> select_by_capability() -> DEFAULT_MODEL fallback.
    Temperature: ROLE_TEMPERATURE dict (unchanged), overridden by explicit temperature arg.
    """
    key = (agent_role, task_complexity)

    # Temperature (unchanged from pre-M11b)
    default_temp = ROLE_TEMPERATURE.get(key, 0.3)
    final_temp = temperature if temperature is not None else default_temp

    # Capability routing (replaces ROLE_MODEL dict lookup)
    if key in ROLE_CAPABILITY:
        capability, max_cost_tier = ROLE_CAPABILITY[key]
        model_id = select_by_capability(capability, max_cost_tier)
    else:
        # Missing key: log and fall back to DEFAULT_MODEL
        logger.warning(
            f"select_llm: no ROLE_CAPABILITY entry for ({agent_role!r}, {task_complexity!r}). "
            f"Falling back to DEFAULT_MODEL={DEFAULT_MODEL!r}"
        )
        model_id = _resolve_openrouter_model_string(DEFAULT_MODEL)

    return LLM(
        model=f"openrouter/{model_id}",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=final_temp,
    )
```

---

## ROLE_TEMPERATURE Additions (bug fixes)

Add the two missing voice entries to preserve the correct temperature for voice agents. No other entries change.

```python
# Add to ROLE_TEMPERATURE alongside existing entries:
("voice", "simple"):    0.8,   # was missing, was silently 0.3
("voice", "moderate"):  0.8,   # was missing, was silently 0.3
```

---

## SpawnJobTool Bug Fixes (same session, separate commit)

Two one-line fixes. No new features. No new tools.

**Fix 1: double `create_job` registration.**
`SpawnJobTool._run()` currently calls `create_job()` at line 1972. `_run_background_job()` calls it again at `worker.py:96`. The second call fails silently (INSERT with duplicate PK). Remove the `create_job` call from `SpawnJobTool`: worker owns job registration.

**Fix 2: `from_number` is not a real Telegram chat_id.**
`SpawnJobTool` sets `from_number=session_key`. Worker then does `chat_id = from_number` and tries to send a Telegram message to a string like `"spawn_job"`. Fix: parse the real chat_id from `session_key`.

```python
# In SpawnJobTool._run(), replace:
from_number = session_key

# With:
from_number = session_key.split(":")[0]  # chat_id is always the first segment
```

No new input fields, no new tools, no API surface change.

**What is explicitly NOT in this commit:**
- `wait_for_result=True`: deferred until a concrete multi-stage crew requires it
- `PollJobTool`: deferred, no current consumer
- `notify_chat_id` payload field: the `session_key.split` fix is cleaner

---

## Test Plan

One new test file: `orchestrator/tests/test_select_llm.py`.

Scope: unit tests only. No live OpenRouter calls. Mock `select_by_capability()` to return a fixed string. Test the routing logic, not the model registry.

Tests to write:
1. Parametrized: for every key in `ROLE_CAPABILITY`, call `select_llm(role, complexity)` and assert result is a non-None `LLM` object with `model` attribute set.
2. Missing key: call `select_llm("unknown_role", "moderate")`, assert fallback to `DEFAULT_MODEL` and a warning is logged.
3. Temperature passthrough: call `select_llm("writer", "complex", temperature=0.99)`, assert `final_temp=0.99`.
4. Temperature default: call `select_llm("writer", "complex")`, assert `final_temp=ROLE_TEMPERATURE.get(("writer","complex"), 0.3)`.
5. Startup validation: temporarily add a bad capability string to `ROLE_CAPABILITY`, assert `_validate_role_capability_dict()` raises `ValueError`.

Estimated: 15-20 lines, runs in under 1 second with mocks.

---

## Success Criteria (verifiable)

**M11b:**
1. All 22 `select_llm()` call sites import and run without error after the change.
2. `python3 -c "from agents import select_llm, ROLE_CAPABILITY; print(len(ROLE_CAPABILITY))"` prints a number >= 30 (all roles covered).
3. `docker exec orc-crewai python3 -c "from agents import select_llm; llm = select_llm('social','moderate'); print(llm.model)"` prints a model containing `grok` (not `claude`).
4. `docker exec orc-crewai python3 -c "from agents import select_llm; llm = select_llm('coder','complex'); print(llm.model)"` prints a model NOT containing `opus` (now routes to o4-mini or GPT-5.1).
5. `docker exec orc-crewai python3 -c "from agents import select_llm; llm = select_llm('voice','moderate'); print(llm.model)"` does not raise (was silently broken before M11b).
6. All existing tests pass: `pytest orchestrator/tests/ -q`.
7. New `test_select_llm.py`: all 5 test cases pass.

**SpawnJobTool bug fix:**
1. `docker exec orc-crewai python3 -c "from tools import SpawnJobTool; import json; r = json.loads(SpawnJobTool()._run(json.dumps({'task':'test','session_key':'12345:proj'}))); print(r)"` returns `{job_id: ..., status: queued}` with no duplicate-key error in logs.
2. Check `docker logs orc-crewai | grep "create_job"`: should appear once per spawned job, not twice.

---

## Build Order

1. Write `test_select_llm.py` (tests first, narrow scope)
2. Write `ROLE_CAPABILITY` dict and `_VALID_CAPABILITIES` + `_validate_role_capability_dict()` in `agents.py`
3. Add missing `ROLE_TEMPERATURE` entries for `voice/simple` and `voice/moderate`
4. Rewrite `select_llm()` body (preserve `ROLE_TEMPERATURE` line explicitly)
5. Run tests: `pytest orchestrator/tests/test_select_llm.py -v`
6. Run full suite: `pytest orchestrator/tests/ -q`
7. Commit: `feat(agents): M11b capability routing: ROLE_CAPABILITY replaces ROLE_MODEL`
8. SCP + docker cp + smoke test (verify grok-4 for social, non-Anthropic for coder)
9. Separate commit: `fix(tools): SpawnJobTool: remove double create_job, fix from_number`
10. SCP + docker cp + smoke test

---

## Decisions Made and Why

| Decision | Rationale |
|---|---|
| One primary capability per role | `select_by_capability()` accepts one string. Two capabilities would require signature change that breaks council.py. |
| Keep `ROLE_TEMPERATURE` untouched | Decoupling temperature from model routing is the correct design. Temperature governs style, model governs capability. |
| `creative_divergence` roles rely on grok-4 with cost-relaxation as fallback | grok-4 is the only creative_divergence model. If excluded, cost relaxation still returns grok-4. Acceptable single-provider dependency for two non-critical roles. Social content quality matters but a one-model fallback to grok-4 at higher cost is preferable to routing to a random cheap model. |
| `MODEL_REGISTRY` not deprecated | 9 deliberate `get_llm()` overrides in `crews.py` are intentional (relay agents, formatters). They stay. M11b does not touch them. |
| `wait_for_result` and `PollJobTool` deferred | No concrete crew needs them today. Karpathy: simplest thing that solves the actual problem. Reopen when a multi-stage crew is being built. |
| Startup validation via `_validate_role_capability_dict()` | A typo in a capability string causes silent fallback to the cheapest model. A `ValueError` at import time surfaces this immediately. 5-line cost for a hard guard. |

---

## Spec Self-Review

- No TBDs or placeholders.
- `ROLE_TEMPERATURE` preservation is called out in both the design and build order: cannot be missed.
- `creative_divergence` single-model risk is documented and accepted with rationale.
- Success criteria are all shell-executable: no vague "it works" statements.
- Scope is narrow: one file for M11b core (`agents.py`), one file for bug fix (`tools.py`), one new test file.
- `MODEL_REGISTRY` non-deprecation is documented explicitly to prevent future cleanup accidents.
