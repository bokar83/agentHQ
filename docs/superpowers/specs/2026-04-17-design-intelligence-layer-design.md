# Design Intelligence Layer — Spec

**Date:** 2026-04-17
**Status:** Approved

---

## What This Builds

A design intelligence layer for agentsHQ so every visual artifact the system produces looks like it came from a premium firm — not a chatbot, not a template, not AI slop.

---

## Core Decisions (Locked)

1. **Single source of truth:** `docs/styleguides/` files are the only place brand decisions live. Agents and crews never hardcode colors, fonts, or layout rules. When the styleguide changes, all downstream output changes automatically on the next run.

2. **Design agent sits between planner and builder** in all visual output crews (website, app, consulting deliverable, 3D website). It is conditional — if the styleguide file fails to load, the crew runs exactly as before (no failure surfaced to user).

3. **On-demand design review** is the same agent in a standalone crew. Trigger: "review this design", "enhance this", "design review".

4. **Two modes based on output type:**
   - Catalyst Works branded output → always reads `styleguide_master.md` + format-specific guide. No selection, no Firecrawl, no decision file.
   - Non-branded output → Firecrawl extracts client brand assets (if URL available), design agent selects from `docs/design-references/` (awesome-design-md files), saves a `design_decision.md` artifact so future runs for the same project start from that decision.

5. **awesome-design-md references** are pre-fetched once and stored as static files in `docs/design-references/`. No runtime network calls. Added to `.gitignore`. Pushed to container via `docker cp`.

6. **No Telegram pause-and-ask.** Agent decides autonomously for all output types and states what it chose and why in its output report. (Council Chairman verdict: the pause-and-ask pattern has no blocking async support in the current orchestrator — it becomes a bypass in practice.)

7. **Design QA checklist** is built into the builder task description, not a separate agent. The builder self-scores against the design brief before returning output.

---

## Architecture

```
engine.py → assemble_crew() → build_*_crew()
                                    ↓
                    DesignContextLoader.load(task_type)
                    reads docs/styleguides/ (disk, no network)
                    returns formatted string or "" on failure
                                    ↓ (injected into builder + QA task descriptions only)
                    planner → researcher → [design_agent] → builder → QA
                                                ↓
                                Is this Catalyst Works output?
                                YES → read styleguide_master.md + format guide
                                NO  → Firecrawl client URL (if provided)
                                      pick from docs/design-references/
                                      save docs/design-decisions/<slug>.md
                                → produce concrete design brief for builder
                                ↓
                    builder reads brief → builds → self-scores against brief checklist
                                ↓
                    QA → save output

On-demand review:
  "review this design" / "enhance this design"
  → router: design_review task type → design_review_crew
  → design_agent (reviewer) → web_builder (apply fixes + save)
```

---

## Files Created or Modified

### New files

| File | Responsibility |
|------|---------------|
| `orchestrator/design_context.py` | `DesignContextLoader` class. Reads styleguide files from disk by task type. Returns formatted string. Resolves paths relative to `__file__` for Docker compatibility. |
| `docs/design-references/` (directory) | 59 awesome-design-md DESIGN.md files, pre-fetched via `npx getdesign@latest add <name>`. Not committed to git. |
| `docs/design-references/INDEX.md` | Maps each reference name to its file path and a one-line description of its design direction. Used by design agent for selection. |
| `docs/design-decisions/` (directory) | Per-project design decision files saved by design agent. Format: `<project-slug>.md`. Not committed to git. |
| `orchestrator/tests/test_design_context.py` | Unit tests for `DesignContextLoader`. |
| `scripts/fetch_design_references.sh` | Shell script to fetch all 59 awesome-design-md files into `docs/design-references/`. Run once, re-run to add new references. |

### Modified files

| File | Change |
|------|--------|
| `orchestrator/agents.py` | Add `build_design_agent()` function. |
| `orchestrator/crews.py` | (1) Add `build_design_review_crew()`. (2) Wire design agent into `build_website_crew()`, `build_app_crew()`, `build_consulting_crew()`, `build_3d_website_crew()`. (3) Add `"design_review_crew"` to `CREW_REGISTRY`. |
| `orchestrator/router.py` | Add `"design_review"` task type entry to `TASK_TYPES`. |
| `orchestrator/engine.py` | Add `"design_review"` to `_build_summary()` `type_labels` dict. |
| `docs/styleguides/styleguide_master.md` | Add `## AGENT USAGE` section at top: which sections agents must read for each output type, self-scoring checklist, anti-patterns list. |
| `.gitignore` | Add `docs/design-references/` and `docs/design-decisions/`. |

---

## DesignContextLoader Interface

```python
# orchestrator/design_context.py

class DesignContextLoader:
    STYLEGUIDE_MAP = {
        "website_build":           ["styleguide_master.md", "styleguide_websites.md"],
        "3d_website_build":        ["styleguide_master.md", "styleguide_websites.md"],
        "app_build":               ["styleguide_master.md", "styleguide_websites.md"],
        "consulting_deliverable":  ["styleguide_master.md", "styleguide_pdf_documents.md"],
        "general_writing":         ["styleguide_master.md", "styleguide_markdown.md"],
        "social_content":          ["styleguide_master.md", "styleguide_linkedin.md"],
        "linkedin_x_campaign":     ["styleguide_master.md", "styleguide_linkedin.md", "styleguide_x_twitter.md"],
    }

    @classmethod
    def load(cls, task_type: str) -> str:
        """
        Returns formatted design context string for injection into task descriptions.
        Returns "" if files not found (silent fallback — crew runs without design layer).
        """
        ...

    @classmethod
    def load_reference(cls, reference_name: str) -> str:
        """
        Load a single awesome-design-md reference by name (e.g. 'linear', 'stripe').
        Returns "" if not found.
        """
        ...
```

---

## Design Agent Task Flow

```
Task: design_brief

INPUT (from injected context + task description):
  - Injected styleguide content (already in task description)
  - user_request (what is being built)
  - Optional: client_url extracted from user_request

LOGIC:
  1. Is this Catalyst Works output?
     Keywords: "catalyst works", "boubacar", "my consulting", "our brand", "cw report"
     If YES: use injected styleguide content. Skip steps 2-4.

  2. Check docs/design-decisions/<slug>.md for prior decision.
     If found: load it. Skip step 3.

  3. If client URL present in request: use firecrawl_scrape to extract
     brand colors (hex), fonts, logo URL, key messaging.
     Then: read docs/design-references/INDEX.md, select most appropriate reference.
     If no URL: select from INDEX.md based on project type alone.

  4. Save design_decision.md to docs/design-decisions/<slug>.md

OUTPUT (design brief passed to builder via context=[task_design_brief]):
  - Exact hex values for: background, primary text, accent, secondary, border
  - Font stack: heading font + body font + mono font (with Google Fonts import URL)
  - Spacing scale (base unit)
  - Component style: button radius, card style, shadow level
  - Layout: max-width, grid columns, section padding
  - Anti-patterns: 3 specific things NOT to do for this output
  - Self-scoring checklist: 5 items builder must verify before returning output
  - If non-branded: which reference was used and why (1 sentence)
```

---

## Design Review Crew Structure

```
build_design_review_crew(user_request: str) -> Crew

Agent 1: design_agent (reviewer role)
  Task: analyze the existing output against the appropriate styleguide/reference
  Expected output: numbered list of specific fixes with exact values

Agent 2: web_builder_agent (apply fixes)
  Task: apply every fix from the review, save updated file
  context=[task_review]
  Expected output: complete revised HTML file saved via save_output
```

---

## Styleguide AGENT USAGE Section (to add to styleguide_master.md)

```markdown
## AGENT USAGE — Read This First

**Version check:** State "Loaded styleguide v[VERSION] — [DATE]" in your output before producing any branded artifact.

**Which sections to load by output type:**
- Website / App: this file + styleguide_websites.md
- PDF / Consulting report: this file + styleguide_pdf_documents.md
- Social content: this file + styleguide_linkedin.md (and styleguide_x_twitter.md for X)
- Markdown document: this file + styleguide_markdown.md

**Self-scoring checklist (run before returning any output):**
- [ ] Clay (#B47C57) appears somewhere in this artifact
- [ ] Midnight Navy (#071A2E) is used as the structural dark anchor
- [ ] No red tones anywhere (not for errors, warnings, or any state)
- [ ] Inter is used for headings/UI (not as body text display font)
- [ ] First visible element leads with a specific claim, not a category description

**Anti-patterns — never repeat these:**
- Purple gradients (any shade of purple as a dominant color)
- Three rounded boxes in a row as a features section
- Generic centered hero on white with stock illustration
- Excited preambles in copy ("We're thrilled to...", "Transform your...")
- Orange (#FF7A00) as a large section background
- Source Serif 4 / Inter used as display fonts at hero scale
- Shadow.md / card with rounded-2xl + shadow-lg on every element
```

---

## awesome-design-md Fetch Script

```bash
# scripts/fetch_design_references.sh
# Run from repo root. Fetches all 59 references into docs/design-references/

DESIGNS=(
  airbnb airtable apple bmw cal claude clay clickhouse cohere coinbase
  composio cursor elevenlabs expo ferrari figma framer hashicorp ibm
  intercom kraken lamborghini linear.app lovable minimax mintlify miro
  mistral.ai mongodb notion nvidia ollama opencode.ai pinterest posthog
  raycast renault replicate resend revolut runwayml sanity semrush sentry
  spacex spotify stripe supabase superhuman tesla together.ai uber vercel
  voltagent warp webflow wise x.ai zapier
)

mkdir -p docs/design-references
cd docs/design-references

for name in "${DESIGNS[@]}"; do
  echo "Fetching $name..."
  npx getdesign@latest add "$name" --output "${name}.md" 2>/dev/null || true
done

echo "Done. $(ls *.md | wc -l) references fetched."
```

---

## .gitignore Additions

```
docs/design-references/
docs/design-decisions/
```

---

## Docker Deploy Commands (post-implementation)

```bash
# 1. Fetch all design references locally
bash scripts/fetch_design_references.sh

# 2. Copy to running container
docker cp docs/design-references/ orc-crewai:/app/docs/design-references/

# 3. Copy new/modified orchestrator files
docker cp orchestrator/design_context.py orc-crewai:/app/orchestrator/design_context.py
docker cp orchestrator/agents.py orc-crewai:/app/orchestrator/agents.py
docker cp orchestrator/crews.py orc-crewai:/app/orchestrator/crews.py
docker cp orchestrator/router.py orc-crewai:/app/orchestrator/router.py
docker cp orchestrator/engine.py orc-crewai:/app/orchestrator/engine.py

# 4. Copy updated styleguide
docker cp docs/styleguides/styleguide_master.md orc-crewai:/app/docs/styleguides/styleguide_master.md

# 5. Restart orchestrator process (not full container restart)
docker exec orc-crewai pkill -f "uvicorn" && docker exec -d orc-crewai uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000
```

---

## Gaps Report (what this does NOT yet do)

| Gap | Impact | Next move |
|-----|--------|-----------|
| PDF rendering pipeline | HTML→PDF conversion not implemented. Design fidelity through CSS print rules only. | Add WeasyPrint or Puppeteer PDF export as a separate task in consulting crew. |
| n8n design context pass-through | When tasks are triggered via n8n webhook, design context is loaded from disk as normal — no special n8n wiring needed. But n8n has no visibility into which styleguide was loaded. | Add `design_reference_used` field to the result dict returned by `run_orchestrator()`. |
| Memory of design decisions across sessions | `docs/design-decisions/` files persist on disk in the container, not in Qdrant. Container restart wipes them. | Move design decisions to Qdrant or PostgreSQL in a future session. |
| Visual QA (screenshot-based) | The self-scoring checklist is text-only. No actual rendering check. | Integrate Playwright screenshot + vision model review as optional QA step. |
| awesome-design-md library growth | New references added to the GitHub repo won't auto-appear. | Re-run `scripts/fetch_design_references.sh` + `docker cp` when needed. |
