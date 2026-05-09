# Session Handoff - Vercel/Hostinger Routing + Coordination Claims - 2026-05-05

## TL;DR
Short session focused on two governance fixes: (1) clarifying that Vercel is preview/testing only and Hostinger is the production deploy path for all websites, and (2) updating the coordination claim rule to require claims in ALL sessions including direct (Boubacar-present) ones, because multiple agents run concurrently.

## What was built / changed
- `skills/vercel-launch/SKILL.md` — description + body rewritten: preview/client-sharing only, never production; output template updated with Hostinger reminder
- `skills/clone-builder/SKILL.md` — Phase 4 split into Step 1 (Vercel preview) + Step 2 (Hostinger production when Boubacar approves)
- `docs/SKILLS_INDEX.md` — 4 descriptions updated: vercel-launch, deploy-to-vercel, vercel-cli-with-tokens (preview only), hostinger-deploy (THE production path)
- `~/.claude/skills/deploy-to-vercel/SKILL.md` — Boubacar rule banner added at top
- `~/.claude/skills/hostinger-deploy/SKILL.md` — "production deploy path" banner added at top
- `CLAUDE.md` — coordination claim rule updated: all sessions claim branch+files, direct sessions skip [READY]+push only

Commits: `c86db2a` (skill files), `584a13a` (CLAUDE.md)

## Decisions made
- **Vercel = preview only.** Never propose Vercel for live/production sites. Triggers: "preview link", "share with client", "test on mobile".
- **Hostinger = all production.** Default when site needs to go live. Use `hostinger-deploy` skill.
- **Coordination claims apply to ALL sessions** (Option B chosen by Boubacar). Direct sessions claim but skip [READY]+push. Rationale: multiple agents can run concurrently even in direct sessions.

## What is NOT done (explicit)
- `vercel-cli-with-tokens` skill body not updated (only SKILLS_INDEX description). If that skill's internal content needs the same banner treatment, do it next session.
- Did NOT use coordination claims THIS session (the rule was being written). Apply retroactively next session.

## Open questions
- Should `clone-builder` eventually default to Hostinger for even the preview step, or keep Vercel for that? Currently: Vercel for preview, Hostinger for live.

## Next session must start here
1. Claim `branch:main` before any file edits: `from skills.coordination import claim; claim('branch:main', '<agent-id>', ttl_seconds=7200)`
2. Claim each file before editing
3. Complete claims after edits

## Files changed this session
- `skills/vercel-launch/SKILL.md`
- `skills/clone-builder/SKILL.md`
- `docs/SKILLS_INDEX.md`
- `CLAUDE.md`
- `~/.claude/skills/deploy-to-vercel/SKILL.md`
- `~/.claude/skills/hostinger-deploy/SKILL.md`
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_vercel_preview_only.md` (new)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_coordination_claims_all_sessions.md` (new)
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md` (updated)
