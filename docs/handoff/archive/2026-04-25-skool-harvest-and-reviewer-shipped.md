# Session handoff , Skool harvest + reviewer shipped, 2026-04-25 evening

## TL;DR

Built two new capabilities end-to-end in one session: a Skool community harvester and a harvest-reviewer crew. Mined the first 5 RoboNuggets R-series lessons (R56-R60). Two Council passes corrected the verdicts twice. Final cut: a 5-build plan for next week (~6.25 hours) gated on Boubacar filling in a Studio Operating Snapshot first.

The Skool harvester is general-purpose and can mine any Skool community Boubacar belongs to.

The harvest-reviewer is the second layer: it reads a harvested community's lessons against an inventory of agentsHQ, scores them through Catalyst Works AND Studio lenses, and emits Notion-DB-ready recommendations.

## What got built today

### Tooling

1. **Inventory snapshot generator** , `scripts/inventory_snapshot.py` writes `docs/agentsHQ_inventory.{md,json}`. 51 skills + 40 orchestrator modules + 71 env keys + 26 reqs. Read this whenever an agent needs to know what already exists in agentsHQ before proposing a new skill.
2. **Skool harvester (basic + dumb, by design)** , `scripts/skool-harvester/`. Three scripts: `skool_login.py` (one-time, saves storage_state), `skool_harvest.py` (single lesson), `skool_walk.py` (paginated classroom walk with `--list`, `--list --deep`, `--new`, `--all`, `--course-filter`, `--max`). Uses `__NEXT_DATA__` parsing, not DOM scraping.
3. **Harvest triage** , `orchestrator/harvest_triage.py`. Pure heuristics, no LLM. Filters Welcome / admin / affiliate noise. Cuts ~50 of 432 RoboNuggets lessons before the LLM ever runs.
4. **Harvest reviewer** , `orchestrator/harvest_reviewer.py`. Mapper + Decision agents on Haiku 4.5, then ONE Council pass on the consolidated batch. Outputs to `workspace/skool-harvest/<community>/_reviews/<batch>.json` and a Notion-payload JSON.
5. **Notion DB created** , Harvested Recommendations in The Forge 2.0. ID `0e60ae9d-dc77-4fa4-8d96-77a2d4aa9c42`, data source `4f752c5e-6dfb-48f6-90f1-4d9811645e78`. 5 rows from R56-R60 batch already written (now updated with corrected dual-lens verdicts).

### New agentsHQ artifacts

- `skills/client-intake/SKILL.md` (built earlier in session as Council-recommended pull from R57).
- `orchestrator/video_analyze.py` (Gemini Files API video tear-down, registered as a tool).
- `orchestrator/niche_research.py` (Apify Reddit scraper -> Supabase, registered as a tool).
- `docs/reference/cross-vendor-fallback-pattern.md` (architectural note pulled from R57).
- `docs/reference/skool-harvest-archive/2026-04-25-r56-r60-full-proposals.md` (complete archive of all 25+ ideas from the harvest, with revisit triggers , nothing is lost).
- `docs/roadmap/studio/operating-snapshot.md` (the Studio numbers Boubacar needs to fill in).
- New env placeholders: `APIFY_API_TOKEN`, `GOOGLE_API_KEY`, `WAVESPEED_API_KEY`, `NOTION_HARVESTED_RECS_DB_ID`, `NOTION_HARVESTED_RECS_DATA_SOURCE_ID`.

### Memory rules saved

- `feedback_n8n_last_resort.md` , n8n is a last resort; default to skill or crew.
- `feedback_existing_stack_first.md` , translate external tools to our stack (Supabase, Notion, Firecrawl, Kie); never duplicate.
- `reference_skool_access.md` , autocli does NOT support Skool, use the Playwright harvester.
- `project_harvested_recommendations_db.md` , Notion DB schema reference.

## What got reviewed (and what the Council said)

5 lessons harvested, 5 Council passes (2 on the framing, 3 inside the reviewer's own Council pass on the batch). Final dual-lens verdicts:

| Lesson | CW | Studio | Combined |
|---|---|---|---|
| R60 Cinematic Sites | T2 | T1 | T1 |
| R59 Beautiful Websites | T1 (revenue lever) | T1 (channel sites) | T1 |
| R58 Figma + Mobile | T3 | T1 (Figma Community brand kits) | T1 |
| R57 Antigravity x Blotato | T2 | T1 (live production line) | T1 |
| R56 Creative Engine | T3 | T1 (gating discipline) | T2 |

Council Pass 3 cut "5 Tier 1s" down to **5 specific builds + 1 Step 0 prerequisite**. Total ~6.25 hours, fits in 1 day.

## Next session must start here

### Step 0 , Boubacar fills in the Studio Operating Snapshot

Doc: `docs/roadmap/studio/operating-snapshot.md`. Empty fields:

- channels currently producing manually (count)
- YT posts shipped in last 7 days
- X posts shipped in last 7 days
- hours/week on Studio in last 7 days
- first 2-3 niches to commit to (working session , Boubacar wants Claude's help)
- X handles per channel
- channel warm-up windows (after research)

**Constraint already known:**
- YouTube: 1 post/channel/week minimum
- X: multiple posts/channel/day
- LinkedIn: NEVER for Studio. Reserved for Boubacar personally + Catalyst Works.
- Top bottleneck #1: quality video content creation
- Top bottleneck #2: knowing what to post about (research-driven)
- Cost/week: currently irrelevant
- New channels need a warm-up period (research before posting aggressively)

**Without Step 0 the rest of the plan is unfalsifiable.** Don't start any Studio build until the numbers exist.

### Step 1 , once snapshot exists, build in this order (~6.25h)

1. Port `R57/references/docs/prompt-best-practices.md` raw to `docs/reference/prompt-best-practices.md` (15 min). BOPA + SEALCaM + dialogue cap. Every kie_media call improves immediately.
2. Cost-confirmation decorator on `skills/kie_media/` (30 min). Pure downside protection.
3. Codify `[channel]_BRAND.md` format + write 1 filled instance for Studio's primary channel (1.5h). Use `R57/references/docs/fabric_BRAND.md` and `imma_BRAND.md` as templates. Drop into `docs/reference/brand-file-examples/`. NOT the interview engine yet , just the file format and one real file.
4. R59 outreach loop MVP (3h). screenshot.js port + Claude-vision rubric + clone-builder single-file mode + git push to `<prospect>-site` repo + Hostinger Git auto-pull. **Acceptance: 1 LinkedIn DM with 1 live Hostinger URL by Sunday.** This is the only direct revenue lever.
5. Port `R57/.agent/skills/blotato_best_practices/SKILL.md` to `skills/blotato/` (1h). URL-passthrough decision tree, post-status polling, platform required fields, scheduling timezone reference. Studio uses Blotato live but the rules live in Boubacar's head , this puts them in version control.

### Step 2 , gated on Step 0 evidence

Each next-week build has an explicit trigger (in the archive doc):

- R56's 7-step gated `/generate-content` → only if Step 0 shows manual prompt time > 1h/week.
- 30-day campaign griot mode → only if Studio publishes daily AND a new channel is queued.
- Round 1-4 brand interview → only if a new channel launches OR a Signal Session books.
- R58 Figma brand-kit pull → only if a channel needs new assets in 14 days.
- R60 cinematic landing pages → only if an existing channel landing page is converting badly.

### Step 3 , defer indefinitely, parked in archive

R59 full toolkit beyond MVP, HARD RULES retrofit on 51 skills, build-log episodic memory, 30-effect cinematic library. All have revisit triggers in `docs/reference/skool-harvest-archive/2026-04-25-r56-r60-full-proposals.md`.

## Open architectural questions (not blocking Step 1)

1. **Execution-state primitive still missing.** Today's griot status is per-post. A 30-record campaign with 4 human gates needs a campaign-level state record. Note as Tier 2 architecture decision; do NOT build speculatively.
2. **Hostinger many-repo question.** Before scaling R59 outreach beyond ~5 prospects, confirm Hostinger handles many small `*-site` repos cleanly. Possible quota.
3. **Niche selection.** Open working session needed.
4. **Channel warm-up best practices.** Open research task.

## What was deliberately NOT done today

- Did NOT build a Blotato skill yet (waiting on Step 1.5).
- Did NOT update agents.py to wire the new tool bundles into specific crews. Reviewer / niche_research / video_analyze are tool-registered but not yet handed to any agent.
- Did NOT archive the unused `6XEaB5k7Kz4ubEck` n8n workflow (per Boubacar's request: keep as reference for now).
- Did NOT run the reviewer on the next batch of R-series lessons (R55 → R51). Wait for prompt updates and Step 0 to land first.
- Did NOT commit any of the work. Local edits only. Boubacar approves the commit before push.

## File map of what changed today

```
agentsHQ/
├── scripts/
│   ├── inventory_snapshot.py                    NEW
│   └── skool-harvester/
│       ├── skool_login.py                        NEW
│       ├── skool_harvest.py                      NEW
│       ├── skool_walk.py                         NEW
│       └── probes/                               NEW (3 probe scripts + README)
├── orchestrator/
│   ├── niche_research.py                         NEW
│   ├── video_analyze.py                          NEW
│   ├── harvest_triage.py                         NEW
│   ├── harvest_reviewer.py                       NEW
│   └── tools.py                                  EDITED (3 new tool bundles wired)
├── skills/
│   ├── client-intake/SKILL.md                    NEW (built mid-session)
│   ├── skool-harvester/SKILL.md                  NEW
│   └── kie_media/SKILL.md                        EDITED (cross-vendor fallback note added)
├── docs/
│   ├── agentsHQ_inventory.md                     NEW (auto-generated)
│   ├── agentsHQ_inventory.json                   NEW (auto-generated)
│   ├── reference/
│   │   ├── cross-vendor-fallback-pattern.md      NEW
│   │   └── skool-harvest-archive/
│   │       └── 2026-04-25-r56-r60-full-proposals.md  NEW
│   ├── roadmap/
│   │   └── studio/
│   │       └── operating-snapshot.md             NEW
│   └── handoff/
│       └── 2026-04-25-skool-harvest-and-reviewer-shipped.md  NEW (this file)
├── workspace/skool-harvest/robonuggets/          NEW (gitignored)
│   ├── _index.json                                432 lessons across 78 courses
│   ├── _review_plan.json                          triage output
│   ├── _reviews/                                  reviewer outputs
│   └── <5 lesson dirs with extracted zips>
└── .env                                          EDITED (5 new placeholders)

`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/`
├── MEMORY.md                                     EDITED
├── feedback_n8n_last_resort.md                   NEW
├── feedback_existing_stack_first.md              NEW
├── reference_skool_access.md                     NEW
└── project_harvested_recommendations_db.md       NEW
```

## Two specific questions to resolve next session, in order

1. Boubacar fills in `docs/roadmap/studio/operating-snapshot.md` empty fields.
2. Boubacar approves the Step 1 sequence (or reorders , R59 outreach loop is currently #4; could move to #1 if revenue beats setup).

After those two, execute Step 1 in one focused session and update the Notion rows + memory at the end.
