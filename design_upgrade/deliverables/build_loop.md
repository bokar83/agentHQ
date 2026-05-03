# Build Loop Orchestration
**agentsHQ: "Humanized Standard" Architecture**
*Pseudocode and CrewAI wiring pattern for the builder-critic loop.*

---

## High-Level Flow

```
START
  |
  v
[BUILDER AGENT]
  Step 0: Verify craft components exist (SmoothScrollProvider.tsx)
  Step 1: Run archetype selection (2-question lookup table)
  Step 2: Write design_brief.md
  Step 3: Confirm Next.js 14+ App Router runtime
  Step 4: Copy craft components to src/components/craft/
  Step 5: Import craft-tokens.css as first import in globals.css
  Step 6: Install dependencies (lenis, gsap, framer-motion)
  Step 7: Build site section by section
         - At each section: re-read design_brief.md, output checkpoint line
  Step 8: Self-check (grep for banned strings, verify mandatory components)
  Step 9: Hand off to critic agent
  |
  v
[CRITIC AGENT]
  Phase 1: Automated linting (grep checks: objective, binary)
  Phase 2: Semantic HTML audit
  Phase 3: Archetype consistency review
  Phase 4: Human judgment scoring (5 criteria, 1-5 scale)
  Output: PASS | REVISE | ESCALATE
  |
  v
[VERDICT ROUTER]
  PASS    -> Deploy
  REVISE  -> Back to builder agent (cycle count +1)
  ESCALATE -> Human review queue
  |
  v
[CYCLE COUNTER]
  Cycle 1 REVISE -> builder gets one revision attempt
  Cycle 2 REVISE -> builder gets one revision attempt
  Cycle 3 REVISE -> override to ESCALATE (hard cap reached)
  |
  v
[HUMAN GATE]  (on ESCALATE)
  Human reviews: design_brief.md, build artifacts, all critic reports
  Human decides: fix specific items and re-run from Step 7 | abandon build
  |
  v
DEPLOY (on PASS)
```

---

## CrewAI Wiring Pattern

```python
from crewai import Agent, Task, Crew, Process

# --- Agent Definitions ---

builder_agent = Agent(
    role="Web Builder",
    goal="Build a Next.js website that passes the Humanized Standard eval rubric",
    backstory="""You are an orchestra conductor, not a musician. Pre-built craft
    components contain the physics and mathematics of premium web design. Your job
    is to orchestrate them according to the declared archetype. You do not write
    GSAP physics from scratch. You do not improvise easing values.""",
    tools=[file_read_tool, file_write_tool, bash_tool],
    verbose=True,
    allow_delegation=False,
)

critic_agent = Agent(
    role="Design Critic",
    goal="Evaluate web builds against the Humanized Standard eval rubric and return PASS, REVISE, or ESCALATE",
    backstory="""You are the quality gate. You do not build. You do not encourage.
    You evaluate. Your verdict is final within the automated loop. You catch every
    AI-tell before a site ships.""",
    tools=[file_read_tool, bash_tool],
    verbose=True,
    allow_delegation=False,
)

# --- Task Definitions ---

def create_build_task(client_brief: str, project_dir: str) -> Task:
    return Task(
        description=f"""
        Build a Next.js website for the following client brief:

        {client_brief}

        Project directory: {project_dir}

        Follow the MANDATORY PRE-BUILD SEQUENCE in builder_prompt.md exactly.
        Write design_brief.md before writing any code.
        Copy craft components from skills/frontend-design/components/ before building.
        Run self-check before handing off to the critic.
        """,
        agent=builder_agent,
        expected_output="A complete Next.js project in the project directory with design_brief.md written.",
    )

def create_critique_task(project_dir: str) -> Task:
    return Task(
        description=f"""
        Evaluate the web build at: {project_dir}

        Read design_brief.md first.
        Run all Phase 1 automated linting checks.
        Run Phase 2 semantic HTML audit.
        Run Phase 3 archetype consistency review.
        Score Phase 4 human judgment criteria (1-5 per criterion).

        Output one of: PASS, REVISE, or ESCALATE.
        If REVISE: list every failure with file:line specificity.
        If ESCALATE: list all failures across all cycles and recommend human action.
        """,
        agent=critic_agent,
        expected_output="A structured verdict: PASS, REVISE (with specific fixes), or ESCALATE (with human action recommendation).",
        context=[build_task],  # critic reads the build task's output
    )

# --- Loop Orchestration ---

def run_build_loop(client_brief: str, project_dir: str, max_cycles: int = 3):
    cycle = 0

    while cycle < max_cycles:
        cycle += 1
        print(f"\n=== BUILD LOOP: Cycle {cycle} of {max_cycles} ===\n")

        build_task = create_build_task(client_brief, project_dir)
        critique_task = create_critique_task(project_dir)

        crew = Crew(
            agents=[builder_agent, critic_agent],
            tasks=[build_task, critique_task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()
        verdict = extract_verdict(result)  # parse "CRITIC VERDICT: X" from result

        if verdict == "PASS":
            print(f"\n=== PASS on cycle {cycle}. Proceeding to deployment. ===\n")
            return {"status": "PASS", "cycles": cycle, "result": result}

        elif verdict == "REVISE":
            if cycle < max_cycles:
                print(f"\n=== REVISE on cycle {cycle}. Builder agent revising. ===\n")
                continue
            else:
                # Cycle cap reached without pass
                print(f"\n=== ESCALATE: cycle cap reached without PASS. Human review required. ===\n")
                return {"status": "ESCALATE", "cycles": cycle, "result": result}

        elif verdict == "ESCALATE":
            print(f"\n=== ESCALATE on cycle {cycle}. Human review required. ===\n")
            return {"status": "ESCALATE", "cycles": cycle, "result": result}

    # Should not reach here
    return {"status": "ESCALATE", "cycles": max_cycles, "result": "Max cycles exceeded"}


def extract_verdict(result: str) -> str:
    """Parse the critic agent's verdict from its output."""
    if "CRITIC VERDICT: PASS" in result:
        return "PASS"
    elif "CRITIC VERDICT: REVISE" in result:
        return "REVISE"
    elif "CRITIC VERDICT: ESCALATE" in result:
        return "ESCALATE"
    else:
        # Unrecognized format: escalate to be safe
        return "ESCALATE"
```

---

## Fallback: Post-Build Grep Script (if CrewAI loop is not wired)

If the CrewAI builder-critic loop is not yet wired, run this script manually after every build to catch objective failures before human review.

```bash
#!/bin/bash
# post_build_check.sh
# Run from the project root after the builder agent completes.
# Exits 0 if all checks pass, 1 if any check fails.

PROJECT_DIR=${1:-"./src"}
FAIL=0

echo "=== agentsHQ Post-Build Automated Check ==="
echo "Checking: $PROJECT_DIR"
echo ""

# Banned string checks (should return 0 matches)
check_banned() {
    local pattern="$1"
    local label="$2"
    local count
    count=$(grep -r --include="*.tsx" --include="*.ts" --include="*.css" "$pattern" "$PROJECT_DIR" 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "FAIL: $label ($count occurrences)"
        grep -rn --include="*.tsx" --include="*.ts" --include="*.css" "$pattern" "$PROJECT_DIR" 2>/dev/null
        FAIL=1
    else
        echo "PASS: $label"
    fi
}

# Presence checks (should return 1+ matches)
check_required() {
    local pattern="$1"
    local file="$2"
    local label="$3"
    local count
    count=$(grep -c "$pattern" "$file" 2>/dev/null || echo 0)
    if [ "$count" -lt 1 ]; then
        echo "FAIL: $label (not found in $file)"
        FAIL=1
    else
        echo "PASS: $label"
    fi
}

echo "--- Banned String Checks ---"
check_banned "ease-in-out" "ease-in-out banned"
check_banned "duration-300" "duration-300 banned"
check_banned "rgba(0,0,0,0.1)" "generic shadow rgba banned"

echo ""
echo "--- Presence Checks ---"

# Read design_brief.md to check archetype
ARCHETYPE=$(grep "Selected archetype:" design_brief.md 2>/dev/null | cut -d' ' -f3)
echo "Declared archetype: $ARCHETYPE"

# SmoothScrollProvider (skip for BRUTALIST and TRUST_ENTERPRISE)
if [[ "$ARCHETYPE" != "BRUTALIST" && "$ARCHETYPE" != "TRUST_ENTERPRISE" ]]; then
    check_required "SmoothScrollProvider" "src/app/layout.tsx" "SmoothScrollProvider in layout"
fi

check_required "KineticText" "$PROJECT_DIR" "KineticText used in build"
check_required "MagneticButton" "$PROJECT_DIR" "MagneticButton used in build"
check_required "craft-tokens.css" "src/app/globals.css" "craft-tokens.css imported first"

echo ""
echo "--- Result ---"
if [ "$FAIL" -eq 0 ]; then
    echo "ALL AUTOMATED CHECKS PASSED"
    echo "Proceed to critic agent for human judgment scoring."
    exit 0
else
    echo "ONE OR MORE CHECKS FAILED"
    echo "Fix the failures above before submitting to the critic agent."
    exit 1
fi
```

Save this as `scripts/post_build_check.sh` and run with `bash scripts/post_build_check.sh ./src`.

---

## Escalation Protocol

When the build loop returns ESCALATE:

1. **Notify Boubacar** via the standard Telegram notification with:
   - Project name
   - Number of cycles completed
   - List of persistent failures from the critic's ESCALATE report

2. **Do not deploy.** No escalated build ships without human sign-off.

3. **Preserve all artifacts.** Do not clean the project directory. The design_brief.md, all critic reports, and the built code are needed for diagnosis.

4. **Log the failure** in `design_upgrade/test_log.md` with:
   - Date
   - Project name
   - Archetype declared
   - Failure type (automated check / archetype drift / human judgment)
   - Specific element that failed
   - Whether this is a new failure type (if yes, consider adding it to the eval rubric as an automatic FAIL criterion)
