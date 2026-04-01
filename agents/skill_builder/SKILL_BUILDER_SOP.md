# Skill Builder Strategic SOP (v2.0)

**Framework**: Transforming Raw Software into Catalyst Assets.
**Goal**: Rapid, ROI-positive colonization of third-party software for agentsHQ.

---

## 🚀 The 9-Phase Strategic Pipeline

### Phase 0: Strategic Intent (ROI Check)

- **Activity**: Define the "Why?".
- **Questions**: How does this tool generate cash by Monday morning?
- **Action**: Map the tool to a `Task Type` (e.g., `hunter`, `consulting`).
- **Deliverable**: A 2-sentence **Strategic Intent Statement**.

### Phase 1: Resource Discovery (CLI-Hub)

- **Activity**: Search for an existing "Harness" or "Skill".
- **Tool**: `cli_hub_explorer`.
- **Action**: Do not reinvent the wheel. If a harness exists, skip to Phase 4.

### Phase 2: Technical Analysis

- **Activity**: Map the GUI/Logic to CLI/API calls.
- **Action**: Identify the core binary (e.g., `ffmpeg`, `magick`, `git`).
- **Check**: Is it already on the VPS? If not, list the `sudo apt` or `pip` commands needed.

### Phase 3: Harness Design & Backend

- **Activity**: Create the `utils/backend.py` (The Connector).
- **Style**: Use `subprocess.run` with proper error handling and JSON stripping.
- **Rule**: Every backend function must have a `strict_json` mode.

### Phase 4: CLI Implementation (Click)

- **Activity**: Construct a professional Click CLI.
- **Style**: Groups (Project, Action, Export).
- **Flags**: Every command MUST support `--json` and `--verbose`.

### Phase 5: Humanization & Branding

- **Activity**: Integrate the `ReplSkin`.
- **Style**: Corporate **Catalyst Works** branding in the REPL header.
- **Voice**: Clean, professional, and results-oriented help menus.

### Phase 6: Automated Verification (TEST.md)

- **Activity**: Create and run `tests/test_cli.py`.
- **Requirement**: Use the **Real Software**. Verify the JSON output schema.
- **Action**: Document results in `TEST.md`.

### Phase 7: System Integration (SKILL.md)

- **Activity**: Generate the internal documentation for other agents.
- **Style**: Clear objective, input/output schemas, and usage examples.
- **Location**: `skills/[tool-name]/SKILL.md`.

### Phase 8: Monday Morning Deliverable

- **Activity**: Output a **Success Plan**.
- **Action**: Tell Boubacar explicitly how to monetize this tool immediately.
- **Style**: "Monday Morning Action: Use this new skill to process 50 leads in 5 minutes."

---

## ⛓️ Quality Constraints (The Catalyst Standard)

1. **Precision**: No "hallucinated" CLI flags. Use `--help` on the REAL binary.
2. **Resilience**: If a tool fails, explain *why* (e.g., "Dependency ffmpeg missing") so the agent can report it accurately.
3. **Speed**: Colonize only what is needed. Don't build a 100-command CLI if 5 commands solve the business problem.
