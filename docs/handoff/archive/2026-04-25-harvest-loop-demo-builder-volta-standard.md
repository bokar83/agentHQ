# Session Handoff: Harvest Loop + Demo Builder + Volta Design Standard
# 2026-04-25 (evening session)

## TL;DR

Long session spanning two major tracks: (1) completing the full Skool harvest
pipeline end-to-end: triage, reviewer, Council, Ideas DB handoff, all 5
Council items built; (2) building the CW prospect demo-builder pipeline (R59
outreach loop) and discovering, through 3 iterations of the same dental site,
that every website we were building looked identical. Ended the session with
the Volta Studio demo: a cinematic dark creative agency site with custom
cursor, particle trail, SplitText hero, pinned horizontal scroll, magnetic
buttons: and locked that as the new design standard going forward.

---

## What was built / changed

### Harvest pipeline
- `orchestrator/harvest_reviewer.py`: Mapper + Decision prompts rewritten
  with dual-lens framing (CW + Studio), Antigravity = Claude Code rule,
  Hostinger not Vercel, new `cw_tier`/`studio_tier`/`combined_tier` fields
- 5 Notion Harvested Recommendations rows updated with Council Pass 3 verdicts
  (R56=Deferred, R57=Approved, R58=Deferred, R59=Approved, R60=Deferred)
- 5 agentsHQ Ideas DB rows created and marked Done (all built this session)

### Council items built (all 5)
1. `docs/reference/prompt-best-practices.md`: BOPA + SEALCaM + dialogue cap
2. `skills/kie_media/SKILL.md`: HARD RULES block with cost gate added
3. `docs/reference/brand-file-format.md` + `docs/reference/brand-file-examples/`
   (format spec + fabric_BRAND.md + imma_BRAND.md samples + catalyst_works_BRAND.md)
4. `skills/blotato/SKILL.md`: URL passthrough decision tree, base64 PS
   upload, platform fields, polling, timezone. Airtable refs removed.
5. `scripts/screenshot.js`: Playwright full-page screenshotter (from R59)
   `skills/site-qualify/SKILL.md`: 11-row visual rubric
   `skills/clone-builder/templates/single_file_premium.md`: 155-line spec
   `skills/demo-builder/SKILL.md`: full 6-step outreach pipeline

### Design standard locked
- `workspace/demo-sites/volta-studio/index.html`: THE reference demo. Every
  future site aims for this level on first try.
- `skills/frontend-design/SKILL.md`: completely rewritten with Volta standard,
  banned skeleton, layout archetype table, font/color rotation, cinematic baseline
- `skills/demo-builder/SKILL.md`: updated with Volta standard reference
- `skills/tab-shutdown/SKILL.md`: NEW. The skill that runs this handoff.

### Memory files written
- `feedback_website_design_standard.md`: Volta is the bar
- `feedback_custom_cursor.md`: never use mix-blend-mode
- `feedback_demo_site_design_diversity.md`: banned skeleton, rotation tables
- `project_demo_builder.md`: pipeline state, builds completed
- `project_harvest_loop_complete.md`: full pipeline wired, R55-R51 ready

### Renamed workspace dir
- `workspace/outreach/` was renamed concept to `workspace/demo-sites/`
  (actual rename still needed: screenshot.js output still goes to
   `workspace/outreach/` in the skill docs; update paths when next run)

---

## Decisions made

1. **Volta is the minimum bar, not the ceiling.** Default to cinematic, pull
   back if asked. Never the reverse.

2. **Studio work is handed off to a separate team.** This tab does NOT work
   on Studio builds. Studio operating snapshot is the Studio team's problem.

3. **Harvest loop is general-purpose.** Any source: Skool lesson, URL,
   YouTube transcript, video: goes through the same harvest pipeline.
   After Council agrees, items go to agentsHQ Ideas DB (Queued).

4. **workspace/outreach renamed to workspace/demo-sites.** More memorable,
   less forgettable. Update any scripts that write to the old path.

5. **`mix-blend-mode` is BANNED on cursor elements.** It makes the cursor
   invisible on dark backgrounds. Explicit colors only.

6. **boubacarbarry.com and catalystworks.com will need redesigns eventually.**
   Boubacar acknowledged this. Not urgent, but flag when those sites are touched.

---

## What is NOT done

- `thepointpediatricdentistry` demo: built (storybook version in
  `workspace/demo-sites/thepointpediatricdentistry/index.html`) but NOT deployed
  to Hostinger. No GitHub repo created. No LinkedIn DM sent.
- `workspace/outreach/` directory still exists alongside `workspace/demo-sites/`.
  Old scripts still reference `workspace/outreach/`. Need to standardize.
- R55-R51 RoboNuggets harvest not run yet. Ready to go.
- `roadmap/harvest.md` not updated with session log (stub roadmap).
- Neither boubacarbarry.com nor catalystworks.com redesigned to Volta standard.

---

## Open questions

1. Does Boubacar want to deploy the dental demo to Hostinger now, or run more
   demos first to build a portfolio before reaching out?
2. What niche / city should the first real outreach batch target? (The Apify
   actor for Google Maps scraping is wired and ready.)
3. R55-R51: run the next harvest batch now or wait?

---

## Next session must start here

1. **Fix workspace path:** Rename `workspace/outreach/` to `workspace/demo-sites/`
   or update all skill references. One or the other: not both paths existing.
2. **Run R55-R51 RoboNuggets harvest.** The reviewer, triage, and Council pipeline
   are all wired and ready. Run the next batch:
   `python orchestrator/harvest_reviewer.py robonuggets --max 5`
   Then push agreed items to the agentsHQ Ideas DB as Queued.

Note: the dental demo site and all other test sites built this session are
workspace-only (gitignored). They are NOT being deployed: they were built
to establish the design standard and test the pipeline. No deployment, no
LinkedIn DM for those test builds.

---

## Files changed this session

```
agentsHQ/
  scripts/
    screenshot.js                              NEW
  skills/
    frontend-design/SKILL.md                  REWRITTEN (Volta standard)
    demo-builder/SKILL.md                      NEW
    site-qualify/SKILL.md                      NEW
    blotato/SKILL.md                           NEW
    kie_media/SKILL.md                         EDITED (HARD RULES added)
    tab-shutdown/SKILL.md                      NEW
    clone-builder/templates/single_file_premium.md  NEW
  docs/
    reference/
      prompt-best-practices.md                NEW
      brand-file-format.md                    NEW
      brand-file-examples/
        fabric_BRAND.md                       NEW (copied from R57)
        imma_BRAND.md                         NEW (copied from R57)
        catalyst_works_BRAND.md               NEW (real instance)
    handoff/
      2026-04-25-harvest-loop-demo-builder-volta-standard.md  NEW (this file)
  orchestrator/
    harvest_reviewer.py                        EDITED (dual-lens prompts)
  workspace/
    demo-sites/
      volta-studio/index.html                 NEW (THE reference demo)
      thepointpediatricdentistry/index.html   NEW (storybook, not deployed)
      build-log.md                            NEW

~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/
  MEMORY.md                                   EDITED (5 new entries)
  feedback_website_design_standard.md         NEW
  feedback_custom_cursor.md                   NEW
  feedback_demo_site_design_diversity.md      NEW
  project_demo_builder.md                     NEW
  project_harvest_loop_complete.md            NEW
  project_harvested_recommendations_db.md     EDITED (full loop documented)

~/.claude/skills/
  tab-shutdown/SKILL.md                       NEW (synced from agentsHQ)
  frontend-design/SKILL.md                   SYNCED (Volta standard)
```

---

## Notion state

- Harvested Recommendations DB (`0e60ae9d...`): 5 rows, all updated with
  dual-lens Council Pass 3 verdicts. R57 + R59 = Approved+Built. Others = Deferred.
- agentsHQ Ideas DB (`33bbcf1a...`): 5 rows, all Status=Done.
- localhost:7700 serving `workspace/demo-sites/`: kill the Python server when done.
