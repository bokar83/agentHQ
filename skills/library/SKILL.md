---
name: library
description: Index for shared internal skill library assets — lists reusable capability packs (cole-templates, agentshq-dispatch) under skills/library/. Use when looking for canonical content templates, cross-skill dispatch logic, or shared references that multiple skills consume. Triggers on "skill library", "shared library", "library assets", "cole templates", "dispatch", "list library", "what's in the library".
---

# Shared Skill Library Index

This is an index folder for cross-skill assets that multiple top-level skills consume. Each child is a real, callable resource — either a skill (with SKILL.md) or a reference template pack.

## Sub-resources

| Path | Type | Purpose |
|------|------|---------|
| `agentshq-dispatch/` | skill | Cross-skill dispatch entry point (`SKILL.md` + `dispatch.sh`). Routes work to the right downstream skill based on intent. |
| `cole-templates/` | reference pack | 102 Nicolas Cole content templates (LinkedIn hooks, long-form, short-form, X hooks). Absorbed 2026-05-11 (G1). Used by content_multiplier + ctq-social. |

## Procedure

When asked to use a shared template or dispatch logic:

1. Identify the requested resource by name (cole-templates, agentshq-dispatch)
2. Open the resource's folder; read its SKILL.md if it has one, or the relevant template file
3. For cole-templates: pick the matching format file based on platform/length intent
4. For agentshq-dispatch: invoke `dispatch.sh` or follow its SKILL.md procedure

## Output Contract

This skill is a routing index. Returns the path to the requested resource. The downstream resource produces the actual artifact.

## Failure Modes

- Auto-applying cole-templates without checking if the format matches Boubacar's voice (per `feedback_cole_format_vs_engagement` and the G4 narrow A/B in absorb-followups.md, only 8 format families have validated lift)
- Editing `library/SKILL.md` to add procedure logic. Procedure belongs in the child resource's own SKILL.md.
