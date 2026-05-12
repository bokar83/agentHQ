---
name: active
description: Index for the active skill workspace — lists in-progress mirrored skills under skills/active/. Use when the user asks "what's in the active workspace", "show me the active skills", "list dispatched skills", or wants to find the active version of a mirrored skill. Triggers on "active workspace", "active skills", "active bundle", "list active", "show me what's in active".
---

# Active Skill Workspace Index

This is an index folder, not a procedural skill. It catalogs in-progress and mirrored skill assets stored under `skills/active/`. Each child entry is a real skill with its own SKILL.md or executable.

## Sub-skills

| Path | Type | Notes |
|------|------|-------|
| `agentshq-dispatch` | symlink → `../library/agentshq-dispatch` | Routes to the canonical dispatch skill in `library/`. Don't edit here — edit the target. |

## Procedure

When asked about an "active" skill or workspace:

1. Read this file to confirm what's listed
2. Route to the named child skill (open its SKILL.md or follow the symlink target)
3. If the requested skill is not listed, check `skills/library/` and `skills/CatalystWorksSkills/`

## Output Contract

This skill produces no artifacts. It is a routing index only.

## Failure Modes

- Treating `skills/active/` as a place to author new skills. It is a workspace pointer; new skills go in their own top-level folder under `skills/`.
- Editing the `agentshq-dispatch` symlink-text file. Edit `skills/library/agentshq-dispatch/` instead.
