# Dependency suggestions, COUNCIL-REVIEWED, 2026-05-01

Sankofa Council voted on each suggested dependency.
Pass rule: at least 2 of 3 voices say 'true blocker'.

- Suggested by Haiku: 200
- Survivors (passed Council): 119
- Killed: 81

## Survivors (recommend writing to Notion)

### T-260059: Automate Notion Scheduled Date and Status update within 5 minutes of approval
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Council reason: B needs notion_url from A to update Notion records; parallel work impossible without A's output.

### T-260059: Automate Notion Scheduled Date and Status update within 5 minutes of approval
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Council reason: B needs notion_url from A's output to update Notion records automatically.

### T-260110: Implement action layer (toggle Griot, toggle dry-run, approve/reject queue, repl
_Source: atlas.md_

**Blocked by T-260158: Implement backend data path for Atlas dashboard**
Council reason: Action layer needs backend data path to function; they could parallelize but B consumes A's output.

### T-260158: Implement backend data path for Atlas dashboard
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: B consumes A's backend data path; Atlas dashboard needs querying infrastructure A builds.

### T-260158: Implement backend data path for Atlas dashboard
_Source: atlas.md_

**Blocked by T-260106: Create feat/atlas-m8-mission-control branch and savepoint**
Council reason: Backend data path requires the branch and savepoint created in A to exist first.

### T-260061: Automate Notion Status flip to Posted and outcome row creation after publish
_Source: atlas.md_

**Blocked by T-260163: Add granular Notion Status values (Publishing, PublishFailed)**
Council reason: B needs A's new Notion Status values (Publishing, PublishFailed) to implement the automation logic.

### T-260127: Add tests for notion_url presence in data fetchers
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Council reason: Tests for notion_url require the feature to exist; B consumes A's output directly.

### T-260127: Add tests for notion_url presence in data fetchers
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Council reason: Tests for notion_url require the feature to exist; B consumes A's output directly.

### T-260127: Add tests for notion_url presence in data fetchers
_Source: atlas.md_

**Blocked by T-260123: Handle notion_url in get_queue() gracefully**
Council reason: Tests for notion_url presence require the graceful handling code to exist and be testable.

### T-260171: Conduct third Council pass on chosen M7b architecture path
_Source: atlas.md_

**Blocked by T-260164: Call Boubacar to decide M7b architecture (new module vs patch)**
Council reason: Council decision (A's output) is required input for third pass review (B).

### T-260126: Update renderQueue to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Council reason: B needs notion_url from A's output to create clickable links.

### T-260126: Update renderQueue to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Council reason: B needs notion_url from A's output to create clickable links.

### T-260165: Implement kill switch auto_publisher.enabled in autonomy_state.json
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: B needs autonomy_state.json structure from A; parallel work requires A's schema first.

### T-260165: Implement kill switch auto_publisher.enabled in autonomy_state.json
_Source: atlas.md_

**Blocked by T-260106: Create feat/atlas-m8-mission-control branch and savepoint**
Council reason: B needs the feat branch created by A to implement the kill switch feature.

### T-260168: Update M2 backfill to skip PublishFailed records
_Source: atlas.md_

**Blocked by T-260163: Add granular Notion Status values (Publishing, PublishFailed)**
Council reason: B consumes the PublishFailed status value that A creates in Notion.

### T-260139: Build M1 three-button row implementation
_Source: atlas.md_

**Blocked by T-260110: Implement action layer (toggle Griot, toggle dry-run, approve/reject queue, repl**
Council reason: M1 three-button row needs action layer toggles/callbacks from T-260110 to function.

### T-260139: Build M1 three-button row implementation
_Source: atlas.md_

**Blocked by T-260108: Implement visual shell with Catalyst Console design system**
Council reason: M1 three-button row is a UI component requiring the design system foundation from Catalyst Console.

### T-260083: Test Chairman Crew with 14+ days of accumulated data
_Source: atlas.md_

**Blocked by T-260080: Design Chairman Crew weekly oversight logic**
Council reason: Testing requires the design logic to exist; design is a concrete input to testing.

### T-260125: Update renderIdeas to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Council reason: B consumes notion_url output from A; renderIdeas needs the data A produces.

### T-260125: Update renderIdeas to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Council reason: B needs notion_url from A's output to create clickable links.

### T-260123: Handle notion_url in get_queue() gracefully
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Council reason: B consumes notion_url output from A; parallel work requires A's output first.

### T-260123: Handle notion_url in get_queue() gracefully
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Council reason: B consumes notion_url output from A; parallel work requires A's output first.

### T-260086: Implement Hunter.io and LinkedIn outreach automation
_Source: atlas.md_

**Blocked by T-260085: Design autonomous lead-finding crew using Hunter.io and LinkedIn APIs**
Council reason: B needs A's design (API integration architecture, crew structure) as input to implement outreach automation.

### T-260160: Add htmx 30-second polling per card
_Source: atlas.md_

**Blocked by T-260158: Implement backend data path for Atlas dashboard**
Council reason: Backend data path is consumed by polling; htmx needs API endpoints to query.

### T-260108: Implement visual shell with Catalyst Console design system
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: Visual shell needs backend data path to query and display; backend is consumed output.

### T-260108: Implement visual shell with Catalyst Console design system
_Source: atlas.md_

**Blocked by T-260159: Build visual shell with Catalyst Console palette and typography**
Council reason: B consumes A's palette and typography outputs; implementation requires design system artifacts.

### T-260124: Update renderContent to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260122: Add notion_url to _fetch_ideas() output**
Council reason: B needs notion_url from A's output to create clickable links; hard dependency.

### T-260124: Update renderContent to create clickable links with external glyph
_Source: atlas.md_

**Blocked by T-260121: Add notion_url to _fetch_content_board() output**
Council reason: B needs notion_url from A's output to render clickable links properly.

### T-260200: Integrate YouTube channel RSS source tracking for African storytelling niche
_Source: atlas.md_

**Blocked by T-260198: Answer design question: define African storytelling YouTube channel source list **
Council reason: B needs A's output: the defined source list is a direct input to RSS integration.

### T-260170: Lock 7 open decisions from spec at start of build session
_Source: atlas.md_

**Blocked by T-260164: Call Boubacar to decide M7b architecture (new module vs patch)**
Council reason: B needs A's decision (M7b architecture choice) to lock the 7 open spec decisions.

### T-260170: Lock 7 open decisions from spec at start of build session
_Source: atlas.md_

**Blocked by T-260171: Conduct third Council pass on chosen M7b architecture path**
Council reason: B consumes A's output: the chosen M7b architecture path needed to lock decisions.

### T-260060: Integrate Blotato/OAuth for one-tap automated publishing
_Source: atlas.md_

**Blocked by T-260061: Automate Notion Status flip to Posted and outcome row creation after publish**
Council reason: B needs A's Notion automation output (Posted status, outcome row) to publish reliably.

### T-260060: Integrate Blotato/OAuth for one-tap automated publishing
_Source: atlas.md_

**Blocked by T-260163: Add granular Notion Status values (Publishing, PublishFailed)**
Council reason: B needs A's Notion status values to properly track publishing outcomes.

### T-260060: Integrate Blotato/OAuth for one-tap automated publishing
_Source: atlas.md_

**Blocked by T-260165: Implement kill switch auto_publisher.enabled in autonomy_state.json**
Council reason: B needs the kill switch config from A to safely enable automated publishing.

### T-260060: Integrate Blotato/OAuth for one-tap automated publishing
_Source: atlas.md_

**Blocked by T-260166: Define tick coordination contract with publish_brief.py**
Council reason: B needs the tick coordination contract defined in A to implement automated publishing correctly.

### T-260062: Build outcome data capture and weekly learning feedback loop
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: B needs A's backend data path to capture and process outcome feedback.

### T-260062: Build outcome data capture and weekly learning feedback loop
_Source: atlas.md_

**Blocked by T-260158: Implement backend data path for Atlas dashboard**
Council reason: B needs A's backend data path to capture and process outcome data; parallel work requires architectural coordination.

### T-260081: Implement approval_queue + task_outcomes data aggregation
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: B aggregates data from sources A builds; A's output directly enables B's input.

### T-260058: Implement daily candidate selection in Griot without manual triggers
_Source: atlas.md_

**Blocked by T-260110: Implement action layer (toggle Griot, toggle dry-run, approve/reject queue, repl**
Council reason: Daily selection needs action layer's approve/reject queue to function; they could parallelize but B consumes A's outputs.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260106: Create feat/atlas-m8-mission-control branch and savepoint**
Council reason: B requires the feat/atlas-m8-mission-control branch created in A to merge to main.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: B tests backend data path built in A; cannot test what doesn't exist yet.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260108: Implement visual shell with Catalyst Console design system**
Council reason: Polish/test/merge requires the visual shell implementation to exist as consumable output.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260110: Implement action layer (toggle Griot, toggle dry-run, approve/reject queue, repl**
Council reason: B (merge) requires A's action layer implementation as a functional dependency before testing.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260126: Update renderQueue to create clickable links with external glyph**
Council reason: B (polish/merge) requires A's clickable links feature to be complete first.

### T-260112: Polish, test, and merge to main
_Source: atlas.md_

**Blocked by T-260125: Update renderIdeas to create clickable links with external glyph**
Council reason: B tests/merges A's renderIdeas changes; A's output is B's input.

### T-260109: Add htmx polling refresh for each card at 30-second intervals
_Source: atlas.md_

**Blocked by T-260108: Implement visual shell with Catalyst Console design system**
Council reason: B needs A's visual shell UI components to implement htmx polling on rendered cards.

### T-260111: Apply JWT-PIN gating and embed /chat as seventh card
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: B needs A's backend data path to query state; JWT gating requires autonomy_state.json access.

### T-260111: Apply JWT-PIN gating and embed /chat as seventh card
_Source: atlas.md_

**Blocked by T-260108: Implement visual shell with Catalyst Console design system**
Council reason: B embeds chat into the visual shell A creates; A's design system output is B's prerequisite.

### T-260230: Implement GET /api/orc/atlas/job/{job_id} endpoint in app.py
_Source: atlas.md_

**Blocked by T-260107: Build backend data path querying Postgres, Notion, and autonomy_state.json**
Council reason: GET endpoint needs backend data path to query; cannot return data without it.

### T-260230: Implement GET /api/orc/atlas/job/{job_id} endpoint in app.py
_Source: atlas.md_

**Blocked by T-260158: Implement backend data path for Atlas dashboard**
Council reason: GET endpoint (B) requires backend data path (A) to exist and function properly.

### T-260202: Integrate research_engine.py to add briefs to approved candidates (optional expa
_Source: atlas.md_

**Blocked by T-260166: Define tick coordination contract with publish_brief.py**
Council reason: B consumes the tick coordination contract defined in A; parallel work impossible without it.

### T-260201: Route approved candidates to existing Atlas Content Board via handlers_approvals
_Source: atlas.md_

**Blocked by T-260110: Implement action layer (toggle Griot, toggle dry-run, approve/reject queue, repl**
Council reason: B routes approved candidates; A implements approval mechanism. B needs A's approve/reject output.

### T-260201: Route approved candidates to existing Atlas Content Board via handlers_approvals
_Source: atlas.md_

**Blocked by T-260161: Implement action layer (toggle Griot, dry-run, approve/reject, publish controls)**
Council reason: B routes approved candidates; A implements approve/reject controls that B depends on.

### T-260234: Implement atlasChat module in atlas.js with core functions
_Source: atlas.md_

**Blocked by T-260106: Create feat/atlas-m8-mission-control branch and savepoint**
Council reason: B needs the branch and savepoint created by A to have a workspace for implementation.

### T-260206: Verify auto-publish fires on schedule
_Source: atlas.md_

**Blocked by T-260165: Implement kill switch auto_publisher.enabled in autonomy_state.json**
Council reason: B verifies auto-publish behavior; A implements the kill switch B must test.

### T-260206: Verify auto-publish fires on schedule
_Source: atlas.md_

**Blocked by T-260166: Define tick coordination contract with publish_brief.py**
Council reason: B verifies auto-publish behavior defined by A's contract; B consumes A's output.

### T-260206: Verify auto-publish fires on schedule
_Source: atlas.md_

**Blocked by T-260161: Implement action layer (toggle Griot, dry-run, approve/reject, publish controls)**
Council reason: B tests auto-publish feature that A implements; A's controls are literal prerequisite for B's verification.

### T-260306: Create savepoint tag before archive cleanup
_Source: atlas.md_

**Blocked by T-260106: Create feat/atlas-m8-mission-control branch and savepoint**
Council reason: B needs the feat/atlas-m8-mission-control branch created by A to create its savepoint tag.

### T-260410: Execute workflow for third prospect (audit → screenshots → render → deploy)
_Source: harvest.md_

**Blocked by T-260404: Build build_hook.py renderer (~140 lines, dependency-free)**
Council reason: B's render step consumes build_hook.py output; A must complete first.

### T-260461: Review first batch of email drafts
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Council reason: Email drafts require the engine built first; reviewers need the system to exist before evaluating output.

### T-260431: Launch SaaS audit upsell to Signal Works prospect list
_Source: harvest.md_

**Blocked by T-260430: Set up $500 SaaS audit offer in sales system**
Council reason: B needs the $500 offer configured in sales system (A's output) to launch the upsell campaign.

### T-260431: Launch SaaS audit upsell to Signal Works prospect list
_Source: harvest.md_

**Blocked by T-260428: Design one-page SaaS audit PDF template**
Council reason: Upsell launch requires the PDF template as a deliverable to prospects.

### T-260457: Build SW email sequence engine with 4-touch cadence
_Source: harvest.md_

**Blocked by T-260462: Enable auto-send for CW and SW pipelines**
Council reason: SW email sequence engine needs auto-send capability that A provides as foundational infrastructure.

### T-260462: Enable auto-send for CW and SW pipelines
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Council reason: Auto-send feature requires the email sequence engine to exist and function properly.

### T-260462: Enable auto-send for CW and SW pipelines
_Source: harvest.md_

**Blocked by T-260463: Wire Studio into email sequence runner**
Council reason: Auto-send requires the email sequence runner wired in; B consumes A's output directly.

### T-260463: Wire Studio into email sequence runner
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Council reason: Studio wiring consumes the email sequence engine as a direct dependency.

### T-260440: Calculate cost-per-conversation by lead source
_Source: harvest.md_

**Blocked by T-260438: Conduct 100+ contact outreach across all sources**
Council reason: Cost-per-conversation requires completed outreach data; cannot calculate without contact results.

### T-260465: Test subject line variants for YC RFS outreach
_Source: harvest.md_

**Blocked by T-260461: Review first batch of email drafts**
Council reason: Email drafts reviewed in A are the direct input for testing subject lines in B.

### T-260412: Execute workflow for fifth prospect (audit → screenshots → render → deploy)
_Source: harvest.md_

**Blocked by T-260404: Build build_hook.py renderer (~140 lines, dependency-free)**
Council reason: Task B's render step explicitly requires build_hook.py output from Task A.

### T-260402: Execute end-to-end playbook on Rod and capture conversion outcome
_Source: harvest.md_

**Blocked by T-260399: Draft 3-variant cover note for Rod (email, SMS, DM)**
Council reason: B executes playbook using cover note from A; cannot test without messaging variant.

### T-260402: Execute end-to-end playbook on Rod and capture conversion outcome
_Source: harvest.md_

**Blocked by T-260400: Add competitor scoring column to Rod report scorecard**
Council reason: B needs the competitor scoring column A adds to execute the playbook and capture outcomes.

### T-260402: Execute end-to-end playbook on Rod and capture conversion outcome
_Source: harvest.md_

**Blocked by T-260397: Add third-party validator screenshots to Rod report scorecard**
Council reason: B needs A's screenshots in the scorecard to execute and validate the playbook outcome.

### T-260430: Set up $500 SaaS audit offer in sales system
_Source: harvest.md_

**Blocked by T-260428: Design one-page SaaS audit PDF template**
Council reason: Sales system needs PDF template design as input before configuring the offer.

### T-260466: Create SaaS audit one-pager
_Source: harvest.md_

**Blocked by T-260428: Design one-page SaaS audit PDF template**
Council reason: B needs A's PDF template as direct input; cannot create one-pager without template design.

### T-260423: Link homepage to governance.html and ai-data-audit.html
_Source: harvest.md_

**Blocked by T-260425: Add meta description, canonical, JSON-LD to ai-data-audit.html and scrub em-dash**
Council reason: B needs ai-data-audit.html file created and cleaned by A before linking to it.

### T-260409: Execute workflow for second prospect (audit → screenshots → render → deploy)
_Source: harvest.md_

**Blocked by T-260404: Build build_hook.py renderer (~140 lines, dependency-free)**
Council reason: B's render step explicitly needs A's build_hook.py renderer output to execute.

### T-260458: Wire SaaS audit PDF into CW T2 email
_Source: harvest.md_

**Blocked by T-260428: Design one-page SaaS audit PDF template**
Council reason: B wires the PDF template (A's output) into email; cannot wire what doesn't exist.

### T-260458: Wire SaaS audit PDF into CW T2 email
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Council reason: B needs the email sequence engine (A's output) to wire the PDF into the email workflow.

### T-260464: Confirm geolisted.co Hostinger connection
_Source: harvest.md_

**Blocked by T-260460: Launch Signal Works landing page at geolisted.co**
Council reason: Landing page launch (A) must complete before confirming hosting connection (B) can be verified.

### T-260456: Build full CW email sequence engine with 5-touch cadence
_Source: harvest.md_

**Blocked by T-260461: Review first batch of email drafts**
Council reason: Email drafts (A) are direct input for building the sequence engine (B).

### T-260413: Review conversion data across 5 prospects and lock highest-converting hook as de
_Source: harvest.md_

**Blocked by T-260404: Build build_hook.py renderer (~140 lines, dependency-free)**
Council reason: B needs build_hook.py output to test conversion data; A produces the renderer B consumes.

### T-260413: Review conversion data across 5 prospects and lock highest-converting hook as de
_Source: harvest.md_

**Blocked by T-260412: Execute workflow for fifth prospect (audit → screenshots → render → deploy)**
Council reason: B needs A's fifth prospect screenshots/render output to review conversion data across all five prospects.

### T-260444: Compute reply rate lift and determine KEEP vs DELETE verdict
_Source: harvest.md_

**Blocked by T-260438: Conduct 100+ contact outreach across all sources**
Council reason: Reply rate lift computation requires contact outreach data; cannot analyze responses without contacts made.

### T-260429: Create upsell email sequence for Signal Works prospects
_Source: harvest.md_

**Blocked by T-260457: Build SW email sequence engine with 4-touch cadence**
Council reason: B needs A's email engine framework to build sequences; parallel work unlikely without duplicating effort.

### T-260411: Execute workflow for fourth prospect (audit → screenshots → render → deploy)
_Source: harvest.md_

**Blocked by T-260404: Build build_hook.py renderer (~140 lines, dependency-free)**
Council reason: Task B's render step explicitly requires build_hook.py renderer output from Task A.

### T-260434: Close $497 Signal Session sale
_Source: harvest.md_

**Blocked by T-260437: Build offer page on Signal Works or CW site**
Council reason: Offer page must exist before closing sale; sales page is literal prerequisite artifact.

### T-260434: Close $497 Signal Session sale
_Source: harvest.md_

**Blocked by T-260430: Set up $500 SaaS audit offer in sales system**
Council reason: Sales system setup (A) must precede recording the sale (B) in that system.

### T-260401: Document 8-step playbook in skills/signal-works-conversion/SKILL.md
_Source: harvest.md_

**Blocked by T-260402: Execute end-to-end playbook on Rod and capture conversion outcome**
Council reason: B documents playbook outcomes from A's execution; A's results are direct input to B.

### T-260439: Log reply and close rates for each lead source
_Source: harvest.md_

**Blocked by T-260438: Conduct 100+ contact outreach across all sources**
Council reason: B requires contact data from A to log reply and close rates per source.

### T-260349: Configure n8n HTTP node to write tasks to Postgres
_Source: echo.md_

**Blocked by T-260348: Create enqueue function for CrewAI to write tasks**
Council reason: B consumes the enqueue function created by A; parallel work requires A's output first.

### T-260349: Configure n8n HTTP node to write tasks to Postgres
_Source: echo.md_

**Blocked by T-260351: Verify schema consistency across all ingestion sources**
Council reason: Schema consistency verification is a prerequisite input for configuring correct Postgres writes.

### T-260339: Generate commit message from diff via active model and enqueue proposal
_Source: echo.md_

**Blocked by T-260338: Implement /propose slash command with git status and test execution**
Council reason: B needs A's /propose command output to generate commit messages from diffs.

### T-260339: Generate commit message from diff via active model and enqueue proposal
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B needs proposal.py functions from A to generate and enqueue proposals.

### T-260339: Generate commit message from diff via active model and enqueue proposal
_Source: echo.md_

**Blocked by T-260332: Unify proposal queue for commit, deploy, publish, and draft actions**
Council reason: B needs A's unified queue infrastructure to enqueue proposals; they cannot be parallelized.

### T-260340: Send Telegram notification for proposal with reply instructions
_Source: echo.md_

**Blocked by T-260339: Generate commit message from diff via active model and enqueue proposal**
Council reason: B needs A's proposal output to send notification with reply instructions.

### T-260340: Send Telegram notification for proposal with reply instructions
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B needs proposal.py functions to send notifications; A creates the required module.

### T-260341: Implement /ack <N> slash command to commit and mark proposal done
_Source: echo.md_

**Blocked by T-260339: Generate commit message from diff via active model and enqueue proposal**
Council reason: Task B's /ack command commits proposals generated by Task A's system.

### T-260341: Implement /ack <N> slash command to commit and mark proposal done
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: Task B's slash command must call proposal functions created in Task A.

### T-260331: Enable agent to continue work without blocking on acknowledgments
_Source: echo.md_

**Blocked by T-260329: Implement asynchronous commit proposal system via slash command**
Council reason: B requires A's asynchronous commit system to avoid blocking on acknowledgments.

### T-260331: Enable agent to continue work without blocking on acknowledgments
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: Task B needs proposal.py functions from Task A to implement non-blocking acknowledgment handling.

### T-260342: Implement /reject <N> slash command to mark proposal rejected
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B needs reject_proposal function from A to implement the slash command.

### T-260342: Implement /reject <N> slash command to mark proposal rejected
_Source: echo.md_

**Blocked by T-260349: Configure n8n HTTP node to write tasks to Postgres**
Council reason: Reject command needs Postgres task storage configured to persist rejection state.

### T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions
_Source: echo.md_

**Blocked by T-260332: Unify proposal queue for commit, deploy, publish, and draft actions**
Council reason: B needs unified queue infrastructure from A to implement proposal functions correctly.

### T-260350: Build unified ack UI for Telegram bot or web view
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B's unified ack UI must call A's ack_proposal function; hard dependency on proposal.py.

### T-260332: Unify proposal queue for commit, deploy, publish, and draft actions
_Source: echo.md_

**Blocked by T-260347: Implement queue generalization for selected proposal kind**
Council reason: B unifies queues built on A's generalized queue abstraction; direct technical dependency.

### T-260332: Unify proposal queue for commit, deploy, publish, and draft actions
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B consumes proposal.py functions from A; parallel work possible but requires coordination.

### T-260347: Implement queue generalization for selected proposal kind
_Source: echo.md_

**Blocked by T-260346: Select highest ack-friction proposal kind from candidates**
Council reason: B needs A's selection output to know which proposal kind to implement for.

### T-260347: Implement queue generalization for selected proposal kind
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B needs proposal.py functions from A to implement queue generalization for proposals.

### T-260347: Implement queue generalization for selected proposal kind
_Source: echo.md_

**Blocked by T-260332: Unify proposal queue for commit, deploy, publish, and draft actions**
Council reason: B implements generalization of A's unified queue; requires A's output as foundation.

### T-260329: Implement asynchronous commit proposal system via slash command
_Source: echo.md_

**Blocked by T-260338: Implement /propose slash command with git status and test execution**
Council reason: B needs A's /propose command implementation to build asynchronous commit proposals upon.

### T-260329: Implement asynchronous commit proposal system via slash command
_Source: echo.md_

**Blocked by T-260339: Generate commit message from diff via active model and enqueue proposal**
Council reason: B needs A's commit message generation output to propose changes via slash command.

### T-260329: Implement asynchronous commit proposal system via slash command
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B needs proposal.py functions from A to implement the slash command system.

### T-260345: Debrief M1 results if interruption-rate reduction is below 50%
_Source: echo.md_

**Blocked by T-260344: Measure M1 interruption-rate reduction after 7 days of real use**
Council reason: B consumes A's measurement results; debrief requires completed data to evaluate.

### T-260348: Create enqueue function for CrewAI to write tasks
_Source: echo.md_

**Blocked by T-260347: Implement queue generalization for selected proposal kind**
Council reason: B needs A's queue generalization output to implement the enqueue function.

### T-260348: Create enqueue function for CrewAI to write tasks
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: Task B (enqueue function) likely imports and uses proposal functions from Task A's proposal.py module.

### T-260330: Build single-keystroke acknowledgment interface for commit proposals
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: B's keystroke interface must consume A's proposal functions to acknowledge proposals.

### T-260330: Build single-keystroke acknowledgment interface for commit proposals
_Source: echo.md_

**Blocked by T-260341: Implement /ack <N> slash command to commit and mark proposal done**
Council reason: B needs the /ack slash command that A implements to build the UI around it.

### T-260356: Execute end-to-end smoke test for Echo M1
_Source: echo.md_

**Blocked by T-260352: Create proposal.py with propose, ack_proposal, reject_proposal functions**
Council reason: Smoke test requires proposal.py functions to exist and work correctly.

### T-260357: Commit Echo M1 to feature branch
_Source: echo.md_

**Blocked by T-260356: Execute end-to-end smoke test for Echo M1**
Council reason: Smoke test must pass before committing; test results are consumed by commit decision.
