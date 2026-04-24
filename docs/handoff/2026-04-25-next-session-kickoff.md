# Next Session Kickoff: First Unsupervised Griot Cycle

**Previous session closed:** 2026-04-24 at hour ~12.5 (hard stop was 14)
**Previous session handoff:** `docs/handoff/2026-04-24-full-autonomy-day-shipped.md`
**Session intent:** observe the first overnight autonomous fire, then pick one item from the candidate queue.

## State at session open

Content pipeline is live on VPS:
- `uvicorn app:app` running from `db6fb22` on main
- 6 heartbeat wakes registered
- `griot.enabled=true, dry_run=true` in `/root/agentsHQ/data/autonomy_state.json`
- First queued post: "One constraint nobody has named yet" (X) scheduled for 2026-04-27 Monday
- Error monitor cron `*/15 * * * *` on VPS

## First 10 minutes: observe Friday + Monday fires

1. **Friday 07:00 MT griot-morning fire** (happened or will happen depending on when the next session opens):
   - Did the wake fire? Check `docker logs orc-crewai --since 24h | grep griot-morning`
   - Did it propose a candidate? Check `approval_queue` for rows with `ts_created > yesterday` and `crew_name='griot'`
   - Did Boubacar receive the Telegram preview? (Ask him)

2. **Friday 07:30 MT publish-brief fire**:
   - Did the brief send? Check `docker logs | grep publish_brief_tick`
   - Did the message land in his Telegram? (Ask him)
   - Since Friday shouldn't have any Queued-today rows (the first post is scheduled Monday), it should be the "empty brief" heads-up.

3. **Monday 07:00 MT + 07:30 MT** (if the session opens after Monday):
   - Monday is the first real publication day. Monday 07:30 brief should include "One constraint nobody has named yet" with the X share URL.
   - If he published it, Notion Status should flip from Queued -> Posted (he does this manually today; Phase 4 could automate).

## Open candidates for this session (in priority order)

Pick ONE, not all. Each is a focused 1-3 hour build. Run the Council before starting.

### Option A: Flip queued -> posted automation (revenue-nearest, 60-90 min)

When Boubacar publishes a post using the morning brief's share URL, the Notion record stays at Status=Queued because nothing tells Notion "the post went live." He has to manually flip it to Posted. Three approaches:

1. **Add a Telegram `/posted <queue_id>` command** that flips Notion status. One line of human work reported back to the bot.
2. **Add a "Mark Posted" button** inside the morning brief's share URL message. Callback_query handler updates Notion. Slightly nicer UX.
3. **Auto-flip on a 24-hour timer** after Scheduled Date. Risky if he forgets to publish - posts that didn't actually go out would be marked Posted.

Recommendation: option 2. It leverages the existing callback_query substrate shipped in Phase 1. Cost: ~90 min + tests.

### Option B: Full Concierge crew (Phase 4 proper)

The error_monitor.sh shell cron is the smoke alarm. The full Concierge crew reads alerts, groups errors by signature, uses Haiku to propose a fix, enqueues to approval_queue. Cost: ~2-3 hours. Worth it only if error_monitor has been firing on real issues in the week.

### Option C: Blotato auto-publisher (if Boubacar decides to pay)

If he's willing to sign up for Blotato at ~$9/mo:
- Sign up
- Get API key
- Configure credential in n8n
- Activate workflow `6XEaB5k7Kz4ubEck` "RN | Notion Social Media Posting via Blotato (n5)"
- Point it at the Content Board query: Status=Queued AND Scheduled Date=today
- Test with one post

Cost: ~60 min if Blotato cooperates. This turns today's manual-one-tap publish into true auto-publish on Scheduled Date.

### Option D: Phase 6 Hunter (blocked until May 6)

Per `project_hunter_upgrade.md` the Hunter.io decision revisits no earlier than 2026-05-06. Do not start this before then.

### Option E: Phase 5 Chairman (blocked until ~2026-05-08)

Needs 2 weeks of approval_queue + task_outcomes data. Starts making sense around 2026-05-08. Pre-5-08 attempts would produce noise, not signal.

### Option F: Revenue work (not autonomy)

The autonomy layer is now operational. Next sessions can legitimately pivot back to revenue: pipeline building (LinkedIn + BNI + South Valley Chamber per `project_pipeline_playbook.md`), discovery call prep, content review, SEO. The autonomy layer supports his work; it is not the work.

## What NOT to do next session

- Do not build Phase 3.5 drafter without first finding a genuinely bad Draft in the Content Board. The 2026-04-21 reorder already Sonnet-polished all 80 records. See `project_autonomy_layer.md` phase table for descope reason.
- Do not ship Phase 2.5 event wakes until a consumer crew (Hunter, event-driven Concierge) actually needs them.
- Do not ship a Phase 5 Chairman stub; let the data accumulate first.

## Health check at session open

Run these three in parallel before any build work:

```
# 1. Three-way sync (should all match)
git rev-parse HEAD
git rev-parse origin/main  # after git fetch origin
ssh root@agentshq.boubacarbarry.com "cd /root/agentsHQ && git rev-parse HEAD"

# 2. Container health + wake count
ssh root@agentshq.boubacarbarry.com 'docker ps --filter name=orc-crewai --format "{{.Status}}"'
# Expect: "Up XX hours (healthy)"

# 3. Error monitor log spot-check (did anything fire overnight?)
ssh root@agentshq.boubacarbarry.com 'tail -30 /var/log/error_monitor.log 2>&1'
```

If (1) is out of sync, run `/nsync`. If (2) is unhealthy, check container logs and rollback to savepoint. If (3) shows repeated alerts, start with Option B (Concierge) instead of any other item.

## Memory entries written this session

Newest first (all in `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\`):
- `reference_notion_content_board_schema.md` - Status is `select`, Arc Priority duplicates, verified types
- `reference_publisher_options.md` - Blotato / OAuth / Telegram-one-tap paths with tradeoffs
- `feedback_inspect_notion_schema_first.md` - always call get_database_schema before update_page
- `feedback_substrate_gates_before_callbacks.md` - safety checks go in heartbeat substrate, not callback bodies
- `feedback_rehearse_rollback_before_big_deploy.md` - time the rollback before flipping Dockerfile etc
- `feedback_operational_test_for_scope.md` - descope anything that doesn't change Boubacar's next morning

## Rollback ladder (newest to oldest)

- `savepoint-pre-shadow-backport-2026-04-24` - before the whole marathon day
- Any of the 5 PR merge commits in main history - normal `git revert <commit>` if one phase needs to be undone

## Key ops reminders

- Pause Griot: flip `enabled=false` in `/root/agentsHQ/data/autonomy_state.json` then `docker compose restart orchestrator`. Or `/pause_autonomy` from Telegram to kill ALL non-self-test crews instantly.
- Telegram commands live: `/queue /approve /reject /autonomy_status /heartbeat_status /cost /spend /outcomes griot 7`
- Boubacar's chat_id: `7792432594` (in .env as `TELEGRAM_CHAT_ID`)
- VPS: `agentshq.boubacarbarry.com` (IP `72.60.209.109`)
- Container: `orc-crewai`, bind `/root/agentsHQ/data:/app/data`, state persists

Good luck. Keep the Council discipline and the hour-14 stop rule.
