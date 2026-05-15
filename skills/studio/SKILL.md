---
name: studio
description: Studio references and pattern docs supporting the studio_*.py orchestrator modules. Not a user-invocable skill. Contains internal references like youtube-hook-patterns.md used by trend_scout and script_generator. Trigger only on internal reference lookups, never via Boubacar slash command.
---

# Studio (references-only)

This is a references-only support skill for the Studio orchestrator modules in `orchestrator/studio_*.py`. It is NOT a user-invocable Boubacar skill.

## Why this exists

The pre-commit lint requires every `skills/<dir>/` to contain a SKILL.md. `skills/studio/references/` holds support docs (e.g., `youtube-hook-patterns.md`) consumed by studio code, but the directory predates the skill-frontmatter rule. This stub satisfies lint without inventing user-facing behavior.

## Contents

- `references/youtube-hook-patterns.md` — hook patterns used by `studio_trend_scout.py` and `studio_script_generator.py`.

## Not for invocation

Do not call this as a skill via the Skill tool. The directory exists only to host module-level reference docs. Studio user-facing operations live in:

- `orchestrator/studio_*.py` modules
- `docs/roadmap/studio.md` (planning artifact)
- `skills/boubacar-skill-creator/` (for building new Studio sub-skills)
