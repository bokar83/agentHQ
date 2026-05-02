# sandbox/

This is the agentsHQ **experimentation and in-flight work workspace**.

## Purpose

Use `sandbox/` when you want to:

- Test a new tool, API, or integration before wiring it into the orchestrator
- Prototype a new agent or crew idea without touching production code
- Park in-flight builds that aren't ready for `skills/`, `output/websites/`, or their own repo yet
- Experiment with prompts, LLM responses, or data pipelines
- Keep exploratory work safe (committed to GitHub) while you iterate

## Rules

1. **`sandbox/` IS tracked in git.** In-flight work is saved so the laptop dying does not lose it. Throwaway content goes in `sandbox/.tmp/` (gitignored).
2. **No secrets, no credentials, no PII, no env vars.** The pre-commit secret scan applies here. If something needs a secret, put the secret in `secrets/` (gitignored) and reference it from sandbox.
3. **Nothing in here is production code.** It can be messy, half-finished, or broken.
4. **One-way door:** production → sandbox is fine (copy a file in to experiment). Sandbox → production requires graduating: move the file to its real home (`orchestrator/`, `skills/`, `output/`, etc.) and remove the sandbox copy.
5. **No imports from sandbox/ in orchestrator or crew code.** Sandbox is never the source of truth.
6. **Each subfolder needs a README.md.** One sentence on what it is, when it can be archived. No README + 60d untouched = candidate for `zzzArchive/`.
7. **Monthly sweep.** First of the month: anything in `sandbox/` not touched in 30 days gets reviewed. Either graduate (promote to its real home) or archive (move to `zzzArchive/_sandbox-sweep-<date>/`). **Nothing is deleted, ever.**

## Structure (suggested)

```
sandbox/
├── README.md             ← This file
├── tools/                ← Testing individual tools (firecrawl, apollo, etc.)
├── prompts/              ← Prompt engineering experiments
├── crews/                ← Draft crew prototypes
├── integrations/         ← New API / service integrations
└── .tmp/                 ← Throwaway scripts (gitignored)
```

## sandbox/ vs other in-flight folders

| If the work is... | It belongs in... |
|---|---|
| A new skill being prototyped | `sandbox/` until it has a name and a SKILL.md, then `skills/<name>/` |
| A website being built | `output/websites/<slug>/` (its own dev branch): never sandbox |
| An app being built | `output/apps/<slug>-app/`: never sandbox |
| A new client engagement | `workspace/clients/<slug>/`: never sandbox |
| Brand work for Catalyst Works | `workspace/catalyst-works/`: never sandbox |
| A throwaway probe / log dump | `sandbox/.tmp/` (gitignored) |
| A satellite product (Dashboards4Sale, etc.) | Its own GitHub repo: never sandbox |

## Hard rule

**The word "delete" does not exist in agentsHQ.** When sandbox content is no longer needed, it is **archived to `zzzArchive/`** with a manifest entry, never deleted. If we ever need it back, the archive is the index.

## Previously used for this

Before `sandbox/` existed, the `Dashboards4Sale/tmp/` folder was used as an ad-hoc sandbox for Google Sheets API scripts. Those scripts have been moved to `projects/dashboards_builder/`. If you are looking for them, they are there.
