# vercel-launch Skill Design

**Date:** 2026-04-04
**Status:** Approved

## Summary

A Claude Code skill that handles the full lifecycle of launching a new app to Vercel: folder creation, GitHub repo creation, git init/push, Vercel linking, and preview deployment. One natural language phrase triggers the entire flow.

## Trigger Phrases

- "Deploy my app" / "Launch my app"
- "Push `<name>` to Vercel"
- "Deploy `<name>` and go live" (triggers production deploy)

## Naming Convention

- Base name extracted from user message (e.g. "attire inspo" or "attire-inspo")
- Folder and repo name formatted as `<name>-app` (e.g. `attire-inspo-app`)
- Matches existing pattern: `boubacarbarry-site`, `catalystworks-site`

## App Folder Location

- Always: `output/apps/<name>-app` relative to agentsHQ root
- Created if it does not exist

## Token Discovery (in order)

1. `.env` in the app folder
2. `.env` in agentsHQ root (auto-detected: `D:\Ai_Sandbox\agentsHQ` on laptop, `/root/agentsHQ` on VPS)
3. `~/.env` as last resort

## Full Flow (8 Steps)

1. Extract base name from user message, format as `<name>-app`
2. Locate or create `output/apps/<name>-app` folder
3. Find `VERCEL_TOKEN` from `.env` lookup chain
4. Check if GitHub repo `bokar83/<name>-app` exists; create it (public) if not
5. If no git history in folder: `git init`, commit all files, set remote, push to `main`
6. Link to Vercel: `vercel link --repo --token <token>`
7. Deploy: `vercel deploy --no-wait --token <token>` (preview default; `--prod` if "go live" was said)
8. Report: repo URL + preview URL formatted as a clean summary

## Output Format

```
App launched!

Repo:    https://github.com/bokar83/<name>-app
Preview: https://<name>-app-xyz.vercel.app

To go live: "deploy <name> live"
```

## Script

- Location: `~/.claude/skills/vercel-launch/scripts/launch.sh`
- Args: `<base-name> [--prod]`
- Stderr: progress messages
- Stdout: JSON `{ previewUrl, repoUrl, appName }`

## GitHub Defaults

- Visibility: public
- Default branch: main
- Owner: bokar83

## What This Skill Does NOT Do

- Does not scaffold app code (that is the future app-building agent's job)
- Does not manage DNS or custom domains
- Does not touch production unless explicitly told "go live"
