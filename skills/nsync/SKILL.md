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

**Dirty working tree = modified tracked files or staged-but-uncommitted files. Untracked files (shown as `??`) are ignored.**

## Step 3 — Auto-resolve (no user input needed)

These situations are safe to handle automatically:

| Situation | Action |
|-----------|--------|
| Local is behind GitHub, working tree clean | `git pull origin main` |
| VPS is behind GitHub, working tree clean | `ssh … git pull origin main` |
| Local is ahead of GitHub, working tree clean | `git push origin main` |
| VPS is ahead of GitHub, working tree clean — and VPS remote has auth | `ssh … git push origin main` |
| Local has staged files not yet committed | Commit them with a descriptive message, then push |
| Local has modified tracked files not yet staged | Stage and commit them, then push |
| Submodule has staged/modified tracked files | Commit inside the submodule first, then update parent pointer, then push both |

**VPS push requires a working token.** The token lives in the VPS remote URL. If push fails with auth error, skip to Step 4.

**Goal: working tree must be zero (no M, no A, no staged changes) on both local and VPS after nsync completes.**

## Step 4 — Stop and ask when there's ambiguity

Pause and present options when:

- A location has **modified tracked files** whose content you're unsure should be committed (e.g. large generated files, secrets)
- There are **merge conflicts**
- The **VPS token is expired** (push auth failure)
- Local and VPS have **diverged from each other** (not just from GitHub)

Present the situation clearly, show which files are affected, and offer 2-3 options. Do not proceed until the user decides.

## Step 5 — Final verification

After any sync actions, re-run all three checks in parallel and confirm:
1. All three locations are on the same commit hash
2. Local `git status --short` shows only `??` untracked lines (no `M`, no `A`)
3. VPS `git status --short` is clean

Report the final table. If working trees are still dirty, go back to Step 3.

## Known facts about this repo

- VPS path: `/root/agentsHQ`
- VPS remote URL format: `https://<token>@github.com/bokar83/agentHQ.git`
- Local uses GitHub CLI for auth (no token needed in URL)
- Local may have untracked files (`??`) that are not in git — these are ignored and do NOT block sync
- `output/` is a git submodule — if it shows as modified, check inside it with `git -C output status --short` and commit staged/tracked changes inside the submodule before updating the parent pointer
- `output/apps/*` and `output/websites/*` may themselves be nested submodules — if `output` still shows `m` after committing session_log/calculatorz-site, run `git -C output status --short` and look for lowercase `m` entries, then check each with `git -C output/apps/<name> status --short` and commit tracked changes there too before updating pointers up the chain
- **The goal is a fully empty source control panel in VSCode.** Every `M` (tracked modified) at every level must be committed and pushed. Only `??` untracked entries and the `.secrets.baseline.new` file are acceptable leftovers.

## Speed rules

- Always run local + GitHub + VPS checks **in parallel** (3 Bash calls in one message)
- Never run sequential checks you can parallelize
- Do not explain steps as you go — just run them and report the result table
