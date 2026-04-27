# Crew Contract: model_review_agent

**Status:** SIGNED
**Signed by:** Boubacar Barry
**Date:** 2026-04-26
**Ceiling:** $0.10 / run

## What this crew does

Runs every Sunday at 08:00 MT. Evaluates MODEL_REVIEW_CANDIDATES against 3 seed
posts from the Content Board using the leGriot quality rubric. Writes a report to
docs/reference/model-review-{date}.md and sends a Telegram summary.

If a challenger model beats the incumbent by >= 3 pts total across 3 seeds, emits
a routing change proposal to the approval_queue. Boubacar approves or rejects via
the existing Telegram Approve/Reject button flow.

## What this crew does NOT do

- Does NOT modify ROLE_CAPABILITY or any routing config.
- Does NOT write to autonomy_state.json.
- Does NOT publish or queue any content.
- Does NOT call any destructive API.

## Cost model

- 4 models x 3 seeds x 1 generation call ~= 12 litellm calls at ~$0.002 avg = ~$0.024
- 12 scoring calls (haiku-4.5) ~= $0.006
- Total per run: ~$0.03. Ceiling is $0.10 to allow headroom for retries.

## Observation period

This crew is low-risk (read-only + Telegram + approval_queue). No 7-day dry-run
required before enabling. Enable immediately after deploy.

## Kill switch

crew_name: model_review_agent
autonomy_state.json key: model_review_agent.enabled (default: false)
Flip via: Telegram toggle or /atlas dashboard

## Rollback

Tag: savepoint-pre-m11d-2026-04-26
Command: git checkout savepoint-pre-m11d-2026-04-26
