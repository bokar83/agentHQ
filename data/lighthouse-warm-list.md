# Lighthouse — Warm Utah Contact List

**Locked:** 2026-05-13 (Day 1, L1 Week 1)
**Owner:** Boubacar Barry
**Sprint window:** 2026-05-13 → 2026-05-17 (W1) + 2026-05-19 → 2026-05-24 (W2)
**Cycle:** one send per weekday at 10:00 MDT
**Cross-ref:** `docs/roadmap/lighthouse.md`, `data/inbound-signal-log.md`

---

## Channel + Bridge Matrix (locked L-R4 2026-05-16)

**Default channel:** LinkedIn DM first → personal email bridge (`bokar83@gmail.com`).
**Bridge timing:** 24hr for LinkedIn-active recipients · 48hr for cold-zone friends (6+ month silence).
**Bridge wording:** `Hey, sent you a quick note Friday - might have buried it in your inbox/LinkedIn. Same offer if you saw it.`
**Activity classifier:** LinkedIn-active = posted in last 14 days OR replied to a DM in last 30 days. Cold-zone = no posts last 90 days AND no DM activity last 90 days. Default LinkedIn-active if uncertain.

## Week 1 batch (V1 + V2 only — 5/13-5/17)

| # | Name | Tag | Channel | Bridge | Template | Send day | Status |
|---|------|-----|---------|--------|----------|----------|--------|
| 1 | Chad Burdette | close friend | text (legacy) → LinkedIn DM default fwd | 24hr | V1 | Wed 5/13 | sent 2026-05-13 ~09:50 (V1, text) · thursday check-in 2026-05-14 done (LinkedIn + text bridge) |
| 2 | Nate Tanner | close friend | LinkedIn DM | 24hr | V1 | Thu 5/14 | sent 2026-05-14 10:00 (V1, LinkedIn) · replied 2026-05-14 11:30 yes · audit delivered 2026-05-14 13:39 (3:21 early on 5 PM SLA) (msg 19e27fad4a12c892) |
| 3 | Chase Weed | close friend | email-personal (legacy) → LinkedIn DM default fwd | 48hr | V1 | Fri 5/15 | sent 2026-05-15 ~10:00 (V1, email-personal bokar83@gmail.com) - fired from Lagoon as remote-location stress test |
| 4 | Chris Whitaker | sister | LinkedIn DM or text (family) | 48hr | V1 | Mon 5/19 | open |
| 5 | Dan Jimenez | close friend + business owner | LinkedIn DM | 24hr | V1 or V2 | — | open |

**Notes:**
- Dan Jimenez is dual-tag. V1 if the closer-friend angle reads cleaner; V2 if the LinkedIn-audit-for-business-owner angle does. Pick the one that reads least transactional given the relationship.
- Chris Whitaker is family — V1 wording fine, but adjust opener to her natural voice (the "Need a favor" template was designed for friends/colleagues; works for a sister but check the tone). Family override: text or LinkedIn DM both fine; bridge still applies.
- Chad + Chase rows preserve legacy channel for the W1 send-of-record. Going forward (any re-touch, any new recipient), follow LinkedIn-DM-first default.

## Week 2 batch (V3 dormant + V4 referral-fresh — 5/19-5/24)

| # | Name | Tag | Channel | Bridge | Template | Send day | Status |
|---|------|-----|---------|--------|----------|----------|--------|
| 6 | Doug Worthington | dormant | LinkedIn DM | 48hr | V3 | Mon 5/19 | open |
| 7 | Benjamin Lambert | dormant | LinkedIn DM | 48hr | V3 | Tue 5/20 | open |
| 8 | Brody Horton | dormant + business owner | LinkedIn DM | 48hr | V3 or V2 (W1 if pulled up) | Wed 5/21 | open |
| 9 | Bruce Decaster | dormant | LinkedIn DM | 48hr | V3 | Thu 5/22 | open |
| 10 | Dawn Thompson | dormant | LinkedIn DM | 48hr | V3 | Fri 5/23 | open |

**Notes:**
- Brody Horton is a candidate to pull into W1 as a V2 business-owner send if you want to bank an audit-for-business signal early. Otherwise treat as W2 V3 dormant.
- W2 mixing rule (per strategy doc): mix V3 with V1/V2 leftovers; don't run an all-dormant week.
- All W2 recipients dormant = 48hr bridge default. Reclassify to 24hr only if recipient posts within W2 send window.

## Pre-flight checks before sending

1. Channel per matrix above. Default LinkedIn DM first → email-personal bridge. Override only for legacy continuations (Chad text, Chase email).
2. Confirm bridge timing classification (24hr LinkedIn-active vs 48hr cold-zone) before send. Set calendar nudge for bridge fire.
3. V1 says delivery by 5 PM same day. Only book that promise on names where you can write the audit same-day.
4. Audit needs LinkedIn profile URL ready before send — pre-pull during 09:50 sprint pre-read.

## Update rules

- After each send: flip Status from `open` → `sent YYYY-MM-DD`
- On reply: append `· replied YYYY-MM-DD · {yes|no|other}`
- On audit delivery: append `· audit delivered YYYY-MM-DD`
- On Thursday check-in: append `· checked-in YYYY-MM-DD`
- Mirror summary into `data/inbound-signal-log.md` at 21:00 ledger time

## Reciprocity / Brandon V5

Brandon V5 audit offer = Monday 2026-05-19. Not part of this 10. Keeps partnership ask cleanly separate from service offer.
