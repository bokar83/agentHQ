---
owner: workspace + satellites
status: active / submodule + nested-submodules
---

# output/ folder anatomy (reference doc; NOT inside the submodule)

> **Why this lives in `docs/reference/` and not at `output/AGENTS.md`:** `output/` is a git submodule, so any file written inside it would commit to the submodule's git repo, not to agentsHQ. This anatomy doc has to live in agentsHQ to be useful as agentsHQ navigation.

> **Confusing folder name, important contents.** Despite the folder name, `output/` (singular) is NOT the agent task output sink (that's `outputs/` plural, becoming `agent_outputs/`). It is a registered git submodule that holds 14 live websites + 5 nested git submodules pointing at separate Next.js app repos. Total: ~996 MB on disk, 14 client/personal websites, 5 satellite app repos.

## CRITICAL: TWO DIFFERENT REPOS, DO NOT MERGE

The agentsHQ `.gitmodules` registers `output/` as pointing at `bokar83/attire-inspo-app`. The local working tree's `output/.git/config` currently points at `bokar83/signal-works-demo-hvac.git` (commit `283f7eba`). **These are two separate repositories. They must NEVER be merged or treated as the same thing.** They share no history. They serve different purposes (attire-inspo-app is a Next.js app for Aminöa; signal-works-demo-hvac is a demo prospect site for the Signal Works pipeline).

The inconsistency means the local `output/` checkout is currently a clone of a different repo than what agentsHQ thinks it is. Resolution requires a careful decision in a dedicated future session:

- Option A: re-clone `output/` from the correct `bokar83/attire-inspo-app` remote (matching `.gitmodules`). The current `signal-works-demo-hvac` checkout would need to be saved elsewhere first.
- Option B: update agentsHQ `.gitmodules` to point at `signal-works-demo-hvac` (matching the live checkout). Re-establish a separate path for `attire-inspo-app` if it is also needed locally.

**Either way: the two repos stay distinct. No merge. No history rewrite that combines them.** Pick which repo `output/` should canonically be, and create a separate path for the other if both are needed locally.

This is tracked as a **dedicated future session** (Compass M5 or its own roadmap). Today's session only documents what was found; nothing is changed in `output/` itself.

## Live mount references (DO NOT MOVE this folder without coordinating)

| Reference | Location | Why it matters |
|---|---|---|
| `skills/vercel-launch/scripts/launch.sh:61` | writes apps to `$AGENTS_ROOT/output/apps/$APP_NAME` | All `vercel-launch` skill invocations land here |
| 30+ historical handoff docs | reference `output/websites/<site>/...` | Snapshot of when written; not auto-updated |
| Submodule registration | `.gitmodules` `[submodule "output"]` | Parent agentsHQ tracks output/ as a submodule pointer |

## What lives here

### `output/websites/` (~996 MB, 14 websites)

Live and historical client + personal websites. Most are Vercel-deployed.

| Website folder | Approx size | Status |
|---|---|---|
| `boubacarbarry.com` (`boubacarbarry-site/`) | 2.4 MB | personal |
| `calculatorz-site.ARCHIVED/` | 33 MB | archived (kept under `.ARCHIVED` suffix per Boubacar's archive convention) |
| `catalystworks-hyperframes/` | 2.6 MB | CW HyperFrames assets |
| `catalystworks.consulting` (`catalystworks-site/`) | 5.4 MB | LIVE: CW main site |
| `convertisseur-en-ligne-site/` | 414 MB | French unit-converter site |
| `geolisted.co` (`geolisted-site/`) | 37 MB | LIVE: Signal Works landing |
| `hrexposed-site/` | 564 KB | personal |
| `humanatwork-site/` | 775 KB | personal |
| `seo-audits/` | 132 KB | audit artifacts |
| `signal-works-demo-dental/` | 15 MB | demo prospect site |
| `signal-works-demo-hvac/` | 14 MB | demo prospect site (this is what the local submodule git points at) |
| `signal-works-demo-roofing/` | 45 MB | demo prospect site |
| `signal-works-landing/` | 19 MB | landing variant |
| `unit-converter-site/` | 411 MB | English unit-converter site |

### `output/apps/` (5 nested git submodules, each its own repo)

Each nested app is a working git repo on disk pointing at its own GitHub satellite:

| Local path | Satellite repo | Use |
|---|---|---|
| `apps/attire-inspo-app-fresh/` | `bokar83/attire-inspo-app-fresh` (per gitlink `cef819df`) | Aminöa (Boubacar's daughter) attire inspo Next.js app |
| `apps/baobab-app/` | `bokar83/baobab-app` (per gitlink `e2fcf717`) | personal app |
| `apps/calculatorz-app/` | `bokar83/calculatorz-app` (per gitlink `360a0ead`) | calculator product |
| `apps/elevate-rebuild-app/` | `bokar83/elevate-rebuild-app` (per gitlink `4f7d6241`) | Rod / Elevate Roofing rebuild preview |
| `apps/signal-works-rod-app/` | `bokar83/signal-works-rod-app` (per gitlink `3e71db27`) | Rod / Elevate Signal Works hook page |

Each nested app is updated by `cd output/apps/<app>` then standard git workflow against its own remote. They do NOT show in agentsHQ git status.

### Top-level Next.js code in `output/` (the original attire-inspo-app)

Beneath `websites/` and `apps/`, the root of `output/` is itself a Next.js app: `app/`, `components/`, `lib/`, `package.json`, `next.config.js`, etc. This is the original attire-inspo-app code that the submodule was created from.

## What does NOT live here

- Agent task output (that's `outputs/` plural -> becoming `agent_outputs/`)
- Source orchestrator code (`orchestrator/`)
- Skills (`skills/`)
- Documentation (`docs/`)

## Rules for LLMs working here

1. **Never `git mv output/` from agentsHQ.** It's a submodule; moving it from the parent breaks the registration AND strands all 14 websites + 5 nested submodules.
2. **To update a website:** `cd output && git checkout main && pull` then edit, then `cd output && git add . && git commit && git push`. The parent agentsHQ then needs `git add output && git commit` to bump the submodule pointer.
3. **To update a nested app (e.g. baobab-app):** `cd output/apps/baobab-app` and treat it as its own repo. Push to `bokar83/baobab-app`. Then `cd output && git add apps/baobab-app && git commit` to bump the gitlink in the parent submodule. Then `cd ../.. && git add output && git commit` again to bump in agentsHQ. Two-level submodule bump.
4. **Per AGENT_SOP `vercel-launch`:** new apps land at `output/apps/<app-name>` via `skills/vercel-launch/scripts/launch.sh`. Don't write apps anywhere else.
5. **The folder name `output/` (singular) vs `outputs/` (plural) is a known footgun.** Be careful in scripts, env vars, and docs.

## Known inconsistencies (Compass M1+ to reconcile)

- `.gitmodules` says submodule URL = `bokar83/attire-inspo-app.git`. Local `output/.git/config` says `bokar83/signal-works-demo-hvac.git`. Choose one canonical URL and update either the parent or the local checkout.
- The original Next.js attire-inspo-app code at `output/` root coexists with `apps/attire-inspo-app-fresh/` (a separate nested submodule). Two attire-inspo-app surfaces. Decide which is the live one; archive the other.
- The folder is named `output/` (singular) but holds builds + websites + nested apps. A future restructure may promote `output/websites/` and `output/apps/` to top-level and retire the `output/` parent. **That restructure is its own dedicated session** because of the 996 MB scale, the nested submodules, and the `vercel-launch.sh` reference. Tracked: `docs/roadmap/compass.md` (likely as M5 or its own roadmap).

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Live mount inventory: [`docs/reference/repo-structure.md`](../docs/reference/repo-structure.md)
- vercel-launch skill: `skills/vercel-launch/SKILL.md`
