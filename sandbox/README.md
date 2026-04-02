# sandbox/

This is the agentsHQ **experimentation and testing workspace**.

## Purpose

Use `sandbox/` when you want to:

- Test a new tool, API, or integration before wiring it into the orchestrator
- Prototype a new agent or crew idea without touching production code
- Run one-off scripts that don't belong in `outputs/` (which is for real deliverables)
- Experiment with prompts, LLM responses, or data pipelines
- Park exploratory work that might become a real feature later

## Rules

1. **Nothing in here is production code.** It can be messy, half-finished, or broken.
2. **When a sandbox experiment graduates to production**, move the relevant code to `orchestrator/`, `agents/`, or `skills/` and delete the sandbox version.
3. **Do not import from sandbox/ in any orchestrator or crew code.** One-way door: production → sandbox (never).
4. **Scripts here are gitignored by default** (see `.gitignore` entry for `sandbox/tmp/`). If you want to commit a sandbox experiment, move it to a named subfolder and commit intentionally.
5. **Clean up periodically.** If a sandbox experiment is older than 30 days and hasn't graduated, either promote it or delete it.

## Structure (suggested)

```
sandbox/
├── README.md             ← This file
├── tools/                ← Testing individual tools (firecrawl, apollo, etc.)
├── prompts/              ← Prompt engineering experiments
├── crews/                ← Draft crew prototypes
├── integrations/         ← New API / service integrations
└── tmp/                  ← Throw-away scripts (gitignored)
```

## Relationship to outputs/

| `sandbox/` | `outputs/` |
|-----------|-----------|
| Work in progress | Finished deliverables |
| Experiments, prototypes | Real results from live crews |
| Gitignored by default | Committed (agent-generated content) |
| You write the code | Crews generate the content |

## Previously used for this

Before `sandbox/` existed, the `Dashboards4Sale/tmp/` folder was used as an ad-hoc sandbox for Google Sheets API scripts. Those scripts have been moved to `projects/dashboards_builder/`. If you are looking for them, they are there.
