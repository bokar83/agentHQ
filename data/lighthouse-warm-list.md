# Lighthouse — Warm Utah Contact List

**Locked:** 2026-05-13 (Day 1, L1 Week 1)
**Owner:** Boubacar Barry
**Sprint window:** 2026-05-13 → 2026-05-17 (W1) + 2026-05-19 → 2026-05-24 (W2)
**Cycle:** one send per weekday at 10:00 MDT
**Cross-ref:** `docs/roadmap/lighthouse.md`, `data/inbound-signal-log.md`

---

## Week 1 batch (V1 + V2 only — 5/13-5/17)

| # | Name | Tag | Template | Suggested send day | Status |
|---|------|-----|----------|---------------------|--------|
| 1 | Chad Burdette | close friend | V1 | Wed 5/13 | sent 2026-05-13 ~09:50 (V1, text) · thursday check-in 2026-05-14 done (LinkedIn + text bridge) |
| 2 | Nate Tanner | close friend | V1 | Thu 5/14 | sent 2026-05-14 10:00 (V1, LinkedIn) · replied 2026-05-14 11:30 yes · audit delivered 2026-05-14 13:39 (3:21 early on 5 PM SLA) (msg 19e27fad4a12c892) |
| 3 | Chase Weed | close friend | V1 | Fri 5/15 | sent 2026-05-15 ~10:00 (V1, text) - fired from Lagoon as remote-location stress test |
| 4 | Chris Whitaker | sister | V1 | Mon 5/19 | open |
| 5 | Dan Jimenez | close friend + business owner | V1 or V2 | — | open |

**Notes:**
- Dan Jimenez is dual-tag. V1 if the closer-friend angle reads cleaner; V2 if the LinkedIn-audit-for-business-owner angle does. Pick the one that reads least transactional given the relationship.
- Chris Whitaker is family — V1 wording fine, but adjust opener to her natural voice (the "Need a favor" template was designed for friends/colleagues; works for a sister but check the tone).

## Week 2 batch (V3 dormant + V4 referral-fresh — 5/19-5/24)

| # | Name | Tag | Template | Suggested send day | Status |
|---|------|-----|----------|---------------------|--------|
| 6 | Doug Worthington | dormant | V3 | Mon 5/19 | open |
| 7 | Benjamin Lambert | dormant | V3 | Tue 5/20 | open |
| 8 | Brody Horton | dormant + business owner | V3 or V2 (W1 if pulled up) | Wed 5/21 | open |
| 9 | Bruce Decaster | dormant | V3 | Thu 5/22 | open |
| 10 | Dawn Thompson | dormant | V3 | Fri 5/23 | open |

**Notes:**
- Brody Horton is a candidate to pull into W1 as a V2 business-owner send if you want to bank an audit-for-business signal early. Otherwise treat as W2 V3 dormant.
- W2 mixing rule (per strategy doc): mix V3 with V1/V2 leftovers; don't run an all-dormant week.

## Pre-flight checks before sending

1. Channel for each: text vs LinkedIn vs email. Default text unless they're a LinkedIn-first person.
2. V1 says delivery by 5 PM same day. Only book that promise on names where you can write the audit same-day.
3. Audit needs LinkedIn profile URL ready before send — pre-pull during 09:50 sprint pre-read.

## Update rules

- After each send: flip Status from `open` → `sent YYYY-MM-DD`
- On reply: append `· replied YYYY-MM-DD · {yes|no|other}`
- On audit delivery: append `· audit delivered YYYY-MM-DD`
- On Thursday check-in: append `· checked-in YYYY-MM-DD`
- Mirror summary into `data/inbound-signal-log.md` at 21:00 ledger time

## Reciprocity / Brandon V5

Brandon V5 audit offer = Monday 2026-05-19. Not part of this 10. Keeps partnership ask cleanly separate from service offer.
