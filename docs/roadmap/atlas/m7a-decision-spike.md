# Atlas M7a: Auto-Publish Decision Spike

**Type:** decision spike, not a build
**Time budget:** 30 minutes hands-on + 7-day Blotato trial period (passive)
**Decision date:** end of trial week (~2026-05-04 or earlier)
**Roadmap entry:** `docs/roadmap/atlas.md` § M7a

## What this is

A one-week trial of Blotato's $29/mo Starter tier (free for 7 days) to validate whether auto-publish to LinkedIn + X is worth $348/year before any code is written. Sankofa Council mandated this spike on 2026-04-25 after rejecting the original "build dormant today" plan. Reasons: (a) Blotato API contract is unknown, (b) account IDs are per-tenant and arrive only after signup, (c) Boubacar uses only 2 of Blotato's 8 platforms today, (d) "draft JSON in repo, import manually" pattern rots immediately.

## Pre-work before signing up

Read these once so the trial is efficient:

- `docs/roadmap/atlas.md` § M7a + M7b (the milestone definitions)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_publisher_options.md` (the 4-path comparison; verified pricing)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_notion_content_board_schema.md` (the schema Blotato will read from if M7b ships)

n8n workflows already on the server that touch Blotato:

| ID | Name | State | Status |
|---|---|---|---|
| `6XEaB5k7Kz4ubEck` | RN Notion Social Media Posting via Blotato (n5) | inactive | Old style: raw HTTP nodes, points at WRONG Notion DB ("Social Posts Planner" not Content Board), wrong field names. Do NOT adapt; rebuild instead. |
| `prGNumzMO5y5mTVY` | RN Blotato n8n node (n12) | inactive | Newer: native `@blotato/n8n-nodes-blotato.blotato` nodes. Reads from Google Sheets, NOT Notion. Reference for node syntax, not for our use case. |
| `y4vdiL4h6NC8ySj1` | RoboNuggets the new Blotato n8n node (n12) | inactive | Duplicate of `prGNumzMO5y5mTVY`. |

If M7b is greenlit after the trial, M7b builds a NEW workflow against the Content Board schema using native Blotato nodes (n12 style), reading from Notion (n5 style). Neither n5 nor n12 alone is the answer.

## Signup steps (~10 min)

1. Go to <https://blotato.com> and click Start Free Trial on the Starter plan.
2. Connect LinkedIn. Note the Blotato accountId for LinkedIn.
3. Connect X (Twitter). Note the Blotato accountId for X.
4. From Blotato dashboard, generate an API key. Save it locally (do NOT commit to git, do NOT add to `.env` until M7b ships).
5. Open the Blotato API docs (link in dashboard) and read the LinkedIn and X publish endpoints. Capture the request shape: required fields, accountId placement, content format, media handling, rate limit headers.

Output of this step: 2 accountIds, 1 API key, 1 page of API contract notes.

## Smoke test (~15 min)

Use Blotato's UI directly (NOT n8n, NOT agentsHQ). Goal: prove auto-publish works end-to-end on the platforms you care about.

1. **LinkedIn manual post.** Paste a real draft from the Content Board (use queue #3 if it has not been published yet, or any other Ready post). Schedule for "publish now." Confirm the post appears on LinkedIn within 60 seconds. Verify formatting, line breaks, hashtags, link unfurl.
2. **X manual post.** Same, but for an X-format post. Confirm character count enforcement, link shortening, posting latency.
3. **Edge cases.** Try one post that is too long for X (should error or truncate). Try one with an emoji-heavy hook. Try one with a link in the first line. Note Blotato's behavior on each.
4. **Latency check.** Note how long Blotato took from "publish" to "live on platform" in each case. M7b's UX assumes ~1 minute. If Blotato regularly takes 5+ min, the design changes.

If any of the 3 platforms fails the smoke test, the trial decision is "drop Blotato, switch M7b to OAuth path."

## Trial-week observation (~5 min/day for 7 days)

After day 1's hands-on test, let it run. Each day, jot one line in a trial log:

- Did the daily post on each platform succeed?
- Any flakiness? Errors? Manual interventions needed?
- Anything Blotato did unexpectedly (auto-truncation, wrong link preview, comment threading)?

If you publish via the brief's tap-share-URL pattern instead during the trial week (not via Blotato), that's fine; the goal of the trial is to evaluate Blotato's unsupervised behavior over a week, which means you need to USE it for a week.

## Decision matrix at trial-end

Fill in honestly:

| Criterion | Pass threshold | Trial result |
|---|---|---|
| LinkedIn posts succeed | 7/7 days | |
| X posts succeed | 7/7 days | |
| Latency from publish to live | <2 min average | |
| Format fidelity (line breaks, hashtags, links) | 100% acceptable | |
| Any data loss or duplicate post | 0 incidents | |
| API contract is documented + stable | Yes | |
| accountIds unchanged across trial | Yes | |
| Boubacar's confidence to leave it unattended | Yes | |

**All Yes / pass:** keep the sub at $29/mo, M7b shipped against verified API behavior. ~60-90 min build.

**Any No on rows 1-5:** drop Blotato. Reframe M7b as direct LinkedIn + X OAuth via n8n native nodes. Multi-day OAuth approval cycles per platform. $0/mo ongoing. Build cost higher (90-120 min after approvals land).

**Yes on rows 1-5 but No on 6-8:** keep Blotato but build M7b with extra defensive logic (retry, idempotency, drift detection). Still cheaper than OAuth.

## Cancellation pre-mortem

If you decide to drop Blotato:
- Cancel the sub before day 7 (otherwise auto-billed $29).
- Do NOT delete the Blotato accountIds you connected; leave them dormant in case a future month brings the case back.
- Save your API contract notes to `docs/roadmap/atlas/m7a-trial-notes.md` (create on cancel) so a future revisit does not re-do the spike.

## What NOT to do during the trial

- Do NOT activate either of the existing inactive n8n Blotato workflows. They point at wrong databases and would post against the wrong content.
- Do NOT add `BLOTATO_API_KEY` to `.env` or to the VPS env file. The orchestrator must not see it until M7b actually ships.
- Do NOT modify any existing n8n workflow. Read-only inspection only, per the n8n hard rule.
- Do NOT spend the $29 if any smoke test fails on day 1.

## Hand-off back to atlas roadmap

When trial decision is made:

- Append a session-log entry to `docs/roadmap/atlas.md` summarizing the trial result.
- Update M7a status: `SHIPPED` (decision made) regardless of which way the decision went.
- Update M7b status: either `READY` (build approved) or `BLOCKED` (path changed to OAuth, multi-day delay).
- If keep: M7b spec gets written next session, build follows the spec.
- If drop: M7b spec is rewritten for the OAuth path.

Either way, M7a is a one-shot milestone. After the trial decision, this file becomes a historical artifact.
