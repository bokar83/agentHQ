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

*Last updated: 2026-05-02*

- M0 SHIPPED today: `docs/GOVERNANCE.md` (64 lines) routing table + AGENT_SOP top-of-file annotation + this roadmap + folder-purpose pre-commit hook (the M0 enforcement piece).
- M1 IN PROGRESS today: Sankofa-audit existing AGENTS.md files + write missing AGENTS.md for 17 uncovered folders.
- M2-M4: queued.

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

### M1: AGENTS.md compliance audit + backfill ⏳ IN PROGRESS 2026-05-02

**What:** Every top-level folder must have an AGENTS.md (or README.md where the rule allows it). Today's audit caught 17 folders missing it. M1 = audit existing 8 to ensure they meet the standard, write the missing 17.

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

### M2: Enforcement layer ⏳ QUEUED

**What:** Convert governance rules from documents to mechanism. Write 5 additional pre-commit hooks (folder-purpose hook ships in M0):

1. ~~folder-purpose hook (every top-level folder needs AGENTS.md or README.md)~~ ✅ M0
2. memory-frontmatter hook (every memory file has name/description/type fields)
3. session-log hook (commits on roadmapped branches must update the session log)
4. redundancy hook (no rule can be added if the same rule exists in another file; grep-check)
5. retirement hook (every quarter, surface rules untouched 90+ days)
6. doc-size hook (any markdown rule doc over 500 lines triggers a "consolidate" warning; AGENT_SOP at 106 today is fine)

**Trigger:** any time after M1 closes.

**ETA:** 2-3 hours when triggered (5 hooks, each ~30 lines Python).

**Success criterion:** all 6 hooks pass on a clean commit; all fail on a planted violation.

---

### M3: Quarterly purge cadence ⏳ QUEUED

**What:** Every 90 days, run a governance review pass. Surface rules untouched 90+ days that have no commits/hooks/memory referencing them. Decide retire vs keep, with manifest entries for any retirement.

**First scheduled run:** 2026-08-02 (90 days after M0 ships).

**Trigger:** date-gated.

**Mechanism:** scheduled remote agent (Claude Code routine) writes `docs/audits/governance-purge-<date>.md` with the candidates, posts to Telegram for Boubacar's review.

**Success criterion:** first run produces a non-empty candidate list AND ≥1 rule actually retires.

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
