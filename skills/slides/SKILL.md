---
name: slides
description: Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide strategies. Triggers on 'slides', 'create slides', 'build a presentation', 'HTML deck', 'presentation', 'slide deck', 'pitch deck'.
argument-hint: "[topic] [slide-count]"
metadata:
  author: claudekit
  version: "1.0.0"
---

# Slides

Strategic HTML presentation design with data visualization.

<args>$ARGUMENTS</args>

## When to Use

- Marketing presentations and pitch decks
- Data-driven slides with Chart.js
- Strategic slide design with layout patterns
- Copywriting-optimized presentation content

## Subcommands

| Subcommand | Description | Reference |
|------------|-------------|-----------|
| `create` | Create strategic presentation slides | `references/create.md` |

## References (Knowledge Base)

| Topic | File |
|-------|------|
| Layout Patterns | `references/layout-patterns.md` |
| HTML Template | `references/html-template.md` |
| Copywriting Formulas | `references/copywriting-formulas.md` |
| Slide Strategies | `references/slide-strategies.md` |

## Routing

1. Parse subcommand from `$ARGUMENTS` (first word)
2. Load corresponding `references/{subcommand}.md`
3. Execute with remaining arguments

---

## Pre-ship gate: /design-audit (mandatory)

Before declaring a slide deck ready for delivery, run `/design-audit <path-to-deck.html>`. The audit scores 5 dimensions /20 (accessibility, performance, theming, responsive, anti-patterns) and writes a markdown audit to `workspace/design-audits/<deck-name>-audit.md`.

**Required scores to ship:**
- Total ≥ 15/20
- Anti-patterns ≥ 3/4 (the AI-slop dimension, the one most likely to fail)
- For Catalyst Works branded decks: ≥ 17/20

**If the audit fails, fix the flagged P0/P1 issues and re-audit before claiming the deck is done.** Common slide failures: Inter font (reflex-reject), side-stripe colored borders on cards, hero-metric template (giant number boxed in a card), glassmorphism panels, identical 3-card grids per content slide.

After multiple decks ship, render the rolled-up HTML report:
```bash
python D:\Ai_Sandbox\agentsHQ\scripts\design-audit\render_report.py --site <slide-set-prefix>
```
