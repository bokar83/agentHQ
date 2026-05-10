# M24: Hermes Self-Healing Execution

**Date:** 2026-05-10  
**Branch:** `feat/atlas-m24-hermes-self-healing`  
**Status:** Approved for Implementation Draft  

---

## 1. Goal Description

Milestone M24 upgrades the passive concierge-triage framework into an active, autonomous self-healing operator named **Hermes**. Under the original M4 implementation, `concierge_crew.py` scrapes the VPS logs, detects errors, and enqueues descriptive triage summaries to the `approval_queue`. 

With M24, once Boubacar approves a `concierge-fix` proposal:
1. An asynchronous background task (`minion:hermes-fix`) is enqueued.
2. The Hermes worker claims the task, checks out a new isolated Git feature branch, and localizes the source files.
3. Strict immunological checks validate that targeted edits reside purely within safe, non-core directories.
4. Hermes uses LLM-powered diagnostics to draft a fix, applies it, and runs `pytest` in an validation loop.
5. Once tests pass, Hermes packages the changes under a `[GATE-NOTE]`-annotated `[READY]` commit and pushes it to GitHub, ready for the Gate to merge and deploy.

---

## 2. System Architecture

```
                                  HUMAN REVIEW
                                        │ (Approves)
                                        ▼
[VPS Logs] ──► concierge_crew ──► approval_queue ──► (Trigger: enqueue("minion:hermes-fix"))
                                                           │
┌──────────────────────────────────────────────────────────┘
▼
minion_worker (claims task)
  │
  ├──► 1. Git checkout -b fix/hermes-<id>
  │
  ├──► 2. Immunological Boundary Check (Allowed/Forbidden paths)
  │
  ├──► 3. LLM Diagnostic & Edit Application Loop (Up to 3 attempts)
  │        │
  │        ├─► Apply edit
  │        └─► Run pytest tests/
  │
  └──► 4. Success? ──► Commit feat(x) + [READY] + [GATE-NOTE: ...] ──► Push to GitHub
```

---

## 3. Immunological Safety Boundaries

Immunological rules are hard-coded constraints evaluated before any file modification. If Hermes determines a fix requires editing a file outside these boundaries, it fails the task immediately to protect the platform.

### Allowed Write Paths
- `skills/[skill-name]/` — Custom skills & task logic.
- `workspace/` — Client workspaces, briefs, and deliverables.
- `agent_outputs/` — Media assets and report outputs.
- `docs/audits/` — Automated security/compliance logs.
- `data/changelog.md` — Platform logs.
- `docs/roadmap/*.md` — Multi-session tracking roadmaps.

### Forbidden Write Paths (HARD BLOCK)
- `CLAUDE.md`, `AGENTS.md`, `docs/AGENT_SOP.md`, `docs/GOVERNANCE.md`, `docs/governance.manifest.json` — System soul and rule layers.
- `.claude/settings.json`, `.vscode/settings.json`, `config/settings.json` — IDE/Agent config.
- `.pre-commit-config.yaml`, `scripts/*.py` — Verification hooks.
- `secrets/`, `.env` — Keys and environment files.
- `orchestrator/*.py` — Central platform routing and scheduling.
- `skills/coordination.py` — Atomic mutex locks and claim mechanisms.

---

## 4. The Self-Healing Execution Loop

### Step 4.1: Intercepting Approval
We extend the `_transition` logic in `orchestrator/approval_queue.py` so that when a transition to `status='approved'` or `status='edited'` occurs for `proposal_type='concierge-fix'`, we automatically queue the background task:

```python
if out.proposal_type == "concierge-fix" and new_status in ("approved", "edited"):
    from skills.coordination import enqueue
    enqueue(
        kind="minion:hermes-fix",
        payload={
            "queue_id": out.id,
            "signature": out.payload.get("signature"),
            "summary": out.payload.get("summary"),
            "samples": out.payload.get("samples"),
            "triage_note": out.payload.get("triage_note"),
            "edited_payload": out.edited_payload,
        }
    )
```

### Step 4.2: Worker Claims & Sandbox Isolation
When `minion_worker.py` claims `"minion:hermes-fix"`, it delegates the payload to `hermes_worker.py:hermes_fix_handler(payload)`. The handler isolates the execution using git:

```python
import subprocess

def checkout_sandbox_branch(queue_id: int) -> str:
    branch_name = f"fix/hermes-{queue_id}"
    # Ensure starting from fresh origin/main
    subprocess.run(["git", "fetch", "origin"], check=True)
    subprocess.run(["git", "checkout", "-b", branch_name, "origin/main"], check=True)
    return branch_name
```

### Step 4.3: Immunological Path Check
Before applying any file changes, the target paths are evaluated:

```python
import os

ALLOWED_PREFIXES = ["skills/", "workspace/", "agent_outputs/", "docs/audits/", "data/changelog.md", "docs/roadmap/"]
FORBIDDEN_FILES = [
    "CLAUDE.md", "AGENTS.md", "docs/AGENT_SOP.md", "docs/GOVERNANCE.md", "docs/governance.manifest.json",
    ".claude/settings.json", ".vscode/settings.json", "config/settings.json", ".pre-commit-config.yaml",
    "skills/coordination.py"
]

def is_path_safe(filepath: str) -> bool:
    normalized = filepath.replace("\\", "/").strip("/")
    
    # Check forbidden specific files or patterns
    if normalized in FORBIDDEN_FILES or normalized.startswith("scripts/") or normalized.startswith("secrets/") or normalized.startswith("orchestrator/") or normalized.startswith(".env"):
        return False
        
    # Check allowed prefixes
    for prefix in ALLOWED_PREFIXES:
        if normalized.startswith(prefix):
            return True
            
    return False
```

### Step 4.4: Diagnostic & Verification Loop
Hermes invokes OpenRouter to localize the file containing the bug and suggest a change. It applies the change and executes tests:

```python
def run_validation_tests() -> bool:
    # Run relevant tests
    res = subprocess.run(["pytest", "tests/"], capture_output=True, text=True)
    return res.returncode == 0
```

If the tests fail, the stdout/stderr of pytest is fed back to the LLM to refine the repair, up to a maximum of 3 attempts.

### Step 4.5: Gate-Note Packaging & Push
Once validation succeeds, Hermes commits and pushes:

```python
def commit_and_push_fix(branch_name: str, queue_id: int, summary: str):
    gate_note = f"[GATE-NOTE: merge-target=main, branch={branch_name}, context=Autonomous Hermes self-healing fix for queue #{queue_id}. Passed pytest validation.]"
    commit_msg = f"fix(concierge): self-healing fix for queue #{queue_id} [READY]\n\n{gate_note}"
    
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "origin", branch_name], check=True)
```

---

## 5. Success Criteria

1. **Trigger Fidelity:** Approving a `concierge-fix` proposal enqueues a `minion:hermes-fix` task.
2. **Sandbox Isolation:** All work runs in a separate git branch checked out from `origin/main`.
3. **Immunological Lockdown:** Any attempt to modify files in the forbidden list is blocked before the write is executed.
4. **Self-Correction:** If the initial fix causes a test failure, Hermes retries up to 3 times using the test output.
5. **Gate Delivery:** A successful fix results in a clean push to origin on the feature branch with a properly formatted `[GATE-NOTE]` and `[READY]` keyword.
