---
name: agent-teams
description: "Coordinate multiple CrewAI crews working in parallel on independent subtasks, with a team lead synthesizing results. VPS equivalent of Claude Code Agent Teams."
risk: safe
source: superpowers
date_added: '2026-03-25'
author: agentsHQ
tags: [orchestration, parallel, crewai, teams, coordination]
capabilities: [parallel-execution, team-coordination, task-decomposition, result-synthesis]
tools: [crewai, fastapi, postgresql, python]
---

# Agent Teams — VPS Orchestrator Pattern

Coordinate multiple CrewAI crews working in parallel on independent subtasks.
One **team lead** decomposes the request, dispatches **teammates** (separate crew
executions) to work concurrently, then synthesizes all results into a single
coherent output.

This is the VPS equivalent of Claude Code's experimental Agent Teams feature.

---

## When to Use

```
Is the task decomposable into 2+ independent subtasks?
    │
    ├─ NO  → Use a standard sequential crew (existing pattern)
    │
    └─ YES → Can subtasks run without needing each other's output first?
                 │
                 ├─ NO  → Sequential crew with context passing (existing)
                 │
                 └─ YES → Use Agent Teams pattern ✓
```

**Use agent teams when:**

- Task covers multiple independent domains (e.g. research + code + design in parallel)
- Competing hypotheses to investigate simultaneously (debugging with 3 theories)
- Parallel content production (3 LinkedIn posts in 3 different tones)
- Cross-module work where modules don't depend on each other
- You want faster turnaround by running work concurrently

**Do NOT use when:**

- Subtask B needs subtask A's output to start
- All agents would edit the same file or resource
- The task is simple enough for one crew
- Token cost of parallel execution outweighs the time savings

---

## Architecture

```
User Request (Telegram → n8n → /run)
        │
        ▼
  TEAM LEAD (Orchestrator Agent)
  ├─ Decomposes request into N independent subtasks
  ├─ Dispatches N teammate crews in parallel (ThreadPoolExecutor)
  ├─ Each teammate runs independently in its own thread
  │       ├─ Teammate 1: research_crew  → result_1
  │       ├─ Teammate 2: code_crew      → result_2
  │       └─ Teammate 3: social_crew    → result_3
  └─ Synthesis crew combines all results → final output
```

---

## Two Modes

### Mode 1: Parallel Crews (Independent Work)

Best for: tasks with clearly separate domains, no inter-agent communication needed.

Each subtask runs as a full crew (with its own planner, specialist, QA).
Results are collected when all finish and passed to a synthesis step.

### Mode 2: Hierarchical Crew (Collaborative Work)

Best for: tasks where agents need to inform each other, debate findings,
or build on each other's intermediate output.

Uses CrewAI's `Process.hierarchical` — a manager LLM (Claude Opus) acts as
team lead inside a single Crew, assigning tasks to agents dynamically and
reviewing their work before allowing them to proceed.

---

## Implementation

### Step 1 — Add to `crews.py`

Add these two functions:

```python
import concurrent.futures
import logging

logger = logging.getLogger(__name__)


def run_parallel_team(subtasks: list[dict]) -> list[dict]:
    """
    Run multiple crews in parallel. Each subtask is an independent crew execution.

    subtasks: list of {"crew_type": str, "task": str, "label": str}
    returns:  list of {"label": str, "crew_type": str, "result": str}

    Example:
        subtasks = [
            {"crew_type": "research_crew", "task": "Research AI in HR", "label": "research"},
            {"crew_type": "social_crew",   "task": "Write LinkedIn post on AI HR", "label": "social"},
        ]
    """
    def _run_one(subtask: dict) -> dict:
        crew_type = subtask["crew_type"]
        task = subtask["task"]
        label = subtask.get("label", crew_type)
        try:
            crew = assemble_crew(crew_type, task)
            result = crew.kickoff()
            logger.info(f"[agent-team] Teammate '{label}' completed")
            return {"label": label, "crew_type": crew_type, "result": str(result), "success": True}
        except Exception as e:
            logger.error(f"[agent-team] Teammate '{label}' failed: {e}")
            return {"label": label, "crew_type": crew_type, "result": f"ERROR: {e}", "success": False}

    max_workers = min(len(subtasks), 5)   # cap at 5 parallel threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_one, st): st for st in subtasks}
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return results


def build_team_synthesis_crew(original_request: str, teammate_results: list[dict]) -> Crew:
    """
    Final synthesis step: takes all teammate outputs and produces one coherent result.
    Uses the consulting_agent as synthesizer (strong at structured summaries).
    """
    from agents import build_consulting_agent, build_qa_agent

    # Format teammate outputs for context
    results_context = "\n\n".join([
        f"### {r['label'].upper()} (via {r['crew_type']})\n{r['result']}"
        for r in teammate_results
    ])

    synthesizer = build_consulting_agent(complexity="moderate")
    qa = build_qa_agent(complexity="simple")

    synthesis_task = Task(
        description=(
            f"Original request: {original_request}\n\n"
            f"Multiple specialist teams have completed their work. "
            f"Synthesize their outputs into one coherent, well-structured deliverable.\n\n"
            f"Teammate outputs:\n{results_context}\n\n"
            f"Produce a unified result that:\n"
            f"- Integrates all relevant findings\n"
            f"- Eliminates redundancy\n"
            f"- Presents a clear, actionable conclusion\n"
            f"- Saves the final output using the save_output tool"
        ),
        agent=synthesizer,
        expected_output="A unified, synthesized deliverable combining all teammate outputs."
    )

    qa_task = Task(
        description=(
            "Review the synthesized output against the original request. "
            "Verify it is complete, coherent, and addresses what was asked. "
            "Flag anything missing or contradictory."
        ),
        agent=qa,
        expected_output="QA verdict: approved or list of issues to fix.",
        context=[synthesis_task]
    )

    return Crew(
        agents=[synthesizer, qa],
        tasks=[synthesis_task, qa_task],
        process=Process.sequential,
        verbose=True,
        memory=False
    )


def build_hierarchical_crew(user_request: str, specialist_agents: list) -> Crew:
    """
    Mode 2: Hierarchical crew where a manager LLM coordinates agents dynamically.
    Use when agents need to inform each other or build on intermediate results.

    specialist_agents: list of Agent objects to include in the team
    """
    from agents import select_llm

    # Each agent gets a general task — the manager LLM assigns work dynamically
    tasks = [
        Task(
            description=(
                f"Work on this request as directed by the team lead: {user_request}\n"
                f"Your role: {agent.role}\n"
                f"Apply your expertise and report findings clearly."
            ),
            agent=agent,
            expected_output=f"Specialist output from {agent.role}."
        )
        for agent in specialist_agents
    ]

    return Crew(
        agents=specialist_agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=select_llm("orchestrator", "complex"),  # Claude Opus as team lead
        verbose=True,
        memory=False
    )
```

### Step 2 — Add team execution to `orchestrator.py`

In `orchestrator.py`, add a helper alongside `run_orchestrator()`:

```python
def run_team_orchestrator(
    subtasks: list[dict],
    original_request: str,
    from_number: str = "unknown"
) -> dict:
    """
    Run multiple crews in parallel and synthesize results.

    subtasks: [{"crew_type": "...", "task": "...", "label": "..."}, ...]
    """
    import time
    from crews import run_parallel_team, build_team_synthesis_crew

    start_time = datetime.now()

    # Phase 1: run all subtasks in parallel
    logger.info(f"[agent-team] Dispatching {len(subtasks)} teammates in parallel")
    teammate_results = run_parallel_team(subtasks)

    successful = [r for r in teammate_results if r["success"]]
    failed     = [r for r in teammate_results if not r["success"]]

    if failed:
        logger.warning(f"[agent-team] {len(failed)} teammate(s) failed: {[f['label'] for f in failed]}")

    # Phase 2: synthesize all results
    synthesis_crew = build_team_synthesis_crew(original_request, successful)
    final_result   = synthesis_crew.kickoff()

    execution_time = (datetime.now() - start_time).total_seconds()

    return {
        "success": True,
        "result": str(final_result),
        "task_type": "agent_team",
        "teammate_count": len(subtasks),
        "teammates_succeeded": len(successful),
        "teammates_failed": len(failed),
        "execution_time": execution_time,
        "files_created": []  # populated by timestamp scan in caller
    }
```

### Step 3 — Add `/run-team` endpoint to `orchestrator.py`

```python
class TeamTaskRequest(BaseModel):
    subtasks: list[dict]   # [{"crew_type": str, "task": str, "label": str}]
    original_request: str
    from_number: str = "unknown"
    session_key: str = "default"

@app.post("/run-team")
async def run_team_endpoint(request: TeamTaskRequest):
    """
    Run multiple crews in parallel (agent teams pattern).
    Caller is responsible for decomposing the request into subtasks.
    """
    result = run_team_orchestrator(
        subtasks=request.subtasks,
        original_request=request.original_request,
        from_number=request.from_number
    )
    return result
```

---

## Usage Example

### From n8n or any HTTP caller:

```json
POST http://72.60.209.109:8000/run-team
{
  "original_request": "I need a research report AND a LinkedIn post AND a Python script all about AI in HR",
  "from_number": "7792432594",
  "subtasks": [
    {
      "crew_type": "research_crew",
      "task": "Research AI adoption trends in HR and talent management",
      "label": "research"
    },
    {
      "crew_type": "social_crew",
      "task": "Write a LinkedIn post about AI transforming HR departments",
      "label": "social"
    },
    {
      "crew_type": "code_crew",
      "task": "Write a Python script that scores CVs against a job description using OpenAI",
      "label": "cv_scorer"
    }
  ]
}
```

All three crews run concurrently. When all finish, synthesis produces
one integrated deliverable. Total time ≈ longest single crew (not sum of all).

---

## Adding Auto-Decomposition (Optional Enhancement)

To let the router automatically detect multi-domain tasks and decompose them,
add a decomposer step in `orchestrator.py`:

```python
def decompose_request(user_request: str) -> list[dict] | None:
    """
    Uses Claude Haiku to detect if a request has multiple independent domains
    and decompose it into subtasks. Returns None if it's a single-domain request.
    """
    from litellm import completion

    prompt = f"""Analyze this request and determine if it contains multiple INDEPENDENT tasks
that could be worked on simultaneously by different specialists.

Request: "{user_request}"

If it has 2+ independent tasks, return JSON:
{{"is_multi_task": true, "subtasks": [{{"crew_type": "...", "task": "...", "label": "..."}}]}}

Valid crew_types: website_crew, research_crew, social_crew, code_crew,
                 consulting_crew, writing_crew, app_crew

If it is a single task, return:
{{"is_multi_task": false}}

Return ONLY valid JSON. No explanation."""

    response = completion(
        model="openrouter/anthropic/claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    result = json.loads(response.choices[0].message.content)
    if result.get("is_multi_task"):
        return result["subtasks"]
    return None
```

Then in `run_orchestrator()`, check before routing to a single crew:

```python
# Check for multi-domain request
subtasks = decompose_request(task_request)
if subtasks and len(subtasks) >= 2:
    return run_team_orchestrator(subtasks, task_request, from_number)
# else fall through to normal single-crew routing
```

---

## Checklist Before Using

- [ ] Subtasks are genuinely independent (no output dependency between them)
- [ ] Each subtask maps to an existing crew_type in CREW_REGISTRY
- [ ] You've capped max_workers at a sensible number (≤5) to avoid API rate limits
- [ ] Synthesis step is appropriate for the combined output type
- [ ] Added error handling — one teammate failing should not block the rest

---

## Limitations (VPS vs Claude Code)

| Feature | Claude Code Agent Teams | This Implementation |
|---|---|---|
| Inter-agent messaging | Direct mailbox between agents | Not supported — use hierarchical mode |
| Task self-claiming | Agents claim tasks autonomously | Team lead assigns via ThreadPoolExecutor |
| Session resumption | Experimental (known issues) | Not applicable — stateless per /run call |
| Display mode | Split panes / in-process | Server logs only |
| Teammate models | Per-teammate model selection | Per-crew model selection via agents.py |
| Max teammates | No hard limit | Recommend ≤5 (API rate limits) |

---

## Related Skills

- `dispatching-parallel-agents` — lighter pattern for simple parallel tasks
- `subagent-driven-development` — sequential subagent dispatch for implementation
- `executing-plans` — structured task execution with checkpoints
