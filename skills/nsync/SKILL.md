---
name: nsync
description: Use at the start or end of any session to verify and sync GitHub, local, and VPS are on the same commit. Triggers on "/nsync", "sync repos", "check sync", "are we in sync", or "before we close".
---

# nsync

Verify and sync three locations — **GitHub**, **local** (`d:\Ai_Sandbox\agentsHQ`), and **VPS** (`/root/agentsHQ`) — to the same commit. Fast. No guessing.

## Step 1 — Gather state in parallel

Run all three simultaneously:

```bash
# Local
git rev-parse HEAD && git status --short

# GitHub (fetch first so origin/main is current)
git fetch origin && git rev-parse origin/main

# VPS
ssh root@72.60.209.109 "cd /root/agentsHQ && git rev-parse HEAD && git status --short"
```

## Step 2 — Compare

Build a quick table:

| Location | Commit | Clean? |
|----------|--------|--------|
| GitHub   | `abc123` | — |
| Local    | `abc123` | modified files? |
| VPS      | `abc123` | modified files? |

**If all three match and no dirty working trees → done. Report "All in sync at `<hash>`."**

## Step 3 — Auto-resolve (no user input needed)

These situations are safe to handle automatically:

| Situation | Action |
|-----------|--------|
| Local is behind GitHub, working tree clean | `git pull origin main` |
| VPS is behind GitHub, working tree clean | `ssh … git pull origin main` |
| Local is ahead of GitHub, working tree clean | `git push origin main` |
| VPS is ahead of GitHub, working tree clean — and VPS remote has auth | `ssh … git push origin main` |

**VPS push requires a working token.** The token lives in the VPS remote URL. If push fails with auth error, skip to Step 4.

## Step 4 — Stop and ask when there's ambiguity

Pause and present options when:

- A location has **uncommitted modified files** (don't auto-commit without asking)
- There are **merge conflicts**
- The **VPS token is expired** (push auth failure)
- Local and VPS have **diverged from each other** (not just from GitHub)

Present the situation clearly, show which files are affected, and offer 2-3 options. Do not proceed until the user decides.

## Step 5 — Final verification

After any sync actions, re-run `git rev-parse HEAD` on all three and confirm they match. Report result.

## Known facts about this repo

- VPS path: `/root/agentsHQ`
- VPS remote URL format: `https://<token>@github.com/bokar83/agentHQ.git`
- Local uses GitHub CLI for auth (no token needed in URL)
- Local may have untracked files that are not in git — these are ignored unless they conflict with a pull

## Speed rules

- Always run local + GitHub + VPS checks **in parallel** (3 Bash calls in one message)
- Never run sequential checks you can parallelize
- Do not explain steps as you go — just run them and report the result table
