---
name: vercel-launch
description: Full app launch workflow for Boubacar's projects. Use when user says "deploy my app", "launch my app", or "push <name> to Vercel". Creates the app folder, GitHub repo, git history, Vercel link, and deploys. App name becomes <name>-app. ALWAYS deploy as preview by default. Only deploy to production when user explicitly says "go live" or "to production".
---

# Vercel Launch

Full one-command launch for apps in `output/apps/`. Handles folder creation, GitHub repo, git init/push, Vercel linking, and deployment.

## How It Works

1. Extract base name from user message → format as `<name>-app`
2. Locate or create `output/apps/<name>-app` (agentsHQ root auto-detected by OS)
3. Find `VERCEL_TOKEN` from `.env` chain: app folder → agentsHQ root → `~/.env`
4. Check if GitHub repo `bokar83/<name>-app` exists; create it (public) if not
5. Git init, commit, set remote, push to `main` (or push changes if already initialized)
6. Link to Vercel with `vercel link --repo`
7. Deploy: **ALWAYS preview by default**. Only use `--prod` if user explicitly said "go live" or "to production"
8. Report repo URL + preview/production URL

## Usage

```bash
bash ~/.claude/skills/vercel-launch/scripts/launch.sh <base-name> [--prod]
```

**Arguments:**
- `base-name` — App name without `-app` suffix. Spaces OK (e.g. `attire inspo` → `attire-inspo-app`)
- `--prod` — Deploy to production instead of preview

**Examples:**
```bash
# Preview deploy (default)
bash ~/.claude/skills/vercel-launch/scripts/launch.sh attire-inspo

# Production deploy
bash ~/.claude/skills/vercel-launch/scripts/launch.sh attire-inspo --prod

# Name with spaces (auto-normalized)
bash ~/.claude/skills/vercel-launch/scripts/launch.sh "budget tracker" --prod
```

## Environment

- **Laptop:** agentsHQ root = `D:/Ai_Sandbox/agentsHQ`
- **VPS:** agentsHQ root = `/root/agentsHQ`
- Auto-detected via `$OSTYPE` / `$OS`

## Output

Script writes progress to stderr and final JSON to stdout:

```json
{
  "appName": "attire-inspo-app",
  "repoUrl": "https://github.com/bokar83/attire-inspo-app",
  "previewUrl": "https://attire-inspo-app-abc123.vercel.app",
  "production": false
}
```

## Present Results to User

After the script completes, present results like this:

```
App launched!

Name:    attire-inspo-app
Repo:    https://github.com/bokar83/attire-inspo-app
Preview: https://attire-inspo-app-abc123.vercel.app

To go live: "deploy attire-inspo live"
```

If production deploy:
```
App is live!

Name:       attire-inspo-app
Repo:       https://github.com/bokar83/attire-inspo-app
Production: https://attire-inspo-app.vercel.app
```

## Naming Convention

Follows the same pattern as websites:
- `boubacarbarry-site`, `catalystworks-site` → websites
- `attire-inspo-app`, `budget-tracker-app` → apps

## Troubleshooting

**Token not found:** Check that `VERCEL_TOKEN=...` exists in `$AGENTS_ROOT/.env`

**gh auth error:** Run `gh auth login` in a terminal first

**Vercel link fails:** Try running `vercel login --token $VERCEL_TOKEN` manually, then retry

**Push rejected:** SSH key may not be set up for GitHub. Run `gh auth setup-git` to configure HTTPS fallback
