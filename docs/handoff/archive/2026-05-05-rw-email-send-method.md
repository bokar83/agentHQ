# Session Handoff - RW Email Send + Send Method Fix - 2026-05-05

## TL;DR

Tail end of the Reserve Works session. Email with the full RW decision package was sent to both addresses via gws CLI in the container after discovering the Gmail MCP only creates drafts. Send method is now documented in memory. Two critical operational rules locked: always send to both email addresses, always use gws not Gmail MCP.

## What was built / changed

- d:/tmp/build_email.py -- RFC 2822 email builder script (scp to VPS, run python3, copy raw to container, send via gws)
- C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\feedback_email_always_both.md -- updated with full 5-step gws send procedure + confirm rule
- C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\MEMORY.md -- line 7 updated to note "HOW to send" in the index entry

## Decisions made

- Gmail MCP `create_draft` is NOT a send. It parks in drafts. Never use it when Boubacar says "send."
- The correct send path: python3 build script on VPS host -> docker cp raw to container -> gws in container.
- Both email addresses required on every send: bokar83@gmail.com AND boubacar@catalystworks.consulting.
- Confirmed working: gws message ID 19df9f3598f239d4, labelIds includes SENT.

## What is NOT done

- The two draft emails from earlier in this session (before the gws fix) are sitting in Gmail drafts. They can be deleted.
- Hotel Club de Kipe rebuild has not started -- that is the next active project.

## Open questions

1. RW P2 vs P4 decision: Boubacar needs to answer within 30 days (by 2026-06-04).
2. Paper trading account: should be open by 2026-05-09 (Friday).

## Next session must start here

1. Check: did Boubacar open thinkorswim paper account by 2026-05-09?
2. Get P2 vs P4 answer (one sentence).
3. Start Hotel Club de Kipe rebuild -- brief at docs/handoff/hotelclubkipe-rebuild-prompt.md. Run /website-teardown then /design-audit before any code.

## Files changed this session

- d:/tmp/build_email.py (new, transient -- VPS send helper)
- memory/feedback_email_always_both.md (updated with gws send procedure)
- memory/MEMORY.md (line 7 updated)
- docs/handoff/2026-05-05-reserve-works-tab-shutdown.md (written earlier in session)
- docs/handoff/2026-05-05-rw-email-send-method.md (this file)
