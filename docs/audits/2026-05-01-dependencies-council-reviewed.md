# Dependencies, FINAL (3-pass review), 2026-05-01

Three-pass review on Boubacar's rule: A blocks B only if NO work on B can happen until A is Done.

- Round 1 (Haiku initial): 200 LLM calls, 128 candidates
- Round 2 (Sankofa Council 2-of-3 voices): 119 survivors
- Round 3 (Strict real-blocker test): 63 survivors
- Round 4 (Meta-work filter): 48 final

Construction analogy: foundation blocks roof. Foundation does NOT block rafter pre-staging.

## 48 real blockers (live in Notion)

### T-260059: Automate Notion Scheduled Date and Status update within 5 minutes of approval
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Reason: T-260059 must consume the notion_url output from T-260122 to update Notion records, making this a direct consumption dependency.

### T-260060: Integrate Blotato/OAuth for one-tap automated publishing
_Source: atlas.md_

**Blocked by T-260166: Define tick coordination contract with publish_brief.py**
Reason: B (OAuth integration for automated publishing) must consume the tick coordination contract that A defines: specifically the function signatures, timing guarantees, and state-machine rules that govern when publish_brief.py can be called; without A's contract, B cannot correctly implement the integration logic.

### T-260061: Automate Notion Status flip to Posted and outcome row creation after publish
_Source: atlas.md_

**Blocked by T-260163: Add granular Notion Status values (Publishing, PublishFailed)**
Reason: B consumes the new Notion Status values (Publishing, PublishFailed) that A produces; B cannot implement the status-flip logic without A's artifact being deployed.

### T-260081: Implement approval_queue + task_outcomes data aggregation
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Reason: B's data aggregation logic must consume the backend data path that A builds (Postgres/Notion/autonomy_state.json queries); without A's query functions and data schemas, B cannot implement aggregation against real data sources.

### T-260083: Test Chairman Crew with 14+ days of accumulated data
_Source: atlas.md_

**Blocked by T-260080: Design Chairman Crew weekly oversight logic**
Reason: B's tests require A's designed logic to exist as a testable artifact (the weekly oversight logic implementation/specification); you cannot meaningfully test accumulated data behavior against logic that hasn't been designed yet.

### T-260109: Add htmx polling refresh for each card at 30-second intervals
_Source: atlas.md_

**Blocked by T-260108: Implement visual shell with Catalyst Console design system**
Reason: B (htmx polling refresh) requires the visual shell and card components from A to exist and be rendered in the DOM before polling can target and refresh them.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260106: Create feat/atlas-m8-mission-control branch and savepoint**
Reason: B (merge to main) literally consumes the artifact A produces (the feat/atlas-m8-mission-control branch with savepoint), and no meaningful work on the merge itself can occur until that branch exists and is ready.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Reason: B (merge to main) cannot proceed without A's backend data path being complete and tested, as the merge would introduce untested/incomplete code; additionally, B consumes A's artifact (the working backend implementation).

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260108: Implement visual shell with Catalyst Console design system**
Reason: B (polish, test, and merge) cannot proceed meaningfully until A (visual shell implementation) is complete, as B must validate and integrate the actual implemented component that A produces.

### T-260123: Handle notion_url in get_queue() gracefully
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Reason: B consumes the notion_url artifact that A produces in _fetch_ideas() output; B cannot gracefully handle what doesn't yet exist in the function's return value.

### T-260123: Handle notion_url in get_queue() gracefully
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Reason: B must consume the notion_url artifact that A produces in _fetch_content_board()'s output signature; without A's actual output structure, B cannot implement graceful handling of a field that doesn't yet exist.

### T-260124: Update renderContent to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Reason: B (renderContent) must consume the notion_url artifact that A produces in _fetch_ideas() output to create the clickable links; without A's output structure, B cannot implement the feature.

### T-260124: Update renderContent to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Reason: B (renderContent) must consume the notion_url artifact that A produces in _fetch_content_board() output to create the clickable links; without A's output structure, B cannot implement the feature.

### T-260125: Update renderIdeas to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Reason: B (renderIdeas) must consume the notion_url artifact that A produces in _fetch_ideas() output; without A's actual signature and data structure, B cannot write the correct link-rendering logic.

### T-260125: Update renderIdeas to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Reason: B (renderIdeas) must consume the notion_url output from A (_fetch_content_board) to create the clickable links; the function signature and data structure from A are required before B's implementation can be completed and tested.

### T-260126: Update renderQueue to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Reason: B (renderQueue) must consume the notion_url artifact that A produces in _fetch_ideas() output to create the clickable links; without A's output structure, B cannot implement the feature.

### T-260126: Update renderQueue to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Reason: B (renderQueue clickable links) must consume the notion_url artifact that A produces in _fetch_content_board() output; without A's actual URL data structure, B cannot implement the link rendering logic correctly.

### T-260127: Add tests for notion_url presence in data fetchers
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Reason: B's tests must verify the exact `notion_url` field that A adds to the function output, so B cannot meaningfully progress until A's artifact (the modified function signature and output structure) exists.

### T-260127: Add tests for notion_url presence in data fetchers
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Reason: B's tests must verify the exact `notion_url` field that A adds to the function output, so B cannot meaningfully progress until A's artifact (the modified function signature and output structure) exists.

### T-260139: Build M1 three-button row implementation
_Source: atlas.md_

**Blocked by T-260108: Implement visual shell with Catalyst Console design system**
Reason: B (M1 three-button row) is a UI component that must consume the Catalyst Console design system tokens, patterns, and component library that A (visual shell) establishes; the button row cannot be meaningfully implemented without A's design system artifacts.

### T-260158: Implement backend data path for Atlas dashboard
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Reason: T-260158 (Atlas dashboard data path) must consume the querying functions/interfaces that T-260107 produces to connect to Postgres, Notion, and autonomy_state.json; without that artifact, the dashboard has no data source to implement against.

### T-260160: Add htmx 30-second polling per card
_Source: atlas.md_

**Blocked by T-260158: Implement backend data path for Atlas dashboard**
Reason: B's polling implementation must consume the backend data path API/endpoints that A produces; without A's deployed data contract, B cannot implement functional polling logic.

### T-260168: Update M2 backfill to skip PublishFailed records
_Source: atlas.md_

**Blocked by T-260163: Add granular Notion Status values (Publishing, PublishFailed)**
Reason: B consumes the artifact A produces (the PublishFailed status value must exist in Notion before M2 backfill can skip records with that status), and no meaningful work on B can proceed without A's output being deployed.

### T-260170: Lock 7 open decisions from spec at start of build session
_Source: atlas.md_

**Blocked by T-260164: Call Boubacar to decide M7b architecture (new module vs patch)**
Reason: B cannot lock decisions on M7b architecture until A produces the decision (new module vs patch), as the architectural choice directly determines which of the 7 open decisions can be resolved.

### T-260202: Integrate research_engine.py to add briefs to approved candidates (optional expa
_Source: atlas.md_

**Blocked by T-260166: Define tick coordination contract with publish_brief.py**
Reason: B must consume the tick coordination contract signature/interface defined in A to integrate research_engine.py with publish_brief.py; without A's contract, B's integration code cannot be written or tested against the actual API.

### T-260230: Implement GET /api/orc/atlas/job/{job_id} endpoint in app.py
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Reason: B's GET endpoint must consume the data-path functions/queries that A builds (Postgres/Notion/autonomy_state.json access layer); the endpoint cannot be meaningfully implemented or tested without A's actual query interface.

### T-260230: Implement GET /api/orc/atlas/job/{job_id} endpoint in app.py
_Source: atlas.md_

**Blocked by T-260158: Implement backend data path for Atlas dashboard**
Reason: B (GET endpoint) must consume the data path artifact that A produces (backend schema, database queries, data retrieval logic); the endpoint cannot be meaningfully implemented without knowing what data structure A will provide.

### T-260329: Implement asynchronous commit proposal system via slash command
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B (asynchronous commit proposal system) must consume the function signatures from A (propose, ack_proposal, reject_proposal) to implement the slash command handler that calls these functions; the exact signatures are required before B's implementation can be completed.

### T-260330: Build single-keystroke acknowledgment interface for commit proposals
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B's keystroke interface must consume the function signatures from A (propose, ack_proposal, reject_proposal) to map keystrokes to the correct function calls, making this a direct consumption dependency.

### T-260332: Unify proposal queue for commit, deploy, publish, and draft actions
_Source: echo.md_

**Blocked by T-260347: Implement queue generalization for selected proposal kind**
Reason: B (unify proposal queue) must consume the generalized queue abstraction that A (implement queue generalization) produces; without A's abstraction, B cannot unify disparate queue implementations into a single interface.

### T-260332: Unify proposal queue for commit, deploy, publish, and draft actions
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B (unify proposal queue) must consume the function signatures from A (propose, ack_proposal, reject_proposal) to integrate them into a unified queue abstraction; the queue cannot be meaningfully designed without knowing what proposal operations it must coordinate.

### T-260339: Generate commit message from diff via active model and enqueue proposal
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B must call the propose, ack_proposal, and reject_proposal functions from A to enqueue proposals, making it a direct consumption dependency.

### T-260340: Send Telegram notification for proposal with reply instructions
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B (Telegram notification) must consume the propose/ack_proposal/reject_proposal functions from A (proposal.py) to trigger notifications on proposal state changes, making A's function signatures a hard requirement for B's implementation.

### T-260341: Implement /ack <N> slash command to commit and mark proposal done
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B's slash command implementation must consume the `ack_proposal()` function signature and behavior that A produces; the command cannot be meaningfully implemented without A's function existing.

### T-260342: Implement /reject <N> slash command to mark proposal rejected
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B's /reject command implementation must consume the reject_proposal function signature and behavior from A's proposal.py module to function correctly.

### T-260345: Debrief M1 results if interruption-rate reduction is below 50%
_Source: echo.md_

**Blocked by T-260344: Measure M1 interruption-rate reduction after 7 days of real use**
Reason: B consumes the measurement result from A (interruption-rate reduction percentage); no meaningful work on the debrief can proceed without knowing whether the threshold was met.

### T-260347: Implement queue generalization for selected proposal kind
_Source: echo.md_

**Blocked by T-260346: Select highest ack-friction proposal kind from candidates**
Reason: B (queue generalization implementation) cannot proceed without A's output (the selected proposal kind), as the generalization must be built specifically for that chosen kind.

### T-260348: Create enqueue function for CrewAI to write tasks
_Source: echo.md_

**Blocked by T-260347: Implement queue generalization for selected proposal kind**
Reason: B (enqueue function for CrewAI) must consume the generalized queue interface/API that A produces; without A's queue abstraction, B cannot implement a correct enqueue function that works with the selected proposal kind.

### T-260350: Build unified ack UI for Telegram bot or web view
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: B (unified ack UI) must consume the function signatures from A (propose, ack_proposal, reject_proposal) to build UI controls that call these functions; the UI cannot be meaningfully integrated without knowing A's exact contract.

### T-260356: Execute end-to-end smoke test for Echo M1
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Reason: The smoke test (B) must consume the propose, ack_proposal, and reject_proposal functions from proposal.py (A) to execute end-to-end; no meaningful progress on the actual test execution can occur without these function signatures and implementations.

### T-260401: Document 8-step playbook in skills/signal-works-conversion/SKILL.md
_Source: harvest.md_

**Blocked by T-260402: Execute end-to-end playbook on Rod and capture conversion outcome**
Reason: T-260402 (execute playbook and capture outcome) produces the conversion data and results that T-260401 (document the 8-step playbook) must accurately reflect; documenting a playbook without its proven execution outcome would be documenting an untested procedure.

### T-260429: Create upsell email sequence for Signal Works prospects
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Reason: B (upsell email sequence) must consume the 4-touch cadence engine from A (email sequence engine) to function; the sequence cannot be created without the underlying engine infrastructure that A delivers.

### T-260434: Close $497 Signal Session sale
_Source: harvest.md_

**Blocked by T-260437: Build offer page on Signal Works or CW site**
Reason: B (closing the sale) requires consuming A's artifact (the built offer page URL/deployment) to present to the customer; no meaningful progress on the actual sale closure can occur without A's deliverable.

### T-260444: Compute reply rate lift and determine KEEP vs DELETE verdict
_Source: harvest.md_

**Blocked by T-260438: Conduct 100+ contact outreach across all sources**
Reason: B consumes the artifact A produces: reply data from the 100+ contact outreach is the essential input needed to compute reply rate lift and make the KEEP vs DELETE verdict.

### T-260462: Enable auto-send for CW and SW pipelines
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Reason: B (auto-send for SW pipeline) literally consumes the email sequence engine artifact that A produces; auto-send cannot function without the underlying sequence engine being built and deployed.

### T-260462: Enable auto-send for CW and SW pipelines
_Source: harvest.md_

**Blocked by T-260463: Wire Studio into email sequence runner**
Reason: B (auto-send for pipelines) must consume the wired Studio-to-email-sequence-runner integration that A produces; auto-send cannot function without the underlying connection A establishes.

### T-260463: Wire Studio into email sequence runner
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Reason: B (wiring Studio into email sequence runner) must consume the email sequence engine API/interface that A produces; without A's completed engine contract, B cannot meaningfully integrate Studio into it.

### T-260464: Confirm geolisted.co Hostinger connection
_Source: harvest.md_

**Blocked by T-260460: Launch Signal Works landing page at geolisted.co**
Reason: B (confirming Hostinger connection to geolisted.co) cannot proceed meaningfully until A (landing page launched at that domain) is complete, as the connection confirmation requires the deployed site to exist and be accessible.
