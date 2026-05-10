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
- M4 SHIPPED 2026-05-02 (evening): `docs/governance.manifest.json` (LLM-readable routing table) + `scripts/validate_governance_manifest.py` drift check + 7 tests. Wired to fire on edits to GOVERNANCE.md or the manifest.
- M5 SHIPPED 2026-05-02 (evening, late): `.gitmodules` canonicalized to `signal-works-demo-hvac`; original attire-inspo-app code relocated from `output/` root to `output/apps/attire-inspo-app/`; reference docs updated. Original 3-4 hour spec collapsed to 10 min once Boubacar reframed: GitHub repos already separate, no merge needed, just local hygiene. Placement rule: apps live in `output/apps/`, websites in `output/websites/`.

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

### M2.5: Routing evaluator gap detection (gbrain pattern) ✅ SHIPPED 2026-05-09

**Pattern source:** garrytan/gbrain `src/core/routing-eval.ts` + `src/core/check-resolvable.ts`. Absorbed 2026-05-09 (PROCEED — pattern-only, no install).

**What the pattern does:** Validates that user intents route to correct skills. Two layers:

- **Layer A (structural, no LLM):** Normalize intent + normalize trigger phrases. Check substring match. Flag if intent matches zero skills (gap) or multiple skills (ambiguity).
- **Fixture lint:** Reject test cases where the intent IS a trigger phrase verbatim (tautology — must paraphrase).

**Six audit checks from gbrain's check-resolvable:**

| Check | What it catches |
|-------|----------------|
| Unreachable skills | Skill in `skills/` with no entry in SKILLS_INDEX.md |
| MECE overlap | Two skills whose trigger phrases would both match the same intent |
| MECE gap | Common user intent pattern no skill covers |
| DRY violation | Logic inlined in a skill that should live in a shared convention file |
| Routing fixture miss | Test fixture didn't match expected skill (Layer A) |
| Stub unreplaced | Skill created from template still contains placeholder text |

**Integration plan for agentsHQ:**

- Add routing fixture JSONL files alongside each skill (`skills/<name>/routing-eval.jsonl`) — 2-3 real intent phrases per skill, paraphrased from trigger phrases.
- Add `scripts/check_routing_gaps.py` that reads all routing fixtures + SKILLS_INDEX.md and runs Layer A check. Output: `CLEAN` or list of gaps/overlaps/misses.
- Wire to pre-commit (warn-only first quarter; strict after fixtures reach >80% skill coverage).

**Pre-condition:** none. **Target:** next compass maintenance window. **Success criterion:** `python scripts/check_routing_gaps.py` returns CLEAN on all skills with fixtures; at least 50% of skills have fixture files.

---

### M6: Monthly self-audit of agentsHQ own config ⏳ QUEUED (first run 2026-05-16)

**Pattern source:** ECC AgentShield concept (absorbed 2026-05-09 from X-thread). Core insight: the Security Scan Gate in agentshq-absorb scans external artifacts but never turns inward. Our own CLAUDE.md, hooks, settings.json, and MCP configs have never been audited.

**What:** Run the Self-Audit Mode checklist (now documented in `skills/agentshq-absorb/SKILL.md`) against agentsHQ's own Claude Code configuration monthly. Four static checks, no external tools:

1. Hardcoded secrets in CLAUDE.md + handoff docs (v2-6 regex)
2. Shell-out patterns in hook scripts (v1-1 patterns)
3. Overly-broad permissions in settings.json (`*` globs, unconstrained Bash)
4. Non-TLS or raw-key MCP transport entries

**Success criterion:** `Check 1-4: CLEAN` on first run (2026-05-16). Any FINDINGS = fix before close. Zero v2-6 matches in CLAUDE.md and all handoff docs.

**Cadence:** monthly. Re-arm after each run. Also trigger on any new hook, MCP server, or settings.json entry added.

**Pre-condition:** none. Run Self-Audit Mode from agentshq-absorb skill.

**First run results (2026-05-09):**

```
SELF-AUDIT RESULTS : agentsHQ config
=====================================
Check 1 (secrets in docs):    CLEAN
Check 2 (hook shell-outs):    CLEAN
Check 3 (broad permissions):  FINDINGS — Read(*), Edit(*), Write(*) in settings.json
                               allow list are unconstrained globs. Intentional
                               (project-wide access for direct sessions) but
                               flagged for Boubacar review. Not an injection risk;
                               a blast-radius risk if a malicious skill runs.
Check 4 (MCP transport):      CLEAN

Overall: FINDINGS PRESENT (Check 3 only — REVIEWED + ACCEPTED 2026-05-09)
Action required: Check 3 reviewed 2026-05-09: Read*/Edit*/Write* broad allows are
                 intentional for direct session workspace access. Accepted. Re-verify
                 monthly that no new unconstrained Bash(*) allow appears.
```

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

### M5: output/ submodule reconciliation + attire-inspo relocation ✅ SHIPPED 2026-05-02 (evening, late)

**What shipped (collapsed scope):** Boubacar reframed the original spec on 2026-05-02 evening: both `bokar83/attire-inspo-app` and `bokar83/signal-works-demo-hvac` already exist as separate GitHub repos and stay separate. The only real work is local hygiene. Three tasks, ~10 min total.

1. **`.gitmodules` canonicalized.** Updated `output/` submodule URL from `bokar83/attire-inspo-app.git` to `bokar83/signal-works-demo-hvac.git` to match the live working-tree checkout. Resolves the long-standing inconsistency where `.gitmodules` and `output/.git/config` disagreed.
2. **attire-inspo-app code relocated.** Copied the original Next.js code (`app/`, `components/`, `lib/`, `public/`, `package.json`, etc., 13 files + 4 dirs) from `output/` root to `output/apps/attire-inspo-app/`. The placement rule: apps in `output/apps/`, websites in `output/websites/`. Boubacar's words: "Just keep it as simple as that for now. If we have to adjust later on, we do so." The `bokar83/attire-inspo-app` GitHub repo is unchanged (this is local-only hygiene). Note: because `output/` is a submodule, this new app sits inside the submodule's working tree (currently checked out as `signal-works-demo-hvac`); cleaning up that submodule's tracked files is a separate follow-up commit on the submodule itself.
3. **Reference docs updated.** `docs/reference/output-folder-anatomy.md` rewritten "CRITICAL: TWO DIFFERENT REPOS" section as "RESOLVED 2026-05-02" with the new state. `docs/reference/repo-structure.md` updated `output/` row to note canonical repo + relocation.

**Descoped from original M5 spec (correctly, per Boubacar's reframe):**

- ❌ "Promote websites/apps to top-level": premature, no business need.
- ❌ "Test all 14 websites resolve": no moves, no test needed.
- ❌ "Test vercel-launch lands at right path": `output/apps/` unchanged.
- ❌ "Decide repo canonicalization": Boubacar decided signal-works-demo-hvac.

**Known follow-up (not blocking M5 close):** the `output/` submodule's working tree may still contain the old attire-inspo files at its root because they were tracked by the previous repo state. Cleaning the submodule's working tree is a commit on `signal-works-demo-hvac` that removes those files. Separate task; submodule-internal; not agentsHQ-side.

---

### M5 (original spec, descoped): output/ submodule restructure

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

### M4: LLM-readable governance manifest ✅ SHIPPED 2026-05-02 (evening)

**What:** Machine-readable mirror of the GOVERNANCE.md routing table at `docs/governance.manifest.json`. Lets every LLM agent (Codex, MCP servers, future bots) load the routing table without parsing markdown. GOVERNANCE.md remains the human-readable source of truth; the manifest is the machine-readable mirror.

**Files shipped:**

- `docs/governance.manifest.json` (~150 lines JSON). Contains: 8 `rule_types` entries (one per routing-table row), `conflict_resolution` (4-tier precedence), `retirement_protocol` (quarterly purge cadence + archive paths), `adding_a_new_rule` (4-step protocol), `session_start_reading_order` (5-file order), `enforcement_hooks.pre_commit` (9 hooks with mode + scope + bypass envs), `compass_status_at_emit_time` snapshot.
- `scripts/validate_governance_manifest.py` (drift check). Validates: JSON parses, required keys present, routing-table row count matches `rule_types` length, hook-script paths exist on disk.
- `tests/test_validate_governance_manifest.py` (7 cases, all green).
- `.pre-commit-config.yaml` wired the validator to fire only on edits to `docs/GOVERNANCE.md` or `docs/governance.manifest.json`.

**Success criterion met:** validator returns `OK: governance manifest in sync with GOVERNANCE.md (8 rule_types, 8 routing-table rows, 9 hooks)`. Codex can now answer "where does a folder-purpose rule live?" by reading only the JSON.

**Notes:**

- Manifest is hand-maintained (not generated). The validator is the discipline: when GOVERNANCE.md gains a row, the next commit fails until the manifest mirrors it. This pushes the discipline onto mechanism without forcing a build step.
- `compass_status_at_emit_time` is a snapshot. It is allowed to drift; the field signals when the manifest was last written, not the live state. If true live state is ever needed, query `docs/roadmap/compass.md` directly.

---

### M6: Security Scan Gate v2 patterns ✅ SHIPPED 2026-05-04

**What:** Extend the v1 security scan (2 patterns shipped 2026-05-04) with the remaining 5 high-value patterns:

1. Typosquatted package names (1-char edit distance from popular libs in requirements.txt / package.json)
2. Hardcoded IPs or exfil endpoints in scripts
3. Environment variable harvesting sent to external URL
4. Secrets committed in history (grep against known patterns)
5. Repo created < 30 days ago with sudden star/fork spike (astroturfed trust signal)

**Also:** add acceptance test fixtures to `skills/agentshq-absorb/fixtures/` with known-malicious and known-clean sample files so false-positive rate is measurable.

**Trigger:** any session focused on agentshq-absorb hardening, OR after v1 patterns generate their first BLOCKED or SUSPICIOUS verdict in the wild.

**Shipped:** v1 (2 patterns) + v2 (4 patterns + 80-pkg reference list) + v3 (astroturfed repo detection via GitHub API) + acceptance test fixtures for all 7 patterns. 4 Notion tasks Done.

**Success criterion:** ≥1 pattern detects a real suspicious repo in 30 days of use; false positive rate on known-clean repos stays at zero.

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
- Sister roadmaps that this one governs: `atlas.md`, `harvest.md`, `studio.md`, `echo.md`

---

## Session Log

### 2026-05-04: n8n-mcp absorb session: M6 security scan gate exercised in the wild

First real-world use of the v1 security scan gate (shipped earlier this session). Ran against `czlonkowski/n8n-mcp`: checked package.json `prepare` script (husky: secretlint only, no shell-out), `.husky/pre-commit` (secretlint on staged files, no curl/wget), `src/telemetry/` (Supabase telemetry present but disclosed in PRIVACY.md, opt-out env var available, sanitizes credentials). Result: STATIC-CLEAN. Gate functioned as designed.

Telemetry disclosure pattern noted: hardcoded Supabase anon key + URL in `TELEMETRY_BACKEND` constant is not a v2 exfil flag when disclosed + opt-out exists. This edge case is worth documenting in M6 v2 pattern work as a false-positive guard.

No compass milestones changed this session. M6 v2 pattern work still queued.

### 2026-05-04: M6 fully complete - v1+v2+v3 all shipped, fixtures written

Continued same session: v2 patterns (typosquatting with 80-pkg reference list, exfil IPs, env var harvesting, hardcoded secrets) + v3 (astroturfed repo detection via GitHub API: age ≤ 30d + stars ≥ 50 = SUSPICIOUS). Acceptance test fixtures written for every pattern under `skills/agentshq-absorb/fixtures/security-scan/`. v3 fixture is a procedure README (GitHub API required - no static file). 4 Notion tasks total, all Done. M6 complete.

### 2026-05-04: Security Scan Gate shipped in agentshq-absorb skill (M6 added)

Added mandatory security scan gate to `skills/agentshq-absorb/SKILL.md`. Fires before any clone or install. Static-only (no external tools). Two v1 patterns shipped: postinstall shell-out and base64/decode-exec chain. Sankofa+Karpathy councils run; Sankofa returned PROCEED-WITH-MODIFICATIONS, all 5 mods applied: shared primitive framing, pattern attribution in verdicts, SUSPICIOUS override path, STATIC-CLEAN label (not CLEAN), v2 patterns deferred. New M6 milestone added for v2 pattern work. Three Notion tasks created (Backlog).

### 2026-05-04: Studio M3 production pipeline shipped, no compass changes

Studio M3 session touched compass.md as part of a bulk commit. No compass milestones changed this session.

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

### 2026-05-02 (evening, late): M4 SHIPPED, manifest + validator live

Built the LLM-readable governance manifest per the M4 spec. Files: `docs/governance.manifest.json` (8 rule_types mirroring the routing table, plus conflict_resolution, retirement_protocol, adding_a_new_rule, session_start_reading_order, enforcement_hooks for all 9 pre-commit hooks, and a compass_status snapshot). Validator at `scripts/validate_governance_manifest.py` with 7 tests (all green); wired to fire only on edits to GOVERNANCE.md or the manifest.

Two new hard rules locked into AGENT_SOP this session (and indexed in MEMORY.md for cross-agent inheritance): (1) auto-update the roadmap + Notion task after every shipped task with no prompting; (2) propose codification (memory / skill / hook / hookify rule) when patterns repeat using the two-strikes rule. The rule additions were demonstrated immediately: M2 + M4 Notion tasks created (M2 backfilled to Done, M4 In Progress → Done in the next push), compass.md updated in the same turn for both shipments.

Compass status as of this entry: M0 + M1 + M2 + M4 SHIPPED. M3 ARMED for 2026-08-02. M5 the only QUEUED milestone. The governance scaffolding is complete; the long-tail work is M5's output/ reconciliation and the open MEMORY.md cap question.

### 2026-05-02 (evening, late): M5 SHIPPED in 10 minutes after scope collapse

Boubacar reframed M5 immediately after M4 closed: both attire-inspo-app and signal-works-demo-hvac already exist as separate GitHub repos. No merge work. The only thing local-side that matters is moving attire-inspo out of `output/` root so the folder stops being a confusion zone. Original 3-4 hour spec → 10 min execution.

Three tasks, all done: (1) `.gitmodules` URL flipped from `attire-inspo-app.git` to `signal-works-demo-hvac.git` to match the live checkout. (2) attire-inspo-app code (`app/`, `components/`, `lib/`, `public/`, package files, configs, dotfiles) copied from `output/` root to `output/apps/attire-inspo-app/` (initial plan was `workspace/aminoa/` but `workspace/` is gitignored; Boubacar reframed to keep it simple: apps in `output/apps/`, websites in `output/websites/`). (3) `output-folder-anatomy.md` and `repo-structure.md` updated to reflect resolved state.

**Compass status post-M5: M0 + M1 + M2 + M4 + M5 SHIPPED. M3 ARMED for 2026-08-02. No queued milestones. Compass scaffolding + enforcement layer + LLM-readable mirror + structural reconciliation all complete.** What remains long-term: the M3 quarterly purge will fire on its own; future Compass work (renaming `output/` to disambiguate from `outputs/`/`agent_outputs/`, raising MEMORY.md cap, etc.) becomes a fresh milestone if/when needed.

### 2026-05-06 (evening): Skill portfolio governance audit

Sankofa Council 30-day audit run. Governance finding: skill directories with stub SKILL.md files may contain active Python imported by orchestrator. Six directories (outreach, forge_cli, email_enrichment, github_skill, local_crm, notion_skill) were nearly archived but caught by import grep. Hard rule added to memory and AGENT_SOP candidate: "grep orchestrator + signal_works before archiving any skill directory."

Skill count: 74 -> 68. SKILLS_INDEX regenerated. Archive manifest at `zzzArchive/2026-05-06-skill-consolidation/MANIFEST.md`.

No Compass milestone changes. This is a governance integrity note.
