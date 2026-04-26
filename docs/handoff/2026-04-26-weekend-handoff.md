# Weekend Handoff: 2026-04-26 (Sunday) onward

**Written:** 2026-04-25 night, end of a 13-hour build day.
**Author:** Claude Code (Atlas instance), Opus 4.7 (1M context).
**Three-way nsync at:** `2c2845c` (local + origin + VPS).
**Tests:** 261/261 passing.

## TL;DR for the next agent

Two big systems shipped today: Atlas auto-publish and Studio engine. Both are live on VPS. Nothing breaks if you do nothing this weekend. Three things would extract more value if you have time.

## What is running RIGHT NOW (no further action required)

| System | State | First fire |
|---|---|---|
| Atlas auto-publisher | LIVE, kill switch ON | Mon 2026-04-27 07:00 MT, X "One constraint nobody has named yet" |
| Studio trend scout | LIVE, kill switch OFF (no YouTube API key) | Won't fire usefully until key + flip |
| Atlas M8 Mission Control dashboard | DEPLOYED at agentshq.boubacarbarry.com/atlas | available now (not verified) |
| Atlas L1 propose / L2 schedule / L4 reconcile | LIVE since earlier today | continuous |
| Two remote routines | armed | Monday 09:00 MT verify, May 14 Firecrawl check |

## Three weekend priorities (in order)

### 1. Monday 2026-04-27 ~07:30 MT: verify the first live auto-publish (~10 min)

Mandatory check. The Atlas M7b auto-publisher fires its first real publish at 07:00 MT Monday. If it works, you do nothing. If it fails, it failed silently or broke something downstream and you need to look.

Quick verification:

```bash
ssh root@72.60.209.109 "docker logs orc-crewai --since 1h | grep -E 'auto_publisher|BLOTATO'"
```

Expected output: a `tick done posted=1` line plus a `BLOTATO: published twitter` line plus a `BLOTATO poll: ... published in 5-9s` line. Should also see a Telegram message in your chat that says `Posted (auto): X / One constraint nobody has named yet / [URL]`.

If you see `failed=1` or `errorMessage` in the logs:
- Open the Notion record (Status will be `PublishFailed`)
- Read the Source Note field for the error
- Decide: fix and flip back to Queued, or leave PublishFailed (slot stays blocked, audit trail preserved)
- Most likely failure mode: Blotato 422 quota or a transient HTTP issue; just retry by flipping Status back to Queued

If everything green: M7b is operationally validated. Continue normal life.

### 2. Provision YouTube API key + flip studio.enabled=True (~10 min)

Studio trend scout currently runs daily at 06:00 MT but writes zero candidates because no `YOUTUBE_API_KEY` is set. Without this, the engine is technically alive but producing nothing useful.

Steps:

1. Go to https://console.cloud.google.com/apis/credentials
2. Create or reuse a Google Cloud project
3. Enable "YouTube Data API v3" for that project
4. Create an API key (no restrictions needed for v0)
5. SSH and add the key:

```bash
ssh root@72.60.209.109 "echo 'YOUTUBE_API_KEY=YOUR_KEY_HERE' >> /root/agentsHQ/.env"
```

6. Flip the studio kill switch:

```bash
ssh root@72.60.209.109 'python3 -c "
import json, pathlib
p = pathlib.Path(\"/root/agentsHQ/data/autonomy_state.json\")
state = json.loads(p.read_text())
state[\"crews\"][\"studio\"] = {\"enabled\": True, \"dry_run\": False}
p.write_text(json.dumps(state, indent=2))
print(\"Studio enabled\")
'"
```

7. Restart container so the AutonomyGuard re-reads state and the env vars are fresh:

```bash
ssh root@72.60.209.109 "docker restart orc-crewai"
```

8. Trigger a manual tick to verify (don't wait for 06:00 MT):

```bash
ssh root@72.60.209.109 "docker exec orc-crewai sh -c 'cd /app && python -c \"from studio_trend_scout import studio_trend_scout_tick; studio_trend_scout_tick()\"'"
```

You should see candidates land in the Studio Pipeline Notion DB (`34ebcf1a-3029-8140-a565-f7c26fe9de86`) and a Telegram brief.

YouTube Data API v3 free quota: 10,000 units/day. Each search costs 100 units, each video stats fetch costs ~3 units per video. The scout uses ~1500-2000 units per niche per run. With 3 niches, daily run uses ~5000-6000 units. Comfortably within quota.

### 3. Verify Atlas M8 Mission Control dashboard (~15 min)

The studio session shipped this in commit `7f3667b` (`feat(atlas-m8): Mission Control dashboard at /atlas (#21)`). I have not verified it works end-to-end. Two checks:

Browser test:

1. Go to `https://agentshq.boubacarbarry.com/atlas`
2. Enter your PIN (same as `/chat`)
3. Verify the 6 cards (Atlas State, Approval Queue, Content Board, Spend 7d, Heartbeats, Errors) all populate with live data
4. Verify the htmx 30s polling refreshes each card

Action layer test (the spec said the action layer fits in 75 min inside M8 itself):

1. Try toggling Griot off, watch the State card update within 30s
2. Toggle Griot back on
3. Verify the autonomy_state.json change persisted via `ssh root@72.60.209.109 "cat /root/agentsHQ/data/autonomy_state.json"`

If anything doesn't work, the studio session has a memory entry on M8 + the spec at `docs/superpowers/specs/2026-04-25-atlas-m8-mission-control-design.md`.

## What you do NOT need to do this weekend

- M2 brand identity for the 3 Studio channels (Sunday session at earliest; can defer to weekday)
- Create First Generation Money YouTube channel
- Register X handles for the 3 channels
- Wire monetization (M6, gated on subscriber thresholds)
- Studio production pipeline M3 (gated on M2)
- Any new milestone work; today already shipped 5 Atlas + 1 Studio milestones

## Where everything lives

### Roadmaps (read first)

- `docs/roadmap/atlas.md` (M7b SHIPPED, full session log at the bottom)
- `docs/roadmap/studio.md` (M1 SHIPPED, full session log at the bottom)
- `docs/roadmap/atlas/m7a-decision-spike.md` (historical, M7a closed)

### Specs

- `docs/superpowers/specs/2026-04-26-atlas-m7b-publisher-design.md` (M7b design doc; built against this)
- `docs/superpowers/specs/2026-04-25-atlas-m8-mission-control-design.md` (M8 design)

### M7b artifacts (Atlas auto-publish)

- `orchestrator/blotato_publisher.py` (BlotatoPublisher class, httpx, M7a-verified API)
- `orchestrator/auto_publisher.py` (heartbeat tick, time-of-day, weekday policy, past-due stagger)
- `orchestrator/auto_publisher_schedule.default.json` (committed default schedule)
- `orchestrator/tests/test_blotato_publisher.py` + `test_auto_publisher.py` (52 tests)
- VPS .env: `BLOTATO_API_KEY`, `BLOTATO_LINKEDIN_ACCOUNT_ID=19365`, `BLOTATO_X_ACCOUNT_ID=17065`
- Blotato API key local-only at `d:/tmp/.env` AND in VPS .env (deploy day was today)
- Notepad at `d:/tmp/m7a-blotato-spike-notes.md` (M7a smoke test artifacts)

### Studio M1 artifacts (engine)

- `orchestrator/studio_trend_scout.py` (heartbeat tick, YouTube Data API)
- `orchestrator/studio_qa_crew.py` (8-check QA crew)
- `orchestrator/tests/test_studio_trend_scout.py` + `test_studio_qa_crew.py` (51 tests)
- Notion Studio Pipeline DB: `34ebcf1a-3029-8140-a565-f7c26fe9de86` (`NOTION_STUDIO_PIPELINE_DB_ID` in VPS .env)
- 3 channel briefs at `docs/roadmap/studio/channels/`:
  - `under-the-baobab.md` (faceless African folktales; channel exists)
  - `ai-catalyst.md` (AI displacement, openly Boubacar Path A; channel exists virgin)
  - `first-generation-money.md` (faceless first-gen finance; channel needs M2 creation)
- `docs/roadmap/studio/operating-snapshot.md` (locked: 3-channel portfolio, Mon-Sat publish, no LinkedIn)

### Skills layer (studio session shipped today)

- `skills/skool-harvester/SKILL.md` (Playwright harvester for Skool community lessons)
- `skills/client-intake/SKILL.md` (Steven Bartlett style brand-discovery interview)
- `scripts/skool-harvester/` (companion scripts)
- `orchestrator/harvest_reviewer.py`, `harvest_triage.py`, `niche_research.py`, `video_analyze.py`

### Critical hard rules in force

- `orchestrator.py` does NOT exist. Sunset 2026-04-25 commit `4d1aeb3`. Never recreate it. App.py is the canonical entrypoint. See `docs/AGENT_SOP.md` for the import map.
- No em dashes anywhere (pre-commit hook enforces). No double-hyphens in prose.
- BLOTATO_API_KEY only flows from `d:/tmp/.env` to VPS .env on deploy day. M7b deploy day was today.
- Studio kill switch (`studio.enabled`) defaults False. Atlas auto_publisher kill switch (`auto_publisher.enabled`) currently True (flipped 18:55 MT).

## Kill switches (use these to pause anything)

```bash
# Pause Atlas auto-publish only
ssh root@72.60.209.109 'python3 -c "
import json, pathlib
p = pathlib.Path(\"/root/agentsHQ/data/autonomy_state.json\")
state = json.loads(p.read_text())
state[\"crews\"][\"auto_publisher\"][\"enabled\"] = False
p.write_text(json.dumps(state, indent=2))
print(\"PAUSED auto_publisher\")
"' && ssh root@72.60.209.109 "docker restart orc-crewai"
```

```bash
# Pause Studio trend scout
ssh root@72.60.209.109 'python3 -c "
import json, pathlib
p = pathlib.Path(\"/root/agentsHQ/data/autonomy_state.json\")
state = json.loads(p.read_text())
state[\"crews\"][\"studio\"][\"enabled\"] = False
p.write_text(json.dumps(state, indent=2))
print(\"PAUSED studio\")
"' && ssh root@72.60.209.109 "docker restart orc-crewai"
```

```bash
# Pause everything (global kill)
ssh root@72.60.209.109 'python3 -c "
import json, pathlib
p = pathlib.Path(\"/root/agentsHQ/data/autonomy_state.json\")
state = json.loads(p.read_text())
state[\"killed\"] = True
state[\"killed_reason\"] = \"manual pause\"
p.write_text(json.dumps(state, indent=2))
print(\"GLOBAL KILL ON\")
"' && ssh root@72.60.209.109 "docker restart orc-crewai"
```

## What I would NOT recommend doing this weekend

- Fresh feature work on a tired Sunday brain after a 13-hour Saturday
- M2 channel branding before sleeping on the M1 engine outputs
- Anything that requires brand-new design judgement (those decisions go better Monday-Wednesday)
- Touching the Atlas heartbeat or autonomy_guard code
- Running pip install or container rebuilds (no reason to)

## If something goes wrong (escalation order)

1. Telegram alert lands → open the Notion record, read the Source Note field
2. Atlas Concierge crew (M4) is NOT shipped yet, so failures route to your Telegram for human action
3. If a publish duplicates: M7b's idempotency safeguard (Status=Publishing flip BEFORE POST) should prevent it; if it happens anyway, that's a bug worth Sankofa Council
4. If everything is on fire: flip the global kill switch above and SSH in to investigate

## Memory entries created today (read these to understand context)

- `reference_blotato_pricing_2026.md` (Starter $20.30, Creator $67.90, Agency $349.30 effective with Skool 30% lifetime discount)
- `project_orchestrator_sunset.md` (the monolith deletion)
- Plus the studio session created several harvest-related entries

---

# COPY-PASTE PROMPT FOR THE NEXT AGENT

The block below is what you paste into the next Claude Code session. It's self-contained and assumes the agent knows nothing.

---

```
You're picking up agentsHQ on Sunday 2026-04-26 (or later).

CURRENT STATE:
- Three-way nsync at commit 2c2845c (or later if other agents committed)
- 261/261 orchestrator tests passing
- Atlas auto-publisher LIVE on VPS, kill switch ON, fires every 5 min
- Studio M1 engine LIVE on VPS, kill switch OFF (waiting for YouTube API key)
- Two remote routines armed (Monday Atlas verification + May 14 Firecrawl check)
- Atlas M8 Mission Control dashboard deployed at agentshq.boubacarbarry.com/atlas (not yet verified by me)

READ FIRST (in this order):
1. docs/handoff/2026-04-26-weekend-handoff.md (this is your full context)
2. docs/AGENT_SOP.md (shared rules; especially the orchestrator.py sunset hard rule)
3. docs/roadmap/atlas.md and docs/roadmap/studio.md (latest session log entries at the bottom)
4. C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\MEMORY.md (links to project + feedback memory)

DO NOT:
- Recreate orchestrator/orchestrator.py. It was deleted 2026-04-25 in commit 4d1aeb3. The codebase is modular now: app.py, engine.py, handlers.py, handlers_chat.py, state.py, constants.py, scheduler.py, heartbeat.py. Full import map in project_orchestrator_sunset.md memory entry.
- Use em dashes anywhere. Pre-commit hook blocks them.
- Skip Sankofa Council on plans with new modules, autonomous behavior, or infra changes. Per feedback_sankofa_major_plans.md.
- Push to VPS without docker cp of changed files. orc-crewai is NOT volume-mounted. Per feedback_container_file_sync.md.

WEEKEND PRIORITIES (only 3, in order):
1. Monday 2026-04-27 around 07:30 MT, verify the first auto-publish fired correctly. Quick check: ssh root@72.60.209.109 "docker logs orc-crewai --since 1h | grep -E 'auto_publisher|BLOTATO'". Expected: tick done posted=1. Telegram alert in Boubacar's chat.
2. Provision Google Cloud YouTube Data API v3 key. Add to VPS .env as YOUTUBE_API_KEY. Flip studio.enabled=True in /root/agentsHQ/data/autonomy_state.json. docker restart. Manual tick to verify candidates land in the Studio Pipeline Notion DB.
3. Verify Atlas M8 Mission Control dashboard at agentshq.boubacarbarry.com/atlas works end-to-end. PIN gates, 6 cards populate, htmx 30s polling refreshes, action layer toggles Griot.

The handoff doc has step-by-step bash commands for each. Just follow them.

WHAT YOU DO NOT NEED TO DO:
- Any new feature work
- Studio M2 brand identity (defer to weekday)
- First Generation Money channel creation (M2 task)
- Monetization wiring

If anything looks off, three escalation steps: read Telegram alerts, read Notion record Source Note, flip the relevant kill switch (commands in the handoff doc).
```

---

End of handoff. Three-way nsync at `2c2845c`. Sleep well.
