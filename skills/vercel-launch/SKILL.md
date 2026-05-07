---
name: vercel-launch
description: Vercel preview deploy for Boubacar's apps — for mobile testing and sharing preview links with clients ONLY. NOT for production. All live/production deployments go to Hostinger (use hostinger-deploy skill). Use when user says "deploy my app to Vercel", "get me a preview link", "share this with a client", or "test on mobile". App name becomes <name>-app. ALWAYS preview only — never production.
---

# Vercel Launch

> **SCOPE: Preview & client sharing only.** Vercel = mobile testing + shareable preview links.
> **ALL production/live deployments go to Hostinger.** Never propose Vercel for a live site.

Full one-command preview launch for apps in `output/apps/`. Handles folder creation, GitHub repo, git init/push, Vercel linking, and preview deployment.

## How It Works

1. Extract base name from user message → format as `<name>-app`
2. Locate or create `output/apps/<name>-app` (agentsHQ root auto-detected by OS)
3. Find `VERCEL_TOKEN` from `.env` chain: app folder → agentsHQ root → `~/.env`
4. Check if GitHub repo `bokar83/<name>-app` exists; create it (public) if not
5. Git init, commit, set remote, push to `main` (or push changes if already initialized)
6. Link to Vercel with `vercel link --repo`
7. Deploy: **ALWAYS preview. Never `--prod`.** Vercel is never the production host.
8. Report repo URL + preview URL. Remind user: "To go live, use Hostinger deploy."

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
Preview ready!

Name:    attire-inspo-app
Repo:    https://github.com/bokar83/attire-inspo-app
Preview: https://attire-inspo-app-abc123.vercel.app

Share this link for client review or mobile testing.
To go LIVE (production): use Hostinger deploy — say "deploy to Hostinger".
```

**Never present a Vercel URL as a production/live deployment.** Always remind user that Hostinger is the live host.

## Naming Convention

Follows the same pattern as websites:
- `boubacarbarry-site`, `catalystworks-site` → websites
- `attire-inspo-app`, `budget-tracker-app` → apps

## Token Auth (no interactive login)

When `vercel login` is unavailable (CI, sandbox, VPS), use token auth:

```bash
# NEVER pass as --token flag (exposed in shell history)
export VERCEL_TOKEN=$(grep '^VERCEL_TOKEN=' .env | cut -d= -f2-)
vercel deploy -y --no-wait
```

If `VERCEL_ORG_ID` + `VERCEL_PROJECT_ID` are both set, no linking step needed.

## Managing Env Vars

```bash
echo "value" | vercel env add VAR_NAME --scope <team-slug>
vercel env ls --scope <team-slug>
vercel env pull --scope <team-slug>   # pull to local .env
vercel env rm VAR_NAME --scope <team-slug> -y
```

## Troubleshooting

**Token not found:** Check that `VERCEL_TOKEN=...` exists in `$AGENTS_ROOT/.env`

**gh auth error:** Run `gh auth login` in a terminal first

**Vercel link fails:** Try running `vercel login --token $VERCEL_TOKEN` manually, then retry

**Push rejected:** SSH key may not be set up for GitHub. Run `gh auth setup-git` to configure HTTPS fallback

**Build failure:** `vercel logs <deployment-url>` — common causes: missing deps, missing env vars, wrong framework in `vercel.json`
