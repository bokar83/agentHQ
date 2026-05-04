# Handoff: Studio M4 Kickoff - 2026-05-03/04

## What shipped this session

### Social Launch Kits
`docs/roadmap/studio/social-launch-kit/` - 3 files, one per channel.
Each has: IG + TikTok bio, avatar file path, link-in-bio strategy, 30-day warm-up protocol, handle checklist, Blotato ID placeholders.

Key warm-up rules baked in (2026 research):
- IG: no link before Day 7, 5-hashtag cap, Stories build trust score
- TikTok: 7-day observation phase, 1-2 posts/day, same IP/device/time window

### Blotato Publisher
`orchestrator/studio_blotato_publisher.py` - M4 publish tick.
- Scans Pipeline DB: Status=scheduled + ScheduledDate=today
- Publishes via Blotato API, flips to published
- Idempotency: flips to rendering BEFORE API call (double-post guard)
- TTL: records stuck in rendering >24h promoted to publish-failed
- Dry-run: `--dry-run` or `STUDIO_PUBLISHER_DRY_RUN=1`

Heartbeat: `studio-blotato-publisher` at 09:00 MT - registered in scheduler.py, live on VPS.

Verified: fires clean, 0 records (expected - no scheduled content yet).

### .env state (Blotato account IDs)
All 3 channels x 4 platforms wired EXCEPT 1stGen IG (Boubacar added during session - should be set now).
YT: 35697 / 35696 / 35698
TikTok: 40989 / 40987 / 40994
IG Baobab: 45174, IG Catalyst: 45176, IG 1stGen: check .env

### IG account status
- `under_thebaobab`: live
- `aicatalyst_official`: submitted selfie, review pending
- `firstgenerationmoney_`: review pending

TikTok: all 3 created by Boubacar, IDs in .env.

## What's uncommitted (not this session's work)
M3 production files (studio_production_crew.py, studio_composer.py, etc.), Dockerfile, CLAUDE.md updates, roadmap/compass changes - all pre-existing M3 work. Next session should commit these with proper M3 context.

## What's next
1. M3 dry-run test is running (QA crew -> production crew -> dry-run)
2. When first Pipeline DB record reaches Status=scheduled + today's date, publisher fires at 09:00 MT
3. M4 ships when first auto-post confirms live

## Env var to check
`BLOTATO_1STGEN_INSTAGRAM_ACCOUNT_ID` - Boubacar added during session. Verify it's in VPS .env.
