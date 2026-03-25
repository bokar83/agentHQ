---
name: General feedback and preferences
description: Corrections and preferences Boubacar has given — apply these without being reminded
type: feedback
---

## File Location

- **Never create files or directories on C: drive.** All project files go in D:\Ai_Sandbox\agentsHQ or D:\Ai_Sandbox\ at minimum.
- If the memory system path points to C:, do NOT create it. Store context files in D:\Ai_Sandbox\agentsHQ\docs\memory\ instead.
- If a directory doesn't exist before writing files, ask before creating it — unless it's clearly inside D:\Ai_Sandbox\.

## Memory / Context

- Session context lives at D:\Ai_Sandbox\agentsHQ\docs\memory\ and is excluded from git via .gitignore.
- At the start of each session, read this folder for context before doing anything.
