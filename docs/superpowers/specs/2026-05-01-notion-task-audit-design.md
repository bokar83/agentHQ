# Notion Task Audit + Golden Gem Rediscovery

**Spec date:** 2026-05-01 (Friday)
**Author:** Boubacar Barry + Claude Code
**Status:** approved for implementation
**Codename:** task-audit

---

## 1. Goal

Make the Notion Tasks DB (`⏳ Tasks`, `249bcf1a3029...`) the One True Source of every actionable task across agentsHQ. After this audit:

> By looking at the Notion task board, Boubacar knows the most important thing he needs to do next. No jumping between roadmaps, plans, specs, and handoffs to figure out priorities.

Concretely, three verifiable success criteria (see Section 9).

This is a one-time Friday cleanup pass. After it ships, ongoing maintenance is a bi-monthly 14-day sweep using the same harvester.

---

## 2. Assumptions (explicit, falsifiable)

1. **Memory `project_*.md` files are excluded as feeders.** They are point-in-time observations, not tasks. Falsifiable: if the audit misses a real task that only existed in memory, this assumption fails and we revise.
2. **Atomic task duration cap = 10% of parent milestone, hard ceiling 8 hours of focused work.** Adopted from the BYU Enterprise PM ruleset surfaced via the NotebookLM audit. Anything bigger gets split.
3. **Estimated row volume: 80-120 Live + Shipped.** If the harvester emits more than 200 Live rows, the script halts and we re-scope.

---

## 3. Sources (feeders)

The harvester reads from these locations only. All read-only.

| Source | Path | Approx file count |
|---|---|---|
| Active roadmaps | `docs/roadmap/atlas.md, harvest.md, studio.md, echo.md` | 4 |
| Future enhancements backlog | `docs/roadmap/future-enhancements.md` | 1 |
| Plan documents | `docs/superpowers/plans/*.md` | 56 |
| Spec documents | `docs/superpowers/specs/*.md` | 45 |
| Session handoffs | `docs/handoff/*.md` | 70 |

**Excluded:** memory files (`~/.claude/projects/.../memory/project_*.md`), Notion Content Board, Ideas DB, CRM, any non-`docs/` markdown.

---

## 4. Architecture

Three layers:

1. **Sources (read-only feeders).** The 176 markdown files above.
2. **Sync layer.** A standalone Python harvester (`scripts/notion_task_audit.py`) that walks sources, extracts atomic tasks, classifies each, and upserts to Notion + writes audit markdown files. One-way only: feeders to Notion, never reverse.
3. **Notion Tasks DB (the truth).** Existing schema plus two new fields (`Source`, `Completion Criteria`). One manual view-filter update at the end.

**Forward-going contract** (deferred per Karpathy; not in this spec): every new handoff must update its parent roadmap, then run the harvester. Captured separately after this audit ships.

---

## 5. Classification rules + P0 dictator

### 5.1 Classification (applied in order)

| Rule | Disposition | Destination |
|---|---|---|
| Source has `SHIPPED`, `DONE`, `✅`, or session-log "shipped" marker | **Shipped** | Notion (Status=Done, Outcome=`shipped <date>`, Source=path) |
| Trigger date >= today, OR markers `IN PROGRESS / QUEUED / NOT STARTED / IN FLIGHT` | **Live** | Notion (Status=Not Started or In Progress, Source=path) |
| No status, last touched >= 60 days ago, never referenced in any later doc | **Archived** | `docs/audits/2026-05-01-archived.md` (NOT Notion) |
| Was planned, never shipped, but the idea is still sound or possibly better than current approach | **Golden Gem** | Notion with Notes prefix `🔍 GOLDEN GEM:` |
| Cannot classify confidently | **Needs review** | `docs/audits/2026-05-01-needs-review.md` |

Golden Gems are reviewed bi-monthly: promote (strip prefix, set Status), archive (move to archived file + delete from Notion), or keep.

### 5.2 P0 dictator selection (priority order)

After all Live tasks are loaded, pick exactly one task to flip `P0 = true`:

1. `Category = Revenue` AND `Due Date <= today + 7 days` AND `Status != Done`. If multiple, soonest Due Date.
2. Else: task whose source roadmap milestone is currently `IN PROGRESS` AND highest revenue impact (Harvest > Atlas > Studio > Echo).
3. Else: soonest-due High priority task across all categories.
4. Else: task tagged `NN2: Revenue Movement` with soonest Due Date.

User confirms chosen P0 at end. If wrong, user names correct P0; rule and reason logged to `docs/audits/2026-05-01-p0-decision.md` so the rule sharpens next pass.

---

## 6. Notion schema migration

**Two new properties** on data source `collection://249bcf1a-3029-814a-9fa7-000bf712902b`:

| Field | Type | Purpose |
|---|---|---|
| `Source` | rich_text | Relative path to feeder doc (e.g. `docs/roadmap/harvest.md#R1a-v3`). Empty for legacy rows until manually triaged. |
| `Completion Criteria` | rich_text | One-sentence verifiable criterion: it is obvious whether the task is done by comparing output with the criterion. PM-rule adoption from NotebookLM audit. |

**No** `Disposition` field (Karpathy: dropped as speculative). Golden Gems use the Notes-prefix convention. Archived items stay out of Notion.

**Manual view filter update** (Notion API cannot reliably edit view filters):
- Open `Active Tasks` view in Notion UI
- Add filter clause: `Notes does not start with 🔍`
- Save view
- One-time, ~30 seconds

**Existing rows** (~25 legacy rows timestamped 2026-04-05): NOT auto-migrated. They flow through `needs-review`. User decides per-row: Live (add Source `legacy/2026-04-05`), Shipped, or Archived.

---

## 7. Harvester pipeline (5 stages)

Implementation: `scripts/notion_task_audit.py`. Standalone Python. ~300 lines target.

### Stage 1: Walk and extract
For each `.md` file, parse markdown. Look for task-shaped content using these heuristics:

- **Roadmap milestone headers:** `### M3:`, `### R1:`, `#### R1a-v3:` etc.
- **Status markers:** `✅ SHIPPED`, `⏳ QUEUED`, `🟡 IN PROGRESS`, `❌ OPEN`.
- **Action lists:** `**Actions:**`, `**Open work:**` blocks; numbered lists under `**What:**`.
- **Triggers/dates:** `Trigger date:`, `Target:`, `ETA:`, ISO dates `YYYY-MM-DD`.
- **Plan/spec/handoff "Next:"** sections at file bottom.

Produces a structured intermediate list of milestone-or-block units with source path, line number, body text, and any explicit status marker.

### Stage 2: Extract atomic tasks via LLM
For each unit, call Claude Haiku (via OpenRouter; key already in `.env`) with:

```
Given this milestone/block description, extract atomic tasks.
A task is an action-verb-led bite <= 8 hours of focused work, OR <= 10%
of the parent milestone's expected duration, whichever is smaller.

Return JSON list with:
  - title (action verb, no fluff)
  - completion_criteria (one sentence, verifiable)
  - estimated_hours (number)
  - source_section (heading or line ref)

If the milestone is shipped, return one Shipped task per major sub-deliverable.
If there is no actionable work, return [].
```

Cost guard: ~80 unit-equivalent calls × ~$0.001 each = ~$0.10 total budget. Hard cap at 200 LLM calls; halt and report if exceeded.

### Stage 3: Classify
Apply Section 5.1 rules in order. Then run a second LLM pass on every task that classified as "Live but never shipped despite being old" with prompt:

```
Given this task description and source context, is this idea still sound,
or is it stale/superseded? If sound, is there any chance it is better than
or complementary to current active work?

Return: {"verdict": "live" | "gem" | "archive", "reason": "<one sentence>"}
```

Verdict `gem` flips disposition to Golden Gem.

### Stage 4: Dedupe
Same task may appear in multiple feeders. Normalize titles (lowercase, strip punctuation, drop date suffixes), group, keep the entry with the most recent source date. `Source` field of kept entry concatenates all paths it appeared in (semicolon-separated).

### Stage 5: Upsert + write audit files
For each task in deduped list:
- Query Notion Tasks DB by exact title match.
- If exists and Status != Done: update `Source` and `Completion Criteria`; do not stomp Status (respects manual edits).
- If exists and Status == Done: skip.
- If does not exist: create new row with all fields.

After all upserts:
- Run P0 dictator (Section 5.2). Set `P0 = true` on chosen task. Clear `P0` on all others.
- Write the three audit markdown files (Section 8).
- Print summary to stdout.

---

## 8. Outputs

1. **Notion Tasks DB**: populated with Live, Shipped, and Golden Gems. P0 row at top.
2. **`docs/audits/2026-05-01-archived.md`**: table of archived items with title, source path, last touched date, one-line "why archived."
3. **`docs/audits/2026-05-01-needs-review.md`**: ambiguous items, user decides row by row.
4. **`docs/audits/2026-05-01-summary.md`**: counts by disposition, the chosen P0 task and its rationale, list of Golden Gems with one-line summaries.
5. **`docs/audits/2026-05-01-p0-decision.md`**: only created if user overrides the auto-picked P0; logs reason for the rule to learn.
6. **`scripts/notion_task_audit.py`**: re-runnable for the bi-monthly sweep via `--mode=sweep --window=14d`.

---

## 9. Success criteria (verifiable)

**C1: P0 dictator works.**
- Open Notion Tasks DB → `Active Tasks` view.
- Exactly one row has `P0 = true`.
- That row sorts to the top.
- The title reads as the single most important revenue or autonomy task right now.
- Boubacar confirms. If wrong, user names correct P0 → rule updated → reason logged in `2026-05-01-p0-decision.md` → P0 step re-runs only.

**C2: Source field populated everywhere on Live rows.**
- Notion query: `Status != Done AND Source is empty` returns zero rows.
- If non-zero, harvester has a bug: fix and re-run upsert step.

**C3: Audit files exist, committed, readable in <5 min each.**
- All three audit markdown files exist in `docs/audits/`.
- Each entry has title + source + 1-line rationale.
- Committed to git.

---

## 10. Failure modes + rollback

| Failure | Recovery |
|---|---|
| Schema migration partially fails | Delete the added field via API. DB returns to original state. No risk to existing rows. |
| Notion 429 rate limit | Script catches, sleeps with exponential backoff, resumes. Each upsert is one atomic call. |
| LLM mis-classifies known-shipped item as Live | Surface in dry-run; user flags; add explicit override rule; re-run. |
| Dedupe collapses two real-but-similar tasks | Surface in dry-run; adjust normalization (e.g., keep date suffix); re-run. |
| P0 picks wrong task | User names correct P0; rule updated; reason logged. |
| Live row count >200 | Script halts. Pause, re-scope per Section 2 assumption. |

**Full rollback** if user hates the result:
- Notion: filter `Source is not empty AND Created today` → multi-select → bulk delete (~5 min).
- Schema fields: delete via API (~10 sec).
- Audit files: `git rm` + restore via save-point tag.

**Save point:** `git tag savepoint-pre-task-audit-2026-05-01` before first run, pushed to origin.

---

## 11. Run sequence (≤60 min focused work)

1. **Pre-flight** (10 min): save-point tag, verify `NOTION_API_KEY`, schema migration via API (verify with fetch), `mkdir -p docs/audits/`.
2. **Stage 1+2 dry-run** (10 min): `python scripts/notion_task_audit.py --dry-run --stages=walk,extract`. Eyeball extracted milestones; verify nothing major is missing.
3. **Stage 3 dry-run** (10 min): `--dry-run --stages=walk,extract,classify`. Spot-check 5-10 dispositions against memory.
4. **Stage 4 dry-run** (10 min): `--dry-run` (full). Eyeball dedupe report, P0 candidate, audit file previews.
5. **Live run** (5 min): `python scripts/notion_task_audit.py`. Writes to Notion + audit files.
6. **Manual filter update** (1 min): in Notion UI, add `Notes does not start with 🔍` filter to `Active Tasks` view.
7. **Verification** (10 min): C1, C2, C3 confirmed. User confirms P0.

If any stage doubles, total stretches to ~90 min. Beyond that, pause and reassess.

---

## 12. Out of scope (deliberate breaks of PM rules)

The NotebookLM PM audit (BYU Enterprise PM Process Guide) surfaced rules we are consciously NOT applying right now. Each break is logged here so the omission is intentional, not accidental.

| PM rule | Our break | Why | Revisit when |
|---|---|---|---|
| Predecessor/successor task graph (Dependency Diagram) | Not adding task-to-task relations to Notion | One-person op; roadmap milestones already encode dependencies in prose | A real task-ordering failure occurs |
| "Is/Is Not" parameters in a central scope log | Stays in roadmap "Descoped Items" tables, NOT replicated to Notion | Already exists at the right level; duplicating to Notion adds noise | A descoped item gets re-attempted because it was not seen |
| Forward-going AGENT_SOP rule (every handoff updates roadmap + Notion) | Deferred to a separate follow-up commit AFTER this audit ships | Karpathy: scope creep against the user's stated goal "clean up tasks today" | After this audit ships and user has 1 week of usage |
| Bi-monthly maintenance ritual | Deferred until after one-time pass produces real output | Karpathy: design the ritual after seeing what 80-120 rows look like, not before | After C1-C3 are verified |

---

## 13. Council record

**Karpathy verdict on Section 1:** HOLD. Required revisions before SHIP:
1. Strip forward-going AGENT_SOP hard rule from Section 1 (deferred).
2. Drop to one new saved view (the `Active Tasks` view filter, not a fresh view).
3. Defer bi-monthly maintenance design until after one-time pass.
4. Replace "~80-120 rows" guess with C1, C2, C3 success criteria.
5. Surface three silent assumptions explicitly (Section 2).
All five applied.

**Sankofa verdict on Section 1 (post-Karpathy):** APPROVED with three constraints. Two adopted (split output: Notion = Live + Shipped + Gems; Archived to file. Real success criterion = P0 row at top reads as most-important revenue/autonomy task). One INVALIDATED by user context (Rod pre-gate dropped: warm message already sent, no touch until next week, cash path healthy with 20+ emails sent + comments + posts + productive call this morning).

**NotebookLM PM audit (BYU Enterprise PM Process Guide):** 5 matches (single source of truth, owner per task, WBS decomposition, parking lot for ideas, weekly cadence). 4 conscious breaks (Section 12). 2 adoptions: Completion Criteria field + 10% duration rule (Section 6, Section 2.2).

**User decisions:**
- Granularity: B (atomic tasks, ≤10% rule).
- Top-of-board: B (P0 checkbox dictator).
- Scope: C (everything, full archaeology).
- Tagging: B → revised to Notes-prefix after PM audit (no separate Disposition field).
- Golden Gems: Y (in Notion with `🔍 GOLDEN GEM:` prefix, bi-monthly review).
- Completion Criteria field: yes.

---

## 14. Cross-references

- **Notion Tasks DB:** `https://app.notion.com/p/249bcf1a302980739c26c61cad212477`
- **Tasks DB ID env var:** `NOTION_TASK_DB_ID` (default `249bcf1a302980739c26c61cad212477` in `orchestrator/tools.py:1526`)
- **Existing tools:** `NotionQueryTasksTool` in `orchestrator/tools.py:1529-1601`
- **Active roadmaps:** `docs/roadmap/atlas.md`, `harvest.md`, `studio.md`, `echo.md`, `future-enhancements.md`
- **PM rules source:** NotebookLM notebook `CW_Catalyst Works Ops` (id `a5c23cdf-8d26-4849-b204-b98fb3a618f9`), source `88a29157-6fb5-469f-bc54-6699146cb5ce` (BYU Enterprise PM Process Guide)
- **Memory:** `feedback_inspect_notion_schema_first.md`, `feedback_notion_db_env_workflow.md`, `feedback_no_em_dashes.md`

---

## 15. Implementation handoff

After spec approval, this hands to `superpowers:writing-plans` skill to produce the step-by-step implementation plan with checkpoints. Codex (per `Codex-First` rule in `AGENT_SOP.md`) writes `scripts/notion_task_audit.py` from the plan.
