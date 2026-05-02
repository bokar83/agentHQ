# Compass: agentsHQ Governance Model

**Codename:** compass
**Status:** active
**Lifespan:** open-ended
**Started:** 2026-05-02
**Owner:** Boubacar Barry
**One-line:** the system that controls how agentsHQ governs itself: where rules live, how they're enforced, how they retire, how new rules get added without sprawl

> **Naming note:** `compass` is a metaphor codename (orientation), not a work-codename like Atlas/Harvest/Studio/Echo/Dashboards4Sale. Sankofa Council 2026-05-02 flagged the convention break; Boubacar approved compass anyway. Logged for transparency, not for re-litigation.

---

## Done Definition

Compass is "done" when:

1. Any rule in agentsHQ is reachable in under 30 seconds from `docs/GOVERNANCE.md`.
2. Every governance rule that can be enforced by mechanism IS enforced by a pre-commit hook, a scheduled audit, or a CI check. Rules a human has to remember decay in 14 days.
3. The 8 sprawled rule surfaces (AGENT_SOP, MEMORY, repo-structure.md, folder AGENTS.md files, pre-commit hooks, Notion, roadmap, Cadence Calendar) are consolidated to a count where each surface has exactly one job. Redundancy retired.
4. A new collaborator (or fresh LLM session) can answer "where does this kind of rule go?" by reading `GOVERNANCE.md` alone, without needing to ask.
5. A retirement protocol is enforced, not just documented. Stale rules get surfaced for retirement automatically, not by manual sweep.

Done = all five true at the same time.

---

## Status Snapshot

*Last updated: 2026-05-02 (evening)*

- M0 SHIPPED 2026-05-02: `docs/GOVERNANCE.md` (64 lines) routing table + AGENT_SOP top-of-file annotation + this roadmap + folder-purpose pre-commit hook (the M0 enforcement piece).
- M1 SHIPPED 2026-05-02: AGENTS.md compliance audit + backfill. 100% folder coverage (was 32%).
- M2 SHIPPED 2026-05-02 (evening): 5 enforcement hooks live (memory-frontmatter, session-log, redundancy, doc-size, retirement-candidates manual stage). 31 tests passing. Surfaced + fixed one pre-existing violation (`docs/memory/brand_catalyst_works.md` was missing frontmatter).
- M3 ARMED for 2026-08-02: quarterly purge agent.
- M4 + M5: queued.

**Coverage today:**

- 8/25 active top-level folders had AGENTS.md before today (32%).
- M1 today brings coverage to 100% by writing the missing 17 + auditing the existing 8.
- Folder-purpose enforcement hook live as of M0 (commits adding new top-level folders without AGENTS.md/README.md will fail).

---

## Milestones

### M0: Governance scaffolding ✅ SHIPPED 2026-05-02

**What:** Path B chosen post-Sankofa+Karpathy audits. AGENT_SOP stays as the rules library (load-bearing). `docs/GOVERNANCE.md` is the 64-line routing table. Conflict-resolution rule, retirement protocol, success criteria, explicit gap statement all locked.

**Files shipped:**

- `docs/GOVERNANCE.md` (64 lines, routing table + protocols)
- `docs/AGENT_SOP.md` top-of-file annotation pointing at GOVERNANCE.md
- `docs/roadmap/compass.md` (this file)
- `docs/roadmap/README.md` Codename Registry entry
- `scripts/check_folder_purpose.py` (new pre-commit hook)
- `.pre-commit-config.yaml` updated to wire the hook
- Memory entry: pointer to GOVERNANCE.md as the constitution

---

### M1: AGENTS.md compliance audit + backfill ✅ SHIPPED 2026-05-02

**What:** Every top-level folder must have an AGENTS.md (or README.md where the rule allows it). 11 missing AGENTS.md written (config, data, deliverables, migrations, projects, research, sql, templates, tests, thepopebot, zzzArchive). 8 existing audited; n8n/AGENTS.md fixed for stale workflows/ subfolder reference. GOVERNANCE.md cross-refs added to all 8 existing. 100% folder-governance coverage; was 32%. Notion task created and marked Done.

**Each AGENTS.md must contain:**

1. Purpose (one sentence answering "what goes here?")
2. What does NOT go here
3. Live-mount notation if applicable (with reference)
4. Graduation/archive triggers (if applicable)
5. Reference to the Folder Governance rule in AGENT_SOP

**Branch:** working directly on main (low-risk doc additions)

**Trigger:** today (this session).

**Success criterion:** `bash scripts/check_folder_purpose.py` returns 0 (all top-level folders compliant).

---

### M2: Enforcement layer ✅ SHIPPED 2026-05-02 (evening)

**What:** Converted governance rules from documents to mechanism. Six pre-commit hooks now live (folder-purpose from M0 plus the five M2 hooks). Total Python: ~750 lines across 5 new scripts; 31 tests passing.

1. ~~folder-purpose hook (every top-level folder needs AGENTS.md or README.md)~~ ✅ M0
2. ✅ `scripts/check_memory_frontmatter.py` (every `docs/memory/*.md` needs YAML frontmatter with valid name/description/type fields). Hard-fail. Surfaced + fixed one pre-existing violation: `docs/memory/brand_catalyst_works.md`.
3. ✅ `scripts/check_session_log_updated.py` (any roadmap edit needs a new dated `### YYYY-MM-DD:` entry, except cosmetic-only changes). Hard-fail; bypass with `SKIP_SESSION_LOG=1`.
4. ✅ `scripts/check_rule_redundancy.py` (token-Jaccard ≥0.85 against the rule corpus across AGENT_SOP, GOVERNANCE, memory, all AGENTS.md). Warn-only; strict mode via `RULE_REDUNDANCY_STRICT=1`.
5. ✅ `scripts/check_retirement_candidates.py` (lists rule-corpus files untouched 90+ days; markdown or plain output). Manual stage in pre-commit; runnable directly any time. Complements the M3 quarterly agent.
6. ✅ `scripts/check_doc_size.py` (per-file growth thresholds: GOVERNANCE 70/85, AGENT_SOP 400/600, MEMORY.md 195/220, memory entries 400/600, folder-AGENTS.md 200/400; skill-payload AGENTS.md exempted because they are skill content, not folder governance; roadmaps exempt). Hard-fail at hard limit; strict mode via `DOC_SIZE_STRICT=1`.

**Wired into:** `.pre-commit-config.yaml` (5 new entries, file-pattern scoped to the rule corpus).

**Tests:** `tests/test_check_memory_frontmatter.py`, `tests/test_check_session_log_updated.py`, `tests/test_check_rule_redundancy.py`, `tests/test_check_retirement_candidates.py`, `tests/test_check_doc_size.py`. 31 cases total, all green.

**Notes:**

- The redundancy hook stays in warn-only mode for now: false-positive risk is real for legitimate cross-references. If it proves clean over a quarter, flip default to strict.
- The MEMORY.md cap chose 195/220, anchored on the system-reminder note that the loader truncates after 200 lines (catches creep before truncation, hard-fails before symptoms hit).
- Skill-payload AGENTS.md exemption (`skills/<name>/AGENTS.md`) was added after the first all-files run flagged Vercel react-best-practices (3750 lines) and postgres-best-practices (1490 lines). These are skill content, not folder governance; the cap is correctly scoped to folder-purpose AGENTS.md (top-level + immediate children of governed folders).

---

### M3: Quarterly purge cadence ⏳ ARMED 2026-05-02 (first run 2026-08-02)

**What:** Every 90 days, run a governance review pass. Surface rules untouched 90+ days that have no commits/hooks/memory referencing them. Decide retire vs keep, with manifest entries for any retirement.

**First scheduled run:** 2026-08-02 09:00 MT (15:00 UTC).

**Routine:** `trig_01YX1FKubUPD2JXTsAPbxhEo` (one-time remote agent, claude-sonnet-4-6). View at https://claude.ai/code/routines/trig_01YX1FKubUPD2JXTsAPbxhEo

**What the agent will do:**

1. Read GOVERNANCE.md, AGENT_SOP.md, compass.md M3 to understand rules.
2. `git log --since='90 days ago'` against each governance surface (AGENT_SOP, GOVERNANCE, repo-structure.md, all folder AGENTS.md, .pre-commit-config.yaml, all roadmap files).
3. For each potentially-stale rule, grep codebase for active references (excluding zzzArchive/, node_modules/, .venv/, external/).
4. Write `docs/audits/governance-purge-2026-08-02.md` with retirement candidates + stale-but-referenced + active surfaces sections. NO automatic retirement.
5. Commit + push (note: SecureWatch hook is slow; agent has been instructed to be patient).
6. Final stdout reports candidate count + audit path.

**Recurrence:** this is a one-time routine; quarterly recurrence to be re-armed in the next session if Boubacar wants the cadence to continue. (Re-arming pattern: update the routine with a new `run_once_at` 90 days out, or convert to a cron expression.)

**Success criterion:** first run produces a non-empty candidate list AND ≥1 rule actually retires (Boubacar's review).

---

### M5: output/ submodule reconciliation + websites/apps restructure ⏳ QUEUED

**Why:** Phase 3 of the 2026-05-02 structural cleanup surfaced two real issues that need a dedicated session:

1. **`output/` .gitmodules mismatch:** agentsHQ's `.gitmodules` registers `output/` as `bokar83/attire-inspo-app`, but the local working tree's `output/.git/config` points at `bokar83/signal-works-demo-hvac.git` (commit `283f7eba`). **These are TWO SEPARATE repos and must NEVER be merged** (Boubacar locked rule 2026-05-02). Resolution requires picking which repo is canonical for `output/` and re-establishing a separate path for the other if both are needed locally.
2. **`output/` structural restructure:** the parent folder holds 14 live websites (~996 MB) + 5 nested git-link submodules (attire-inspo-app-fresh, baobab-app, calculatorz-app, elevate-rebuild-app, signal-works-rod-app). Original Phase 3 plan to "promote websites/apps to top-level + move attire-inspo to workspace/aminoa" is too high-blast-radius for a multi-purpose session. Needs its own focused 3-4 hour window.

**Trigger:** dedicated window when Boubacar is fresh and has 3-4 hours.

**Scope:**

1. Decide repo canonicalization for `output/` (Option A: re-clone from `bokar83/attire-inspo-app`; Option B: update `.gitmodules` to match `signal-works-demo-hvac`).
2. Save the non-canonical repo's local checkout to a separate path before any change.
3. Decide structural endpoint: keep `output/` as parent OR promote `output/websites/` and `output/apps/` to top-level.
4. If promoting: update `skills/vercel-launch/scripts/launch.sh:61` + every other reference + AGENTS.md for new top-level dirs.
5. Decide attire-inspo-app destination: `workspace/aminoa/attire-inspo-app/` (per Boubacar's daughter-folder direction) OR keep at current location.
6. Test each of 14 websites resolves and renders correctly post-move.
7. Test `vercel-launch` skill on a throwaway test app to confirm it lands at the right path.
8. Three-way nsync.

**Reference:** `docs/reference/output-folder-anatomy.md` (full anatomy + do-not-merge warning, written 2026-05-02).

**Branch:** `feat/output-restructure-and-reconciliation`

**ETA:** 3-4 hours dedicated.

**Success criteria:**

- `.gitmodules` URL matches local `output/.git/config` URL (one chosen canonical state).
- The two repos remain distinct on disk; no merge attempted.
- All 14 websites resolve at expected paths (whatever the new home is).
- `vercel-launch` test produces a working Vercel deploy from the post-restructure path.
- All 5 nested submodules still bind correctly.

---

### M4: LLM-readable governance manifest ⏳ QUEUED

**What:** A machine-readable version of the governance routing table. JSON or YAML at `docs/governance.manifest.json`. Lets every LLM agent (Claude Code, Codex, future MCP servers) load the routing table without reading the markdown.

**Schema:**

```json
{
  "rule_types": [
    {"name": "...", "source_of_truth": "...", "enforcement": [...], "review_cadence": "..."}
  ],
  "conflict_resolution": [...],
  "retirement_protocol": {...}
}
```

**Trigger:** when the routing table stabilizes (post-M2, when enforcement layer is in place).

**ETA:** 30 minutes (mechanical conversion of the markdown table).

**Success criterion:** Codex can answer "where does a folder-purpose rule live?" by reading only the JSON.

---

## Descoped Items

- **300-line meta-document constitution.** Sankofa Council 2026-05-02 verdict: that's the dying-enterprise pattern. Skipped in favor of 64-line routing table + load-bearing AGENT_SOP.
- **Renaming AGENT_SOP to GOVERNANCE.** Path A from the Karpathy audit. Cascade risk too high (every memory entry, CLAUDE.md, CODEX.md, session-start hook references AGENT_SOP). Path B chosen.

---

## Cross-References

- Constitution: `docs/GOVERNANCE.md`
- Rules library: `docs/AGENT_SOP.md`
- Sankofa audit: 2026-05-02 chat
- Karpathy audit: 2026-05-02 chat
- Memory: `reference_folder_governance.md` (Folder Governance rule)
- Sister roadmaps that this one governs: `atlas.md`, `harvest.md`, `studio.md`, `echo.md`, `dashboards4sale.md`

---

## Session Log

### 2026-05-02: Roadmap created, M0 SHIPPED, M1 in progress

Sankofa Council + Karpathy audit on 2026-05-02 reframed the proposed 300-line GOVERNANCE.md as documentation-of-documentation that would have made sprawl worse. Council recommended (a) Path B: separate routing table + load-bearing AGENT_SOP, (b) cap routing table at 80 lines, (c) ship one enforcement hook today (folder-purpose), (d) schedule the rest as multi-session compass work, (e) name the gap explicitly so future sessions don't think governance is "done."

All recommendations adopted. M0 shipped: `docs/GOVERNANCE.md` (64 lines), AGENT_SOP top-of-file annotation, compass.md, Codename Registry entry, `scripts/check_folder_purpose.py` pre-commit hook + `.pre-commit-config.yaml` wiring.

M1 (AGENTS.md audit + backfill) in progress this same session. 17 folders need AGENTS.md; 8 existing need Sankofa-audit pass. Doing both today, no deferral.

Next: M2 (full enforcement layer, 5 more hooks), trigger any time after M1 closes.

### 2026-05-02 (evening): M2 SHIPPED, all 5 enforcement hooks live

Built the 5 remaining enforcement hooks per the M2 spec, ~750 lines of Python across 5 scripts plus 31 test cases (all green). Total wall time inside the session: ~2 hours focused. Files: `scripts/check_memory_frontmatter.py`, `scripts/check_session_log_updated.py`, `scripts/check_rule_redundancy.py`, `scripts/check_retirement_candidates.py`, `scripts/check_doc_size.py`; tests under `tests/test_check_*.py`; wiring in `.pre-commit-config.yaml`.

Surfaced and fixed one pre-existing violation: `docs/memory/brand_catalyst_works.md` had no frontmatter. Added `name`/`description`/`type: reference`. The file's body content is unchanged.

Two design calls worth flagging:

1. **Redundancy hook is warn-only by default.** Token-Jaccard at 0.85 against the rule corpus. False-positive risk is real for legitimate cross-references between AGENT_SOP and memory entries; warn-only buys data before flipping default to strict. Set `RULE_REDUNDANCY_STRICT=1` to opt in.
2. **Skill-payload AGENTS.md exempted from the doc-size cap.** First all-files run flagged Vercel react-best-practices (3750 lines) and postgres-best-practices (1490 lines). Those are skill content, not folder governance. The cap is correctly scoped to folder-purpose AGENTS.md (top-level + immediate children of governed folders).

Open question still on the table: keep MEMORY.md cap at 195/220 or raise it to 250/300 as governance work expands? Today's MEMORY.md is at 205 lines (5 over the loader truncation point); the user's auto-memory file was the original target of the question, and the in-repo `docs/memory/MEMORY.md` is only 25 lines.

Next: M4 (LLM-readable governance manifest, ~30 min mechanical conversion) is the smallest queued item. M5 (output/ submodule reconciliation) is a 3-4 hour dedicated window per the existing Notion task.
