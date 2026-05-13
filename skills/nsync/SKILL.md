---
name: nsync
description: Use at the start or end of any session to verify and sync GitHub, local, and VPS to the same commit AND leave the VSCode Source Control panel empty. Triggers on "/nsync", "sync repos", "check sync", "are we in sync", or "before we close".
---

# nsync

Bring **GitHub**, **local** (`d:\Ai_Sandbox\agentsHQ`), and **VPS** (`/root/agentsHQ`) to the same commit AND leave the VSCode Source Control panel showing zero items (tracked-modified **and** untracked). Fast. No guessing.

## The real goal

The Source Control panel counts both `M` (tracked-modified) and `??` (untracked) entries. "All synced" is not done if the panel still shows items. Every leftover must land in one of four buckets:

1. **Commit**: it belongs in the repo
2. **Gitignore**: it's machine-local / runtime / generated
3. **Delete**: it's orphaned scratch / dead / accidental
4. **Escalate**: it's ambiguous (large file, secrets risk, unknown origin)

No fifth bucket. "Leave it there" is not an option.

## Step 1. Gather state in parallel

Run all three simultaneously (3 Bash calls in one message):

```bash
# Local
git rev-parse HEAD && git status --short

# GitHub (fetch so origin/main is current)
git fetch origin && git rev-parse origin/main

# VPS
ssh root@72.60.209.109 "cd /root/agentsHQ && git rev-parse HEAD && git status --short"
```

## Step 2. Compare commits

| Location | Commit | Working tree |
|----------|--------|--------------|
| GitHub   | `abc123` | n/a |
| Local    | `abc123` | items? |
| VPS      | `abc123` | items? |

If all three hashes match AND both working trees are empty, you're done. Report `All in sync at <hash>, Source Control empty.`

## Step 3. Sync commits (auto-resolve)

Handle these without asking:

| Situation | Action |
|-----------|--------|
| Local behind GitHub, tree clean | `git pull origin main` |
| VPS behind GitHub, tree clean | `ssh ... git pull origin main` |
| Local ahead of GitHub, tree clean | `git push origin main` |
| VPS ahead of GitHub, tree clean, VPS token works | `ssh ... git push origin main` |
| Local has staged but uncommitted files | Commit with descriptive message, push |
| Local has modified tracked files | Stage, commit, push |
| Submodule has modified tracked files | Commit inside submodule, update parent pointer, push both |
| Nested submodule (`output/apps/*`, `output/websites/*`) modified | Commit at deepest level first, bubble pointer up each level |

If VPS push fails with auth error, go to Step 5 (escalate).

## Step 4. Triage leftover items (the new discipline)

After commits sync, list every remaining entry in `git status --short` at every level (parent repo, `output/` submodule, each nested submodule, any other submodule like `skills/community/`). Classify each into one of four buckets:

### Bucket A. Commit

- Project code, configs, docs, skill files, migrations
- Meant to be shared across machines

### Bucket B. Gitignore

Add to the right `.gitignore`:

- Runtime data: `*.log`, `session_log.jsonl`, `data/`, `.tmp/`, SQLite dbs
- Generated artifacts: `.next/`, `build/`, `coverage/`, bundles
- Secrets & baselines: `.env*`, `secrets/`, `.secrets.baseline.new`
- Scratch dirs: `scratch/`, `tmp/`, `codex_ssh/`
- Machine-local tool dirs: `.vscode/settings.json`, `.idea/`, `node_modules/`
- Ephemeral test files: `test_*.py` at repo root, `*.chunk`, `tmp_upload/`
- Archived folders: `websites/*.ARCHIVED/`

For items inside a submodule whose `.gitignore` is upstream-managed (e.g. `skills/community/`), use `.git/modules/<path>/info/exclude` or `<submodule>/.git/info/exclude` for machine-local ignores. Never commit them upstream.

### Bucket C. Delete

- Unknown scratch files the user didn't create intentionally
- `.DS_Store`, `Thumbs.db`, `desktop.ini` that slipped past gitignore
- `.temp-execution-*.js`, stale `package-lock.json` in skill dirs
- Archived site folders with no recovery value

Use `rm` (or `Remove-Item` on PS). Never `git rm --cached` for untracked files (they're already not tracked).

### Bucket D. Escalate (Step 5)

Any item where any of these are true:

- Contains or might contain secrets (`.env*`, `*.key`, `credentials*`, token files)
- Larger than ~10 MB
- You cannot tell what created it or whether it's load-bearing
- Appears inside a standalone nested repo (e.g. `output/websites/humanatwork-site/` is a separate GitHub repo, not a submodule)
- Part of an in-flight branch or uncommitted work you didn't author in this session

## Step 5. Escalate ambiguous items

Pause and present to the user. Show:

- The file path
- Size / type / first hint of contents (safe preview, never cat secrets)
- Your recommendation and 2 to 3 alternatives

Do not proceed until the user decides. Buckets B/C actions are reversible; escalate anything that isn't.

## Step 6. Final verification

Silently run the local IDE skill link refresh before the final status checks:

```bash
python scripts/setup_local_agents.py >/dev/null 2>&1 || true
```

**Then sync submodule URLs on VPS (before submodule update). 2026-05-13 incident: VPS's `output/.git/config` was stuck on a stale URL (`attire-inspo-app.git`) while `.gitmodules` said `signal-works-demo-hvac.git`. `git pull` does NOT propagate `.gitmodules` URL changes to existing submodule `.git/config`. Result: `git submodule update` fails with "not our ref" even when the SHA is on the correct remote.**

```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git submodule sync --recursive && git submodule update --init --recursive"
```

`git submodule sync` rewrites each submodule's `.git/config` URL from `.gitmodules`. Cheap, idempotent. Always run on VPS after pulling main, before declaring sync.

Re-run all three checks in parallel. Confirm:

1. All three locations on the same commit hash
2. Local `git status --short` is empty (no `M`, no `A`, no `??`)
3. VPS `git status --short` is empty
4. Every submodule (`output/`, `skills/community/`, plus any nested) is also empty when checked with `git -C <path> status --short`

If a submodule update fails with `remote error: upload-pack: not our ref <SHA>`, FIRST GUESS is stale URL. Run `git submodule sync <path>` on that consumer before investigating the SHA itself.

If anything still shows up, go back to Step 4. Do not report success until the Source Control panel is empty.

Report the final table and a one-line per-location summary of what was triaged (e.g. `local: committed 2, gitignored 4, deleted 1`).

## Known facts about this repo

- VPS path: `/root/agentsHQ`
- VPS remote URL: `https://<token>@github.com/bokar83/agentHQ.git`
- Local uses GitHub CLI for auth (no token in URL)
- `output/` is a git submodule with its own `.gitignore` at `output/.gitignore`
- `output/apps/*` and `output/websites/*` may be nested submodules; commit deepest first, then bubble pointers up
- `output/websites/humanatwork-site/` is a **standalone repo** (not a submodule of `output/`). It tracks itself; don't commit its pointer from `output/`
- `skills/community/` is a submodule whose upstream is not ours. Use `skills/community/.git/info/exclude` for machine-local ignores; never edit its tracked `.gitignore`
- `.secrets.baseline.new` is regenerated by the pre-commit hook every run. Always in the ignore list, never commit

## Speed rules

- Always run local + GitHub + VPS checks **in parallel** (3 Bash calls in one message)
- Batch all gitignore edits and deletes into one message per level before re-checking
- Never run sequential checks you can parallelize
- Report the final table only; don't narrate each step
