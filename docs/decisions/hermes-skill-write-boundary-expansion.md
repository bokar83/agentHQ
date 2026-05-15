# Hermes Write Boundary Expansion: `skills/**/references/`

Status: PROPOSAL (not yet approved). Awaiting Boubacar review.
Date opened: 2026-05-14.
Owner: Compass M7 scope.

## Why this exists

The absorb_crew agent (Phase 1-3, shipped 2026-05-14) reliably classifies
inbound artifacts as PROCEED / ARCHIVE-AND-NOTE / DONT_PROCEED. About 70%
of PROCEED verdicts are small-tier: `enhance skills/X` or `extend skills/X`
or `new tool`. The actual wiring of those PROCEEDs back into the repo is
still done by hand by Boubacar in a Claude Code session. At the current
absorb cadence (5-7 per day, ~1-2 PROCEEDs per day) the wiring lag is the
new bottleneck.

Auto-wiring small-tier PROCEEDs requires the Hermes self-healing agent
(CLAUDE.md L370-385) to have write permission on the relevant repo paths.
Today the Hermes ALLOWED list explicitly excludes anything under `skills/`,
which means even appending a single reference question to
`skills/client-intake/references/intake-questions-by-topic.md` is a
constitutional violation.

This doc proposes a narrow expansion of the Hermes write boundary that
unlocks ~90% of future small-tier PROCEED auto-wiring without giving
Hermes the ability to modify executable skill surfaces.

## The proposal

Add three new entries to the Hermes ALLOWED writes table in CLAUDE.md:

| Path pattern | Purpose |
|--------------|---------|
| `skills/**/references/*.md` | Data files referenced by a skill (templates, question banks, lookup tables, style notes). Pure markdown content, no frontmatter, no executable. |
| `skills/**/patterns/*.md` | Pattern documentation appended to a skill's pattern library. Pure markdown, no executable. |
| `skills/**/data/*.json` | Static JSON data files consumed at read-time by a skill. No code paths trigger on writes. |

The Hermes FORBIDDEN list stays unchanged. Specifically: `SKILL.md` itself
in every skill directory, all `*.py` files in any skill directory, all
`scripts/` directories inside skills, and the `evals/` directory inside
any skill all remain forbidden.

## Why this is safe (the case)

### Executable surfaces stay protected

A skill's executable surface is `SKILL.md` (the frontmatter `description`
field drives skill activation, the body of `SKILL.md` is the prompt the
agent reads when the skill is invoked) plus any `*.py` or `*.sh` files
inside the skill directory. None of these are touched by this expansion.

`references/*.md`, `patterns/*.md`, and `data/*.json` are **read-only data
inputs** consumed by the skill at run time. They are functionally identical
to a row added to a CSV file in `data/` (which Hermes is already allowed
to write to). Letting Hermes append to them is the same surface as letting
Hermes write to `data/changelog.md`, which is in the current ALLOWED list.

### No privilege escalation

Hermes cannot use a reference-file edit to gain new permissions. The skill
that reads the reference file already has the permissions it has, granted
at skill invocation by the human session that triggered the skill. Adding
a new question to `intake-questions-by-topic.md` does not change what
`skills/client-intake/SKILL.md` is allowed to do; it just changes what
content the skill quotes back to the user when invoked.

### No agent self-modification

The Hermes hard rule against self-modification (cannot edit `CLAUDE.md`,
`AGENT_SOP.md`, `GOVERNANCE.md`) is unchanged. Hermes still cannot:

- Edit a `SKILL.md` frontmatter to change which trigger phrases fire
- Add or remove a tool in a skill's `tools=` allowlist
- Edit a skill's Python helpers
- Add a new skill directory (creates SKILL.md, which is forbidden)
- Edit gate_agent, coordination, or any orchestrator Python module

### Gate review still mandatory

Every Hermes-spawned PR still goes through the Gate. Gate runs the
existing Karpathy pre-commit hook and the pre-commit checks. The Gate
auto-resolve drop bug (see `feedback_gate_resolve_drops_co_located_blocks.md`)
already has the same blast radius for human-spawned PRs in this surface, so
this proposal does not widen that risk.

## Risk vectors and mitigations

| Risk | Mitigation |
|------|------------|
| Hermes writes contradictory questions to a reference file | Karpathy mandatory on every Hermes PR. Gate reviews diff. Worst case is bad content, not bad code. Reversible by a 1-line revert. |
| Hermes writes a `data/*.json` that an existing skill cannot parse | Existing skills consuming JSON already validate or fall through on parse error. Mitigation is the same as for any human-written JSON edit: pre-commit check (if one exists) catches it, else next-skill-run fails noisily and Boubacar reverts. |
| Hermes auto-wires too many small-tier PROCEEDs and Content Board fills with low-quality copy | Out of scope here; that is a Phase 4 rate-limit decision, not a boundary decision. The boundary just gives Hermes the *ability* to write; the absorb agent's verdict gate decides *which* edits Hermes attempts. |
| Boundary creep: a future maintainer adds `skills/**/*.py` to ALLOWED | Compass governance owns this. The boundary table is in `CLAUDE.md` which is on the Hermes FORBIDDEN list, so Hermes itself cannot widen the boundary. Boubacar review required for every CLAUDE.md edit. |

## Migration plan

1. **Approve the boundary expansion** (Boubacar reviews this doc, edits
   CLAUDE.md L370-385 to add the three new ALLOWED rows). One branch,
   Gate review, merge.

2. **Update `scripts/check_hermes_write_boundary.py`** (Compass M7
   enforcement hook) to reflect the new ALLOWED list. Add a test case
   that asserts Hermes CAN write to
   `skills/client-intake/references/foo.md` and CANNOT write to
   `skills/client-intake/SKILL.md`. One branch, Gate review, merge.

3. **Ship Phase 4 absorb_auto_wire crew** (separate branch, Gate
   review). Listens for `done` rows in `absorb_queue` with
   `verdict='PROCEED'` and `placement IN ('enhance', 'extend', 'new_tool')`
   AND `placement_target` matches a path inside the new ALLOWED globs.
   Spawns a Hermes job that creates a feature branch, appends the
   reference / pattern / data file, commits, pushes [READY]. Gate
   reviews. Telegram alert on merge.

4. **Test with one absorb** (Boubacar picks a low-stakes small-tier
   PROCEED from the followups queue). Verify the auto-wire branch
   lands cleanly, Gate review catches nothing, content is acceptable.

5. **Enable for all small-tier PROCEEDs.** Add a Telegram approval
   step where Boubacar can flip a kill switch per absorb if the
   auto-wired content looks off, before Hermes pushes. Default state:
   auto-wire ON, opt-out per absorb via Telegram reject.

## What this proposal does NOT do

- Does not expand Hermes write access to `SKILL.md`, ever
- Does not expand Hermes write access to any `*.py` file in any skill
- Does not expand Hermes write access to any `*.py` file in orchestrator
- Does not expand Hermes write access to `settings.json`, `.pre-commit-config.yaml`, `docker-compose.yml`, or any config file
- Does not change the existing `data/changelog.md`, `agent_outputs/`, or `workspace/` ALLOWED entries
- Does not weaken the wildcard permission rule (`"*"` glob still forbidden)
- Does not let Hermes create new directories (creating
  `skills/foo/references/` would require the parent `skills/foo/` to
  exist, which requires `SKILL.md` first, which is FORBIDDEN)

## Open questions for Boubacar

1. Are you comfortable with Hermes appending to existing reference files
   without your review? Or do you want a Telegram approval gate per
   auto-wire PR (in addition to Gate review)?
2. Should `skills/**/data/*.json` be in scope or out of scope?  Including
   it would let Hermes update lookup tables like an ICP list. Excluding it
   keeps the boundary at markdown-only.
3. Should the boundary apply to all 75 skills or only a hand-picked
   subset? An allowlist of opted-in skills (`ctq-social`, `client-intake`,
   `library`, `boubacar-prompts`) is more conservative than blanket
   skills/**.
4. Rate limit on auto-wires per day? Default proposal: 3 auto-wires per
   day max, anything beyond queues for Boubacar review. Lower / higher?

## Decision tracking

Boubacar approval needed on: (a) the three new ALLOWED rows verbatim,
(b) the per-absorb Telegram approval gate yes/no, (c) the
data/*.json inclusion yes/no, (d) the per-skill allowlist or
blanket skills/** access, (e) the per-day rate limit.

When approved, this doc becomes the migration spec. Each step above lands
as its own [READY] branch.

---

## M7 status update (2026-05-15)

All 5 Boubacar decisions resolved with recommended defaults:
  1. Gate-review-only (no per-PR Telegram gate)
  2. Markdown only (data/*.json deferred to Phase 5)
  3. Per-skill allowlist: ctq-social, client-intake, library, boubacar-prompts
  4. Rate limit: 3 auto-wires per 24h America/Denver
  5. ALLOWED rows verbatim approved

Migration plan executed in 3 companion branches landing today:
  - feat/hermes-boundary-expand-2026-05-15 (CLAUDE.md ALLOWED expansion)
  - feat/hermes-boundary-enforce-2026-05-15 (scripts/check_hermes_write_boundary.py + tests + pre-commit wiring)
  - feat/absorb-auto-wire-crew-2026-05-15 (orchestrator/absorb_auto_wire.py + migration 011)

Phase 5 (data/*.json inclusion + per-skill allowlist expansion) re-opens after 30+ shipped auto-wires + zero incidents.

