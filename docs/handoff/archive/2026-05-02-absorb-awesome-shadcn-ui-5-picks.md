# Session Handoff - awesome-shadcn-ui absorb (5 surgical picks) - 2026-05-02

## TL;DR

Full /agentshq-absorb run on birobirobiro/awesome-shadcn-ui (~400 entries). After Sankofa/Karpathy and multiple framing refinements, landed on 5 cherry-picked items from the list, each integrated as a behavior change inside an existing skill rather than a new skill or reference dump. Commit e9ce02f on main. Three-way sync verified (local + GitHub + VPS all at bef06c5). Citation-check routine armed for 2026-05-15 (trig_01872JML9WrBFNsSPGrzh7nP).

## What was built / changed

**New files (committed e9ce02f):**
- `skills/ui-styling/references/shadcn-agent-ui.md`: 21st.dev Agent Elements as the canonical start for agent/chat/tool-call UIs
- `skills/ui-styling/references/shadcn-pdf.md`: pdfx as the structured-PDF lane (invoice, SOW, statement)

**Modified files (same commit):**
- `skills/ui-styling/references/shadcn-theming.md`: tweakcn theme generator section appended at bottom
- `skills/clone-builder/SKILL.md`: one-line tweakcn pointer at scaffold/globals.css step (line 183)
- `skills/frontend-design/SKILL.md`: "Specialized contexts (defer to ui-styling)" block added after CRAFT REFERENCE LIBRARY section
- `skills/design/SKILL.md`: structured-PDF routing row added to sub-skill table (line 33)
- `skills/seo-strategy/SKILL.md`: Mode 2 revenue-weighted prioritization rule added after Mode 2 Workflow Overview
- `docs/reviews/absorb-log.md`: verdict appended
- `docs/reviews/absorb-followups.md`: 5-edit followup appended, target 2026-05-15
- `.secrets.baseline`: updated by detect-secrets hook (line number shifts)

**User-level only (NOT in repo):**
- `~/.claude/skills/design-audit/SKILL.md`: Mode 4 (memoire-backed token-drift extraction) added after Mode 3

**Memory:**
- New: `memory/feedback_large_repo_cherry_pick_not_import.md`
- Indexed at MEMORY.md line 80 (chained with Karpathy/Sankofa rule)

**Routine:**
- `trig_01872JML9WrBFNsSPGrzh7nP` fires 2026-05-15T15:00:00Z: citation check, auto-removes uncited refs, updates absorb-followups.md

## Decisions made

1. **Large-repo absorb = cherry-pick, never index-mirror.** Karpathy discipline applies at the absorb layer, not just the code layer. Codified as a HARD RULE in `feedback_large_repo_cherry_pick_not_import.md`.

2. **Post-shadcn-ui-handoff routing:** all shadcn-substrate picks route through `ui-styling` (canonical home). frontend-design, clone-builder, design all get one-line pointers rather than full integrations.

3. **design-audit lives in user-level skills** (`~/.claude/skills/`), not agentsHQ. Edits there do NOT sync via nsync and are NOT in git. This is a known surface boundary: log it in absorb-followups when it happens.

4. **Revenue-weighted SEO prioritization** (from auditzap framing): Mode 2 fix lists now sort by revenue lever first, severity second. The framing was absorbed, not the tool.

5. **Citation kill-switch discipline:** any absorb edit that earns zero real citations by the target date gets removed via PR. The routine enforces this automatically.

6. **Sankofa/Karpathy calibration:** both were run but the Council was too conservative on free public web tools (pilot ceremonies for tools you can test in 2 minutes is overkill). The right posture: Sankofa for placement decisions, Karpathy for integration plans. Free tools get a 5-minute test-drive, not a scheduled pilot.

## What is NOT done (explicit)

- **v4.6.0 content sweep** of the three demoted shadcn reference files (`shadcn-components.md`, `shadcn-theming.md`, `shadcn-accessibility.md`): pending. The scheduled routine `trig_013N5SeBrAtcyMQm4bufYwxt` handles this on 2026-05-09. Do NOT redo manually unless that routine fails.
- **memoire CLI verification**: not run this session. Mode 4 is written into design-audit SKILL.md but the actual `npx m-moire diagnose <url>` command has not been tested. The "adds beyond rubric" bar will be defined on first real invocation.
- **tweakcn output quality test**: not run. The "on-brand bar" will be defined on first clone-builder invocation that uses it.
- **markitdown helper script**: separate open followup from 2026-05-02 `scripts/markitdown_helper.py`. Target 2026-05-09.

## Open questions

- None blocking. The parallel session added 3 common-mistakes entries to agentshq-absorb/SKILL.md (commit 4d0a234): worth reviewing to see what patterns it captured before the next absorb run.

## Next session must start here

1. Read `git log --oneline -5` to confirm you're at `bef06c5` on main.
2. If any new absorb target is queued, run `/agentshq-absorb <url>`: Phase 1 registry check will auto-surface all prior verdicts.
3. If it's 2026-05-09 or later, check if `trig_013N5SeBrAtcyMQm4bufYwxt` ran successfully (v4.6.0 shadcn content sweep). If not, run the sweep manually: update `shadcn-components.md`, `shadcn-theming.md`, `shadcn-accessibility.md` with v4 content from `skills/ui-styling/cache/`.
4. If it's 2026-05-09 or later, check if `markitdown_helper.py` followup was completed. If not, implement it: `pip install markitdown`, write `scripts/markitdown_helper.py`, validate on 3 artifacts.

## Files changed this session

```
docs/handoff/2026-05-02-absorb-awesome-shadcn-ui-5-picks.md  (this file)
docs/reviews/absorb-log.md
docs/reviews/absorb-followups.md
skills/clone-builder/SKILL.md
skills/design/SKILL.md
skills/frontend-design/SKILL.md
skills/seo-strategy/SKILL.md
skills/ui-styling/references/shadcn-agent-ui.md  (new)
skills/ui-styling/references/shadcn-pdf.md  (new)
skills/ui-styling/references/shadcn-theming.md
.secrets.baseline
~/.claude/skills/design-audit/SKILL.md  (user-level, not in repo)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_large_repo_cherry_pick_not_import.md
```

## Sync state at close

| Surface | HEAD |
|---|---|
| Local | bef06c5 |
| GitHub origin/main | bef06c5 |
| VPS /root/agentsHQ | bef06c5 |
