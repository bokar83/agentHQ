# Atlas M7b: Auto-Publish via Blotato API, Design Spec

**Status:** DESIGN, awaiting build session
**Spec date:** 2026-04-26 (build session targets Sunday morning at the earliest)
**Spec author:** drafted 2026-04-25 evening as the closeout of the M7a session
**Owner:** Boubacar Barry
**Roadmap:** `docs/roadmap/atlas.md` § M7b

---

## Why this spec exists

Atlas M7a verified the Blotato API works (5-9 sec end-to-end latency, verbatim publish, contract matches docs). M7b is the build that uses M7a's verified contract to close the L3 publish loop without Boubacar's daily tap. M7a closed Saturday 2026-04-25. M7b was scoped at 60-90 minutes. The Sankofa Council ran on the proposed design same evening and surfaced one fatal bug, one structural gap, one architectural disagreement, and three smaller flaws that all need resolution before code starts.

This spec captures the Council's findings, names the open decisions Boubacar must make at the top of the build session, and documents the must-fix items so the build session does not relitigate them.

---

## Council findings (Saturday 2026-04-25 evening)

### Fatal bug, must fix in any design

**Idempotency strategy in the proposed design is wrong about which failure mode it prevents.**

Proposal was: persist `postSubmissionId` to Notion BEFORE polling, so a poll-loop crash does not re-submit.

The Contrarian caught the gap: the most common failure is the POST returning 200 + postSubmissionId, then the Notion write to persist that ID failing (network blip, Notion rate limit, anything). Next 5-min tick: same Notion record still says Status=Queued with no Submission ID, so the orchestrator submits AGAIN. Two identical posts on Boubacar's LinkedIn 5 minutes apart.

**Required fix:** persist a placeholder BEFORE the POST, not after. Two viable mechanisms:

1. **Notion Status=Publishing transition before POST.** New Status value flips before the API call. Any tick that sees Status=Publishing skips the record. After successful POST, write postSubmissionId. After successful poll, flip Status=Posted.
2. **Client-generated UUID written to Submission ID field BEFORE POST.** If Blotato accepts a request-id or correlation-id header for client-side dedup, pass the UUID in both the body and the header. Blotato may reject duplicate submissions with the same UUID.

Decision needed: 1 or 2. Option 1 is simpler but requires the Notion schema change. Option 2 depends on a Blotato feature not surfaced in M7a's docs review; need to test.

### Structural gap, must fix in any design

**The state machine is undermodeled.** The proposal had Status=Queued silently meaning three different things: waiting for Scheduled Date, in-flight with postSubmissionId, failed and awaiting human. Three states, one label.

**Required fix:** granular Status values OR move state out of Notion. Two options:

1. **Granular Notion Status values:** add `Publishing` (in-flight), keep `Posted` (terminal success), add `PublishFailed` (terminal failure, human attention). `Queued` reverts to its original meaning (waiting for Scheduled Date).
2. **Postgres state machine, Notion mirror:** `orc-postgres` holds a publish_attempts table with full state machine, Notion only sees Queued -> Posted or Queued -> PublishFailed transitions. Decouples runtime state from human-visible state.

Decision needed: 1 or 2. Option 1 is the minimum viable change. Option 2 is correct long-term but is a bigger build.

### Architectural disagreement, Boubacar must call

**Is M7b a new module or a 30-line patch on publish_brief.py?**

The First Principles Thinker challenged the new-module framing. publish_brief.py already does most of the work. Adding "if Scheduled Date hits and Boubacar has not tapped Posted, call Blotato" to the existing tick is much smaller than building a parallel publisher module + new heartbeat wake + new state machine.

The Expansionist countered: a new module is justified IF Studio M4 will reuse it. Atlas's two platforms (LinkedIn, X) are a strict subset of Studio's eight (YouTube, TikTok, IG, Threads, Spotify, etc.). A platform-agnostic publisher module built once for Atlas serves Studio M4 with near-zero refactor cost. A publish_brief.py patch ships faster but Studio M4 has to refactor.

Two paths:

**Path A: New module, platform-agnostic (Council Expansionist favored)**

- Files: `orchestrator/blotato_publisher.py` (publisher), `orchestrator/auto_publisher.py` (tick), modifications to `orchestrator/tools.py`, `orchestrator/heartbeat.py`
- Build estimate: 3-4 hours including tests, save point, branch, deploy, verify (NOT 60-90 min as originally scoped)
- Studio M4 cost: 30-60 min on top
- Right answer if Studio M4 ships within ~6 weeks

**Path B: Patch publish_brief.py (Council First Principles favored)**

- Files: `orchestrator/publish_brief.py` modified (add auto-publish branch), `orchestrator/tools.py` modified
- Build estimate: 60-90 min including tests
- Studio M4 cost: 4-6 hour refactor when Studio M4 ships
- Right answer if Studio M4 is months out OR the publish_brief.py patch is small enough to easily extract later

Boubacar's call. The decision matters because Path A and Path B have different specs from this point forward.

### Smaller flaws, must address regardless of path

1. **No kill switch named for auto_publisher specifically.** Atlas Phase 0 built `autonomy_state.json` with `griot.enabled` etc. M7b must add `auto_publisher.enabled` so Boubacar can pause auto-publish without pausing all of Atlas. Five-line addition; non-negotiable.

2. **Tick coordination with publish_brief.** Both ticks could try to publish the same record. Pick one of:
   - (a) auto_publisher only fires on records publish_brief has already briefed AND a flag says no human reply within X minutes
   - (b) auto_publisher and publish_brief query disjoint Notion views
   - (c) auto_publisher inherits publish_brief's job entirely on Scheduled Date and publish_brief stops sending briefs for past-due records
   
   Decision needed: a, b, or c. Option (b) is cleanest for Path A. Option (c) is natural for Path B (one tick).

3. **Weekday-only window misses Saturday-Sunday Scheduled Dates.** griot scheduler is weekday-only because it picks; auto_publisher must be 7-days-a-week because it executes. Different jobs, different windows. Heartbeat wake cron expression must reflect this.

4. **Skipped slot interaction with M2 backfill.** A PublishFailed record on a yesterday-or-today slot will look like a Skipped slot to M2's backfill phase. M2 will pull a new candidate into the same slot. The two ticks must not race. Resolution: M2's backfill must skip records with Status=PublishFailed (ignore the slot until human intervention) OR PublishFailed records must move to Status=Skipped to free the slot. Pick one in spec.

5. **Posted URL field structure.** Currently a single Notion field. M7b should write structured Posted URL data (or two fields if cross-posting LinkedIn AND X) so future M5 (analytics) and M8 (channel performance) can read cleanly. Five-minute decision now saves rework later.

---

## Open decisions Boubacar must make at the top of the build session

| # | Decision | Options | Default if no input |
|---|---|---|---|
| 1 | Idempotency mechanism | Notion Status=Publishing OR client-generated UUID | Notion Status=Publishing (simpler, no Blotato feature dependency) |
| 2 | State machine location | Granular Notion Status OR Postgres + Notion mirror | Granular Notion Status (smaller change, faster build) |
| 3 | New module vs publish_brief.py patch | Path A (new module, platform-agnostic) OR Path B (patch) | Path A IF Studio M4 ships within 6 weeks; Path B otherwise |
| 4 | Tick coordination | (a), (b), or (c) above | (b) disjoint views for Path A; (c) one tick for Path B |
| 5 | Kill switch | auto_publisher.enabled in autonomy_state.json | Required, not optional |
| 6 | Posted URL schema | Single field or per-platform fields | Per-platform fields if cross-posting LinkedIn + X today |
| 7 | M2 backfill interaction | PublishFailed blocks slot OR auto-flips to Skipped | PublishFailed blocks slot (audit trail preserved) |

---

## Required reads before code starts

- This spec (you are reading it)
- `docs/roadmap/atlas/m7a-decision-spike.md` (M7a contract, now historical but the API shape is here)
- `docs/roadmap/atlas.md` § M7b milestone block
- `d:/tmp/m7a-blotato-spike-notes.md` (smoke test results, full API contract notes, credentials)
- `orchestrator/publish_brief.py` (current state of the M1 path, M7b extends or coexists)
- `orchestrator/griot_scheduler.py` (M2 backfill phase, M7b must not race it)
- `orchestrator/heartbeat.py` (where new wake registers)
- Memory: `feedback_savepoint_before_big_changes.md`, `feedback_new_branch_per_feature.md`, `feedback_always_wire_tools.md`, `feedback_inspect_notion_schema_first.md`

---

## Build session checklist (do not skip)

1. Pull main, verify three-way nsync. Confirm studio session's commits landed cleanly. If studio is mid-flight, wait.
2. Create save point: `savepoint-pre-atlas-m7b-publisher-2026-04-26` (use the actual build date)
3. Open branch `feat/atlas-m7b-publisher` off main
4. At top of session: lock decisions 1-7 above. Write them into the build session's first commit message so the choices are auditable.
5. If decision 1 is Notion Status=Publishing: add the Status value to Notion select FIRST, verify schema, then write code. Per `feedback_inspect_notion_schema_first.md`.
6. Write tests alongside code. Failure paths first. Mocked Blotato HTTP. Mocked Notion writes.
7. Local test pass before any deploy.
8. VPS deploy: SCP changed files, container rebuild, manual smoke (one real publish via the auto-publisher path on a real record), verify Notion + LinkedIn/X both reflect the publish.
9. Add `BLOTATO_API_KEY`, `BLOTATO_LINKEDIN_ACCOUNT_ID`, `BLOTATO_X_ACCOUNT_ID` to VPS `.env` AT DEPLOY DAY ONLY. Not before.
10. Three-way nsync. Update Atlas roadmap M7b block with shipped status. Append session log entry. Push.

---

## Hard rules in force during the build

- No em dashes anywhere (pre-commit hook blocks them)
- No double hyphens in prose (same hook flags `word--word`)
- No swearing
- No new files outside `d:/Ai_Sandbox/agentsHQ`
- Save point first, then code (per `feedback_savepoint_before_big_changes.md`)
- Branch first, then code (per `feedback_new_branch_per_feature.md`)
- Wire publisher methods as BaseTool entries in `tools.py` (per `feedback_always_wire_tools.md`)
- Verify Notion schema before writing payloads (per `feedback_inspect_notion_schema_first.md`)
- BLOTATO_API_KEY does not enter the repo or VPS .env until deploy day; lives in `d:/tmp/.env` until then
- Test before live (per `feedback_test_before_live.md`)
- Verification before completion (per superpowers verification skill)

---

## What gets shipped on M7b complete

- L3 Publish flips from 🟡 PARTIAL to ✅ LIVE
- Atlas Done Definition is 4-of-5 loops closed (L5 still trigger-gated on data)
- Studio M4 is unblocked (whichever path was chosen here, Studio M4 builds against the same Blotato contract)
- A real Boubacar LinkedIn or X post fires automatically from a Notion Scheduled Date without his hand on the keyboard

---

## Council session reference

Two Sankofa Council passes ran on M7-related decisions today:

- **Pass 1 (afternoon):** rejected "build M7 dormant" plan, forced the M7a/M7b split, made the Blotato signup a verified-against-real-API spike before any code
- **Pass 2 (evening, this spec):** stress-tested M7b proposed design, surfaced the duplicate-post idempotency bug, the state machine gap, and the new-module-vs-patch architectural disagreement

Pass 2 verdict: do not start coding tonight. Write this spec, sleep on the open decisions, build with discipline tomorrow at the earliest.

The Sankofa Council on the spec ITSELF (a third pass) is recommended at the top of the build session, focused on whichever path Boubacar picks. That third Council pass should be 5 minutes; this spec did the heavy lifting.
